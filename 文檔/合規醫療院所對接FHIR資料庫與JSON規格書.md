# 合規醫療院所對接 FHIR 資料庫與 JSON 規格書

本文件專為實現「跨院互通」、「符合衛生福利部 TW Core IG 規範」所設計。定義了在 PostgreSQL 資料庫中必須建立的**關聯式實體資料表（SQL Schema）**，以及資料交換時必須封裝的 **FHIR JSON 欄位結構**。

---

## 1. 醫療合規資料庫設計 (PostgreSQL SQL Schema)

為了符合 FHIR 的實體關聯規範（Patient ➔ Device ➔ Observation），地端資料庫必須捨棄單一扁平表，改為以下三張核心關聯表：

### ① 病患基本資料表 (`patients`)
```sql
CREATE TABLE patients (
    id VARCHAR(50) PRIMARY KEY,                    -- 對應 FHIR Patient.id (系統識別碼)
    mrn VARCHAR(50) UNIQUE NOT NULL,               -- 病歷號/身分證字號 (FHIR Patient.identifier - 必填)
    name VARCHAR(100) NOT NULL,                    -- 姓名 (FHIR Patient.name - 必填)
    gender VARCHAR(10) NOT NULL,                   -- 性別 (FHIR Patient.gender: male/female/other - 必填)
    birth_date DATE NOT NULL,                      -- 出生日期 (FHIR Patient.birthDate - 必填)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### ② 監測設備資料表 (`devices`)
```sql
CREATE TABLE devices (
    id VARCHAR(50) PRIMARY KEY,                    -- 對應 FHIR Device.id
    serial_number VARCHAR(100) UNIQUE NOT NULL,    -- 設備唯一序號 (FHIR Device.identifier)
    manufacturer VARCHAR(100) NOT NULL,            -- 製造商 (如: FLIR, Infineon)
    model_number VARCHAR(100) NOT NULL,            -- 型號 (如: E53, MR60)
    device_type VARCHAR(100) NOT NULL,             -- 設備類型 (如: Thermal-Camera, Radar)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### ③ 生理與行為觀測指標表 (`observations`)
```sql
CREATE TABLE observations (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,  -- 關聯病患 (必填)
    device_id VARCHAR(50) REFERENCES devices(id) ON DELETE SET NULL,            -- 關聯感測器 (強烈推薦)
    status VARCHAR(20) NOT NULL DEFAULT 'final',                                -- 狀態 (final - 必填)
    category VARCHAR(50) NOT NULL,                                              -- 分類 (vital-signs 或 survey)
    loinc_code VARCHAR(20) NOT NULL,                                            -- 國際 LOINC Code (必填)
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,                              -- 量測時間戳記 (必填)
    
    -- 數值型數據存儲欄位 (適用於體溫、心率、呼吸率)
    value_numeric NUMERIC(6, 2),                                                -- 量測數值
    value_unit VARCHAR(20),                                                     -- 單位 (如: Cel, /min)
    
    -- 狀態型數據存儲欄位 (適用於姿態、跌倒、離床)
    value_code VARCHAR(50),                                                     -- SNOMED CT 狀態碼 (如: 102538003)
    value_display VARCHAR(100),                                                 -- 狀態中文名稱 (如: 躺著, 離床)
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 建立時間與病患索引，優化跨院大量查詢效能
CREATE INDEX idx_obs_patient_code ON observations(patient_id, loinc_code);
CREATE INDEX idx_obs_time ON observations(recorded_at DESC);
```

---

## 2. 交換與傳輸 JSON 欄位規格 (JSON Payload)

當其他醫院或衛生福利部平台要求提取數據時，後端必須能輸出標準符合 **HL7 FHIR R4** 與 **TW Core IG** 的 JSON 物件。

### ① 數值型資料 JSON 範例：心率 (Heart Rate)
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
        "code": "8867-4",
        "display": "Heart rate"
      }
    ]
  },
  "subject": {
    "reference": "Patient/patient-01"
  },
  "device": {
    "reference": "Device/device-mr60-01"
  },
  "effectiveDateTime": "2026-07-13T10:35:00+08:00",
  "valueQuantity": {
    "value": 78,
    "unit": "beats/minute",
    "system": "http://unitsofmeasure.org",
    "code": "/min"
  }
}
```

### ② 狀態型資料 JSON 範例：跌倒辨識 (Fall Detection)
```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "survey",
          "display": "Survey"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "75276-6",
        "display": "Accidental fall indicator"
      }
    ]
  },
  "subject": {
    "reference": "Patient/patient-01"
  },
  "device": {
    "reference": "Device/device-radar-01"
  },
  "effectiveDateTime": "2026-07-13T10:35:10+08:00",
  "valueCodeableConcept": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "242526002",
        "display": "Accidental fall"
      }
    ],
    "text": "跌倒"
  }
}
```

---

## 3. 官方權威來源與參考連結 (References)

1.  **台灣衛福部 TW Core IG 病患 (Patient) Profile 規範**：
    *   *必填項目：mrn (病歷識別碼), name (姓名), gender (性別)*
    *   連結網址：[TW Core Patient Profile](https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition-Patient-twcore.html)
2.  **台灣衛福部 TW Core IG 生命徵象 (Vital Signs) 規範**：
    *   *必填項目：status, code, subject, valueQuantity*
    *   連結網址：[TW Core Observation Vital Signs Profile](https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition-Observation-vitalSigns-twcore.html)
3.  **HL7 FHIR 國際官方設備 (Device) 資源定義**：
    *   *定義如何宣告監測設備之型號與序號*
    *   連結網址：[HL7 FHIR Device Specification](https://hl7.org/fhir/R4/device.html)
4.  **LOINC 國際醫學術語數據庫 (LOINC Codes)**：
    *   *心率 LOINC `8867-4` / 體溫 LOINC `8310-5` 官方定義網頁*
    *   連結網址：[LOINC Search Portal](https://loinc.org/)
