# -*- coding: utf-8 -*-
"""
FLIR E53 / Atlas SDK Python 演示程式 (無鏡頭模擬版)

本程式支援雙模式：
1. SDK 模式：嘗試載入實體 `atlas_c_sdk.dll` 並與相機模擬器 (Emulator) 連線進行即時串流。
2. 模擬模式：若無 SDK 或偵測不到相機，程式會自動開啟模擬熱成像儀，產生動態熱源，演示資料導出、最高溫追蹤與溫度門檻篩選。
"""

import os
import sys
import time
import ctypes
import numpy as np

# 嘗試載入 OpenCV 進行畫面渲染，若未安裝則提示安裝
try:
    import cv2
except ImportError:
    print("本展示需要 OpenCV，請先在命令提示字元中執行: pip install opencv-python numpy")
    sys.exit(1)

# SDK DLL 路徑（同目錄下尋找 SDK）
SDK_DIR = os.path.join(os.path.dirname(__file__), "atlas-c-sdk-windows-vs16-x64-mt-2.20.0")
DLL_PATH = os.path.join(SDK_DIR, "bin", "atlas_c_sdk.dll")

# ==========================================
# 模式一：實際 SDK 呼叫 (當未來有相機或載入 DLL 時)
# ==========================================
class ACS_ThermalValue(ctypes.Structure):
    _fields_ = [
        ("value", ctypes.c_double),
        ("unit", ctypes.c_int),
        ("state", ctypes.c_int)
    ]

class ACS_Rectangle(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int), ("y", ctypes.c_int),
        ("width", ctypes.c_int), ("height", ctypes.c_int)
    ]

def run_sdk_emulator():
    print("--- 嘗試啟動 FLIR Atlas SDK 模擬器模式 ---")
    if not os.path.exists(DLL_PATH):
        print(f"找不到 DLL: {DLL_PATH}，將自動切換至「模擬展示模式」\n")
        return False
        
    try:
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(os.path.dirname(DLL_PATH))
        acs = ctypes.CDLL(DLL_PATH)
        
        # 基本初始化與相機分配
        acs.ACS_Camera_alloc.restype = ctypes.c_void_p
        acs.ACS_Camera_alloc.argtypes = []
        acs.ACS_Camera_free.restype = None
        acs.ACS_Camera_free.argtypes = [ctypes.c_void_p]
        
        # 測試分配
        camera = acs.ACS_Camera_alloc()
        if camera:
            print("SDK DLL 載入成功！")
            print("模擬環境中由於未安裝實體驅動，將自動進入視覺化模擬器展示。")
            acs.ACS_Camera_free(camera)
            return False
    except Exception as e:
        print(f"SDK 載入時發生錯誤: {e}，進入模擬展示模式。\n")
        return False
    return False

