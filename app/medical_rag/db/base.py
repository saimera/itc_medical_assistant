from sqlalchemy.orm import DeclarativeBase  # SQLAlchemy ke declarative model base ko import karo

class Base(DeclarativeBase):  # Future database models ke liye shared parent class
     pass  # Abhi Base mein extra configuration nahi

    