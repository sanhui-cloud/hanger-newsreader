@echo off
chcp 65001 >nul
echo === Global News Reader - Setup ===
echo.

:: ── 1. Find a usable Python ─────────────────────────────────────────────────

set PYTHON_CMD=

:: Try the 'py' launcher first (points to python.org installs, skips Store version)
where py >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('py --version 2^>^&1') do echo Found: %%i ^(via py launcher^)
    set PYTHON_CMD=py
    goto :check_store
)

:: Fall back to 'python'
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ from:
    echo         https://www.python.org/downloads/
    echo         During install, tick "Add Python to PATH".
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo Found: %%i
set PYTHON_CMD=python

:check_store
:: Detect Microsoft Store Python (its path contains "WindowsApps")
for /f "tokens=*" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.executable)"') do set PY_EXE=%%i
echo %PY_EXE% | findstr /i "WindowsApps" >nul
if not errorlevel 1 (
    echo.
    echo [ERROR] You have the Microsoft Store version of Python, which cannot
    echo         create virtual environments reliably.
    echo.
    echo  Please install Python from: https://www.python.org/downloads/
    echo  During install, tick "Add Python to PATH".
    echo  Then run this setup again.
    echo.
    pause
    exit /b 1
)

:: ── 2. Check if venv already exists ─────────────────────────────────────────

if exist "venv\Scripts\activate.bat" (
    echo Virtual environment already exists. Checking for updates...
    call venv\Scripts\activate.bat
    echo Updating dependencies if needed...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
    if errorlevel 1 (
        echo [WARN] Mirror failed, retrying with default source...
        pip install -r requirements.txt --quiet
    )
    echo.
    echo ====================================
    echo  Environment is up to date.
    echo  Run launch.bat to start the app.
    echo ====================================
    pause
    exit /b 0
)

:: ── 3. Create venv ───────────────────────────────────────────────────────────

echo Creating virtual environment...
%PYTHON_CMD% -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    echo Please ensure you are using Python 3.10+ from python.org.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

:: ── 4. Install dependencies ──────────────────────────────────────────────────

echo Installing dependencies (using Tsinghua mirror for speed)...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo.
    echo [WARN] Mirror install failed. Retrying with default PyPI...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
)

echo.
echo ====================================
echo  Setup complete!
echo  Run launch.bat to start the app.
echo ====================================
pause
