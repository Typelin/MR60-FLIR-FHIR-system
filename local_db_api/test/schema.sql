-- ==========================================
-- MR60-FLIR-FHIR 系統資料庫重構 DDL 腳本
-- 定位: local_db_api/test/schema.sql
-- ==========================================

-- 1. 清理舊資料表
DROP TABLE IF EXISTS observations CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS test_temperature CASCADE;

-- 2. 建立病患基本資料表 (Patients)
CREATE TABLE patients (
    id VARCHAR(50) PRIMARY KEY,                    -- 對應 FHIR Patient.id
    mrn VARCHAR(50) UNIQUE NOT NULL,               -- 病歷號/健保卡號
    name VARCHAR(100) NOT NULL,                    -- 姓名
    gender VARCHAR(10) NOT NULL,                   -- 性別 (male/female/other)
    birth_date DATE NOT NULL,                      -- 出生日期
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. 建立監測設備資料表 (Devices)
CREATE TABLE devices (
    id VARCHAR(50) PRIMARY KEY,                    -- 對應 FHIR Device.id
    serial_number VARCHAR(100) UNIQUE NOT NULL,    -- 設備唯一序號
    manufacturer VARCHAR(100) NOT NULL,            -- 製造商
    model_number VARCHAR(100) NOT NULL,            -- 型號
    device_type VARCHAR(100) NOT NULL,             -- 設備類型 (如: Radar, Thermal-Camera)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. 建立生理與行為觀測指標表 (Observations)
CREATE TABLE observations (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    device_id VARCHAR(50) REFERENCES devices(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'final',
    category VARCHAR(50) NOT NULL,                  -- vital-signs 或 survey
    loinc_code VARCHAR(20) NOT NULL,                -- 國際 LOINC Code
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,  -- 量測時間戳記
    
    -- 數值型數據存儲欄位 (適用於體溫、心率、呼吸率)
    value_numeric NUMERIC(6, 2),
    value_unit VARCHAR(20),
    
    -- 狀態型數據存儲欄位 (適用於姿態、跌倒、離床)
    value_code VARCHAR(50),
    value_display VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. 建立效能優化索引
CREATE INDEX idx_obs_patient_code ON observations(patient_id, loinc_code);
CREATE INDEX idx_obs_time ON observations(recorded_at DESC);

-- ==========================================
-- 植入預設測試資料 (Seeding Mock Data)
-- ==========================================

-- 預設病患 (林某某, 生理性別: 女, 生日: 1985-04-12)
INSERT INTO patients (id, mrn, name, gender, birth_date)
VALUES ('patient-01', 'MRN998877', '林某某', 'female', '1985-04-12')
ON CONFLICT (id) DO NOTHING;

-- 預設毫米波雷達設備 (Infineon MR60-Radar)
INSERT INTO devices (id, serial_number, manufacturer, model_number, device_type)
VALUES ('device-radar-01', 'MR60-SN-8821', 'Infineon', 'MR60-Radar', 'Radar')
ON CONFLICT (id) DO NOTHING;

-- 預設熱成像相機設備 (FLIR E53-Camera)
INSERT INTO devices (id, serial_number, manufacturer, model_number, device_type)
VALUES ('device-camera-01', 'FLIR-SN-5309', 'FLIR', 'E53-Camera', 'Thermal-Camera')
ON CONFLICT (id) DO NOTHING;
