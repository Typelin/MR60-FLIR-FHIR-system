@echo off
chcp 65001 >nul
title [測試]一鍵啟動測試服務
echo 正在一鍵啟動測試服務與背景穿牆通道...
python server.py
