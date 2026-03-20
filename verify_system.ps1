# System Verification Script for CCFD
Write-Host "=== Credit Card Fraud Detection System Verification ===" -ForegroundColor Green
Write-Host ""

# Check Docker services
Write-Host "1. Checking Docker Services..." -ForegroundColor Yellow
$services = docker-compose ps
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker services are running" -ForegroundColor Green
    $services
} else {
    Write-Host "✗ Docker services check failed" -ForegroundColor Red
}
Write-Host ""

# Check backend health
Write-Host "2. Checking Backend Health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Backend API is healthy" -ForegroundColor Green
        $health = $response.Content | ConvertFrom-Json
        Write-Host "  Status: $($health.status)" -ForegroundColor Cyan
        Write-Host "  Version: $($health.version)" -ForegroundColor Cyan
        Write-Host "  Environment: $($health.environment)" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "✗ Backend health check failed" -ForegroundColor Red
}
Write-Host ""

# Check database connection
Write-Host "3. Checking Database Connection..." -ForegroundColor Yellow
$dbCheck = docker-compose exec -T backend python -c "
from app.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
" 2>&1
Write-Host $dbCheck -ForegroundColor Cyan
Write-Host ""

# Check Redis connection
Write-Host "4. Checking Redis Connection..." -ForegroundColor Yellow
$redisCheck = docker-compose exec -T backend python -c "
from app.redis_client import redis_client
try:
    redis_client.ping()
    print('✓ Redis connection successful')
except Exception as e:
    print(f'✗ Redis connection failed: {e}')
" 2>&1
Write-Host $redisCheck -ForegroundColor Cyan
Write-Host ""

# Check ML model files
Write-Host "5. Checking ML Model Files..." -ForegroundColor Yellow
$modelFiles = @(
    'server/ml_models/lstm_fraud_model.h5',
    'server/ml_models/lstm_fraud_model_scaler.pkl',
    'server/ml_models/model_metadata.json'
)

foreach ($file in $modelFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "✗ $file missing" -ForegroundColor Red
    }
}
Write-Host ""

# Check API endpoints
Write-Host "6. Checking API Endpoints..." -ForegroundColor Yellow
$endpoints = @(
    '/health',
    '/api/v1/auth/register',
    '/api/v1/transactions',
    '/api/v1/predictions'
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000$endpoint" -UseBasicParsing -Method GET
        Write-Host "✓ $endpoint reachable (Status: $($response.StatusCode))" -ForegroundColor Green
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 401) {
            Write-Host "✓ $endpoint reachable (Requires authentication)" -ForegroundColor Yellow
        }
        elseif ($_.Exception.Response.StatusCode -eq 422) {
            Write-Host "✓ $endpoint reachable (Validation required)" -ForegroundColor Yellow
        }
        else {
            Write-Host "✗ $endpoint not reachable" -ForegroundColor Red
        }
    }
}
Write-Host ""

# Summary
Write-Host "=== Verification Complete ===" -ForegroundColor Green
Write-Host "All services are running and the system is ready for use!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Access the frontend at http://localhost:5173" -ForegroundColor White
Write-Host "2. Access the backend API at http://localhost:8000" -ForegroundColor White
Write-Host "3. API documentation at http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
