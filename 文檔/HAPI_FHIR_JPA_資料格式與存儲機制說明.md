# HAPI FHIR JPA Starter 資料格式與資料庫存儲傳輸機制說明書

本文件深入解析基於 **HAPI FHIR JPA Server Starter** 框架下，標準醫療資源（以體溫量測為例）的 **JSON 格式內容**、**RESTful API 傳輸協議**，以及其在 **PostgreSQL 資料庫中的底層存儲與索引機制**。

---

## 1. 標準 FHIR JSON 範例格式：以體溫量測 (Observation) 為例

當前端網頁與 HAPI FHIR 伺服器通訊時，傳輸的資料是以標準符合 HL7 FHIR 規範的 **JSON** 格式進行封裝。以下為一筆標準的體溫 Observation 資源內容：

```json
{
  "resourceType": "Observation",
  "id": "example-temperature",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs",
          "display": "Vital Signs"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "8310-5",
        "display": "Body temperature"
      }
    ]
  },
  "subject": {
    "reference": "Patient/example-patient",
    "display": "王大明"
  },
  "effectiveDateTime": "2026-07-11T21:13:23+08:00",
  "valueQuantity": {
    "value": 37.5,
    "unit": "C",
    "system": "http://unitsofmeasure.org",
    "code": "Cel"
  }
}
```

### 📝 核心欄位解析：
*   **`resourceType`**：資源類型，此處為 `Observation`（臨床觀察/測量值）。
*   **`status`**：檢驗狀態，`final` 代表此測量已完成。
*   **`code`**：核心語意。使用國際標準 LOINC 編碼，`8310-5` 即代表「體溫 (Body temperature)」。
*   **`subject`**：量測對象。使用 FHIR 邏輯連結（Reference）指向特定的 Patient 資源。
*   **`effectiveDateTime`**：測量時間。採用 ISO 8601 標準時間格式。
*   **`valueQuantity`**：測量數值。包含實質數值 `37.5` 與國際 UCUM 單位 `Cel` (°C)。

---

## 2. FHIR 資料的傳輸機制 (Transmission)

FHIR 採用標準的 **HTTP RESTful API** 進行通訊，資料以 `application/fhir+json` 或 `application/json` 格式傳輸。

### ① 新增紀錄 (Create)
*   **HTTP 方法**：`POST`
*   **API 網址**：`https://[您的公網網址]/fhir/Observation`
*   **Headers**：`Content-Type: application/fhir+json`
*   **Payload**：上述的 Observation JSON 內容。
*   **伺服器回應**：`201 Created`，並在 Header 的 `Location` 帶回該資源在資料庫中被分配到的永久 ID。

### ② 查詢紀錄 (Query / Search)
*   **HTTP 方法**：`GET`
*   **API 網址**：`https://[您的公網網址]/fhir/Observation?patient=example-patient&code=8310-5`
*   **功能**：HAPI FHIR 伺服器會解析 Query Parameters（病人 ID 與 LOINC Code），並回傳一個包含所有符合條件的 Observation 的 **Bundle (打包資源)** JSON。

---

## 3. HAPI FHIR JPA 於資料庫 (PostgreSQL) 的存儲機制

當您將上述 JSON 傳送給 HAPI FHIR JPA 伺服器後，伺服器並非簡單地建立一張扁平的資料表，而是透過 **Hibernate/JPA** 將其寫入一組高度結構化的複雜關聯表群中（約 40-50 張表）。其核心存儲機制如下：

### ① 原始 JSON 存儲：`HFJ_RES_VER` (資源版本表)
*   **機制**：FHIR 規定資源必須有版本控制。HAPI FHIR 會把整個原始的 Observation JSON 內容（包括所有嵌套結構），進行 **GZIP 壓縮**，然後以 **BLOB (Binary Large Object) 二進位形式** 存入 `HFJ_RES_VER` 資料表的 `RES_TEXT_VC` 或 `RES_TEXT` 欄位中。
*   **優點**：確保完整的 FHIR 資料結構百分之百不丟失，且便於版本回溯。

### ② 搜尋參數提取與索引：`HFJ_SPIDX_*` (搜尋索引表)
為了讓使用者能快速查詢（例如：搜尋溫度大於 37.5 度的紀錄），HAPI FHIR 在存入 BLOB 的同時，會自動解析 JSON 欄位，並將需要被檢索的關鍵數據提取出來，存入對應的**索引表**：
*   **`HFJ_SPIDX_QUANTITY`**：提取數值欄位。會存入 `37.5`、`Cel` 等，以便支援 `temperature=gt37.5` 的範圍查詢。
*   **`HFJ_SPIDX_DATE`**：提取時間欄位。存入 `2026-07-11...`，以便支援時間區間查詢。
*   **`HFJ_SPIDX_STRING` / `HFJ_SPIDX_TOKEN`**：提取字串與代碼識別子（如 `8310-5`）。

這是一種 **「外側關聯索引，內側壓縮 BLOB」** 的混合式設計。查詢時，資料庫先透過索引表快速定位到資源 ID，再從資源版本表中把壓縮的 JSON 解壓回傳給前端。

---

## 4. 本專案目前的「扁平資料表」與「官方標準」之對照

為了快速開發與驗證穿牆通訊，本專案目前使用的是扁平式（Flat Table）資料表 `test_temperature`：

| 欄位名稱 | 資料類型 | 對應標準 FHIR 欄位 | 說明 |
| :--- | :--- | :--- | :--- |
| **`id`** | SERIAL (PK) | `Observation.id` | 系統分配唯一碼 |
| **`patient_name`** | VARCHAR | `Observation.subject.display` | 暫以字串紀錄病人姓名 |
| **`temperature`** | NUMERIC | `Observation.valueQuantity.value` | 量測體溫數值 |
| **`recorded_at`** | TIMESTAMP | `Observation.effectiveDateTime` | 測量時間戳記 |

### 💡 評估與未來遷移：
我們目前採用的這種輕量化設計，是極佳的「敏捷開發原型」。因為我們在 `server.py` 中已經將資料庫的讀寫包裝成了符合 RESTful 的 `/api` 介面。

未來如果要改為對接官方標準的 **HAPI FHIR JPA**：
1.  我們只需要維持前端 `web_frontend` 的介面不變。
2.  將前端 API 網址指向 HAPI FHIR 的標準 Endpoint (如 `/fhir/Observation`)。
3.  將 Python 伺服器改寫成：讀取實體相機數據後，組裝成第一節所示的 **標準 Observation JSON**，直接 POST 到 HAPI FHIR 伺服器。
4.  JPA 伺服器便會自動打理好後面所有的 PostgreSQL 高階存儲，無縫實現醫療級整合！
