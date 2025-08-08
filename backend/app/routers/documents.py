from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import uuid
import json
import re
from io import BytesIO
from datetime import datetime

from app.database import get_management_db, get_company_db
from app import models, schemas
from app import auth
from app.models_company import Document as CompanyDocument, User as CompanyUser
from app.services.aws_service import aws_service
from app.services.groq_service import groq_service
from app.services.email_extensions import get_extended_email_service
from ..schemas import DocumentResponse, DocumentCreate, SystemDocumentResponse, SystemDocumentCreate
from ..models import SystemDocument, SystemUser
from ..database import get_management_db

router = APIRouter()

def get_allowed_extensions():
    return ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'csv', 'xlsx', 'xls']

# SYSTEM ADMIN DOCUMENT ENDPOINTS - MUST COME BEFORE GENERIC ROUTES
@router.get("/system/folders", response_model=List[str])
async def list_system_folders(
    current_user: SystemUser = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """List all folders used by system admin documents"""
    folders = management_db.query(SystemDocument.folder_name).filter(
        SystemDocument.user_id == current_user.id,
        SystemDocument.folder_name.isnot(None)
    ).distinct().all()
    
    # Extract folder names from tuples and return as list
    folder_names = [folder[0] for folder in folders if folder[0]]
    return sorted(folder_names)

@router.post("/system/upload", response_model=SystemDocumentResponse)
async def upload_system_document(
    file: UploadFile = File(...),
    folder_name: Optional[str] = Form(None),
    current_user: SystemUser = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """Upload a document for system admin"""
    # Read file content first
    file_content = await file.read()
    
    # Check file size (max 100MB for system admins)
    if len(file_content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 100MB")
    
    # Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    
    # Validate file type
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    allowed_extensions = get_allowed_extensions()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type .{file_extension} not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        filename = f"{file_id}.{file_extension}"
        
        # Get bucket name from user record
        bucket_name = getattr(current_user, 's3_bucket_name', None)
        if not bucket_name:
            # This should not happen, but as fallback
            fallback_bucket_name = f"system-admin-{current_user.id.lower()}"
            clean_fallback_bucket = re.sub(r'[^a-z0-9.-]', '-', fallback_bucket_name).strip('-')
            bucket_name = clean_fallback_bucket
        
        # Create S3 key
        folder_path = f"{folder_name}/" if folder_name else ""
        s3_key = f"system-documents/{current_user.id}/{folder_path}{filename}"
        
        # Upload to S3
        await aws_service.upload_file_to_s3(
            bucket_name=bucket_name,
            file_content=file_content,
            s3_key=s3_key,
            content_type=file.content_type
        )
        
        # Create document record
        document = SystemDocument(
            id=file_id,
            filename=filename,
            original_filename=file.filename,
            file_path=s3_key,
            file_size=len(file_content),
            file_type=file.content_type or 'application/octet-stream',
            s3_key=s3_key,
            folder_name=folder_name,
            user_id=current_user.id,
            processed=False
        )
        
        management_db.add(document)
        management_db.commit()
        management_db.refresh(document)
        
        # Update document with metadata
        management_db.query(SystemDocument).filter(SystemDocument.id == document.id).update({
            'metadata_json': json.dumps({
                'uploaded_by': current_user.username,
                'uploaded_at': datetime.utcnow().isoformat(),
                'file_size_mb': round(len(file_content) / (1024 * 1024), 2)
            })
        })
        management_db.commit()
        
        print(f"✅ System document uploaded successfully: {document.id}")
        
        return document
        
    except Exception as e:
        management_db.rollback()
        print(f"Failed to process system document {document.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload system document: {str(e)}")

@router.get("/system/", response_model=List[SystemDocumentResponse])
async def list_system_documents(
    folder_name: Optional[str] = None,
    current_user: SystemUser = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """List system admin documents"""
    query = management_db.query(SystemDocument).filter(
        SystemDocument.user_id == current_user.id
    )
    
    # Apply folder filter if specified
    if folder_name is not None:
        if folder_name == "":
            # Filter for documents without folder
            query = query.filter(SystemDocument.folder_name.is_(None))
        else:
            # Filter for specific folder
            query = query.filter(SystemDocument.folder_name == folder_name)
    
    documents = query.order_by(SystemDocument.created_at.desc()).all()
    
    # Convert SQLAlchemy objects to dictionaries to avoid DetachedInstanceError
    document_list = []
    for doc in documents:
        document_data = {
            "id": doc.id,
            "filename": doc.filename,
            "original_filename": doc.original_filename,
            "file_path": doc.file_path,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "s3_key": doc.s3_key,
            "folder_name": doc.folder_name,
            "user_id": doc.user_id,
            "processed": doc.processed,
            "metadata_json": doc.metadata_json,
            "created_at": doc.created_at
        }
        document_list.append(document_data)
    
    return document_list

@router.get("/system/{document_id}", response_model=SystemDocumentResponse)
async def get_system_document(
    document_id: str,
    current_user: SystemUser = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """Get a specific system admin document"""
    document = management_db.query(SystemDocument).filter(
        SystemDocument.id == document_id,
        SystemDocument.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="System document not found")
    
    # Convert SQLAlchemy object to dictionary to avoid DetachedInstanceError
    document_data = {
        "id": document.id,
        "filename": document.filename,
        "original_filename": document.original_filename,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "file_type": document.file_type,
        "s3_key": document.s3_key,
        "folder_name": document.folder_name,
        "user_id": document.user_id,
        "processed": document.processed,
        "metadata_json": document.metadata_json,
        "created_at": document.created_at
    }
    
    return document_data

@router.delete("/system/{document_id}")
async def delete_system_document(
    document_id: str,
    current_user: SystemUser = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """Delete a system admin document"""
    document = management_db.query(SystemDocument).filter(
        SystemDocument.id == document_id,
        SystemDocument.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="System document not found")
    
    try:
        # Get bucket name from user record
        bucket_name = getattr(current_user, 's3_bucket_name', None)
        if not bucket_name:
            # This should not happen, but as fallback
            fallback_bucket_name = f"system-admin-{current_user.id.lower()}"
            clean_fallback_bucket = re.sub(r'[^a-z0-9.-]', '-', fallback_bucket_name).strip('-')
            bucket_name = clean_fallback_bucket
        
        # Delete from S3
        await aws_service.delete_file_from_s3(bucket_name, document.s3_key)
        
        # Delete from database
        management_db.delete(document)
        management_db.commit()
        
        print(f"✅ System document deleted successfully: {document_id}")
        return {"message": "System document deleted successfully"}
        
    except Exception as e:
        management_db.rollback()
        print(f"Failed to delete system document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete system document: {str(e)}")

@router.get("/system/{document_id}/download")
async def download_system_document(
    document_id: str,
    current_user: SystemUser = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """Download a system admin document"""
    document = management_db.query(SystemDocument).filter(
        SystemDocument.id == document_id,
        SystemDocument.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="System document not found")
    
    try:
        # Get bucket name from user record
        bucket_name = getattr(current_user, 's3_bucket_name', None)
        if not bucket_name:
            # This should not happen, but as fallback
            fallback_bucket_name = f"system-admin-{current_user.id.lower()}"
            clean_fallback_bucket = re.sub(r'[^a-z0-9.-]', '-', fallback_bucket_name).strip('-')
            bucket_name = clean_fallback_bucket
        
        # Get download URL from S3
        download_url = await aws_service.get_download_url(bucket_name, document.s3_key)
        
        return {
            "download_url": download_url,
            "filename": document.original_filename,
            "file_size": document.file_size
        }
        
    except Exception as e:
        print(f"Failed to get download URL for system document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get download URL: {str(e)}")

# COMPANY DOCUMENT ENDPOINTS
@router.get("/folders", response_model=List[str])
async def list_folders(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get list of folders for the current user"""
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        if current_user.role in ["hr_admin", "hr_manager"]:
            # Admins and managers can see all folders
            folders = company_db.query(CompanyDocument.folder_name).filter(
                CompanyDocument.folder_name.isnot(None)
            ).distinct().all()
        else:
            # Regular users can only see their own folders
            folders = company_db.query(CompanyDocument.folder_name).filter(
                CompanyDocument.user_id == current_user.id,
                CompanyDocument.folder_name.isnot(None)
            ).distinct().all()
        
        # Extract folder names from tuples and return as list
        folder_names = [folder[0] for folder in folders if folder[0]]
        return sorted(folder_names)
        
    finally:
        company_db.close()

@router.post("/upload", response_model=schemas.DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    folder_name: Optional[str] = Form(None),
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Read file content first
    file_content = await file.read()
    
    # Check file size (max 50MB)
    if len(file_content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB")
    
    # Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    
    # Validate file type
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    allowed_extensions = get_allowed_extensions()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type .{file_extension} not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        filename = f"{file_id}.{file_extension}"
        
        # Create S3 key
        folder_path = f"{folder_name}/" if folder_name else ""
        s3_key = f"company-documents/{company_id}/{folder_path}{filename}"
        
        # Upload to S3
        await aws_service.upload_file_to_s3(
            bucket_name=company.s3_bucket_name,
            file_content=file_content,
            s3_key=s3_key,
            content_type=file.content_type
        )
        
        # Create document record
        document = CompanyDocument(
            id=file_id,
            filename=filename,
            original_filename=file.filename,
            file_path=s3_key,
            file_size=len(file_content),
            file_type=file.content_type or 'application/octet-stream',
            s3_key=s3_key,
            folder_name=folder_name,
            user_id=current_user.id,
            company_id=company_id,
            processed=False
        )
        
        company_db.add(document)
        company_db.commit()
        company_db.refresh(document)
        
        # Update document with metadata
        company_db.query(CompanyDocument).filter(CompanyDocument.id == document.id).update({
            'metadata_json': json.dumps({
                'uploaded_by': current_user.username,
                'uploaded_at': datetime.utcnow().isoformat(),
                'file_size_mb': round(len(file_content) / (1024 * 1024), 2)
            })
        })
        company_db.commit()
        
        print(f"✅ Company document uploaded successfully: {document.id}")
        
        return document
        
    except Exception as e:
        company_db.rollback()
        print(f"Failed to process company document {document.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload company document: {str(e)}")
    finally:
        company_db.close()

@router.get("/", response_model=List[schemas.DocumentResponse])
async def list_documents(
    folder_name: Optional[str] = None,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        query = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == company_id
        )
        
        # Apply folder filter if specified
        if folder_name is not None:
            if folder_name == "":
                # Filter for documents without folder
                query = query.filter(CompanyDocument.folder_name.is_(None))
            else:
                # Filter for specific folder
                query = query.filter(CompanyDocument.folder_name == folder_name)
        
        # Apply user-based filtering
        if current_user.role not in ["hr_admin", "hr_manager"]:
            # Regular users can only see their own documents
            query = query.filter(CompanyDocument.user_id == current_user.id)
        
        documents = query.order_by(CompanyDocument.created_at.desc()).all()
        
        # Convert SQLAlchemy objects to dictionaries to avoid DetachedInstanceError
        document_list = []
        for doc in documents:
            document_data = {
                "id": doc.id,
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "file_path": doc.file_path,
                "file_size": doc.file_size,
                "file_type": doc.file_type,
                "s3_key": doc.s3_key,
                "folder_name": doc.folder_name,
                "user_id": doc.user_id,
                "company_id": doc.company_id,
                "processed": doc.processed,
                "metadata_json": doc.metadata_json,
                "created_at": doc.created_at
            }
            document_list.append(document_data)
        
        return document_list
        
    finally:
        company_db.close()

@router.get("/{document_id}", response_model=schemas.DocumentResponse)
async def get_document(
    document_id: str,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        query = company_db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id,
            CompanyDocument.company_id == company_id
        )
        
        # Apply user-based filtering
        if current_user.role not in ["hr_admin", "hr_manager"]:
            # Regular users can only see their own documents
            query = query.filter(CompanyDocument.user_id == current_user.id)
        
        document = query.first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Convert SQLAlchemy object to dictionary to avoid DetachedInstanceError
        document_data = {
            "id": document.id,
            "filename": document.filename,
            "original_filename": document.original_filename,
            "file_path": document.file_path,
            "file_size": document.file_size,
            "file_type": document.file_type,
            "s3_key": document.s3_key,
            "folder_name": document.folder_name,
            "user_id": document.user_id,
            "company_id": document.company_id,
            "processed": document.processed,
            "metadata_json": document.metadata_json,
            "created_at": document.created_at
        }
        
        return document_data
        
    finally:
        company_db.close()

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        query = company_db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id,
            CompanyDocument.company_id == company_id
        )
        
        # Apply user-based filtering
        if current_user.role not in ["hr_admin", "hr_manager"]:
            # Regular users can only delete their own documents
            query = query.filter(CompanyDocument.user_id == current_user.id)
        
        document = query.first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        try:
            # Delete from S3
            await aws_service.delete_file_from_s3(company.s3_bucket_name, document.s3_key)
            
            # Delete from database
            company_db.delete(document)
            company_db.commit()
            
            print(f"✅ Company document deleted successfully: {document_id}")
            return {"message": "Document deleted successfully"}
            
        except Exception as e:
            company_db.rollback()
            print(f"Failed to delete company document {document_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
            
    finally:
        company_db.close()

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        query = company_db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id,
            CompanyDocument.company_id == company_id
        )
        
        # Apply user-based filtering
        if current_user.role not in ["hr_admin", "hr_manager"]:
            # Regular users can only download their own documents
            query = query.filter(CompanyDocument.user_id == current_user.id)
        
        document = query.first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        try:
            # Get download URL from S3
            download_url = await aws_service.get_download_url(company.s3_bucket_name, document.s3_key)
            
            return {
                "download_url": download_url,
                "filename": document.original_filename,
                "file_size": document.file_size
            }
            
        except Exception as e:
            print(f"Failed to get download URL for company document {document_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get download URL: {str(e)}")
            
    finally:
        company_db.close()