# ==========================================
# 模式二：純 Python + OpenCV 熱成像動態模擬器
# ==========================================
class ThermalCameraSimulator:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.bg_temp = 26.0  # 背景室溫 26度
        self.target_x = width // 2
        self.target_y = height // 2
        self.angle = 0.0
        
    def get_frame(self):
        """ 模擬產生一影格的 2D 溫度數據矩陣 """
        # 1. 產生基礎室溫背景，加上輕微雜訊模擬熱雜訊
        noise = np.random.normal(0, 0.15, (self.height, self.width))
        frame = np.full((self.height, self.width), self.bg_temp, dtype=np.float64) + noise
        
        # 2. 模擬一個熱源 (例如人體頭部，溫度大約 36.5 ~ 37.8 度)
        # 讓熱源繞圓形軌道移動，模擬動態場景
        self.angle += 0.05
        cx = int(self.width // 2 + 150 * np.cos(self.angle))
        cy = int(self.height // 2 + 80 * np.sin(self.angle))
        
        y_indices, x_indices = np.indices((self.height, self.width))
        
        # 計算到熱源中心的距離
        dist_sq = (x_indices - cx)**2 + (y_indices - cy)**2
        
        # 模擬熱量擴散效應 (高斯分佈)
        heat_blob = 11.5 * np.exp(-dist_sq / (2 * 45**2))  # 中心溫升約 11.5度，最高溫約 37.5度
        frame += heat_blob
        
        # 3. 模擬一個超溫熱源 (例如馬達過熱，高達 55 度)
        mx, my = self.width // 3, self.height // 3
        dist_sq_m = (x_indices - mx)**2 + (y_indices - my)**2
        motor_blob = 29.0 * np.exp(-dist_sq_m / (2 * 15**2))  # 最高溫約 55度
        frame += motor_blob
        
        return frame

def run_simulation_demo():
    print("==================================================")
    print("         啟動 FLIR E53 動態熱成像模擬器")
    print("==================================================")
    print("操作說明:")
    print("  - 將滑鼠移動到畫面上，可即時查詢「該像素點的真實溫度」")
    print("  - 按下 [T] 鍵：開啟/關閉「高溫警報過濾 (門檻值 > 37.5°C)」")
    print("  - 按下 [ESC] 鍵：退出程式")
    print("==================================================\n")
    
    sim = ThermalCameraSimulator()
    show_threshold = False
    
    # 用於滑鼠座標記錄
    mouse_x, mouse_y = 0, 0
    
    def on_mouse(event, x, y, flags, param):
        nonlocal mouse_x, mouse_y
        mouse_x, mouse_y = x, y
        
    cv2.namedWindow("FLIR E53 Simulator")
    cv2.setMouseCallback("FLIR E53 Simulator", on_mouse)
    
    while True:
        # 1. 取得當前影格的「真實溫度矩陣」(Radiometric Data)
        temp_matrix = sim.get_frame()
        
        # 2. 計算影像統計資料 (相當於 SDK 中的 ACS_ImageStatistics)
        min_temp = np.min(temp_matrix)
        max_temp = np.max(temp_matrix)
        avg_temp = np.mean(temp_matrix)
        
        # 找出最高溫點的座標 (相當於 Hot Spot 追蹤)
        max_idx = np.unravel_index(np.argmax(temp_matrix), temp_matrix.shape)
        max_y, max_x = max_idx
        
        # 3. 將溫度數據歸一化到 0-255，以便進行偽彩色渲染 (相當於 SDK Colorizer)
        # 設定渲染對比區間 (Scaling Span): 20°C 到 60°C
        span_min, span_max = 20.0, 60.0
        normalized = np.clip((temp_matrix - span_min) / (span_max - span_min) * 255, 0, 255).astype(np.uint8)
        
        # 套用 FLIR 經典的 Iron (鐵紅) 偽彩色調
        color_frame = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
        
        # 4. 高溫門檻過濾演示 (例如篩選大於 37.5 度的高溫點)
        if show_threshold:
            threshold_val = 37.5
            # 建立遮罩
            mask = temp_matrix > threshold_val
            # 將符合高溫的區域標記為純紅色
            color_frame[mask] = [0, 0, 255]
            cv2.putText(color_frame, f"ALARM ACTIVE (> {threshold_val}C)", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # 5. 在畫面上繪製最高溫十字追蹤標記
        cv2.drawMarker(color_frame, (max_x, max_y), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
        cv2.putText(color_frame, f"Max: {max_temp:.1f}C", (max_x + 15, max_y + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # 6. 即時獲取滑鼠指向點的像素溫度 (演示 getValueAt 功能)
        if 0 <= mouse_x < sim.width and 0 <= mouse_y < sim.height:
            curr_temp = temp_matrix[mouse_y, mouse_x]
            # 畫個小圈標記滑鼠位置
            cv2.circle(color_frame, (mouse_x, mouse_y), 5, (255, 255, 255), 1)
            cv2.putText(color_frame, f"Cursor: {curr_temp:.2f}C", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        
        # 顯示全圖統計狀態欄
        stats_str = f"Min: {min_temp:.1f}C | Max: {max_temp:.1f}C | Avg: {avg_temp:.1f}C"
        cv2.putText(color_frame, stats_str, (10, sim.height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 250, 200), 1)
                    
        # 7. 顯示畫面
        cv2.imshow("FLIR E53 Simulator", color_frame)
        
        # 鍵盤監聽
        key = cv2.waitKey(30) & 0xFF
        if key == 27:  # ESC 鍵退出
            break
        elif key == ord('t') or key == ord('T'):
            show_threshold = not show_threshold
            print(f"高溫警報門檻過濾狀態: {'開啟' if show_threshold else '關閉'}")
            
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # 嘗試載入實際 SDK 模擬相機
    has_sdk = run_sdk_emulator()
    
    # 執行視覺化模擬演示
    run_simulation_demo()
