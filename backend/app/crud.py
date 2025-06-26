from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas, auth
from app.utils.helpers import generate_unique_id

# User CRUD operations
def get_user(db: Session, user_id: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def get_users_by_company(db: Session, company_id: str, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).filter(
        models.User.company_id == company_id,
        models.User.is_active == True
    ).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        company_id=user.company_id,
        s3_folder=f"users/{user.username}/"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Company CRUD operations
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
        database_name=f"db_{company_id}",
        s3_bucket_name=""  # Will be set after S3 bucket creation
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

# Document CRUD operations
def get_document(db: Session, document_id: str) -> Optional[models.Document]:
    return db.query(models.Document).filter(models.Document.id == document_id).first()

def get_documents_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[models.Document]:
    return db.query(models.Document).filter(
        models.Document.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_documents_by_company(db: Session, company_id: str, skip: int = 0, limit: int = 100) -> List[models.Document]:
    return db.query(models.Document).filter(
        models.Document.company_id == company_id
    ).offset(skip).limit(limit).all()

def create_document(db: Session, document: schemas.DocumentCreate, user_id: str, company_id: str) -> models.Document:
    db_document = models.Document(
        filename=document.filename,
        original_filename=document.original_filename,
        file_path=document.file_path,
        file_size=document.file_size,
        file_type=document.file_type,
        s3_key=document.s3_key,
        user_id=user_id,
        company_id=company_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def update_document_metadata(db: Session, document_id: str, metadata: dict) -> Optional[models.Document]:
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if document:
        document.metadata_json = metadata
        document.processed = True
        db.commit()
        db.refresh(document)
    return document

# Chat CRUD operations
def get_chat_history(db: Session, user_id: str, limit: int = 50) -> List[models.ChatHistory]:
    return db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == user_id
    ).order_by(models.ChatHistory.created_at.desc()).limit(limit).all()

def create_chat_message(db: Session, user_id: str, company_id: str, question: str, answer: str, context_docs: List[str] = None) -> models.ChatHistory:
    db_chat = models.ChatHistory(
        user_id=user_id,
        company_id=company_id,
        question=question,
        answer=answer,
        context_documents=context_docs or []
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat 