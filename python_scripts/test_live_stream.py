# -*- coding: utf-8 -*-
"""
測試腳本 2: 即時熱成像串流與測溫 (test_live_stream.py)
用途: 連接實體相機 (E53 USB Type-C) 或 模擬器，進行即時溫度串流並印出每秒的統計數據。
"""

import os
import sys
import time
import ctypes

# 設定 SDK 核心 DLL 的相對路徑（同目錄下尋找 SDK）
SDK_DIR = os.path.join(os.path.dirname(__file__), "atlas-c-sdk-windows-vs16-x64-mt-2.20.0")
DLL_PATH = os.path.join(SDK_DIR, "bin", "atlas_c_sdk.dll")

if not os.path.exists(DLL_PATH):
    print(f"錯誤: 找不到 DLL 檔案，請確認 SDK 資料夾名稱是否正確。")
    print(f"預期路徑: {DLL_PATH}")
    sys.exit(1)

if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(os.path.dirname(DLL_PATH))

acs = ctypes.CDLL(DLL_PATH)

# --- 定義資料結構與常數 ---
class ACS_ThermalValue(ctypes.Structure):
    _fields_ = [
        ("value", ctypes.c_double),
        ("unit", ctypes.c_int),
        ("state", ctypes.c_int),
    ]

class ACS_Rectangle(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int), ("y", ctypes.c_int),
        ("width", ctypes.c_int), ("height", ctypes.c_int)
    ]

# 核心常數 (定義在 enum.h 與 identity.h)
ACS_CommunicationInterface_usb = 0x01
ACS_CommunicationInterface_emulator = 0x08
ACS_TemperatureUnit_celsius = 0

# --- 宣告函式原型 ---
acs.ACS_Discovery_alloc.restype = ctypes.c_void_p
acs.ACS_Discovery_alloc.argtypes = []

acs.ACS_Discovery_free.restype = None
acs.ACS_Discovery_free.argtypes = [ctypes.c_void_p]

acs.ACS_DiscoveredCamera_getIdentity.restype = ctypes.c_void_p
acs.ACS_DiscoveredCamera_getIdentity.argtypes = [ctypes.c_void_p]

acs.ACS_DiscoveredCamera_getDisplayName.restype = ctypes.c_char_p
acs.ACS_DiscoveredCamera_getDisplayName.argtypes = [ctypes.c_void_p]

acs.ACS_Identity_copy.restype = ctypes.c_void_p
acs.ACS_Identity_copy.argtypes = [ctypes.c_void_p]

acs.ACS_Identity_free.restype = None
acs.ACS_Identity_free.argtypes = [ctypes.c_void_p]

acs.ACS_Camera_alloc.restype = ctypes.c_void_p
acs.ACS_Camera_alloc.argtypes = []

acs.ACS_Camera_free.restype = None
acs.ACS_Camera_free.argtypes = [ctypes.c_void_p]

# 掃描 API 宣告
acs.ACS_Discovery_scan.restype = None
acs.ACS_Discovery_scan.argtypes = [
    ctypes.c_void_p, ctypes.c_int, 
    ctypes.c_void_p, ctypes.c_void_p, 
    ctypes.c_void_p, ctypes.c_void_p, 
    ctypes.c_void_p
]

# 相機連線與串流 API 宣告
acs.ACS_Camera_connect.restype = ctypes.c_int  # 回傳 ACS_Error
acs.ACS_Camera_connect.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, 
    ctypes.c_void_p, ctypes.c_void_p, 
    ctypes.c_void_p, ctypes.c_void_p
]

acs.ACS_Camera_disconnect.restype = None
acs.ACS_Camera_disconnect.argtypes = [ctypes.c_void_p]

acs.ACS_Camera_getStreamCount.restype = ctypes.c_size_t
acs.ACS_Camera_getStreamCount.argtypes = [ctypes.c_void_p]

acs.ACS_Camera_getStream.restype = ctypes.c_void_p
acs.ACS_Camera_getStream.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

acs.ACS_Stream_isThermal.restype = ctypes.c_bool
acs.ACS_Stream_isThermal.argtypes = [ctypes.c_void_p]

# Stream 控制
acs.ACS_Stream_start.restype = None
acs.ACS_Stream_start.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

acs.ACS_Stream_stop.restype = None
acs.ACS_Stream_stop.argtypes = [ctypes.c_void_p]

# Streamer 與 Renderer
acs.ACS_ThermalStreamer_alloc.restype = ctypes.c_void_p
acs.ACS_ThermalStreamer_alloc.argtypes = [ctypes.c_void_p]

acs.ACS_ThermalStreamer_asStreamer.restype = ctypes.c_void_p
acs.ACS_ThermalStreamer_asStreamer.argtypes = [ctypes.c_void_p]

acs.ACS_Streamer_asRenderer.restype = ctypes.c_void_p
acs.ACS_Streamer_asRenderer.argtypes = [ctypes.c_void_p]

acs.ACS_Streamer_free.restype = None
acs.ACS_Streamer_free.argtypes = [ctypes.c_void_p]

acs.ACS_Renderer_update.restype = None
acs.ACS_Renderer_update.argtypes = [ctypes.c_void_p]

# 影像數據攔截 API
acs.ACS_ThermalStreamer_withThermalImage.restype = None
acs.ACS_ThermalStreamer_withThermalImage.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

acs.ACS_ThermalImage_getWidth.restype = ctypes.c_int
acs.ACS_ThermalImage_getWidth.argtypes = [ctypes.c_void_p]

acs.ACS_ThermalImage_getHeight.restype = ctypes.c_int
acs.ACS_ThermalImage_getHeight.argtypes = [ctypes.c_void_p]

