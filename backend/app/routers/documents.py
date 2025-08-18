from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import uuid
import json
import re
from io import BytesIO
from datetime import datetime
from datetime import timedelta
from sqlalchemy import or_
from sqlalchemy import func

from app.database import get_management_db, get_company_db
from app import models, schemas
from app import auth
from app.models_company import Document as CompanyDocument, User as CompanyUser, DocumentCategory, DocumentFolder, DocumentAccess, DocumentAuditLog
from app.services.aws_service import aws_service
from app.services.groq_service import groq_service
from app.services.email_extensions import get_extended_email_service
from ..schemas import DocumentResponse, DocumentCreate, SystemDocumentResponse, SystemDocumentCreate
from ..models import SystemDocument, SystemUser

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

# Enhanced Document Management Endpoints
@router.get("/categories", response_model=List[schemas.DocumentCategoryResponse])
async def list_document_categories(
    current_user = Depends(auth.get_current_user_or_system_user),
    company_db: Session = Depends(get_company_db)
):
    """List all document categories for the company"""
    # For system admins, show categories from all companies
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        categories = company_db.query(DocumentCategory).filter(
            DocumentCategory.is_active == True
        ).order_by(DocumentCategory.sort_order).all()
    else:
        # For company users, show only their company's categories
        categories = company_db.query(DocumentCategory).filter(
            DocumentCategory.company_id == current_user.company_id,
            DocumentCategory.is_active == True
        ).order_by(DocumentCategory.sort_order).all()
    
    return categories

@router.post("/categories", response_model=schemas.DocumentCategoryResponse)
async def create_document_category(
    category: schemas.DocumentCategoryCreate,
    current_user: CompanyUser = Depends(auth.get_current_user),
    company_db: Session = Depends(get_company_db)
):
    """Create a new document category"""
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db_category = DocumentCategory(
        **category.dict(),
        company_id=current_user.company_id
    )
    company_db.add(db_category)
    company_db.commit()
    company_db.refresh(db_category)
    return db_category

@router.get("/folders", response_model=List[schemas.DocumentFolderResponse])
async def list_document_folders(
    category_id: Optional[str] = None,
    current_user = Depends(auth.get_current_user_or_system_user),
    company_db: Session = Depends(get_company_db)
):
    """List document folders, optionally filtered by category"""
    # For system admins, show folders from all companies
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        query = company_db.query(DocumentFolder).filter(
            DocumentFolder.is_active == True
        )
    else:
        # For company users, show only their company's folders
        query = company_db.query(DocumentFolder).filter(
            DocumentFolder.company_id == current_user.company_id,
            DocumentFolder.is_active == True
        )
    
    if category_id:
        query = query.filter(DocumentFolder.category_id == category_id)
    
    folders = query.order_by(DocumentFolder.sort_order).all()
    return folders

@router.post("/folders", response_model=schemas.DocumentFolderResponse)
async def create_document_folder(
    folder: schemas.DocumentFolderCreate,
    current_user: CompanyUser = Depends(auth.get_current_user),
    company_db: Session = Depends(get_company_db)
):
    """Create a new document folder"""
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db_folder = DocumentFolder(
        **folder.dict(),
        company_id=current_user.company_id,
        created_by_user_id=current_user.id
    )
    company_db.add(db_folder)
    company_db.commit()
    company_db.refresh(db_folder)
    return db_folder

