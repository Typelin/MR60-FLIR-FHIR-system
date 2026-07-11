# -*- coding: utf-8 -*-
"""
資料庫連線測試 (test_db.py)
用途: 測試 Python 是否能透過 psycopg2 驅動程式成功連線至本地 PostgreSQL，並印出資料庫版本。
"""

import psycopg2

def test_connection():
    print("正在嘗試連線至本地 PostgreSQL 資料庫...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="Yusheng1214",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        print("\n" + "="*50)
        print("[SUCCESS] Python 已成功連線至 PostgreSQL 資料庫！")
        print(f"資料庫版本: {db_version[0]}")
        print("="*50 + "\n")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print("\n" + "="*50)
        print("[FAIL] Python 無法連線至 PostgreSQL！")
        print(f"錯誤原因: {e}")
        print("="*50 + "\n")

if __name__ == "__main__":
    test_connection()
