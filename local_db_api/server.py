# -*- coding: utf-8 -*-
"""
伺服器連線測試 (server_test.py)
用途: 啟動一個簡單的 Web 伺服器監聽 Port 8080，用於配合 Cloudflare Tunnel 測試穿牆連線。
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 設定回應 HTTP 200 OK 狀態與 JSON 格式
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        # 允許跨網域 (CORS)，方便後續網頁呼叫
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        # 回傳測試用的 JSON 數據
        response = {
            "status": "online",
            "message": "連線成功！您已順利透過 Cloudflare Tunnel 連線至學校電腦。",
            "test_port": 8080
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))

def run_server(port=8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, SimpleServerHandler)
    print(f"測試伺服器已啟動！")
    print(f"正在監聽 Port: {port}")
    print("請使用 Cloudflare Tunnel 進行穿牆連線測試...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在關閉測試伺服器...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
