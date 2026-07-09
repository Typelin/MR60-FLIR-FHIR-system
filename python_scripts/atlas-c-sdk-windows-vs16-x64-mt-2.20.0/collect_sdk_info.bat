@echo off
chcp 65001 > nul
set OUTPUT_FILE=sdk_summary.txt

if exist %OUTPUT_FILE% del %OUTPUT_FILE%

echo ============================================================ >> %OUTPUT_FILE%
echo [1] DLL 檔案清單 >> %OUTPUT_FILE%
echo ============================================================ >> %OUTPUT_FILE%
for /r %%F in (*.dll) do (
    echo %%~nxF  ^(相對路徑: %%~pnxF^) >> %OUTPUT_FILE%
)
echo. >> %OUTPUT_FILE%
echo. >> %OUTPUT_FILE%

echo ============================================================ >> %OUTPUT_FILE%
echo [2] .h 與 .c 標頭/源碼檔案內容彙整 >> %OUTPUT_FILE%
echo ============================================================ >> %OUTPUT_FILE%
echo. >> %OUTPUT_FILE%

for /r %%F in (*.h *.c) do (
    echo ------------------------------------------------------------ >> %OUTPUT_FILE%
    echo FILE: %%~pnxF >> %OUTPUT_FILE%
    echo ------------------------------------------------------------ >> %OUTPUT_FILE%
    type "%%F" >> %OUTPUT_FILE%
    echo. >> %OUTPUT_FILE%
    echo. >> %OUTPUT_FILE%
)

echo 收集完成！結果已儲存至 %OUTPUT_FILE%
pause