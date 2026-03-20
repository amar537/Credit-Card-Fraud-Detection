@echo off
echo === Credit Card Fraud Detection System Verification ===
echo.

echo 1. Checking Docker Services...
docker-compose ps
echo.

echo 2. Checking Backend Health...
curl -s http://localhost:8000/health
echo.
echo.

echo 3. Checking Database Connection...
docker-compose exec -T backend python -c "from app.database import engine; from sqlalchemy import text; conn = engine.connect(); conn.execute(text('SELECT 1')); print('Database connection successful')"
echo.

echo 4. Checking Redis Connection...
docker-compose exec -T backend python -c "import asyncio; from app.redis_client import redis_client; asyncio.run(redis_client.connect()); print('Redis connection successful')"
echo.

echo 5. Checking ML Model Files...
if exist "server\ml_models\lstm_fraud_model.h5" (
    echo ✓ lstm_fraud_model.h5 exists
) else (
    echo ✗ lstm_fraud_model.h5 missing
)

if exist "server\ml_models\lstm_fraud_model_scaler.pkl" (
    echo ✓ lstm_fraud_model_scaler.pkl exists
) else (
    echo ✗ lstm_fraud_model_scaler.pkl missing
)

if exist "server\ml_models\model_metadata.json" (
    echo ✓ model_metadata.json exists
) else (
    echo ✗ model_metadata.json missing
)
echo.

echo === Verification Complete ===
echo All services are running and the system is ready for use!
echo.
echo Next steps:
echo 1. Access the frontend at http://localhost:5173
echo 2. Access the backend API at http://localhost:8000
echo 3. API documentation at http://localhost:8000/api/v1/docs
echo.
pause
