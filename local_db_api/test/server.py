# -*- coding: utf-8 -*-
"""
伺服器連線與互動測試 (server.py)
定位: 位於 local_db_api/test/，處理 GET/POST 連線測試，並在背景啟動桌面 3 層上的 cloudflared.exe。
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
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 處理連線可用性測試
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        response = {
            "status": "online",
            "message": "連線成功！您已順利透過 Cloudflare Tunnel 連線至學校電腦。",
            "test_port": 8080
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))

    def do_POST(self):
        # 處理體溫模擬上傳測試 (POST)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            patient_name = data.get("patient_name", "未指定")
        except Exception:
            patient_name = "解析失敗"
            
        # 模擬產生合理的體溫 (36.2 到 38.2 度)
        simulated_temp = round(random.uniform(36.2, 38.2), 1)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        
        response = {
            "status": "success",
            "message": f"成功接收數據！已為「{patient_name}」模擬寫入體溫 {simulated_temp} °C",
            "data": {
                "patient": patient_name,
                "temperature": simulated_temp,
                "unit": "Celsius",
                "timestamp": now_str,
                "loinc_code": "8310-5 (Body temperature)"
            }
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
