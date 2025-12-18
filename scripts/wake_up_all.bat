@echo off
cd /d "%~dp0"

echo ====================================================
echo [SYSTEM] AI System Boot Loader
echo [PATH] %CD%
echo ====================================================

:: 1. Check Python
set PYTHON_EXE=py
%PYTHON_EXE% --version >nul 2>&1
if %ERRORLEVEL% neq 0 set PYTHON_EXE=python

:: 2. Check if Windows Terminal (wt.exe) exists
where wt >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Windows Terminal not found. Using classic CMD.
    goto CLASSIC_MODE
)

:: ==========================================================
:: [MODE A] Windows Terminal (Clean & Split View)
:: ==========================================================
echo [INFO] Windows Terminal detected! Launching in split view...

:: Structure: 
:: [ Tab 1: Runner ] | [ Tab 2: Server (Top) ]
::                   | [ Tab 3: Dashboard (Bottom) ]

start wt ^
    -w 0 new-tab -p "Command Prompt" -d "%CD%" cmd /k "title [1] Runner & %PYTHON_EXE% run_all.py" ^
    ; split-pane -V -d "%CD%" -p "Command Prompt" cmd /k "title [2] API Server & %PYTHON_EXE% ..\src\core\server.py" ^
    ; split-pane -H -d "%CD%" -p "Command Prompt" cmd /k "title [3] Dashboard & %PYTHON_EXE% -m streamlit run ..\src\core\dashboard.py"

exit

:: ==========================================================
:: [MODE B] Classic CMD (Fallback for Compatibility)
:: ==========================================================
:CLASSIC_MODE
echo 1/3 Launching Main Runner...
start "AI_Main_Runner" cmd /k "%PYTHON_EXE% run_all.py"

echo 2/3 Launching API Server...
start "AI_API_Server" cmd /k "title API Server & %PYTHON_EXE% ..\src\core\server.py"

echo 3/3 Launching Dashboard...
start "AI_Dashboard" cmd /k "title Dashboard & %PYTHON_EXE% -m streamlit run ..\src\core\dashboard.py"

echo.
echo [SUCCESS] Launched in Classic Mode.
timeout /t 5
exit