@echo off
setlocal enableextensions enabledelayedexpansion

set REPO_ROOT=%~dp0

rem Check if python executable is available in PATH
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo =====================================================
    echo   [ERROR] PYTHON 3 IS REQUIRED TO RUN THIS MENU
    echo =====================================================
    echo.
    echo Python 3.8 or higher is not installed or not found in your system PATH.
    echo.
    echo How to fix:
    echo   1. Download Python from: https://www.python.org/downloads/
    echo   2. IMPORTANT: Check the box "Add python.exe to PATH" during installation.
    echo   3. Restart your terminal / command prompt and run menu.cmd again.
    echo.
    echo =====================================================
    pause
    exit /b 1
)

rem Locate menu script in skirmish directory
set MENU_SCRIPT=%REPO_ROOT%skirmish\menu.py

if not exist "%MENU_SCRIPT%" (
    echo =====================================================
    echo   [ERROR] MENU SCRIPT NOT FOUND
    echo =====================================================
    echo.
    echo Could not locate menu.py at %MENU_SCRIPT%
    echo Please ensure skirmish\menu.py is present.
    echo.
    echo =====================================================
    pause
    exit /b 1
)

rem Launch Python menu hub
python "%MENU_SCRIPT%" %*
set EXIT_CODE=%ERRORLEVEL%

rem Handle execution error if Python exited with non-zero code
if %EXIT_CODE% neq 0 (
    if %EXIT_CODE% neq 130 (
        echo.
        echo [NOTE] Menu exited with return code %EXIT_CODE%.
        pause
    )
)

exit /b %EXIT_CODE%
