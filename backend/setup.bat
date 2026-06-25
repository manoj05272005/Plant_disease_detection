@echo off
REM ========================================
REM Crop Disease Detection Backend Setup
REM Quick Start Script for Windows
REM ========================================

echo.
echo ===================================
echo Crop Disease Detection Backend
echo Quick Start Setup
echo ===================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

REM Check if virtual environment exists
if exist "venv\" (
    echo [INFO] Virtual environment already exists
) else (
    echo [STEP 1/5] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

echo.
echo [STEP 2/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

echo.
echo [STEP 3/5] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

echo.
echo [STEP 4/5] Checking configuration...
if not exist ".env" (
    echo [WARNING] .env file not configured
    echo Please update .env file with your settings:
    echo   - MONGODB_URL
    echo   - SECRET_KEY
    echo.
    echo Generate SECRET_KEY:
    python -c "import secrets; print(secrets.token_hex(32))"
    echo.
    pause
)

echo.
echo [STEP 5/5] Creating necessary directories...
if not exist "uploads\" mkdir uploads
if not exist "uploads\images\" mkdir uploads\images
if not exist "uploads\heatmaps\" mkdir uploads\heatmaps
if not exist "uploads\reports\" mkdir uploads\reports
if not exist "models\" mkdir models
if not exist "logs\" mkdir logs
echo [OK] Directories created

echo.
echo ===================================
echo Setup Complete!
echo ===================================
echo.
echo To start the server, run:
echo   python app/main.py
echo.
echo Or with uvicorn:
echo   uvicorn app.main:app --reload
echo.
echo API Documentation will be available at:
echo   http://localhost:8000/docs
echo.
echo Health Check:
echo   http://localhost:8000/health
echo.
echo ===================================
echo.

REM Ask if user wants to start the server
set /p START_SERVER="Do you want to start the server now? (Y/N): "
if /i "%START_SERVER%"=="Y" (
    echo.
    echo Starting server...
    echo Press Ctrl+C to stop the server
    echo.
    python app/main.py
)

pause
