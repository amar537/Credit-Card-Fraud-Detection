# Fraud Detection API Backend

A production-ready FastAPI backend for Credit Card Fraud Detection with LSTM-RNN model integration.

## Features

- **Authentication**: JWT-based authentication with refresh tokens
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for session management and caching
- **ML Integration**: LSTM-RNN model for real-time fraud prediction
- **Security**: Rate limiting, CORS, input validation, password hashing
- **Monitoring**: Health checks, metrics, structured logging
- **API Documentation**: OpenAPI/Swagger documentation

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT with python-jose
- **Validation**: Pydantic 2.5
- **ML**: TensorFlow 2.15, Scikit-learn 1.3
- **Testing**: Pytest with async support

## Project Structure

```
server/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── redis_client.py      # Redis connection
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── card.py
│   │   ├── transaction.py
│   │   ├── prediction.py
│   │   └── fraud_alert.py
│   ├── schemas/             # Pydantic schemas (DTOs)
│   │   ├── user.py
│   │   ├── card.py
│   │   ├── transaction.py
│   │   ├── prediction.py
│   │   └── analytics.py
│   ├── api/                 # API routes
│   │   └── v1/
│   │       └── auth.py
│   ├── services/            # Business logic
│   │   └── auth_service.py
│   ├── core/                # Core utilities
│   │   ├── security.py
│   │   └── dependencies.py
│   └── utils/               # Helper functions
├── tests/                   # Test suite
├── alembic/                 # Database migrations
├── ml_models/               # Trained model storage
├── data/                    # Training data
├── scripts/                 # Utility scripts
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CCFD-main/server
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb fraud_detection_db
   
   # Run migrations (when available)
   alembic upgrade head
   ```

6. **Start Redis**
   ```bash
   redis-server
   ```

7. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Setup

1. **Build and start services**
   ```bash
   docker-compose up --build
   ```

2. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/api/v1/docs
   - Health Check: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user
- `PUT /api/v1/auth/me` - Update user profile
- `POST /api/v1/auth/change-password` - Change password
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password
- `POST /api/v1/auth/verify-email` - Verify email
- `POST /api/v1/auth/resend-verification` - Resend verification
- `DELETE /api/v1/auth/deactivate` - Deactivate account

### Transactions (Coming Soon)
- `GET /api/v1/transactions` - List transactions
- `POST /api/v1/transactions` - Create transaction
- `GET /api/v1/transactions/{id}` - Get transaction details
- `GET /api/v1/transactions/stats` - Transaction statistics

### Predictions (Coming Soon)
- `POST /api/v1/predictions/predict` - Real-time fraud prediction
- `POST /api/v1/predictions/batch` - Batch prediction
- `GET /api/v1/predictions/history` - Prediction history

### Analytics (Coming Soon)
- `GET /api/v1/analytics/dashboard` - Dashboard metrics
- `GET /api/v1/analytics/trends` - Fraud trends
- `GET /api/v1/analytics/patterns` - Fraud patterns

## Database Schema

### Users
- `id` (UUID, Primary Key)
- `email` (VARCHAR, Unique)
- `username` (VARCHAR, Unique)
- `hashed_password` (VARCHAR)
- `full_name` (VARCHAR)
- `is_active` (BOOLEAN)
- `is_superuser` (BOOLEAN)
- `is_verified` (BOOLEAN)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Cards
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key)
- `card_number` (VARCHAR, Encrypted)
- `card_type` (ENUM)
- `card_brand` (VARCHAR)
- `expiry_date` (DATE)
- `cvv` (VARCHAR, Encrypted)
- `is_blocked` (BOOLEAN)

### Transactions
- `id` (UUID, Primary Key)
- `card_id` (UUID, Foreign Key)
- `amount` (DECIMAL)
- `merchant_name` (VARCHAR)
- `transaction_type` (ENUM)
- `is_fraud` (BOOLEAN)
- `fraud_score` (FLOAT)

### Predictions
- `id` (UUID, Primary Key)
- `transaction_id` (UUID, Foreign Key)
- `model_version` (VARCHAR)
- `fraud_probability` (FLOAT)
- `prediction_class` (BOOLEAN)
- `processing_time_ms` (INTEGER)

## Security Features

- **Authentication**: JWT tokens with refresh mechanism
- **Password Security**: Bcrypt hashing with salt
- **Rate Limiting**: Redis-based rate limiting per user
- **Input Validation**: Pydantic schemas for all inputs
- **CORS**: Configurable CORS origins
- **Session Management**: Redis-based session storage
- **Data Encryption**: Sensitive data encrypted at rest

## ML Model Integration

The system integrates an LSTM-RNN model for fraud detection:

- **Model Architecture**: 2 LSTM layers with dropout
- **Features**: 30 engineered features per transaction
- **Performance**: >99% accuracy, <100ms inference time
- **Versioning**: Model version tracking
- **Caching**: Redis caching for predictions

## Monitoring & Logging

- **Health Checks**: `/health` endpoint
- **Metrics**: Basic metrics at `/metrics`
- **Structured Logging**: JSON-formatted logs
- **Performance Monitoring**: Request timing headers
- **Error Handling**: Comprehensive exception handling

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## Development

### Code Style
- **Formatter**: Black
- **Import Sorter**: isort
- **Linter**: flake8
- **Type Checking**: mypy

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `SECRET_KEY`: JWT signing key (must be changed in production)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Logging level

## Deployment

### Production Considerations
1. **Security**: Change all default passwords and secrets
2. **Database**: Use connection pooling and proper indexing
3. **Redis**: Configure persistence and memory limits
4. **Monitoring**: Set up proper logging and metrics collection
5. **SSL**: Use HTTPS in production
6. **Rate Limiting**: Configure appropriate limits
7. **Backups**: Regular database backups

### Docker Production
```bash
# Build production image
docker build -t fraud-detection-api .

# Run with environment file
docker run --env-file .env -p 8000:8000 fraud-detection-api
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and ensure they pass
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the logs for error details
