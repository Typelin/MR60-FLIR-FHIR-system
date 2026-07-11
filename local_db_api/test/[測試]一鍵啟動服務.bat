@echo off
chcp 65001 >nul
title [Test] Launching Test Server
echo Starting Server and Cloudflare Tunnel...
python server.py
