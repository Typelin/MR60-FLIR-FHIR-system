# 多模態生理訊號與行為偵測 FHIR 對接規格書

本文件定義本專案所蒐集之 **5 項多模態生理訊號與行為偵測資料**（心率與呼吸率、跌倒辨識、體溫、姿態辨識、離床監測）如何對接至 **HL7 FHIR (TW Core IG)** 國際醫療標準，並定義後端伺服器 (API Backend) 之核心功能。

---

## 1. 資料欄位與 FHIR Observation 標準對照表

在 FHIR 標準中，上述所有生理數據與行為狀態皆屬於臨床觀察值，因此統一採用 **`Observation`** 資源進行封裝。為符合衛生福利部 **TW Core IG** 規範，需對應至標準代碼（LOINC 或 SNOMED CT）與 UCUM 單位：

| 序號 | 監測項目 | 物理數值/狀態值 | FHIR 資源類型 | 國際標準代碼 (System & Code) | 單位/值集規範 (UCUM/SNOMED) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **心率 (Heart Rate)** | 數值 (bpm) | `Observation` | **LOINC**:`8867-4` <br>*(Heart rate)* | **UCUM**:`/min` <br>*(次/分鐘)* |
| **2** | **呼吸率 (Respiratory Rate)** | 數值 (bpm) | `Observation` | **LOINC**:`9279-1` <br>*(Respiratory rate)* | **UCUM**:`/min` <br>*(次/分鐘)* |
| **3** | **體溫 (Body Temperature)** | 數值 (°C) | `Observation` | **LOINC**:`8310-5` <br>*(Body temperature)* | **UCUM**:`Cel` <br>*(攝氏度)* |
| **4** | **姿態辨識 (Posture)** | 狀態值：<br>1. 躺著 (Lying)<br>2. 站立 (Standing) | `Observation` | **LOINC**:`8361-8` <br>*(Body position)* | **SNOMED CT**:<br>1. `102538003` *(Lying position)*<br>2. `10904000` *(Standing)* |
| **5** | **離床監測 (Bed Exit)** | 狀態值：<br>1. 在床 (In Bed)<br>2. 離床 (Out of Bed) | `Observation` | **LOINC**:`96773-7` <br>*(Bed exit status)* | **SNOMED CT**:<br>1. `102539006` *(Lying in bed)*<br>2. `262068006` *(Out of bed)* |
| **6** | **跌倒辨識 (Fall Detection)** | 狀態值：<br>1. 跌倒 (Fallen)<br>2. 有人 (Present)<br>3. 無人 (Absent) | `Observation` | **LOINC**:`75276-6` <br>*(Accidental fall indicator)* | **SNOMED CT / Local**:<br>1. `242526002` *(Accidental fall)*<br>2. `260385009` *(Present)*<br>3. `272186001` *(Absent)* |

---

## 2. 後端伺服器 (Backend) 核心任務與分工

為了實現與 HAPI FHIR 的無縫對接，我們的 Python 後端（或是未來正式的 HAPI FHIR 伺服器）需要執行以下核心功能：

### ① 數據接收與格式轉譯 (Data Gateway & Parser)
*   **任務**：地端的雷達/熱成像等感測器傳送的是扁平的 JSON 數據（例如：`{"sensor_id": "01", "temp": 37.5, "posture": "lying"}`）。
*   **後端職責**：後端接收到數據後，必須**自動將其拆解並序列化（Serialize）成符合上述表格的 FHIR JSON 格式**（以符合 `Observation` 的定義）。

### ② 數據合法性驗證 (Validation Interceptor)
*   **任務**：確保寫入的資料格式正確。
*   **後端職責**：檢查寫入的資料中，LOINC 代碼是否正確、時間戳記是否符合 ISO 8601 格式、必填欄位（例如：`status`, `code`, `subject`）是否缺失。如果不符，回傳 `400 Bad Request` 並拒絕寫入。

### ③ FHIR RESTful API 接口提供 (RESTful APIs)
*   後端需提供標準的 RESTful 接口供前端網頁（Dashboard）調用：
    *   `POST /fhir/Observation`：接收並新增一筆生理/行為紀錄。
    *   `GET /fhir/Observation?subject=Patient/1&code=8310-5`：查詢特定病患的體溫歷史紀錄。
    *   `GET /fhir/Observation?code=75276-6&value-concept=242526002`：快速篩選「目前處於跌倒狀態」的異常警報。

---

## 3. 標準 FHIR JSON 資料範例

### 💡 姿態辨識 (Posture) 封裝範例
```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "social-history",
          "display": "Social History"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "8361-8",
        "display": "Body position"
      }
    ]
  },
  "subject": {
    "reference": "Patient/example-patient"
  },
  "effectiveDateTime": "2026-07-13T10:30:00+08:00",
  "valueCodeableConcept": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "102538003",
        "display": "Lying position"
      }
    ],
    "text": "躺著"
  }
}
```
*(說明：數值類型的體溫、心率使用 `valueQuantity`；而狀態類型的姿態、離床、跌倒，則使用 `valueCodeableConcept` 並對應 SNOMED CT 概念編碼。)*

---

## 4. FHIR 強制與推薦之上下文元數據 (Context Metadata)

僅有感測器獲得的「5 種生理/行為數值」在標準 FHIR 中是**不完整的**。根據 HL7 FHIR 與衛生福利部 TW Core IG 的規定，每一筆 `Observation` 資源**必須強制綁定上下文元數據**，否則會被視為無效資料。

以下為除了 5 項感測器數值之外，後端必須自動生成或綁定的欄位：

### ① 強制欄位 (Mandatory Elements - 基數為 `1..1`)
1.  **`status` (量測狀態)**：
    *   *規定*：必須說明此觀察值的狀態（如：`registered` 登記, `preliminary` 初步, `final` 最終）。
    *   *實務*：由於本系統由感測器自動採集並完成判定，後端轉譯時一律填入 **`"final"`**。
2.  **`subject` (病人對象)**：
    *   *規定*：在 TW Core IG 中，此欄位是**強制必填 (`1..1`)**。必須指向一個特定的 **`Patient` (病患)** 資源（例如：`Patient/example-patient`）。
    *   *解析*：這代表後端在寫入溫度或心率時，必須明確知道「這是哪一個病人的數據」。病患的個人隱私資訊（如：姓名、身分證字號、生日、性別）是獨立儲存在 `Patient` 資源中的，`Observation` 僅作關聯引用。
3.  **`effectiveDateTime` (量測時間戳記)**：
    *   *規定*：必須精確紀錄該訊號被偵測到的時間。
    *   *格式*：必須使用符合 ISO 8601 的國際標準時間格式（如：`2026-07-13T10:30:00+08:00`）。

### ② 推薦欄位 (Recommended Elements - 強烈建議填寫)
1.  **`device` (量測設備/感測器資訊)**：
    *   *說明*：指向一個 **`Device` (醫療設備)** 資源。
    *   *實務*：強烈建議在 Observation 中綁定 `{"reference": "Device/mr60-radar-01"}`。`Device` 資源中會儲存該感測器的**製造商 (Manufacturer)**、**設備型號 (Model)**、以及**序號 (Serial Number)**。這在智慧醫療與 IoT 監測中極為重要，用於確保數據的可追溯性與校準紀錄。
2.  **`category` (分類)**：
    *   *說明*：對於心率、呼吸率、體溫，必須標明分類代碼為 `vital-signs` (生命徵象)；對於離床、跌倒、姿態，建議歸類為 `social-history` 或自訂感測器監控類別。

