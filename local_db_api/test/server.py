# -*- coding: utf-8 -*-
"""
多執行緒伺服器與靜態網頁伺服 (server.py)
定位: 位於 local_db_api/test/。
功能: 
  1. 多執行緒伺服：解決 Keep-Alive 連線阻塞問題。
  2. 自動資料庫初始化：啟動時讀取 schema.sql 重設並建立三表關聯結構。
  3. API 分流：支援多模態生理與行為訊號 (心率、呼吸、體溫、姿態、離床、跌倒) 的對接寫入 (POST) 與撈取 (GET)。
  4. 靜態網頁替換與自動清理機制。
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

def initialize_database():
    """啟動時自動讀取 schema.sql 初始化資料表與預設病患、設備資料"""
    sql_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "schema.sql"))
    if not os.path.exists(sql_path):
        print(f"\n[提示] 找不到資料庫腳本: {sql_path}，跳過自動初始化。")
        return
        
    print("\n[DB] 正在根據 schema.sql 重構資料庫三表結構...")
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        with open(sql_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
        cursor.execute(sql_script)
        conn.commit()
        print("[DB] PostgreSQL 資料庫重構與預設資料初始化成功！")
    except Exception as e:
        print(f"[DB] 資料庫初始化失敗: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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
                
        elif path == '/api/fhir':
            conn = None
            cursor = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        o.id, 
                        o.patient_id, 
                        p.name AS patient_name,
                        p.gender AS patient_gender,
                        to_char(p.birth_date, 'YYYY-MM-DD') AS patient_birth,
                        p.mrn AS patient_mrn,
                        o.device_id,
                        d.model_number AS device_model,
                        d.manufacturer AS device_manufacturer,
                        d.serial_number AS device_serial,
                        o.status,
                        o.category,
                        o.loinc_code,
                        o.value_numeric,
                        o.value_unit,
                        o.value_code,
                        o.value_display,
                        to_char(o.recorded_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS timestamp
                    FROM observations o
                    LEFT JOIN patients p ON o.patient_id = p.id
                    LEFT JOIN devices d ON o.device_id = d.id
                    ORDER BY o.recorded_at DESC;
                """)
                rows = cursor.fetchall()
                
                bundle = {
                    "resourceType": "Bundle",
                    "type": "searchset",
                    "total": len(rows),
                    "entry": []
                }
                
                added_patients = set()
                
                for row in rows:
                    obs_id = row[0]
                    patient_id = row[1]
                    patient_name = row[2]
                    patient_gender = row[3]
                    patient_birth = row[4]
                    patient_mrn = row[5]
                    device_id = row[6]
                    device_model = row[7]
                    device_manufacturer = row[8]
                    device_serial = row[9]
                    status = row[10]
                    category = row[11]
                    loinc_code = row[12]
                    val_num = float(row[13]) if row[13] is not None else None
                    val_unit = row[14]
                    val_code = row[15]
                    val_display = row[16]
                    timestamp = row[17]
                    
                    if patient_id and patient_id not in added_patients:
                        added_patients.add(patient_id)
                        
                        # 插入 Patient
                        bundle["entry"].append({
                            "fullUrl": f"http://60gigahertz.uk/fhir/Patient/{patient_id}",
                            "resource": {
                                "resourceType": "Patient",
                                "id": patient_id,
                                "identifier": [
                                    {
                                        "use": "official",
                                        "system": "http://www.mhw.gov.tw/mrn",
                                        "value": patient_mrn
                                    }
                                ],
                                "name": [
                                    {
                                        "use": "official",
                                        "text": patient_name
                                    }
                                ],
                                "gender": patient_gender,
                                "birthDate": patient_birth
                            }
                        })
                        
                        # 插入 Linkage (跨院聯結示範)
                        bundle["entry"].append({
                            "fullUrl": f"http://60gigahertz.uk/fhir/Linkage/linkage-{patient_id}",
                            "resource": {
                                "resourceType": "Linkage",
                                "id": f"linkage-{patient_id}",
                                "active": True,
                                "item": [
                                    {
                                        "type": "source",
                                        "resource": {
                                            "reference": f"Patient/{patient_id}"
                                        }
                                    },
                                    {
                                        "type": "alternate",
                                        "resource": {
                                            "reference": "Patient/patient-alternate-999"
                                        }
                                    }
                                ]
                            }
                        })
                        
                    obs_resource = {
                        "resourceType": "Observation",
                        "id": f"obs-{obs_id}",
                        "status": status,
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": category,
                                        "display": "Vital Signs" if category == "vital-signs" else "Survey"
                                    }
                                ]
                            }
                        ],
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": loinc_code,
                                    "display": "Body temperature" if loinc_code == "8310-5" else (
                                               "Heart rate" if loinc_code == "8867-4" else (
                                               "Respiratory rate" if loinc_code == "9279-1" else (
                                               "Body position" if loinc_code == "8361-8" else (
                                               "Bed exit status" if loinc_code == "96773-7" else "Accidental fall indicator"
                                               ))))
                                }
                            ]
                        },
                        "subject": {
                            "reference": f"Patient/{patient_id}"
                        },
                        "device": {
                            "reference": f"Device/{device_id}"
                        },
                        "effectiveDateTime": timestamp
                    }
                    
                    if val_num is not None:
                        obs_resource["valueQuantity"] = {
                            "value": val_num,
                            "unit": "Cel" if loinc_code == "8310-5" else "bpm",
                            "system": "http://unitsofmeasure.org",
                            "code": val_unit
                        }
                    elif val_code is not None:
                        obs_resource["valueCodeableConcept"] = {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": val_code,
                                    "display": val_display
                                }
                            ]
                        }
                        
                    bundle["entry"].append({
                        "fullUrl": f"http://60gigahertz.uk/fhir/Observation/obs-{obs_id}",
                        "resource": obs_resource
                    })

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(bundle, ensure_ascii=False).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": f"FHIR Bundle 轉換失敗: {str(e)}"}, ensure_ascii=False).encode("utf-8"))
                return
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        elif path == '/api' or path.startswith('/api/'):
            conn = None
            cursor = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                # 多表 JOIN 查詢所有 Observation 觀測資料與對應的病患、設備資料
                cursor.execute("""
                    SELECT 
                        o.id, 
                        o.patient_id, 
                        p.name AS patient_name,
                        o.device_id,
                        d.model_number AS device_model,
                        o.status,
                        o.category,
                        o.loinc_code,
                        o.value_numeric,
                        o.value_unit,
                        o.value_code,
                        o.value_display,
                        to_char(o.recorded_at, 'YYYY-MM-DD HH24:MI:SS') AS timestamp
                    FROM observations o
                    LEFT JOIN patients p ON o.patient_id = p.id
                    LEFT JOIN devices d ON o.device_id = d.id
                    ORDER BY o.recorded_at DESC;
                """)
                rows = cursor.fetchall()
                
                records = []
                for row in rows:
                    records.append({
                        "id": row[0],
                        "patient_id": row[1],
                        "patient_name": row[2],
                        "device_id": row[3],
                        "device_model": row[4],
                        "status": row[5],
                        "category": row[6],
                        "loinc_code": row[7],
                        "value_numeric": float(row[8]) if row[8] is not None else None,
                        "value_unit": row[9],
                        "value_code": row[10],
                        "value_display": row[11],
                        "timestamp": row[12]
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
                patient_id = data.get("patient_id", "patient-01")
                metric_type = data.get("metric_type")
                value = data.get("value")
                
                # 根據指標類型對應正確的設備與規範代碼
                category = "vital-signs"
                loinc_code = ""
                value_numeric = None
                value_unit = None
                value_code = None
                value_display = None
                
                # 自動設備/硬體編號對照分流
                if metric_type == "heart_rate" or metric_type == "respiration_rate":
                    device_id = "device-radar-01"   # 心率呼吸雷達
                elif metric_type == "fall":
                    device_id = "device-radar-02"   # 跌倒監測雷達
                else:
                    device_id = "device-camera-01"  # 體溫、姿態、離床均由熱感影像解析
                
                if metric_type == "heart_rate":
                    loinc_code = "8867-4"
                    value_numeric = float(value)
                    value_unit = "/min"
                elif metric_type == "respiration_rate":
                    loinc_code = "9279-1"
                    value_numeric = float(value)
                    value_unit = "/min"
                elif metric_type == "body_temperature":
                    loinc_code = "8310-5"
                    value_numeric = float(value)
                    value_unit = "Cel"
                elif metric_type == "posture":
                    category = "social-history"
                    loinc_code = "8361-8"
                    if value == "lying":
                        value_code = "102538003"
                        value_display = "躺著"
                    elif value == "standing":
                        value_code = "10904000"
                        value_display = "站立"
                elif metric_type == "bed_exit":
                    category = "survey"
                    loinc_code = "96773-7"
                    if value == "in_bed":
                        value_code = "102539006"
                        value_display = "在床"
                    elif value == "out_of_bed":
                        value_code = "262068006"
                        value_display = "離床"
                elif metric_type == "fall":
                    category = "survey"
                    loinc_code = "75276-6"
                    if value == "fallen":
                        value_code = "242526002"
                        value_display = "跌倒"
                    elif value == "present":
                        value_code = "260385009"
                        value_display = "有人"
                    elif value == "absent":
                        value_code = "272186001"
                        value_display = "無人"
                else:
                    raise ValueError(f"不支援的監測數據指標: {metric_type}")
                # 寫入 PostgreSQL 資料庫的 observations 資料表
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO observations 
                        (patient_id, device_id, category, loinc_code, recorded_at, value_numeric, value_unit, value_code, value_display)
                    VALUES 
                        (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s);
                """, (patient_id, device_id, category, loinc_code, value_numeric, value_unit, value_code, value_display))
                conn.commit()
                
                response = {
                    "status": "success",
                    "message": f"成功寫入觀測資料！指標類型: {metric_type}，值: {value}"
                }
                status_code = 200
            except Exception as e:
                response = {
                    "status": "error",
                    "message": f"寫入觀測資料失敗: {str(e)}"
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
        
    print(f"偵測到桌面 cloudflared.exe，正在啟動永久命名隧道 [school-fhir]...")

    global ACTIVE_TUNNEL_URL
    ACTIVE_TUNNEL_URL = "https://60gigahertz.uk"
    
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000

    cmd = [cloudflared_path, "tunnel", "run", "--url", "http://localhost:8080", "school-fhir"]
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
    
    browser_opened = False
    
    for line in iter(proc.stdout.readline, ""):
        print(f"[Cloudflare] {line.strip()}")
        
        if "Connection" in line and "registered" in line and not browser_opened:
            print("\n" + "="*50)
            print(f"永久公網網址: {ACTIVE_TUNNEL_URL}")
            print("="*50 + "\n")
            webbrowser.open("http://localhost:8080")
            browser_opened = True

def run_server(port=8080):
    # 啟動時自動重設並建立新三表結構與載入初始資料
    initialize_database()
    
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
