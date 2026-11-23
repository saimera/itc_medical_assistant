from sqlalchemy import text 
from app.medical_rag.db.session import SessionLocal

with SessionLocal() as session:
    # Test the database connection by executing a simple query to retrieve the current database name.
    database_name = session.execute(text("SELECT current_database()")).scalar_one() 
    print(f"Connected to database: {database_name}")