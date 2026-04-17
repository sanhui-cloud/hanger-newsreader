@echo off
chcp 65001 >nul
echo === Global News Reader - Setup ===
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ and add it to PATH.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if venv already exists
if exist "venv\Scripts\activate.bat" (
    echo Virtual environment already exists. Checking for updates...
    call venv\Scripts\activate.bat
    echo Updating dependencies if needed...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo [ERROR] Failed to update dependencies.
        pause
        exit /b 1
    )
    echo.
    echo ====================================
    echo  Environment is up to date.
    echo  Run launch.bat to start the app.
    echo ====================================
    pause
    exit /b 0
)

echo Python found. Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip --quiet

echo Installing dependencies (this may take a minute)...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ====================================
echo  Setup complete!
echo  Run launch.bat to start the app.
echo ====================================
pause
