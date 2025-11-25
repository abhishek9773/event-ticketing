from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
from typing import Generator

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable is not set in .env file.")

engine = create_engine(DATABASE_URL)

# 2. Create the Session Local class
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# 3. Create the Base Class for Models
# This is the base class from which all SQLAlchemy models will inherit.
Base = declarative_base()

# 4. Database Session Dependency
def get_db() -> Generator:
    """
    Dependency function for FastAPI routes to manage the database session lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()