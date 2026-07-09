@echo off
chcp 65001 >nul
title FHIR 穿牆測試一鍵啟動工具

echo ==================================================
echo        FHIR 穿牆測試與網頁控制面板一鍵啟動
echo ==================================================
echo.

:: 檢查桌面（上一層目錄）是否有 cloudflared.exe
if not exist "..\cloudflared.exe" (
    echo [警告] 找不到桌面的 cloudflared.exe 執行檔！
    echo 請確保您已將 cloudflared.exe 放在您的電腦桌面上。
    echo.
    pause
    exit /b
)

echo [1/3] 正在獨立視窗中啟動 Python 測試伺服器 (Port 8080)...
start "Python 測試伺服器" cmd /c "cd local_db_api && python server.py"

echo [2/3] 正在獨立視窗中啟動 Cloudflare 穿牆隧道 (cloudflared)...
start "Cloudflare 穿牆隧道" cmd /c "..\cloudflared.exe tunnel --url http://localhost:8080"

echo [3/3] 正在等待穿牆隧道建立 (3 秒)...
timeout /t 3 /nobreak >nul

echo 正在開啟瀏覽器測試控制面板...
start "" "local_db_api\index.html"

echo.
echo ==================================================
echo 啟動完成！
echo 請在 [Cloudflare 穿牆隧道] 視窗中複製產生的 trycloudflare.com 網址。
echo 並貼入網頁的輸入框中，點選「發送測試請求」按鈕進行連線測試。
echo ==================================================
echo.
pause
