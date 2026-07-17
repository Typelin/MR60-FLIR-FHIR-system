# -*- coding: utf-8 -*-
"""
MR60 Dual-Radar WiFi UDP Logger (mr60_logger.py)
功能:
  1. 啟動 UDP Socket 監聽，接收來自兩台 ESP32 經由 WiFi 熱點傳輸的 MR60 雷達數據。
  2. 支援動態解析 Comma-Separated Payload: `Sensor_ID,breath_rate,heart_rate,distance`。
  3. 即時將結果安全地寫入 `mr60_sensor_log.csv` 中。
  4. 內建自動模擬發送模式 (Simulation Mode)，在沒有硬體或未開啟實體 UDP 接收時依然可以測試功能。
"""

import os
import sys
import time
import csv
import socket
import threading
from datetime import datetime

# ==================== 參數設定 ====================
UDP_IP = "0.0.0.0"       # 監聽所有介面的連入連線
UDP_PORT = 12345         # 與 ESP32 .ino 設定相符的 UDP 連接埠
CSV_FILE_PATH = "mr60_sensor_log.csv"
SIMULATION_MODE = False  # 是否強制啟用模擬數據生成模式

# 線程鎖鎖定 CSV 寫入，避免併發寫入衝突
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

def run_udp_server():
    """啟動 UDP 接收端伺服器線程"""
    print(f"[啟動] UDP 伺服器正在監聽 {UDP_IP}:{UDP_PORT} ...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
    except Exception as e:
        print(f"❌ 錯誤: 無法綁定 UDP Port {UDP_PORT}: {str(e)}")
        print("      系統將自動切換為 [模擬器模式] 進行測試。")
        start_simulation_threads()
        return

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            payload = data.decode("utf-8", errors="ignore").strip()
            # 格式: Sensor_ID,breath_rate,heart_rate,distance 或 Sensor_ID,init,message
            parts = payload.split(",")
            
            if len(parts) >= 3:
                sensor_id = parts[0]
                
                # 處理上線初始化訊號
                if parts[1] == "init":
                    print(f"📡 [系統提示] 設備 {sensor_id} 已連線上線！訊息: {parts[2]} (來源: {addr[0]})")
                    continue
                    
                # 處理感測數據
                try:
                    breath = float(parts[1])
                    heart = float(parts[2])
                    dist = float(parts[3]) if len(parts) >= 4 else 0.0
                    log_to_csv(sensor_id, breath, heart, dist)
                except ValueError:
                    print(f"⚠️ [解析警告] 收到來自 {addr[0]} 的無效數據格式: {payload}")
                    
        except Exception as e:
            print(f"⚠️ 接收資料出錯: {str(e)}")
            time.sleep(0.1)

def run_simulation(sensor_id):
    """模擬器模式：當無實體設備連入時產生模擬數據"""
    import random
    print(f"[模擬器] {sensor_id} 已啟動模擬數據發送...")
    
    base_breath = 18.0 if sensor_id == "MR60_1" else 15.0
    base_heart = 72.0 if sensor_id == "MR60_1" else 68.0
    base_dist = 120.0 if sensor_id == "MR60_1" else 200.0

    while True:
        try:
            breath = round(base_breath + random.uniform(-1.5, 1.5), 2)
            heart = round(base_heart + random.uniform(-3.0, 3.0), 2)
            dist = round(base_dist + random.uniform(-5.0, 5.0), 2)
            
            log_to_csv(sensor_id, breath, heart, dist)
            time.sleep(random.uniform(2.0, 4.0))
        except KeyboardInterrupt:
            break

def start_simulation_threads():
    """啟動多個模擬雷達數據的發送線程"""
    t1 = threading.Thread(target=run_simulation, args=("MR60_1",), daemon=True)
    t2 = threading.Thread(target=run_simulation, args=("MR60_2",), daemon=True)
    t1.start()
    t2.start()

def main():
    print("=" * 60)
    print("      MR60 雙雷達 WiFi UDP CSV 數據接收記錄器已啟動")
    print("=" * 60)
    
    initialize_csv()
    
    if SIMULATION_MODE:
        print("[提示] 已手動設定強制啟用 [模擬模式] 運行。")
        start_simulation_threads()
    else:
        # 啟動實體 UDP 接收線程
        udp_thread = threading.Thread(target=run_udp_server, daemon=True)
        udp_thread.start()
        
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[結束] 使用者中斷，正在關閉記錄器...")
        sys.exit(0)

if __name__ == "__main__":
    main()
