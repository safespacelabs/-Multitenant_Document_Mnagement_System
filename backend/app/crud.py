"""
CRUD operations - Legacy compatibility layer
Note: This is kept for backward compatibility but the new system uses 
company-specific databases with direct SQLAlchemy operations in routers.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas, auth
from app.models_company import User as CompanyUser, Document as CompanyDocument
from app.utils.helpers import generate_unique_id

# Management Database CRUD operations (System users and companies)
def get_system_user(db: Session, user_id: str) -> Optional[models.SystemUser]:
    return db.query(models.SystemUser).filter(models.SystemUser.id == user_id).first()

def get_system_user_by_email(db: Session, email: str) -> Optional[models.SystemUser]:
    return db.query(models.SystemUser).filter(models.SystemUser.email == email).first()

def get_system_user_by_username(db: Session, username: str) -> Optional[models.SystemUser]:
    return db.query(models.SystemUser).filter(models.SystemUser.username == username).first()

# Company CRUD operations (Management Database)
def get_company(db: Session, company_id: str) -> Optional[models.Company]:
    return db.query(models.Company).filter(models.Company.id == company_id).first()

def get_company_by_email(db: Session, email: str) -> Optional[models.Company]:
    return db.query(models.Company).filter(models.Company.email == email).first()

def get_companies(db: Session, skip: int = 0, limit: int = 100) -> List[models.Company]:
    return db.query(models.Company).filter(models.Company.is_active == True).offset(skip).limit(limit).all()

def create_company(db: Session, company: schemas.CompanyCreate) -> models.Company:
    company_id = generate_unique_id("comp")
    db_company = models.Company(
        id=company_id,
        name=company.name,
        email=company.email,
        database_name=f"company_{company_id}",
        s3_bucket_name=""  # Will be set after S3 bucket creation
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

# Company Database CRUD operations (for individual companies)
def get_company_user(db: Session, user_id: str) -> Optional[CompanyUser]:
    """Get user from company database"""
    return db.query(CompanyUser).filter(CompanyUser.id == user_id).first()

def get_company_user_by_email(db: Session, email: str) -> Optional[CompanyUser]:
    """Get user by email from company database"""
    return db.query(CompanyUser).filter(CompanyUser.email == email).first()

def get_company_user_by_username(db: Session, username: str) -> Optional[CompanyUser]:
    """Get user by username from company database"""
    return db.query(CompanyUser).filter(CompanyUser.username == username).first()

def get_company_users(db: Session, skip: int = 0, limit: int = 100) -> List[CompanyUser]:
    """Get all active users from company database"""
    return db.query(CompanyUser).filter(
        CompanyUser.is_active == True
    ).offset(skip).limit(limit).all()

def create_company_user(db: Session, user: schemas.CompanyUserCreate) -> CompanyUser:
    """Create user in company database"""
    hashed_password = auth.get_password_hash(user.password)
    db_user = CompanyUser(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role.value,
        s3_folder=f"users/{user.username}/"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Document CRUD operations (Company Database)
def get_company_document(db: Session, document_id: str) -> Optional[CompanyDocument]:
    """Get document from company database"""
    return db.query(CompanyDocument).filter(CompanyDocument.id == document_id).first()

def get_documents_by_company_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[CompanyDocument]:
    """Get documents by user from company database"""
    return db.query(CompanyDocument).filter(
        CompanyDocument.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_all_company_documents(db: Session, skip: int = 0, limit: int = 100) -> List[CompanyDocument]:
    """Get all documents from company database"""
    return db.query(CompanyDocument).offset(skip).limit(limit).all()

def create_company_document(
    db: Session, 
    document: schemas.DocumentCreate, 
    user_id: str
) -> CompanyDocument:
    """Create document in company database"""
    db_document = CompanyDocument(
        filename=document.filename,
        original_filename=document.original_filename,
        file_path=document.file_path,
        file_size=document.file_size,
        file_type=document.file_type,
        s3_key=document.s3_key,
        user_id=user_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def update_company_document_metadata(db: Session, document_id: str, metadata: dict) -> Optional[CompanyDocument]:
    """Update document metadata in company database"""
    document = db.query(CompanyDocument).filter(CompanyDocument.id == document_id).first()
    if document:
        # Update using SQLAlchemy update method
        db.query(CompanyDocument).filter(CompanyDocument.id == document_id).update({
            CompanyDocument.metadata_json: metadata,
            CompanyDocument.processed: True
        })
        db.commit()
        db.refresh(document)
    return document

# Legacy functions for backward compatibility (deprecated)
def get_user(db: Session, user_id: str) -> Optional[CompanyUser]:
    """Legacy: Use get_company_user instead"""
    return get_company_user(db, user_id)

def get_user_by_email(db: Session, email: str) -> Optional[CompanyUser]:
    """Legacy: Use get_company_user_by_email instead"""
    return get_company_user_by_email(db, email)

def get_user_by_username(db: Session, username: str) -> Optional[CompanyUser]:
    """Legacy: Use get_company_user_by_username instead"""
    return get_company_user_by_username(db, username)

# Note: Old User and ChatHistory CRUD operations removed
# These are now handled directly in company databases via routers 