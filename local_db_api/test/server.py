# -*- coding: utf-8 -*-
"""
資料庫對接測試伺服器 (server.py)
定位: 位於 local_db_api/test/，處理前端 GET/POST 請求，讀寫 PostgreSQL 資料庫，並啟動背景穿牆。
"""

import os
import re
import sys
import json
import random
import datetime
import psycopg2
import subprocess
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# PostgreSQL 連線設定值
DB_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "Yusheng1214",
    "port": "5432"
}

class SimpleServerHandler(BaseHTTPRequestHandler):
    def get_db_connection(self):
        # 建立資料庫連線
        return psycopg2.connect(**DB_CONFIG)

    def do_GET(self):
        # 處理前端 GET 請求，回傳資料庫中所有體溫紀錄
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # 從 PostgreSQL 查詢 test_temperature 資料表並按時間排序
            cursor.execute("SELECT id, patient_name, temperature, recorded_at FROM test_temperature ORDER BY recorded_at DESC;")
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                records.append({
                    "id": row[0],
                    "patient_name": row[1],
                    "temperature": float(row[2]),
                    "recorded_at": row[3].strftime("%Y-%m-%d %H:%M:%S")
                })
            
            cursor.close()
            conn.close()
            
            # 回傳查詢結果
            self.wfile.write(json.dumps(records, ensure_ascii=False).encode("utf-8"))
            
        except Exception as e:
            # 資料庫連線失敗或無資料表時，回傳錯誤訊息
            error_response = {
                "error": "資料庫讀取失敗",
                "details": str(e),
                "tip": "請確認您的 PostgreSQL 是否已啟動，且已執行 SQL 建立 test_temperature 資料表。"
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode("utf-8"))

    def do_POST(self):
        # 處理前端 POST 請求，將體溫模擬數據寫入 PostgreSQL 資料庫
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            patient_name = data.get("patient_name", "未指定")
        except Exception:
            patient_name = "解析失敗"
            
        # 模擬產生合理的體溫 (36.2 到 38.2 度)
        simulated_temp = round(random.uniform(36.2, 38.2), 1)
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        
        try:
            # 寫入 PostgreSQL 資料庫
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO test_temperature (patient_name, temperature) VALUES (%s, %s) RETURNING id, recorded_at;",
                (patient_name, simulated_temp)
            )
            new_id, recorded_at = cursor.fetchone()
            
            conn.commit()  # 提交變更
            cursor.close()
            conn.close()
            
            response = {
                "status": "success",
                "message": f"成功寫入 PostgreSQL 資料庫！已為「{patient_name}」模擬寫入體溫 {simulated_temp} °C",
                "data": {
                    "id": new_id,
                    "patient": patient_name,
                    "temperature": simulated_temp,
                    "timestamp": recorded_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "loinc_code": "8310-5 (Body temperature)"
                }
            }
        except Exception as e:
            response = {
                "status": "error",
                "message": "資料庫寫入失敗",
                "details": str(e)
            }
            
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        # 處理跨網域 CORS 預檢請求
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def launch_cloudflare_tunnel():
    # 尋找桌面（相對於 local_db_api/test/ 三層上）
    cloudflared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cloudflared.exe"))
    
    if not os.path.exists(cloudflared_path):
        print(f"\n[提示] 未在桌面找到 cloudflared.exe。期望路徑: {cloudflared_path}")
        print("將僅啟動本地 API，不啟動 Cloudflare 穿牆通道。")
        return
        
    print(f"偵測到桌面 cloudflared.exe，正在啟動背景穿牆通道...")
    
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000  # CREATE_NO_WINDOW

    cmd = [cloudflared_path, "tunnel", "--url", "http://localhost:8080"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore",
        creationflags=creationflags
    )
    
    # 讀取日誌抓取公網連結
    for line in iter(proc.stdout.readline, ""):
        print(f"[Cloudflare] {line.strip()}")
        
        if ".trycloudflare.com" in line:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                tunnel_url = match.group(0)
                print("\n" + "="*50)
                print(f"🎉 穿牆成功！您的公網測試網址為:")
                print(f"   {tunnel_url}")
                print("="*50 + "\n")
                
                # 自動開啟網頁控制面板，並帶入 URL 參數
                html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html"))
                webbrowser.open(f"file:///{html_path}?tunnel={tunnel_url}")

def run_server(port=8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, SimpleServerHandler)
    
    print(f"測試伺服器已啟動！正在監聽 Port: {port}")
    
    # 用獨立執行緒（Thread）啟動 Cloudflare 穿牆，避免阻擋 HTTP 伺服器
    tunnel_thread = threading.Thread(target=launch_cloudflare_tunnel, daemon=True)
    tunnel_thread.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在關閉測試伺服器與釋放穿牆通道...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