acs.ACS_ThermalImage_getValueAt.restype = ACS_ThermalValue
acs.ACS_ThermalImage_getValueAt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

# --- 回呼函式 (Callbacks) 類型定義 ---
ON_CAMERA_FOUND = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
ON_DISCOVERY_ERROR = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
ON_DISCONNECTED = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
ON_IMAGE_RECEIVED = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_ulong))
ON_STREAM_ERROR = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
WITH_THERMAL_IMAGE = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)

# 全局變數用於儲存掃描到的相機標誌
found_camera_identity = None

# --- 實作回呼邏輯 ---
def py_on_camera_found(discovered_camera, context):
    global found_camera_identity
    name = acs.ACS_DiscoveredCamera_getDisplayName(discovered_camera).decode('utf-8', errors='replace')
    print(f"尋找到相機: {name}")
    identity = acs.ACS_DiscoveredCamera_getIdentity(discovered_camera)
    found_camera_identity = acs.ACS_Identity_copy(identity)

def py_on_discovery_error(interface, error_struct, context):
    print(f"掃描界面 {interface} 時出錯。")

def py_on_disconnected(error_struct, context):
    print("相機連線中斷！")

def py_on_image_received(counter_ptr):
    counter_ptr.contents.value += 1

def py_on_stream_error(error_struct, context):
    pass

# 將 Python 函式打包為 C Callback
c_on_camera_found = ON_CAMERA_FOUND(py_on_camera_found)
c_on_discovery_error = ON_DISCOVERY_ERROR(py_on_discovery_error)
c_on_disconnected = ON_DISCONNECTED(py_on_disconnected)
c_on_image_received = ON_IMAGE_RECEIVED(py_on_image_received)
c_on_stream_error = ON_STREAM_ERROR(py_on_stream_error)

# 即時影格數據處理回呼
last_log_time = 0
def py_with_thermal_image(thermal_image, context):
    global last_log_time
    now = time.time()
    
    if now - last_log_time >= 1.0:
        w = acs.ACS_ThermalImage_getWidth(thermal_image)
        h = acs.ACS_ThermalImage_getHeight(thermal_image)
        cx, cy = w // 2, h // 2
        
        center_val = acs.ACS_ThermalImage_getValueAt(thermal_image, cx, cy)
        if center_val.state == 1: # OK
            print(f"[即時測溫] 解析度: {w}x{h} | 中心點 ({cx}, {cy}) 溫度: {center_val.value:.2f} °C")
        else:
            print(f"[即時測溫] 中心點溫度狀態異常 (狀態碼: {center_val.state})")
        last_log_time = now

c_with_thermal_image = WITH_THERMAL_IMAGE(py_with_thermal_image)

def scan_and_get_camera(interface_type):
    global found_camera_identity
    found_camera_identity = None
    
    discovery = acs.ACS_Discovery_alloc()
    print("開始掃描相機硬體...")
    acs.ACS_Discovery_scan(discovery, interface_type, c_on_camera_found, c_on_discovery_error, None, None, None)
    
    for _ in range(50):
        if found_camera_identity is not None:
            break
        time.sleep(0.1)
        
    acs.ACS_Discovery_free(discovery)
    return found_camera_identity

def main():
    identity = scan_and_get_camera(ACS_CommunicationInterface_usb)
    
    if not identity:
        print("未偵測到實體 USB 熱成像相機。自動切換至 SDK 內建模擬器 (Emulator)...")
        identity = scan_and_get_camera(ACS_CommunicationInterface_emulator)
        
    if not identity:
        print("錯誤: 無法找到任何實體相機或內建模擬器。")
        sys.exit(1)
        
    camera = acs.ACS_Camera_alloc()
    print("正在與相機建立連線...")
    acs.ACS_Camera_connect(camera, identity, None, c_on_disconnected, None, None)
    acs.ACS_Identity_free(identity)
    
    stream = None
    stream_count = acs.ACS_Camera_getStreamCount(camera)
    for i in range(stream_count):
        s = acs.ACS_Camera_getStream(camera, i)
        if acs.ACS_Stream_isThermal(s):
            stream = s
            break
            
    if not stream:
        print("錯誤: 該相機不支援熱成像串流！")
        acs.ACS_Camera_free(camera)
        sys.exit(1)
        
    thermal_streamer = acs.ACS_ThermalStreamer_alloc(stream)
    streamer = acs.ACS_ThermalStreamer_asStreamer(thermal_streamer)
    renderer = acs.ACS_Streamer_asRenderer(streamer)
    
    callbacks_received = ctypes.c_ulong(0)
    callback_context = ctypes.byref(callbacks_received)
    
    print("啟動熱成像即時串流...")
    acs.ACS_Stream_start(stream, c_on_image_received, c_on_stream_error, callback_context)
    
    print("\n>>> 串流已啟動。正在每秒輸出測溫數據。按 Ctrl+C 可停止連線 <<<\n")
    
    last_frame_count = 0
    try:
        while True:
            current_frames = callbacks_received.value
            if current_frames > last_frame_count:
                last_frame_count = current_frames
                acs.ACS_Renderer_update(renderer)
                acs.ACS_ThermalStreamer_withThermalImage(thermal_streamer, c_with_thermal_image, None)
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n正在停止串流與中斷連線...")
        
    finally:
        acs.ACS_Stream_stop(stream)
        acs.ACS_Streamer_free(streamer)
        acs.ACS_Camera_disconnect(camera)
        acs.ACS_Camera_free(camera)
        print("已安全關閉相機連線。")

if __name__ == "__main__":
    main()
