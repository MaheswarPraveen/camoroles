@echo off
echo ===================================================
echo   Deploying Camouroles to Cloudflare Workers
echo ===================================================

echo [1/3] Checking syntax...
node -c worker.js
if %errorlevel% neq 0 (
    echo [ERROR] Syntax error in worker.js
    pause
    exit /b %errorlevel%
)
node -c static/app.js
if %errorlevel% neq 0 (
    echo [ERROR] Syntax error in static/app.js
    pause
    exit /b %errorlevel%
)
echo [OK] Code syntax verified.

echo [2/3] Checking Cloudflare credentials...
wrangler whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Please log into Cloudflare in the browser that opens...
    wrangler login
)

echo [3/3] Deploying to Cloudflare Workers (workers.dev)...
wrangler deploy

echo.
echo ===================================================
echo   Deployment completed!
echo ===================================================
pause
