# PostgreSQL 資料庫安裝與設定指引

本文件指導您如何在**本機電腦**與**學校電腦**上安裝、設定 PostgreSQL 資料庫，並使用 Python 進行連線測試，以實現符合 FHIR 標準的專業地端醫療資料庫整合。

---

## 1. 下載與安裝 PostgreSQL (Windows 版)

請在本機與學校電腦上下載並安裝官方推薦的 EDB 安裝包：

1.  **下載連結**：
    👉 **[PostgreSQL 官方 Windows 下載頁面](https://www.postgresql.org/download/windows/)**
    *   點選 **「Download the installer」**。
    *   建議選擇 **PostgreSQL 15 或 16 (x86-64)** 版本下載。
2.  **安裝精靈步驟指引**：
    *   雙擊安裝包執行，一路點選 **Next**。
    *   **選擇元件 (Select Components)**：建議全選（包含 `PostgreSQL Server`、`pgAdmin 4` 視覺化工具、`Stack Builder`、`Command Line Tools`）。
    *   **設定密碼 (Password)**：請設定資料庫超級管理員 (`postgres`) 的密碼，**建議兩台電腦設定一模一樣的密碼**（例如：`admin123`），這樣您的程式碼就不用改來改去。
    *   **Port 設定**：預設為 **`5432`**，請保持預設。
    *   **地區設定 (Locale)**：選擇 **[Default locale]** 即可。
    *   一路點選 **Next** 直到安裝完成。

---

## 2. 安裝 Python 資料庫驅動程式

在 Python 中要連線並操作 PostgreSQL，需要安裝 `psycopg2` 驅動程式。

請在兩台電腦的命令提示字元 (CMD) 中執行以下指令：
```bash
pip install psycopg2-binary
```
*（提示：使用 `psycopg2-binary` 版本不需要在 Windows 上安裝編譯器，一秒即可安裝完成）*

---

## 3. Python 連線測試範例

您可以將以下程式碼加入您的測試腳本中，驗證 Python 是否能成功連上 PostgreSQL 資料庫：

```python
import psycopg2

def test_db_connection():
    try:
        # 連線設定值
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",       # 預設資料庫
            user="postgres",           # 預設超級管理員
            password="您的密碼",        # 您安裝時設定的密碼
            port="5432"
        )
        
        # 建立游標
        cursor = conn.cursor()
        
        # 執行簡單查詢獲取資料庫版本
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        print("\n==================================================")
        print("  🎉 PostgreSQL 連線成功！")
        print(f"  資料庫版本: {db_version[0]}")
        print("==================================================\n")
        
        # 關閉連線
        cursor.close()
        conn.close()
        
    except Exception as error:
        print("\n==================================================")
        print("  ❌ PostgreSQL 連線失敗！")
        print(f"  錯誤原因: {error}")
        print("==================================================\n")

if __name__ == "__main__":
    test_db_connection()
```

---

## 4. 未來對接 FHIR Server 的優勢
當您將數據存入 PostgreSQL 後：
*   **欄位彈性**：可以使用 `JSONB` 格式儲存複雜的 FHIR JSON 數據，保有與 NoSQL 同等的靈活性。
*   **系統對接**：未來若要改裝官方 Java HAPI FHIR Server，可以直接將資料庫連線字串指向同一個 PostgreSQL，無縫升級為國家級醫療資訊系統。
