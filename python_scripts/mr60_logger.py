# -*- coding: utf-8 -*-
"""
MR60 Dual-Radar CSV Logger (mr60_logger.py)
功能:
  1. 雙執行緒併發讀取兩個 COM Port (COM3/COM4 或自訂) 的 MR60 雷達感測數據。
  2. 即時解析呼吸率 (breath_rate)、心率 (heart_rate) 與距離 (distance)。
  3. 將結果以包含時間戳的格式寫入 `mr60_sensor_log.csv` 中。
  4. 內建自動模擬模式 (Simulation Mode) - 當找不到實體 COM Port 時自動降級為模擬測試模式，便於離線除錯。
"""

import os
import re
import sys
import time
import csv
import threading
from datetime import datetime

# 嘗試載入 pyserial 函式庫，若無則提示
try:
    import serial
except ImportError:
    print("[警告] 找不到 'pyserial' 函式庫，實體串口讀取功能將受限。")
    print("      您可以使用指令安裝: pip install pyserial")
    serial = None

# ==================== 參數設定 ====================
PORT1 = "COM3"           # 雷達 1 的串口號 (Windows: COMx, Linux/Mac: /dev/ttyUSBx)
PORT2 = "COM4"           # 雷達 2 的串口號
BAUDRATE = 115200        # 與 Arduino .ino 設定相符的鮑率
CSV_FILE_PATH = "mr60_sensor_log.csv"
SIMULATION_MODE = False  # 是否強制啟用模擬模式

# 正則表達式解析
# 格式 1 (單行併發): breath_rate: 17.00 bpm, heart_rate: 75.00 bpm, distance: 100.00 cm
# 格式 2 (分行輸出): breath_rate: 17.00 bpm 或 heart_rate: 75.00 bpm
pattern_breath = re.compile(r"breath_rate:\s*([\d\.]+)")
pattern_heart = re.compile(r"heart_rate:\s*([\d\.]+)")
pattern_dist = re.compile(r"distance:\s*([\d\.]+)")

# 線程鎖鎖定 CSV 寫入，避免檔案競爭衝突
csv_lock = threading.Lock()

def initialize_csv():
    """初始化 CSV 檔案並寫入欄位標頭"""
    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Sensor_ID", "Breath_Rate_BPM", "Heart_Rate_BPM", "Distance_CM"])
        print(f"[初始化] 已建立並初始化 CSV 日誌檔案: {CSV_FILE_PATH}")

def log_to_csv(sensor_id, breath, heart, dist):
    """安全地將單筆觀測資料寫入 CSV"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with csv_lock:
        with open(CSV_FILE_PATH, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, sensor_id, breath, heart, dist])
    print(f"[{timestamp}] [寫入成功] 來源: {sensor_id} | 呼吸: {breath} bpm | 心跳: {heart} bpm | 距離: {dist} cm")

def parse_and_log(sensor_id, line, buffer):
    """解析單行串口資料並在取得完整讀數時寫入日誌"""
    line = line.strip()
    if not line:
        return

    # 解析單行中可能出現的數值
    m_breath = pattern_breath.search(line)
    m_heart = pattern_heart.search(line)
    m_dist = pattern_dist.search(line)

    if m_breath:
        buffer["breath"] = float(m_breath.group(1))
    if m_heart:
        buffer["heart"] = float(m_heart.group(1))
    if m_dist:
        buffer["dist"] = float(m_dist.group(1))

    # 檢查是否已集齊三個指標 (或判定為完整單行輸出格式)
    if "breath" in buffer and "heart" in buffer and "dist" in buffer:
        log_to_csv(sensor_id, buffer["breath"], buffer["heart"], buffer["dist"])
        # 清空 Buffer 進行下一次收集
        buffer.clear()

def read_serial_thread(sensor_id, port):
    """負責單個串口資料讀取的線程函數"""
    print(f"[啟動] 開始監聽雷達 {sensor_id}，連接埠: {port}，鮑率: {BAUDRATE}...")
    
    # 初始化解析暫存器
    buffer = {}
    
    try:
        ser = serial.Serial(port, BAUDRATE, timeout=1.0)
        # 清除輸入快取
        ser.reset_input_buffer()
        
        while True:
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode("utf-8", errors="ignore")
                    parse_and_log(sensor_id, line, buffer)
                except Exception as e:
                    print(f"[{sensor_id}] 讀取或解析資料出錯: {str(e)}")
            time.sleep(0.01)
            
    except Exception as e:
        print(f"❌ 錯誤: 無法開啟或讀取連接埠 {port} ({sensor_id}): {str(e)}")
        print(f"      線程 {sensor_id} 將自動降級為 [模擬器模式] 進行測試。")
        run_simulation(sensor_id)

def run_simulation(sensor_id):
    """模擬器模式：當無實體串口連線時自動產生仿真數據"""
    import random
    print(f"[模擬器] {sensor_id} 已啟動模擬資料發送...")
    
    # 針對不同雷達模擬不同的基準值
    base_breath = 18.0 if sensor_id == "MR60_1" else 15.0
    base_heart = 72.0 if sensor_id == "MR60_1" else 68.0
    base_dist = 120.0 if sensor_id == "MR60_1" else 200.0

    while True:
        try:
            # 隨機產生微幅飄動的模擬數據
            breath = round(base_breath + random.uniform(-1.5, 1.5), 2)
            heart = round(base_heart + random.uniform(-3.0, 3.0), 2)
            dist = round(base_dist + random.uniform(-5.0, 5.0), 2)
            
            log_to_csv(sensor_id, breath, heart, dist)
            
            # 每隔 2 到 4 秒隨機間隔送一次資料
            time.sleep(random.uniform(2.0, 4.0))
        except KeyboardInterrupt:
            break

def main():
    print("=" * 60)
    print("         MR60 雙雷達 CSV 數據即時記錄器已啟動")
    print("=" * 60)
    
    # 初始化 CSV
    initialize_csv()
    
    # 檢查是否啟用實體串口模式
    if serial is None or SIMULATION_MODE:
        print("[提示] 檢測到實體串口程式庫缺失或手動設定，全面以 [模擬模式] 運行。")
        t1 = threading.Thread(target=run_simulation, args=("MR60_1",), daemon=True)
        t2 = threading.Thread(target=run_simulation, args=("MR60_2",), daemon=True)
    else:
        # 實體串口線程設定
        t1 = threading.Thread(target=read_serial_thread, args=("MR60_1", PORT1), daemon=True)
        t2 = threading.Thread(target=read_serial_thread, args=("MR60_2", PORT2), daemon=True)
        
    t1.start()
    t2.start()
    
    try:
        # 讓主執行緒維持運行，直到手動終止
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[結束] 使用者中斷，正在關閉記錄器...")
        sys.exit(0)

if __name__ == "__main__":
    main()
