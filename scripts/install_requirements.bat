@echo off
cd /d "%~dp0"
echo [System] Installing Python Dependencies...
echo ------------------------------------------

:: 필요한 모든 라이브러리 한 번에 설치
py -m pip install requests selenium webdriver-manager google-generativeai streamlit fastapi uvicorn pypdf holidays python-dateutil beautifulsoup4 plotly

echo.
echo [SUCCESS] 모든 설치가 완료되었습니다!
pause