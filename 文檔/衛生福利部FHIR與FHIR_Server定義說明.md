# 衛生福利部 FHIR 與 FHIR Server 定義說明書

本文件詳盡說明了 **HL7 FHIR 醫療資訊標準規範**、**中華民國衛生福利部（MOHW）台灣核心實作指引（TW Core IG）** 以及 **FHIR Server（以開源標竿 HAPI FHIR 為主）** 的定義、技術特徵與資料來源，作為本專題開發設計之核心參考文獻。

---

## 1. 什麼是 FHIR？ (Fast Healthcare Interoperability Resources)

### ① 定義與起源
**FHIR**（讀音為 "Fire"）是由國際醫療資訊標準組織 **HL7 (Health Level Seven International)** 於 2014 年起推動的最新一代「快速健康照護互通資源」標準。它是基於現代 Web 技術（如 HTTP RESTful API、JSON、XML、OAuth2）設計的，旨在解決傳統醫療標準（如 HL7 V2、V3、CDA）開發門檻高、資料格式難以互通的痛點。

### ② 核心概念：資源 (Resources)
FHIR 的核心是將所有醫療活動與實體拆解成極小、可重用的積木，稱為**「資源 (Resources)」**。
*   例如：
    *   **Patient (病人)**：紀錄基本身分資料。
    *   **Observation (觀察值/檢驗數據)**：紀錄體溫、血壓、熱成像測溫結果等臨床測量值。
    *   **Practitioner (醫事人員)**：紀錄醫事人員資料。

### ③ 醫療互通性的三個層次
FHIR 能夠實現全球公認的醫療數據整合，主因在於它滿足了三個層次的互通性：
1.  **技術互通性 (Technical Interoperability)**：透過標準的 TCP/IP、HTTP RESTful API 傳輸。
2.  **結構互通性 (Syntactic Interoperability)**：統一使用 JSON 或 XML 格式封裝。
3.  **語意互通性 (Semantic Interoperability)**：強制對應國際醫學術語集（如 LOINC 檢驗代碼、SNOMED CT 臨床術語、ICD-10 診斷碼），確保不同醫院的系統能理解數據代表的真實醫學含意（例如本專案中體溫對應的 LOINC Code：`8310-5`）。

---

## 2. 什麼是 衛生福利部 台灣核心實作指引 (TW Core IG)？

### ① 定義與定位
為了響應全球智慧醫療趨勢並推動台灣醫療機構間的電子病歷（EHR）互通，中華民國**衛生福利部（MOHW）**以 HL7 FHIR R4.0.1 版本為基礎，制定了 **「台灣核心實作指引 (Taiwan Core Implementation Guide，簡稱 TW Core IG)」**。

*   **國道系統比喻**：HL7 FHIR 是汽車與引擎的國際技術標準，而 **TW Core IG** 則是衛福部專為台灣醫療環境鋪設的「高速公路交通規則與道路規格」。
*   **在地化（Localization）的體現**：
    *   **台灣專屬值集 (ValueSets)**：將台灣特有的醫療編碼導入標準，如：健保用藥品項代碼、台灣國民身份證字號格式、健保特約醫院代碼、中文版 ICD-10-CM/PCS 診斷與手術碼。
    *   **在地化延伸 (Extensions)**：例如符合台灣書寫習慣的地址格式、出生地申報、特定醫療給付規則等。

### ② 專案中的重要性
任何在台灣開發的 FHIR 系統，都必須以 TW Core IG 作為底層架構基礎（Base Profile），繼承其欄位定義與約束（Constraints），以確保未來能與衛福部的「電子病歷交換大平台」無縫對接。

---

## 3. 什麼是 FHIR Server？

### ① 定義
**FHIR Server** 是醫療資訊系統中專門設計用來「儲存」、「解析」、「驗證」並「交換」符合 FHIR 標準 JSON 格式數據的後端伺服器軟體。

### ② 核心功能與處理機制
1.  **標準化的 RESTful API 接口**：
    外部設備或前端網頁不直接操作資料庫，而是向 FHIR Server 發送標準 HTTP 請求：
    *   `GET /Patient`：查詢病人資料。
    *   `POST /Observation`：新增一筆測溫資料。
    *   `PUT /Observation/{id}`：修改數據。
