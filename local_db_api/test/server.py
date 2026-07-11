# -*- coding: utf-8 -*-
"""
多執行緒伺服器與靜態網頁伺服 (server.py)
定位: 位於 local_db_api/test/。
功能: 
  1. 多執行緒伺服：解決 Keep-Alive 連線阻塞問題。
  2. 靜態網頁與資料庫 API 分流。
  3. 防止二次彈窗 Bug：加入 browser_opened 鎖定旗標，確保 webbrowser.open 只在啟動時執行一次。
  4. 自動清理機制。
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
import atexit
import psycopg2
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

# 全局變數
ACTIVE_TUNNEL_URL = "無 (僅限本地連線)"
running_subprocesses = []

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="Yusheng1214",
        port="5432"
    )

def cleanup_subprocesses():
    for proc in running_subprocesses:
        try:
            print(f"正在釋放背景穿牆通道 (PID: {proc.pid})...")
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

atexit.register(cleanup_subprocesses)

class SimpleServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == '/' or path == '/index.html':
            html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "web_frontend", "index.html"))
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                content = content.replace("{{TUNNEL_URL}}", ACTIVE_TUNNEL_URL)
                
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"讀取 index.html 失敗: {str(e)}".encode("utf-8"))
                
        elif path == '/api' or path.startswith('/api/'):
            conn = None
            cursor = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
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
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == '/api' or path.startswith('/api/'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            conn = None
            cursor = None
            try:
                data = json.loads(post_data.decode('utf-8'))
                patient_name = data.get("patient_name", "未指定")
                temperature = data.get("temperature", 37.0)
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO test_temperature (patient_name, temperature) VALUES (%s, %s);",
                    (patient_name, temperature)
                )
                conn.commit()
                
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
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def launch_cloudflare_tunnel():
    global ACTIVE_TUNNEL_URL
    cloudflared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cloudflared.exe"))
    
    if not os.path.exists(cloudflared_path):
        print(f"\n[提示] 未在桌面找到 cloudflared.exe。期望路徑: {cloudflared_path}")
        print("將僅啟動本地 API 與靜態伺服器，不啟動 Cloudflare 穿牆通道。")
        webbrowser.open("http://localhost:8080")
        return
        
    print(f"偵測到桌面 cloudflared.exe，正在啟動背景穿牆通道...")
    
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000

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
    
    running_subprocesses.append(proc)
    
    browser_opened = False  # 用於記錄瀏覽器是否已開過
    
    # 讀取日誌抓取公網連結
    for line in iter(proc.stdout.readline, ""):
        print(f"[Cloudflare] {line.strip()}")
        
        # 只有在瀏覽器尚未開啟時，才解析網址並開啟
        if ".trycloudflare.com" in line and not browser_opened:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                tunnel_url = match.group(0)
                ACTIVE_TUNNEL_URL = tunnel_url
                print("\n" + "="*50)
                print(f"🎉 穿牆成功！您的公網測試網址為:")
                print(f"   {tunnel_url}")
                print("="*50 + "\n")
                
                # 自動開啟本地 8080 網頁
                webbrowser.open("http://localhost:8080")
                browser_opened = True  # 鎖定旗標，防二次彈出

def run_server(port=8080):
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, SimpleServerHandler)
    
    print(f"多執行緒測試伺服器已啟動！正在監聽 Port: {port}")
    
    tunnel_thread = threading.Thread(target=launch_cloudflare_tunnel, daemon=True)
    tunnel_thread.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在關閉測試伺服器...")
        cleanup_subprocesses()
        httpd.server_close()

if __name__ == "__main__":
    run_server()
