@echo off
setlocal
cd /d "%~dp0"

:: ---------------------------------------------------
:: [1] 관리자 권한 체크
:: ---------------------------------------------------
openfiles >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 관리자 권한이 필요합니다!
    echo ==================================================
    echo 이 파일을 우클릭하고 '관리자 권한으로 실행' 해주세요.
    echo ==================================================
    echo.
    pause
    exit
)

:: ---------------------------------------------------
:: [2] 경로 설정
:: ---------------------------------------------------
set "CURRENT_DIR=%~dp0"
:: 끝에 역슬래시(\) 제거
if "%CURRENT_DIR:~-1%"=="\" set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

echo.
echo [System] AI Protocol Auto-Registration (Debug Mode)
echo [Path] %CURRENT_DIR%
echo --------------------------------------------------

:: ---------------------------------------------------
:: [3] 레지스트리 등록 (실패 시 에러 보이게 >nul 제거)
:: ---------------------------------------------------

echo 1. Creating Root Key (HKCR\aisys)...
reg add "HKCR\aisys" /ve /t REG_SZ /d "URL:AI System Protocol" /f
if %errorlevel% neq 0 goto ERROR_HANDLER

echo 2. Setting URL Protocol...
reg add "HKCR\aisys" /v "URL Protocol" /t REG_SZ /d "" /f
if %errorlevel% neq 0 goto ERROR_HANDLER

echo 3. Setting Command Path...
:: 경로에 공백이 있어도 작동하도록 따옴표(\")를 명확히 지정
reg add "HKCR\aisys\shell\open\command" /ve /t REG_SZ /d "\"%CURRENT_DIR%\wake_up_all.bat\"" /f
if %errorlevel% neq 0 goto ERROR_HANDLER

echo.
echo [SUCCESS] ✅ 성공적으로 등록되었습니다!
echo [TEST] 이제 Win+R을 누르고 aisys://run 을 입력해보세요.
pause
exit

:ERROR_HANDLER
echo.
echo [FAIL] ❌ 레지스트리 등록 중 오류가 발생했습니다.
pause
exit