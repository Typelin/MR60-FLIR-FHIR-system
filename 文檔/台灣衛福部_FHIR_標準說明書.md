# 台灣衛福部 FHIR 標準說明書 (白話對照指南)

本文件將中華民國衛生福利部（衛福部）推行的 **臺灣核心實作指引 (TW Core IG)** 規範，以開發者易讀的「白話文」與「資料表」形式進行整理，協助您快速理解如何將 FLIR E53 測溫數據對接至符合國家標準的醫療資訊系統。

---

## 1. 核心觀念白話對照表

在閱讀衛福部的標準網站時，請對照以下表格，將專用術語轉換為一般的網頁/資料庫開發觀念：

| 官方規格術語 | 開發者白話翻譯 | 說明與實務對應 |
| :--- | :--- | :--- |
| **Resources** (資源) | **基礎資料表 / 空白表單** | HL7 官方定義的最基礎格式（例如：`Observation` 代表空白的觀察記錄表）。 |
| **Profiles** (實作指引) | **填表說明與欄位限制** | 衛福部制定的台灣在地化格式。例如：要求體溫必須使用攝氏度、身分證格式必須符合台灣規範。 |
| **Cardinality** (基數) | **必填或選填** | 欄位出現次數限制：<br>• `1..1`：**必填**，且只能寫 1 筆數據。<br>• `0..*`：**選填**，可留空，或寫多筆（例如多個電話）。 |
| **Terminology** (術語集) | **下拉選單的選項** | 規定某些欄位必須填入「標準醫療代碼」。例如：體溫代碼必須填入 LOINC 代碼 `8310-5`。 |
| **Value Set** (值集) | **下拉選單的合法值範圍** | 例如性別欄位，其值集限定只能從 `male`、`female` 等代碼中選擇。 |
| **SHALL** (必須) | **必須遵守 (否則拒收)** | 用戶端傳送的 JSON 數據中，如果漏掉此欄位，FHIR 伺服器會直接阻擋並報錯。 |
| **SHOULD** (建議) | **建議提供** | 建議填寫，如果漏掉，伺服器仍會接受資料，但會給予警告。 |

---

## 2. 您的專案需要關注的規格：Observation (生命徵象)

針對您的 **FLIR E53 熱成像測溫專案**，您在衛福部網站上唯一需要關注的資源是 **Observation (觀察紀錄)** 下的 **Vital Signs (生命徵象 - 體溫)** 格式。

### 📊 關鍵欄位對應關係
若要將 E53 讀取到的數值存入資料庫，您的 JSON 必須包含以下標準欄位：

*   **`status` (狀態)**：通常填入 `"final"`（代表最終檢測結果）。
*   **`code` (檢驗項目)**：必須指向 LOINC 代碼 `8310-5`（表示 Body Temperature 體溫）。
*   **`subject` (對象)**：關聯至特定的病人（例如 `"Patient/example"`）。
*   **`valueQuantity` (數值與單位)**：
    *   `value`：填入您用 Python 讀取到 FLIR 鏡頭的真實溫度（例如 `37.5`）。
    *   `unit`：固定為 `"C"`。
    *   `code`：固定為 `"Cel"`（攝氏度標準代碼）。

---

## 3. 符合衛福部標準的體溫 JSON 範例

以下是當您的 Python 程式獲取到體溫後，要上傳至後端伺服器時，必須組裝成的標準 FHIR JSON 格式：

```json
{
  "resourceType": "Observation",
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
    "reference": "Patient/example"
  },
  "valueQuantity": {
    "value": 37.5,
    "unit": "C",
    "system": "http://unitsofmeasure.org",
    "code": "Cel"
  }
}
```
*(註：當您的網頁前端使用 API 讀取這個 JSON 後，便能直接取出 `value` 顯示在瀏覽器畫面上)*
