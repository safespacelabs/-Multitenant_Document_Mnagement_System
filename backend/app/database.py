from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import MANAGEMENT_DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW

# Management database engine (backward compatibility)
engine = create_engine(
    MANAGEMENT_DATABASE_URL,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_pre_ping=True  # Enables connection health checks
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Legacy function for backward compatibility - returns management DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import the new database manager for multi-tenant support
from app.services.database_manager import db_manager

def get_management_db():
    """Get management database session using the new database manager"""
    db = db_manager.management_session_local()
    try:
        yield db
    finally:
        db.close()

def get_company_db(company_id: str = None, database_url: str = None):
    """Get company-specific database session"""
    if company_id and database_url:
        return db_manager.get_company_db(company_id, database_url)
    else:
        # For system admin users, get the first available company database
        # This allows system admins to view documents from all companies
        return db_manager.get_default_company_db()

def get_default_company_db():
    """Get a default company database for system admin operations"""
    return db_manager.get_default_company_db()