# -*- coding: utf-8 -*-
"""
測試腳本 1: 讀取熱成像照片並導出溫度數據 (test_rjpeg.py)
用途: 測試讀取從 E53 記憶卡導出的 Radiometric JPEG (.jpg) 照片，並輸出全圖溫度統計。
"""

import os
import sys
import ctypes
import numpy as np

# 設定 SDK 核心 DLL 的相對路徑（同目錄下尋找 SDK）
SDK_DIR = os.path.join(os.path.dirname(__file__), "atlas-c-sdk-windows-vs16-x64-mt-2.20.0")
DLL_PATH = os.path.join(SDK_DIR, "bin", "atlas_c_sdk.dll")

if not os.path.exists(DLL_PATH):
    print(f"錯誤: 找不到 DLL 檔案，請確認 SDK 資料夾名稱是否正確。")
    print(f"預期路徑: {DLL_PATH}")
    sys.exit(1)

# Windows 下加載 DLL 及其相依庫
if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(os.path.dirname(DLL_PATH))

# 使用標準 C 呼叫約定 (CDLL) 加載 SDK
acs = ctypes.CDLL(DLL_PATH)

# --- 定義資料結構 ---
class ACS_ThermalValue(ctypes.Structure):
    _fields_ = [
        ("value", ctypes.c_double),
        ("unit", ctypes.c_int),
        ("state", ctypes.c_int),
    ]

class ACS_Rectangle(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("width", ctypes.c_int),
        ("height", ctypes.c_int),
    ]

# --- 宣告 SDK 函式原型 ---
acs.ACS_ThermalImage_alloc.restype = ctypes.c_void_p
acs.ACS_ThermalImage_alloc.argtypes = []

acs.ACS_ThermalImage_free.restype = None
acs.ACS_ThermalImage_free.argtypes = [ctypes.c_void_p]

acs.ACS_NativeString_createFrom.restype = ctypes.c_void_p
acs.ACS_NativeString_createFrom.argtypes = [ctypes.c_char_p]

acs.ACS_NativeString_get.restype = ctypes.c_wchar_p
acs.ACS_NativeString_get.argtypes = [ctypes.c_void_p]

acs.ACS_NativeString_free.restype = None
acs.ACS_NativeString_free.argtypes = [ctypes.c_void_p]

acs.ACS_ThermalImage_openFromFile.restype = None
acs.ACS_ThermalImage_openFromFile.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]

acs.ACS_ThermalImage_setTemperatureUnit.restype = None
acs.ACS_ThermalImage_setTemperatureUnit.argtypes = [ctypes.c_void_p, ctypes.c_int]

acs.ACS_ThermalImage_getWidth.restype = ctypes.c_int
acs.ACS_ThermalImage_getWidth.argtypes = [ctypes.c_void_p]

acs.ACS_ThermalImage_getHeight.restype = ctypes.c_int
acs.ACS_ThermalImage_getHeight.argtypes = [ctypes.c_void_p]

acs.ACS_ThermalImage_getValues.restype = None
acs.ACS_ThermalImage_getValues.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_double),
    ctypes.c_size_t,
    ctypes.POINTER(ACS_Rectangle),
]

acs.ACS_ThermalImage_getValueAt.restype = ACS_ThermalValue
acs.ACS_ThermalImage_getValueAt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

acs.ACS_getLastErrorMessage.restype = ctypes.c_char_p
acs.ACS_getLastErrorMessage.argtypes = []

# 常數定義
ACS_TemperatureUnit_celsius = 0

def last_error_message():
    """ 獲取 SDK 的最後錯誤訊息，若無錯誤則回傳 None """
    msg = acs.ACS_getLastErrorMessage()
    if msg:
        decoded = msg.decode("utf-8", errors="replace")
        return decoded if decoded.strip() else None
    return None

def main(image_path):
    if not os.path.isfile(image_path):
        print(f"錯誤: 找不到圖片檔案: {image_path}")
        sys.exit(1)

    print(f"載入圖片: {image_path}")
    
    # 1. 分配熱影像記憶體
    image = acs.ACS_ThermalImage_alloc()
    if not image:
        raise RuntimeError("無法分配 ACS_ThermalImage 空間")

    # 2. 將 Python 字串轉換為 C 原生寬字元字串路徑
    native_path = acs.ACS_NativeString_createFrom(image_path.encode("utf-8"))
    if not native_path:
        acs.ACS_ThermalImage_free(image)
        raise RuntimeError("無法轉換原生路徑字串")

    try:
        # 3. 開啟熱成像圖片
        acs.ACS_ThermalImage_openFromFile(image, acs.ACS_NativeString_get(native_path))
        err = last_error_message()
        if err:
            raise RuntimeError(f"開啟檔案失敗: {err}")

        # 4. 設定溫度單位為攝氏度
        acs.ACS_ThermalImage_setTemperatureUnit(image, ACS_TemperatureUnit_celsius)

        # 5. 讀取影像尺寸
        width = acs.ACS_ThermalImage_getWidth(image)
        height = acs.ACS_ThermalImage_getHeight(image)
        if width <= 0 or height <= 0:
            raise RuntimeError(f"無效的影像尺寸: {width}x{height}")

        print(f"影像解析度: {width} x {height}")

        # 6. 導出全圖溫度矩陣
        pixel_count = width * height
        values = (ctypes.c_double * pixel_count)()
        rect = ACS_Rectangle(0, 0, width, height)

        acs.ACS_ThermalImage_getValues(image, values, ctypes.sizeof(values), ctypes.byref(rect))
        err = last_error_message()
        if err:
            raise RuntimeError(f"讀取溫度矩陣失敗: {err}")

        # 轉成 Numpy 陣列進行科學統計
        all_values = np.array(values)
        min_temp = np.min(all_values)
        max_temp = np.max(all_values)
        avg_temp = np.mean(all_values)

        # 7. 讀取中心像素溫度
        center_x = width // 2
        center_y = height // 2
        center_value = acs.ACS_ThermalImage_getValueAt(image, center_x, center_y)

        # 8. 輸出結果
        print("\n================ 溫度數據分析 ================")
        print(f"全圖最低溫: {min_temp:.2f} °C")
        print(f"全圖最高溫: {max_temp:.2f} °C")
        print(f"全圖平均溫: {avg_temp:.2f} °C")
        
        if center_value.state == 1: # OK
            print(f"中心像素 ({center_x}, {center_y}) 溫度: {center_value.value:.2f} °C")
        else:
            print(f"中心像素溫度狀態異常 (狀態碼: {center_value.state})")
        print("============================================\n")

    finally:
        # 9. 釋放資源，避免記憶體洩漏
        acs.ACS_NativeString_free(native_path)
        acs.ACS_ThermalImage_free(image)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用說明: python test_rjpeg.py <FLIR_圖片路徑.jpg>")
        sys.exit(1)

    main(sys.argv[1])
