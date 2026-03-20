#!/usr/bin/env python3
"""
Local development environment setup script.
Sets up PostgreSQL, Redis, and creates initial data for testing.

Usage:
    python setup_local_env.py
"""

import os
import sys
import subprocess
import psycopg2
import redis
from pathlib import Path
import json
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LocalEnvironmentSetup:
    """Setup local development environment for fraud detection system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.server_dir = self.project_root / "server"
        self.env_file = self.server_dir / ".env"
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'fraud_detection',
            'user': 'fraud_user',
            'password': 'fraud_pass'
        }
        
        # Redis configuration
        self.redis_config = {
            'host': 'localhost',
            'port': 6379,
            'db': 0
        }
    
    def create_env_file(self):
        """Create .env file for local development."""
        print("Creating .env file for local development...")
        
        env_content = f"""
# Local Development Environment Variables
DATABASE_URL=postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}
REDIS_URL=redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}

# Application Settings
DEBUG=true
LOG_LEVEL=info
ENVIRONMENT=development

# JWT Settings
JWT_SECRET=local-dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Settings
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# ML Model Settings
MODEL_PATH=./ml_models/lstm_fraud_model.h5
SEQUENCE_LENGTH=10

# Cache Settings
CACHE_TTL_TRANSACTIONS=300
CACHE_TTL_PREDICTIONS=300
CACHE_TTL_STATS=600

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads
""".strip()
        
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ .env file created: {self.env_file}")
    
    def setup_database(self):
        """Setup PostgreSQL database."""
        print("Setting up PostgreSQL database...")
        
        try:
            # Connect to PostgreSQL server (default postgres database)
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='postgres',
                user='postgres',
                password='password'  # Default PostgreSQL password
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Create user if not exists
            try:
                cursor.execute(f"CREATE USER {self.db_config['user']} WITH PASSWORD '{self.db_config['password']}'")
                print(f"✅ Created database user: {self.db_config['user']}")
            except psycopg2.errors.DuplicateObject:
                print(f"ℹ️ Database user already exists: {self.db_config['user']}")
            
            # Create database if not exists
            try:
                cursor.execute(f"CREATE DATABASE {self.db_config['database']} OWNER {self.db_config['user']}")
                print(f"✅ Created database: {self.db_config['database']}")
            except psycopg2.errors.DuplicateDatabase:
                print(f"ℹ️ Database already exists: {self.db_config['database']}")
            
            # Grant privileges
            cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {self.db_config['database']} TO {self.db_config['user']}")
            
            conn.close()
            
            # Test connection to the new database
            test_conn = psycopg2.connect(**self.db_config)
            test_conn.close()
            print("✅ Database connection test successful")
            
        except psycopg2.OperationalError as e:
            print(f"❌ Database connection failed: {e}")
            print("Please ensure PostgreSQL is running and accessible")
            return False
        
        return True
    
    def setup_redis(self):
        """Setup Redis connection."""
        print("Setting up Redis...")
        
        try:
            r = redis.Redis(**self.redis_config)
            r.ping()
            print("✅ Redis connection successful")
            
            # Test basic operations
            r.set('test_key', 'test_value', ex=10)
            value = r.get('test_key')
            if value == b'test_value':
                print("✅ Redis operations working correctly")
                r.delete('test_key')
            
        except redis.ConnectionError as e:
            print(f"❌ Redis connection failed: {e}")
            print("Please ensure Redis is running and accessible")
            return False
        
        return True
    
    def create_directories(self):
        """Create necessary directories."""
        print("Creating necessary directories...")
        
        directories = [
            self.server_dir / "ml_models",
            self.server_dir / "uploads",
            self.server_dir / "logs",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
    
    def create_dummy_model(self):
        """Create a dummy ML model for testing."""
        print("Creating dummy ML model...")
        
        try:
            # Change to server directory
            os.chdir(self.server_dir)
            
            # Create dummy model script
            dummy_script = self.server_dir / "scripts" / "create_dummy_model.py"
            dummy_script.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dummy_script, 'w') as f:
                f.write("""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf
import numpy as np
from app.ml.model import FraudDetectionModel

