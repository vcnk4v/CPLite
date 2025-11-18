import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL from environment variable with fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cplite:cplitepassword@summary-db:5432/summary_service_db",
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for database models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    """
    Get database session.
    Yields a database session that will be closed after the request is complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
