# Tennis Reservation - 서버 실행 스크립트

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Tennis Reservation Server Starter" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Python 경로 확인
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python이 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "https://www.python.org/downloads/ 에서 설치하세요." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/3] Python 가상환경 설정..." -ForegroundColor Green
Set-Location "$PSScriptRoot\backend"

# 가상환경이 없으면 생성
if (-not (Test-Path "venv")) {
    Write-Host " Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# 가상환경 활성화
& ".\venv\Scripts\Activate.ps1"

# 의존성 설치
Write-Host " Checking dependencies..." -ForegroundColor Yellow
pip install fastapi uvicorn selenium webdriver-manager requests python-dotenv pydantic --quiet

Write-Host ""
Write-Host "[2/3] FastAPI 서버 실행 중..." -ForegroundColor Green
Write-Host " http://localhost:8000 에서 접근 가능" -ForegroundColor Cyan
Write-Host " Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

uvicorn server:app --host 0.0.0.0 --port 8000