@router.get("/enhanced", response_model=schemas.DocumentManagementResponse)
async def list_enhanced_documents(
    category_id: Optional[str] = None,
    folder_id: Optional[str] = None,
    file_type: Optional[str] = None,
    search_query: Optional[str] = None,
    tags: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    access_level: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user = Depends(auth.get_current_user_or_system_user),
    company_db: Session = Depends(get_company_db)
):
    """Enhanced document listing with advanced filtering and pagination"""
    
    # Build query
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins can see documents from all companies
        query = company_db.query(CompanyDocument)
    else:
        # Company users can only see their company's documents
        query = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id
        )
    
    # Apply filters
    if category_id:
        query = query.filter(CompanyDocument.document_category == category_id)
    
    if folder_id:
        query = query.filter(CompanyDocument.folder_name == folder_id)
    
    if file_type and file_type != "All Files":
        query = query.filter(CompanyDocument.file_type.contains(file_type))
    
    if search_query:
        search_filter = or_(
            CompanyDocument.original_filename.contains(search_query),
            CompanyDocument.description.contains(search_query),
            CompanyDocument.tags.contains([search_query])
        )
        query = query.filter(search_filter)
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',')]
        query = query.filter(CompanyDocument.tags.contains(tag_list))
    
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(CompanyDocument.created_at >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(CompanyDocument.created_at <= date_to_obj)
        except ValueError:
            pass
    
    if status:
        query = query.filter(CompanyDocument.status == status)
    
    if access_level:
        query = query.filter(CompanyDocument.access_level == access_level)
    
    if user_id:
        query = query.filter(CompanyDocument.user_id == user_id)
    
    # Apply access control
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins can see all documents
        pass
    elif current_user.role not in ['hr_admin', 'hr_manager']:
        # Regular users can only see their own documents or public documents
        query = query.filter(
            or_(
                CompanyDocument.user_id == current_user.id,
                CompanyDocument.is_public == True,
                CompanyDocument.access_level == "public"
            )
        )
    
    # Get total count
    total_count = query.count()
    
    # Apply sorting
    if hasattr(CompanyDocument, sort_by):
        sort_column = getattr(CompanyDocument, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        # Default sorting
        query = query.order_by(CompanyDocument.created_at.desc())
    
    # Apply pagination
    offset = (page - 1) * page_size
    documents = query.offset(offset).limit(page_size).all()
    
    # Get categories and folders for the response
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins can see categories and folders from all companies
        categories = company_db.query(DocumentCategory).filter(
            DocumentCategory.is_active == True
        ).all()
        folders = company_db.query(DocumentFolder).filter(
            DocumentFolder.is_active == True
        ).all()
    else:
        # Company users can only see their company's categories and folders
        categories = company_db.query(DocumentCategory).filter(
            DocumentCategory.company_id == current_user.company_id,
            DocumentCategory.is_active == True
        ).all()
        folders = company_db.query(DocumentFolder).filter(
            DocumentFolder.company_id == current_user.company_id,
            DocumentFolder.is_active == True
        ).all()
    
    # Calculate pagination info
    total_pages = (total_count + page_size - 1) // page_size
    
    return schemas.DocumentManagementResponse(
        documents=documents,
        categories=categories,
        folders=folders,
        total_count=total_count,
        current_page=page,
        total_pages=total_pages
    )

@router.post("/bulk-operation")
async def bulk_document_operation(
    operation: schemas.BulkDocumentOperation,
    current_user = Depends(auth.get_current_user_or_system_user),
    company_db: Session = Depends(get_company_db)
):
    """Perform bulk operations on documents"""
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins can perform bulk operations on all documents
        documents = company_db.query(CompanyDocument).filter(
            CompanyDocument.id.in_(operation.document_ids)
        ).all()
    elif current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    else:
        # Company users can only perform bulk operations on their company's documents
        documents = company_db.query(CompanyDocument).filter(
            CompanyDocument.id.in_(operation.document_ids),
            CompanyDocument.company_id == current_user.company_id
        ).all()
    
    if len(documents) != len(operation.document_ids):
        raise HTTPException(status_code=400, detail="Some documents not found")
    
    try:
        if operation.operation == "delete":
            for doc in documents:
                company_db.delete(doc)
            
        elif operation.operation == "move":
            if not operation.target_folder_id:
                raise HTTPException(status_code=400, detail="Target folder required for move operation")
            
            for doc in documents:
                doc.folder_name = operation.target_folder_id
                
        elif operation.operation == "archive":
            for doc in documents:
                doc.status = "archived"
                
        elif operation.operation == "share":
            if not operation.user_ids or not operation.access_type:
                raise HTTPException(status_code=400, detail="User IDs and access type required for share operation")
            
            for doc in documents:
                for user_id in operation.user_ids:
                    # For system admins, use the document's company_id; for company users, use their company_id
                    company_id = getattr(current_user, 'company_id', doc.company_id)
                    access = DocumentAccess(
                        document_id=doc.id,
                        user_id=user_id,
                        access_type=operation.access_type,
                        granted_by_user_id=current_user.id,
                        company_id=company_id
                    )
                    company_db.add(access)
        
        company_db.commit()
        
        # Log the bulk operation
        for doc in documents:
            # For system admins, use the document's company_id; for company users, use their company_id
            company_id = getattr(current_user, 'company_id', doc.company_id)
            audit_log = DocumentAuditLog(
                document_id=doc.id,
                user_id=current_user.id,
                action=f"bulk_{operation.operation}",
                details={"operation": operation.operation, "affected_documents": len(documents)},
                company_id=company_id
            )
            company_db.add(audit_log)
        
        company_db.commit()
        
        return {"message": f"Bulk {operation.operation} completed successfully", "affected_documents": len(documents)}
        
    except Exception as e:
        company_db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk operation failed: {str(e)}")

@router.get("/audit-logs", response_model=List[schemas.DocumentAuditLogResponse])
async def get_document_audit_logs(
    document_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user = Depends(auth.get_current_user_or_system_user),
    company_db: Session = Depends(get_company_db)
):
    """Get document audit logs (HR admins, managers, and system admins only)"""
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins can see all audit logs
        query = company_db.query(DocumentAuditLog)
    elif current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    else:
        # Company users can only see their company's audit logs
        query = company_db.query(DocumentAuditLog).filter(
            DocumentAuditLog.company_id == current_user.company_id
        )
    
    if document_id:
        query = query.filter(DocumentAuditLog.document_id == document_id)
    
    if user_id:
        query = query.filter(DocumentAuditLog.user_id == user_id)
    
    if action:
        query = query.filter(DocumentAuditLog.action == action)
    
    # Apply pagination
    offset = (page - 1) * page_size
    logs = query.order_by(DocumentAuditLog.created_at.desc()).offset(offset).limit(page_size).all()
    
    return logs

@router.get("/stats")
async def get_document_statistics(
    current_user = Depends(auth.get_current_user_or_system_user),
    company_db: Session = Depends(get_company_db)
):
    """Get document statistics for the company or all companies (for system admins)"""
    
    # Base query for documents
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins can see stats from all companies
        base_query = company_db.query(CompanyDocument)
        category_filter = CompanyDocument.document_category.isnot(None)
        file_type_filter = True
        size_filter = True
    else:
        # Company users can only see their company's stats
        base_query = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id
        )
        category_filter = CompanyDocument.document_category.isnot(None)
        file_type_filter = CompanyDocument.company_id == current_user.company_id
        size_filter = CompanyDocument.company_id == current_user.company_id
    
    # Total documents
    total_documents = base_query.count()
    
    # Documents by category
    category_stats = company_db.query(
        CompanyDocument.document_category,
        func.count(CompanyDocument.id)
    ).filter(category_filter).group_by(CompanyDocument.document_category).all()
    
    # Documents by file type
    file_type_stats = company_db.query(
        CompanyDocument.file_type,
        func.count(CompanyDocument.id)
    ).filter(file_type_filter).group_by(CompanyDocument.file_type).all()
    
    # Recent uploads (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_uploads = base_query.filter(
        CompanyDocument.created_at >= thirty_days_ago
    ).count()
    
    # Storage usage
    total_size = company_db.query(func.sum(CompanyDocument.file_size)).filter(size_filter).scalar() or 0
    
    return {
        "total_documents": total_documents,
        "category_distribution": dict(category_stats),
        "file_type_distribution": dict(file_type_stats),
        "recent_uploads_30_days": recent_uploads,
        "total_storage_bytes": total_size,
        "total_storage_mb": round(total_size / (1024 * 1024), 2)
    }