def create_dummy_model():
    print("Creating dummy LSTM model...")
    
    # Create model instance
    model = FraudDetectionModel()
    
    # Build model with dummy input shape
    input_shape = (10, 20)  # sequence_length=10, features=20
    model.build_model(input_shape)
    
    # Save model
    model_path = "ml_models/lstm_fraud_model.h5"
    model.save_model(model_path)
    
    print(f"✅ Dummy model saved to: {model_path}")
    
    # Test loading
    test_model = FraudDetectionModel()
    test_model.load_model(model_path)
    print("✅ Model loading test successful")

if __name__ == "__main__":
    create_dummy_model()
""")
            
            # Run dummy model creation
            result = subprocess.run([sys.executable, str(dummy_script)], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Dummy model created successfully")
                print(result.stdout)
            else:
                print(f"❌ Failed to create dummy model: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating dummy model: {e}")
            return False
        
        return True
    
    def run_database_migrations(self):
        """Run database migrations."""
        print("Running database migrations...")
        
        try:
            os.chdir(self.server_dir)
            
            # Run Alembic migrations
            result = subprocess.run([
                sys.executable, "-m", "alembic", "upgrade", "head"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Database migrations completed successfully")
                print(result.stdout)
            else:
                print(f"❌ Migration failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error running migrations: {e}")
            return False
        
        return True
    
    def test_backend_startup(self):
        """Test backend startup."""
        print("Testing backend startup...")
        
        try:
            os.chdir(self.server_dir)
            
            # Test imports
            test_script = """
import sys
sys.path.append('.')

try:
    from app.main import app
    from app.database import engine
    from app.ml.inference import PredictionEngine
    print("✅ All imports successful")
    
    # Test database connection
    import asyncio
    async def test_db():
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        print("✅ Database connection test successful")
    
    asyncio.run(test_db())
    
    # Test model loading
    engine = PredictionEngine()
    print("✅ PredictionEngine loaded successfully")
    
except Exception as e:
    print(f"❌ Backend test failed: {e}")
    sys.exit(1)
"""
            
            result = subprocess.run([sys.executable, "-c", test_script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Backend startup test successful")
                print(result.stdout)
                return True
            else:
                print(f"❌ Backend startup test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing backend: {e}")
            return False
    
    def generate_test_data(self):
        """Generate synthetic test data."""
        print("Generating synthetic test data...")
        
        try:
            os.chdir(self.server_dir)
            
            # Run data generation script
            script_path = "scripts/generate_test_data.py"
            output_path = "data/synthetic_transactions.csv"
            
            result = subprocess.run([
                sys.executable, script_path,
                "--output", output_path,
                "--samples", "1000",
                "--fraud-ratio", "0.05"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Test data generated successfully")
                print(result.stdout)
                return True
            else:
                print(f"❌ Test data generation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error generating test data: {e}")
            return False
    
    def run_setup(self):
        """Run complete local environment setup."""
        print("🚀 Starting local environment setup...")
        print(f"Project root: {self.project_root}")
        
        steps = [
            ("Create .env file", self.create_env_file),
            ("Setup database", self.setup_database),
            ("Setup Redis", self.setup_redis),
            ("Create directories", self.create_directories),
            ("Create dummy model", self.create_dummy_model),
            ("Run migrations", self.run_database_migrations),
            ("Test backend", self.test_backend_startup),
            ("Generate test data", self.generate_test_data),
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            try:
                if not step_func():
                    failed_steps.append(step_name)
            except Exception as e:
                print(f"❌ {step_name} failed with exception: {e}")
                failed_steps.append(step_name)
        
        print("\n" + "="*50)
        print("🎯 SETUP SUMMARY")
        print("="*50)
        
        if not failed_steps:
            print("✅ All setup steps completed successfully!")
            print("\n🚀 Next steps:")
            print("1. Start backend: uvicorn app.main:app --reload")
            print("2. Start frontend: cd ../client && npm run dev")
            print("3. Open browser: http://localhost:5173")
            print("4. Test API: http://localhost:8000/docs")
        else:
            print(f"❌ Failed steps: {', '.join(failed_steps)}")
            print("\n🔧 Please resolve the issues above and re-run the setup")
        
        return len(failed_steps) == 0


def main():
    """Main setup function."""
    setup = LocalEnvironmentSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
