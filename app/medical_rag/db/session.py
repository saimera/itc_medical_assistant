import os  # Environment variable read karne ke liye

from dotenv import load_dotenv  # .env file load karne ke liye
from sqlalchemy import create_engine  # Database engine banane ke liye
from sqlalchemy.orm import sessionmaker  # Session factory banane ke liye

load_dotenv()  # .env ke variables environment mein load karo

DATABASE_URL = os.getenv("DATABASE_URL")  # PostgreSQL connection URL lo

if not DATABASE_URL:  # URL missing ho to
    raise RuntimeError("DATABASE_URL .env mein set nahi hai")  # Samajhne layak error dikhao

engine = create_engine(DATABASE_URL, pool_pre_ping=True)  # Database connections manage karne wala engine banao
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)  # Engine se sessions banane ki factory banao
