@echo off
REM Startup script for Crop Disease Detection Backend

echo ========================================
echo Crop Disease Detection Backend Setup
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.original to .env and configure it.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Create necessary directories
echo Creating upload directories...
if not exist uploads\images mkdir uploads\images
if not exist uploads\heatmaps mkdir uploads\heatmaps
if not exist uploads\reports mkdir uploads\reports
if not exist logs mkdir logs
if not exist models mkdir models
echo.

REM Check if model files exist
if not exist models\crop_disease_master_model.keras (
    echo WARNING: AI model not found at models\crop_disease_master_model.keras
    echo Copying from Model directory...
    copy "..\Model\model\crop_disease_master_model.keras" "models\" >nul 2>&1
    copy "..\Model\data\new_label_map.txt" "models\" >nul 2>&1
)
echo.

echo ========================================
echo Starting FastAPI Server...
echo ========================================
echo.
echo Access the API at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

REM Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
