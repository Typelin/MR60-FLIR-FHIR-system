@echo off
chcp 65001 >nul
title Launching Server
echo Starting Server and Cloudflare Tunnel...
cd local_db_api
python server.py
