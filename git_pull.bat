@echo off
title Git Sync Tool
echo ====================================
echo   Syncing project from GitHub...
echo ====================================
echo.
git pull
echo.
echo ====================================
echo   Sync completed! Closing in 3 seconds...
echo ====================================
timeout /t 3 >nul
