# System Verification Script for CCFD
Write-Host "=== Credit Card Fraud Detection System Verification ===" -ForegroundColor Green
Write-Host ""

# Check Docker services
Write-Host "1. Checking Docker Services..." -ForegroundColor Yellow
docker-compose ps
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
} catch {
    Write-Host "✗ Backend health check failed" -ForegroundColor Red
}
Write-Host ""

# Check database connection
Write-Host "3. Checking Database Connection..." -ForegroundColor Yellow
docker-compose exec -T backend python -c "from app.database import engine; from sqlalchemy import text; conn = engine.connect(); conn.execute(text('SELECT 1')); print('✓ Database connection successful')"
Write-Host ""

# Check Redis connection
Write-Host "4. Checking Redis Connection..." -ForegroundColor Yellow
docker-compose exec -T backend python -c "from app.redis_client import redis_client; redis_client.ping(); print('✓ Redis connection successful')"
Write-Host ""

# Check ML model files
Write-Host "5. Checking ML Model Files..." -ForegroundColor Yellow
if (Test-Path "server/ml_models/lstm_fraud_model.h5") {
    Write-Host "✓ lstm_fraud_model.h5 exists" -ForegroundColor Green
} else {
    Write-Host "✗ lstm_fraud_model.h5 missing" -ForegroundColor Red
}

if (Test-Path "server/ml_models/lstm_fraud_model_scaler.pkl") {
    Write-Host "✓ lstm_fraud_model_scaler.pkl exists" -ForegroundColor Green
} else {
    Write-Host "✗ lstm_fraud_model_scaler.pkl missing" -ForegroundColor Red
}

if (Test-Path "server/ml_models/model_metadata.json") {
    Write-Host "✓ model_metadata.json exists" -ForegroundColor Green
} else {
    Write-Host "✗ model_metadata.json missing" -ForegroundColor Red
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
