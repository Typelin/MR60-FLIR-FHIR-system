# -*- coding: utf-8 -*-
"""
伺服器連線與互動測試 (server.py)
定位: 位於 local_db_api/test/，連線 PostgreSQL 資料庫以處理 GET/POST 連線測試，並在背景啟動桌面 3 層上的 cloudflared.exe。
"""

import os
import re
import sys
import json
import random
import datetime
import subprocess
import webbrowser
import threading
import psycopg2
from http.server import HTTPServer, BaseHTTPRequestHandler

def get_db_connection():
    # 建立 PostgreSQL 資料庫連線
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="Yusheng1214",
        port="5432"
    )

class SimpleServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 處理連線可用性測試 - 從 PostgreSQL 讀取所有體溫紀錄
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # 依據時間降序排列讀取紀錄
            cursor.execute("""
                SELECT id, patient_name, temperature, 
                       to_char(recorded_at, 'YYYY-MM-DD HH24:MI:SS') 
                FROM test_temperature 
                ORDER BY recorded_at DESC;
            """)
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                records.append({
                    "id": row[0],
                    "patient_name": row[1],
                    "temperature": float(row[2]),
                    "timestamp": row[3]
                })
                
            cursor.close()
            conn.close()
            
            response = {
                "status": "success",
                "database": "connected",
                "records": records
            }
            status_code = 200
        except Exception as e:
            response = {
                "status": "error",
                "message": f"資料庫讀取失敗: {str(e)}",
                "records": []
            }
            status_code = 500

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))

    def do_POST(self):
        # 處理體溫寫入資料庫測試 (POST)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            patient_name = data.get("patient_name", "未指定")
            temperature = data.get("temperature", 37.0)
            
            # 寫入 PostgreSQL 資料庫
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO test_temperature (patient_name, temperature) VALUES (%s, %s);",
                (patient_name, temperature)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            response = {
                "status": "success",
                "message": f"成功將「{patient_name}」的體溫 {temperature} °C 寫入 PostgreSQL 資料庫！"
            }
            status_code = 200
        except Exception as e:
            response = {
                "status": "error",
                "message": f"寫入資料庫失敗: {str(e)}"
            }
            status_code = 500
        
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        # 處理跨網域 CORS 預檢請求
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def launch_cloudflare_tunnel():
    # 尋找桌面（相對於 local_db_api/test/ 三層上，即 C:\Users\xxx\Desktop\cloudflared.exe）
    cloudflared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cloudflared.exe"))
    
    if not os.path.exists(cloudflared_path):
        print(f"\n[提示] 未在桌面找到 cloudflared.exe。期望路徑: {cloudflared_path}")
        print("將僅啟動本地 API，不啟動 Cloudflare 穿牆通道。")
        return
        
    print(f"偵測到桌面 cloudflared.exe，正在啟動背景穿牆通道...")
    
    # 在 Windows 下設定 CREATE_NO_WINDOW 避免彈出額外的 cmd 視窗
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
                
                # 自動開啟網頁控制面板，並帶入 URL 參數 (新位置在 web_frontend)
                html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "web_frontend", "index.html"))
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
