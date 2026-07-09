:: UTF-8 BOM 保護行，請勿刪除此行
@echo off
chcp 65001 >nul
title 一鍵啟動測試服務
echo 正在一鍵啟動測試服務與背景穿牆隧道...
cd local_db_api
python server.py
