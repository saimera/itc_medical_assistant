from sqlalchemy import text  # Simple SQL query chalane ke liye
from app.medical_rag.db.session import SessionLocal# Apni session factory import karo

with SessionLocal() as session:  # Session kholo aur kaam ke baad band karo
    database_name = session.execute(text("SELECT current_database()")).scalar_one()  # Connected database ka naam lo
    print(f"Connected to database: {database_name}")  # Result dikhao