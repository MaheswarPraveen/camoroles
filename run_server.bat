@echo off
title camOroles Server (Port 8000)
cd /d "%~dp0"
echo ========================================================
echo  camOroles Engine - Running on http://127.0.0.1:8000
echo ========================================================
python serve.py
pause
