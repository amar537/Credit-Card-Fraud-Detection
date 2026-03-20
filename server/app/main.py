from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from sqlalchemy import text
from app.api.v1 import auth, transactions, predictions, analytics
from app.redis_client import redis_client
from fastapi.staticfiles import StaticFiles
import os
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.models.user import User
from app.core.security import get_password_hash

# Configure logging
log_level = settings.LOG_LEVEL.upper() if hasattr(settings.LOG_LEVEL, 'upper') else settings.LOG_LEVEL
logging.basicConfig(
    level=log_level,
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Fraud Detection API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Lightweight schema guard to auto-add missing columns on existing DBs
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE IF EXISTS predictions
                ADD COLUMN IF NOT EXISTS risk_level VARCHAR(50) DEFAULT 'low';
            """))
            conn.execute(text("""
                ALTER TABLE IF EXISTS predictions
                ADD COLUMN IF NOT EXISTS feedback_notes TEXT;
            """))
        logger.info("Schema guard executed: predictions columns ensured")
    except Exception as e:
        logger.error(f"Schema guard failed: {e}")
    
    # Connect to Redis
    await redis_client.connect()
    logger.info("Redis connection established")

    # Seed/update admin user if configured
    try:
        if settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
            db = SessionLocal()
            try:
                admin = AuthService.get_user_by_email(db, settings.ADMIN_EMAIL)
                if not admin:
                    # Create admin
                    user_data = UserCreate(
                        email=settings.ADMIN_EMAIL,
                        username=(settings.ADMIN_EMAIL.split("@", 1)[0])[:30],
                        password=settings.ADMIN_PASSWORD,
                        full_name="Admin",
                        is_active=True,
                    )
                    admin = AuthService.create_user(db, user_data)
                    admin.is_superuser = True
                    admin.is_verified = True
                    db.commit()
                    db.refresh(admin)
                    logger.info("Admin user created: %s", settings.ADMIN_EMAIL)
                else:
                    # Ensure flags and allow password change if needed
                    updated = False
                    if not admin.is_superuser:
                        admin.is_superuser = True
                        updated = True
                    if not admin.is_active:
                        admin.is_active = True
                        updated = True
                    if not admin.is_verified:
                        admin.is_verified = True
                        updated = True
                    # Update password to ADMIN_PASSWORD
                    if settings.ADMIN_PASSWORD:
                        try:
                            admin.hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
                            updated = True
                        except Exception:
                            pass
                    if updated:
                        db.commit()
                        db.refresh(admin)
                    logger.info("Admin user ensured: %s", settings.ADMIN_EMAIL)
            finally:
                db.close()
    except Exception as e:
        logger.error("Failed to seed admin user: %s", e)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Fraud Detection API...")
    await redis_client.disconnect()
    logger.info("Redis connection closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A production-ready Credit Card Fraud Detection System with LSTM-RNN model",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors(),
            "status_code": 422,
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "path": str(request.url)
        }
    )


# Include API routers
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["authentication"])
app.include_router(transactions.router, prefix=settings.API_V1_STR, tags=["transactions"])
app.include_router(predictions.router, prefix=settings.API_V1_STR, tags=["predictions"])
app.include_router(analytics.router, prefix=settings.API_V1_STR, tags=["analytics"])

# Custom ReDoc HTML
def custom_redoc_html():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!-- Preload fonts -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Roboto', sans-serif;
            }}
            .loading {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                font-size: 1.2rem;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <div id="redoc-container" class="loading">Loading API Documentation...</div>
        <!-- Using unpkg as an alternative CDN -->
        <script src="https://unpkg.com/redoc@2.0.0/bundles/redoc.standalone.min.js"></script>
        <script>
            // Fallback to local Redoc if CDN fails
            function loadRedoc() {{
                if (typeof Redoc === 'undefined') {{
                    console.warn('CDN failed, loading from local fallback...');
                    var script = document.createElement('script');
                    script.src = '/static/redoc.standalone.js';
                    script.onload = initRedoc;
                    document.head.appendChild(script);
                }} else {{
                    initRedoc();
                }}
            }}

            function initRedoc() {{
                Redoc.init(
                    '{settings.API_V1_STR}/openapi.json', 
                    {{
                        scrollYOffset: 50,
                        hideDownloadButton: false,
                        expandResponses: "200,201,204",
                        requiredPropsFirst: true,
                        theme: {{
                            colors: {{
                                primary: {{ main: '#1890ff' }},
                                success: {{ main: '#52c41a' }},
                                warning: {{ main: '#faad14' }},
                                error: {{ main: '#f5222d' }},
                            }},
                            typography: {{
                                fontFamily: "'Roboto', sans-serif",
                                headings: {{
                                    fontFamily: "'Montserrat', sans-serif"
                                }}
                            }}
                        }}
                    }}, 
                    document.getElementById('redoc-container'),
                    function() {{
                        document.getElementById('redoc-container').classList.remove('loading');
                    }}
                );
            }}

            // Load Redoc when the page is ready
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', loadRedoc);
            }} else {{
                loadRedoc();
            }}
        </script>
    </body>
    </html>
    """

# Serve static files (for fallback ReDoc JS if needed)
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

# Custom ReDoc route
@app.get(settings.API_V1_STR + "/redoc", include_in_schema=False)
async def redoc_ui():
    return HTMLResponse(custom_redoc_html())


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Fraud Detection API",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health"
    }


# Metrics endpoint (basic implementation)
@app.get("/metrics", tags=["Metrics"])
async def metrics():
    """Basic metrics endpoint."""
    return {
        "uptime": time.time(),
        "version": settings.APP_VERSION,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
