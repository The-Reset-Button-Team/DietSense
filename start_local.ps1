# =============================================================================
# DietSense - Local Startup Script (Windows PowerShell)
# Initializes local SQLite database and launches both backend & frontend
# =============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " DietSense - Starting Local Architecture                  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Initialize local SQLite database
Write-Host ""
Write-Host "[1/3] Initializing local SQLite database..." -ForegroundColor Yellow
python backend/db/init_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Database initialization encountered an error." -ForegroundColor Red
    exit 1
}

# Step 2: Launch Backend
Write-Host ""
Write-Host "[2/3] Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python run_backend.py"

# Step 3: Launch Frontend
Write-Host ""
Write-Host "[3/3] Launching Next.js Frontend on http://localhost:3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " DietSense is running!" -ForegroundColor Green
Write-Host "   Frontend:          http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API:       http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
