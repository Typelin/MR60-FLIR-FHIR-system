# -*- coding: utf-8 -*-
"""
伺服器連線測試 (server.py)
用途: 啟動 Web 伺服器，自動在背景啟動桌面上的 cloudflared.exe 進行穿牆，
      並自動解析出公網網址，自動開啟網頁控制面板填入參數。
"""

import os
import re
import sys
import json
import subprocess
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
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

def launch_cloudflare_tunnel():
    # 尋找桌面（相對於本檔案兩層上，即 C:\Users\xxx\Desktop\cloudflared.exe）
    cloudflared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cloudflared.exe"))
    
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
        # 印出 cloudflared 的 log 在同一個視窗中，方便觀察與除錯
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
