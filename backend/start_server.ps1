# PowerShell script to start the backend server
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting Crop Disease Detection Backend" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Navigate to backend directory
Set-Location $PSScriptRoot

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please ensure .env file exists in the backend directory." -ForegroundColor Yellow
    exit 1
}

# Start the server
Write-Host "Starting FastAPI server on http://0.0.0.0:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
