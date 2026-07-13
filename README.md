# MR60-FLIR-FHIR 醫療熱成像與 FHIR 標準整合系統

本專案旨在建置一套符合中華民國衛生福利部 **HL7 FHIR (Fast Healthcare Interoperability Resources)** 標準之醫療熱成像測溫系統。系統能透過 FLIR Atlas C SDK 對接實體熱成像相機，實時提取溫度矩陣，自動轉換為標準 Observation 格式，並在地端資料庫與公網安全傳輸間進行無縫整合。

---

## 🛠️ 系統架構設計

*   **前端展示**：採用極簡現代化暗色系 Web 監控面板 (Vanilla HTML/CSS/JS)，實時呈現病患資訊與歷史測溫圖表。
*   **後端服務**：基於 Python 的多執行緒伺服器 (`server.py`)，處理靜態網頁伺服、資料庫 RESTful API 接口，並動態控制穿牆隧道。
*   **資料儲存**：使用地端 **PostgreSQL** 關聯式資料庫，儲存病患體溫紀錄。
*   **安全傳輸**：透過 **Cloudflare Tunnel (cloudflared)** 穿透無公網環境，將本地服務以 HTTPS 安全加密連線發布至專屬網域。

---

## 📅 歷史開發節點與歷程 (Timeline)

### 階段一：系統雛形驗證 (2026/07/09)
*   **外網穿透測試**：成功使用 Cloudflare 臨時快速通道 (trycloudflare.com) 驗證校外公網連線。
*   **SDK 動態連結**：驗證 Python 成功透過 `ctypes` 載入官方 `atlas_c_sdk.dll` 驅動。
*   **靜態圖像解析**：完成 RJPEG 圖像熱矩陣讀取模擬（NumPy 矩陣提取）。
*   **模擬器開發**：完成無相機時的 OpenCV 動態熱源追蹤模擬器。

### 階段二：地端架構整合與專屬網域開通 (2026/07/11 - 當前進度)
*   **地端資料庫部署**：完成地端 PostgreSQL 16 安裝配置與 `test_temperature` 資料表建置。
*   **多執行緒重構**：後端伺服器升級為多執行緒架構，解決因長連接 (Keep-Alive) 造成的併發阻塞問題，並修復資料庫連線洩漏。
*   **永久網域綁定**：註冊專屬網域 **`60gigahertz.uk`** 並對接 `school-fhir` 永久命名隧道，公網網址永久固定為 `https://60gigahertz.uk`。
*   **安全部署最佳化**：建立「免憑證/免登入」的安全部署方案，避免地端主機暴露帳號最高管理權限。
*   **規格文檔研析**：完成衛福部 TW Core IG 規格說明與 HAPI FHIR JPA 底層 GZIP/Blob + 索引儲存機制的研析文檔。

---

## 📊 開發進度追蹤 (Progress Checklist)

*   [x] 地端資料庫建置與 TablePlus 連線設定
*   [x] 多執行緒核心伺服器與 RESTful API 設計
*   [x] 現代化靜態 Web 監控面板設計
*   [x] 專屬永久加密網域 `https://60gigahertz.uk` 設定與綁定
*   [x] 地端主機免密碼/免管理憑證安全部署方案
*   [x] 台灣衛福部 FHIR 與 HAPI FHIR 底層儲存規格文檔撰寫
*   [ ] **[待相機到貨]** 實體 FLIR E53 相機即時影像串流與 SDK 對接
*   [ ] **[待相機到貨]** 實體測溫數據實時自動寫入 PostgreSQL 資料庫
*   [ ] **[選用]** 遷移至標準 HAPI FHIR JPA Server 資料格式

---

## 📁 專案目錄結構

```text
MR60_FLIR_FHIR-system/
├── web_frontend/                # 前端監控網頁內容
│   └── index.html               # 現代化 Web 監控面板
├── local_db_api/
│   └── test/                    # 測試伺服器與資料庫腳本
│       ├── server.py            # 主伺服器 (多執行緒 Web + API)
│       ├── test_db.py           # PostgreSQL 連線測試腳本
│       └── [測試]一鍵啟動服務.bat # 本機一鍵啟動腳本
├── 文檔/                         # 專案技術規格書與說明書
│   ├── PostgreSQL_資料庫安裝與設定指引.md
│   ├── 前後端分離架構與重要性說明.md
│   ├── 衛生福利部FHIR與FHIR_Server定義說明.md
│   ├── HAPI_FHIR_JPA_資料格式與存儲機制說明.md
│   ├── 地端安全部署與技術里程碑紀錄.md
│   └── 當前進度_20260711.md
├── git_pull.bat                 # 地端一鍵拉取同步腳本
└── README.md                    # 本專案說明文件
```
