from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\''))
    tables = [row[0] for row in result]
    print("Tables in database:")
    for table in tables:
        print(f"  - {table}")
