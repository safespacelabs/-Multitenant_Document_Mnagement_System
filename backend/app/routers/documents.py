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
from ..schemas import DocumentResponse, DocumentCreate, SystemDocumentResponse, SystemDocumentCreate
from ..models import SystemDocument, SystemUser
from ..database import get_management_db

router = APIRouter()

def get_allowed_extensions():
    return ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'csv', 'xlsx', 'xls']

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
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else uuid.uuid4().hex
        
        # Create S3 key with optional folder
        if folder_name and folder_name.strip():
            # Create custom folder first
            await aws_service.create_custom_folder(
                bucket_name=str(company.s3_bucket_name),
                user_id=str(current_user.id),
                folder_name=folder_name.strip()
            )
            # Sanitize folder name for S3 key
            safe_folder_name = folder_name.strip().replace(' ', '_').replace('/', '_')
            s3_key = f"users/{current_user.id}/{safe_folder_name}/{unique_filename}"
        else:
            s3_key = f"users/{current_user.id}/{unique_filename}"
        
        # Upload to S3 - wrap bytes in BytesIO to make it file-like
        file_obj = BytesIO(file_content)
        s3_url = await aws_service.upload_file(
            bucket_name=str(company.s3_bucket_name),
            file_key=s3_key,
            file_data=file_obj,
            user_id=str(current_user.id),
            company_id=str(company_id)
        )
        
        # Create document record in company database
        document = CompanyDocument(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=s3_url,
            file_size=len(file_content),
            file_type=file.content_type or 'application/octet-stream',
            s3_key=s3_key,
            folder_name=folder_name.strip() if folder_name and folder_name.strip() else None,
            user_id=current_user.id,
            processed=False
        )
        
        company_db.add(document)
        company_db.commit()
        company_db.refresh(document)
        
        # Process document with Groq API in background
        try:
            metadata = await groq_service.extract_document_metadata(file_content, file.filename)
            # Update the document attributes directly using text() for raw SQL
            company_db.execute(
                text("UPDATE documents SET metadata_json = :metadata, processed = :processed WHERE id = :doc_id"),
                {"metadata": json.dumps(metadata), "processed": True, "doc_id": document.id}
            )
            company_db.commit()
        except Exception as e:
            print(f"Failed to process document {document.id}: {str(e)}")
        
        return document
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")
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
        # Build base query
        if current_user.role in ["hr_admin", "hr_manager"]:
            # Admins and managers can see all company documents
            query = company_db.query(CompanyDocument)
        else:
            # Regular users can only see their own documents
            query = company_db.query(CompanyDocument).filter(
                CompanyDocument.user_id == current_user.id
            )
        
        # Apply folder filter if specified
        if folder_name is not None:
            if folder_name == "":
                # Filter for documents without folder (empty string means root folder)
                query = query.filter(CompanyDocument.folder_name.is_(None))
            else:
                # Filter for specific folder
                query = query.filter(CompanyDocument.folder_name == folder_name)
        
        documents = query.order_by(CompanyDocument.created_at.desc()).all()
        return documents
        
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
        document = company_db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check access permissions
        if current_user.role not in ["hr_admin", "hr_manager"] and str(document.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return document
        
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
        document = company_db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check access permissions
        if current_user.role not in ["hr_admin", "hr_manager"] and str(document.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        try:
            # Delete from S3
            await aws_service.delete_file(
                bucket_name=str(company.s3_bucket_name),
                file_key=str(document.s3_key)
            )
        except Exception as e:
            print(f"Warning: Failed to delete S3 file: {str(e)}")
        
        # Delete from database
        company_db.delete(document)
        company_db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
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
        document = company_db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check access permissions
        if current_user.role not in ["hr_admin", "hr_manager"] and str(document.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # For now, return the S3 path since we don't have presigned URL method
        # In production, you'd implement generate_presigned_url in AWSService
        download_url = document.file_path
        
        return {"download_url": download_url, "filename": document.original_filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")
    finally:
        company_db.close()

# ======================================
# SYSTEM ADMIN DOCUMENT ENDPOINTS
# ======================================

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
    
    folder_list = [folder[0] for folder in folders if folder[0]]
    return sorted(folder_list)

@router.post("/system/upload", response_model=SystemDocumentResponse)
async def upload_system_document(
    file: UploadFile = File(...),
    folder_name: Optional[str] = Form(None),
    current_user: SystemUser = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """Upload a document to system admin storage"""
    # Validate file
    file_size = file.size or 0
    if file_size > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(status_code=413, detail="File too large")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Read file content
    file_content = await file.read()
    
    # Ensure system admin has S3 bucket setup
    if not getattr(current_user, 's3_bucket_name', None):
        # Initialize system admin S3 bucket
        bucket_name = f"system-admin-{current_user.id.lower()}"
        folder_name_s3 = f"system-admin-{current_user.id}"
        
        try:
            # The create_system_admin_bucket method returns the cleaned bucket name
            clean_bucket_name = await aws_service.create_system_admin_bucket(bucket_name, folder_name_s3)
            # Update system user with the cleaned S3 bucket name
            management_db.query(SystemUser).filter(SystemUser.id == current_user.id).update({
                's3_bucket_name': clean_bucket_name,
                's3_folder': folder_name_s3
            })
            management_db.commit()
            # Refresh current_user object
            management_db.refresh(current_user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to setup S3 storage: {str(e)}")
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    
    # Create S3 key with folder structure
    s3_folder = getattr(current_user, 's3_folder', f"system-admin-{current_user.id}")
    if folder_name:
        s3_key = f"{s3_folder}/{folder_name}/{unique_filename}"
    else:
        s3_key = f"{s3_folder}/{unique_filename}"
    
    try:
        # Convert bytes to BytesIO for S3 upload
        file_data = BytesIO(file_content)
        
        # Get bucket name from user record
        bucket_name = getattr(current_user, 's3_bucket_name', None)
        if not bucket_name:
            # This should not happen since we initialize bucket above, but as fallback
            fallback_bucket_name = f"system-admin-{current_user.id.lower()}"
            clean_fallback_bucket = re.sub(r'[^a-z0-9.-]', '-', fallback_bucket_name).strip('-')
            bucket_name = clean_fallback_bucket
        
        # CRITICAL: Ensure bucket exists in mock service before upload
        folder_name_s3 = getattr(current_user, 's3_folder', f"system-admin-{current_user.id}")
        try:
            # This will create the bucket if it doesn't exist, or do nothing if it does
            await aws_service.create_system_admin_bucket(bucket_name, folder_name_s3)
        except Exception as bucket_error:
            print(f"Warning: Bucket creation check failed: {str(bucket_error)}")
            # Continue anyway - the upload might still work
        
        # Upload to S3
        file_url = await aws_service.upload_file(
            bucket_name=bucket_name,
            file_key=s3_key,
            file_data=file_data,
            user_id=str(current_user.id),
            company_id="system"  # System-level company ID
        )
        
        # Create document record
        document = SystemDocument(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_url,
            file_size=file_size,
            file_type=file.content_type or "application/octet-stream",
            s3_key=s3_key,
            folder_name=folder_name,
            user_id=current_user.id
        )
        
        management_db.add(document)
        management_db.commit()
        management_db.refresh(document)
        
        # Process document with Groq API in background
        try:
            metadata = await groq_service.extract_document_metadata(file_content, file.filename)
            # Update document with metadata using SQLAlchemy update
            management_db.query(SystemDocument).filter(SystemDocument.id == document.id).update({
                'metadata_json': metadata,
                'processed': True
            })
            management_db.commit()
            management_db.refresh(document)
        except Exception as e:
            print(f"Failed to process system document {document.id}: {str(e)}")
        
        return document
        
    except Exception as e:
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
    return documents

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
    
    return document

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
        
        # Ensure bucket exists before attempting delete
        folder_name_s3 = getattr(current_user, 's3_folder', f"system-admin-{current_user.id}")
        try:
            await aws_service.create_system_admin_bucket(bucket_name, folder_name_s3)
        except Exception as bucket_error:
            print(f"Warning: Bucket verification failed: {str(bucket_error)}")
        
        # Delete from S3
        await aws_service.delete_file(
            bucket_name=bucket_name,
            file_key=str(document.s3_key)
        )
    except Exception as e:
        print(f"Warning: Failed to delete S3 file: {str(e)}")
    
    # Delete from database
    management_db.delete(document)
    management_db.commit()
    
    return {"message": "System document deleted successfully"}

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
    
    # Ensure bucket exists for download operations (in case we need to generate presigned URLs later)
    try:
        bucket_name = getattr(current_user, 's3_bucket_name', None)
        folder_name_s3 = getattr(current_user, 's3_folder', f"system-admin-{current_user.id}")
        if bucket_name:
            await aws_service.create_system_admin_bucket(bucket_name, folder_name_s3)
    except Exception as bucket_error:
        print(f"Warning: Bucket verification failed for download: {str(bucket_error)}")
    
    # Return download URL
    return {"download_url": document.file_path, "filename": document.original_filename} 