2.  **資料驗證器 (Validator)**：
    當後端接收到 JSON 數據時，FHIR Server 會自動對照規範。例如，若欄位格式不符、必填欄位缺失、或是 LOINC 術語代碼不正確，伺服器會直接拒絕寫入並回傳錯誤訊息，確保寫入資料庫的數據 100% 正確乾淨。
3.  **搜尋參數索引 (Search Parameters)**：
    FHIR Server 會自動對 JSON 內部深度嵌套的欄位（如：Observation 中的溫度值）建立特殊索引，使開發者能快速執行如「查詢 2026 年大於 37.5 度的所有測溫紀錄」等複雜查詢。

---

## 4. 全球主流開源實作：HAPI FHIR Server

在開發與部署 FHIR 系統時，業界極少從零開發伺服器，而是採用經過認證的開源框架。其中最權威、最主流的便是 **HAPI FHIR**。

*   **技術源流**：由加拿大大學健康網絡 (UHN) 開發，現由開源社群及 Smile Digital Health 維護，採用 Apache 2.0 授權，完全免費開源。
*   **Java 架構與關聯資料庫支援**：
    HAPI FHIR 是以 Java 語言編寫的工業級解決方案。其 JPA 模組能與 **PostgreSQL** 資料庫完美對接，自動將複雜的 FHIR 資源寫入結構化的 PostgreSQL SQL 資料表中，且自動處理 JSONB 欄位的檢索優化。
*   **TW Core IG 導入**：
    HAPI FHIR 支援直接載入衛福部的 TW Core IG 驗證包。載入後，伺服器便會自動以台灣本土標準對所有傳入的資料進行核對，是建置本土醫療院所系統的首選。

### ⑤ 衛福部推薦 HAPI FHIR 與 PostgreSQL 的關聯性
在衛生福利部官方的「臺灣核心實作指引實作範例平台」中，官方將 **HAPI FHIR** 列為首選架設方案。
因為 HAPI FHIR 的資料庫持久化（JPA）模組需要處理高度複雜的 FHIR JSON 欄位查詢，且必須在不收授權費的開源資料庫上運行，**PostgreSQL 的 JSONB (Binary JSON) 欄位檢索性能為所有開源資料庫之冠**。因此，衛福部推薦使用 HAPI FHIR，**在實務上即等同於強烈推薦採用 PostgreSQL 作為底層資料庫**（此為全球 FHIR 開發社群公認的最優解 / Best Practice）。

---

## 5. 官方資料來源與參考文獻 (Citations)

本文件內容與後續系統開發規格均嚴格參照以下官方標準與文件：

1.  **臺灣醫療資訊標準指引大平台 (衛福部官方 IG)**：
    *   *MOHW Taiwan Core Implementation Guide (TW Core IG R4)*
    *   連結網址：[https://twcore.mohw.gov.tw/ig/twcore/](https://twcore.mohw.gov.tw/ig/twcore/)
2.  **HL7 FHIR 國際官方標準規範**：
    *   *HL7 FHIR R4 (v4.0.1) Specification*
    *   連結網址：[https://hl7.org/fhir/R4/](https://hl7.org/fhir/R4/)
3.  **HAPI FHIR 開源框架官方文檔**：
    *   *HAPI FHIR - The Open Source FHIR API for Java*
    *   連結網址：[https://hapifhir.io/](https://hapifhir.io/)
4.  **衛生福利部電子病歷交換標準推動計畫**：
    *   *中華民國衛生福利部資訊處 - 電子病歷交換標準規劃報告*
    *   連結網址：[https://www.mohw.gov.tw/](https://www.mohw.gov.tw/)
5.  **臺灣核心實作指引實作範例平台（衛福部官方樣章平台）**：
    *   *MOHW Taiwan Core Sample Sandbox Portal*
    *   連結網址：[https://twcore.mohw.gov.tw/twsample/](https://twcore.mohw.gov.tw/twsample/)
6.  **衛福部官方 HAPI FHIR 架設教學與說明指引**：
    *   *MOHW HAPI FHIR Server Installation Guide*
    *   連結網址：[https://twcore.mohw.gov.tw/twsample/Server/Hapi](https://twcore.mohw.gov.tw/twsample/Server/Hapi)
