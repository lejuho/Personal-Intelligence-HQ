@echo off
cd /d "%~dp0\.."

echo ====================================================
echo [SYSTEM] AI System Boot Loader (Docker Mode)
echo [PATH] %CD%
echo ====================================================

:: Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not running! Please start Docker Desktop first.
    pause
    exit /b 1
)

echo [INFO] Starting Docker Containers...
docker-compose up -d

echo.
echo [SUCCESS] System launched in background.
echo - Backend: http://localhost:8000
echo - Dashboard: http://localhost:8501
echo.
echo Closing this window in 5 seconds...
timeout /t 5
exit