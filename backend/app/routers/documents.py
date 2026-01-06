from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
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
from app.models_document_analysis import DocumentAnalysis
from app.services.aws_service import aws_service
from app.services.document_analysis_service import document_analysis_service
from app.services.email_extensions import get_extended_email_service
from app.services.rag_service import rag_service
import logging

logger = logging.getLogger(__name__)
from ..schemas import DocumentResponse, DocumentCreate, SystemDocumentResponse, SystemDocumentCreate
from ..models import SystemDocument, SystemUser

router = APIRouter()

# Category mapping for Document Health Snapshot
HEALTH_CATEGORY_MAPPING = {
    "i9_work_auth": {
        "display_name": "I-9 & Work Authorization",
        "icon": "briefcase",
        "keywords": ["i-9", "i9", "work authorization", "visa", "employment eligibility", "work permit"]
    },
    "safety_osha": {
        "display_name": "Safety / OSHA",
        "icon": "shield",
        "keywords": ["osha", "safety", "training", "hazard", "certification"]
    },
    "payroll_davis_bacon": {
        "display_name": "Payroll & Davis-Bacon",
        "icon": "dollar-sign",
        "keywords": ["payroll", "davis-bacon", "wage", "certified payroll"]
    },
    "employee_relations": {
        "display_name": "Employee Relations",
        "icon": "users",
        "keywords": ["performance", "review", "disciplinary", "complaint", "hr policy", "relations"]
    }
}

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
    print(f"🚀 Upload request received for user: {current_user.username}")
    print(f"📁 Folder name: {folder_name}")
    print(f"📄 File: {file.filename}, Size: {file.size}, Type: {file.content_type}")
    
    # Read file content first
    file_content = await file.read()
    print(f"📊 File content read, size: {len(file_content)} bytes")
    
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
    
    print(f"🏢 Company found: {company.name}, S3 bucket: {company.s3_bucket_name}")
    
    # Check if company has S3 bucket, create one if not
    if not company.s3_bucket_name:
        print(f"⚠️ Company {company.name} has no S3 bucket, creating one...")
        try:
            bucket_name = await aws_service.create_company_bucket(company_id)
            # Update company record with bucket name
            company.s3_bucket_name = bucket_name
            management_db.commit()
            print(f"✅ Created S3 bucket: {bucket_name}")
        except Exception as e:
            print(f"❌ Failed to create S3 bucket: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create S3 bucket: {str(e)}")
    
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
        
        print(f"🔑 S3 key: {s3_key}")
        
        # Upload to S3
        await aws_service.upload_file_to_s3(
            bucket_name=company.s3_bucket_name,
            file_content=file_content,
            s3_key=s3_key,
            content_type=file.content_type
        )
        
        print(f"☁️ File uploaded to S3 successfully")
        
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
        
        # Process document with AI analysis
        try:
            print(f"🤖 Starting AI analysis for document: {document.id}")
            analysis_result = await document_analysis_service.process_document_upload(
                document_id=document.id,
                file_content=file_content,
                filename=file.filename,
                folder_name=folder_name,
                user_id=current_user.id,
                user_name=current_user.username,
                user_email=current_user.email,
                company_db=company_db
            )

            if analysis_result["success"]:
                print(f"✅ AI analysis completed successfully for document: {document.id}")
                if analysis_result.get("expiry_detected"):
                    print(f"⚠️ Expiry date detected in document: {document.id}")
            else:
                print(f"❌ AI analysis failed for document: {document.id}, Error: {analysis_result.get('error')}")

        except Exception as e:
            print(f"❌ AI analysis error for document {document.id}: {str(e)}")

        # Upload to RAG service for advanced vector search and QA
        try:
            logger.info(f"📤 Uploading document to RAG service: {document.id}")
            rag_upload_result = await rag_service.upload_document(
                file_content=file_content,
                filename=file.filename,
                company_id=str(company_id),
                user_id=str(current_user.id),
                metadata={
                    "document_id": document.id,
                    "folder_name": folder_name,
                    "uploaded_by": current_user.username,
                    "company_name": company.name
                }
            )

            # Store RAG document ID for future reference
            rag_document_id = rag_upload_result.get("document_id")
            if rag_document_id:
                # Update document metadata with RAG document ID
                metadata = json.loads(document.metadata_json or '{}')
                metadata['rag_document_id'] = rag_document_id
                metadata['rag_ingestion_status'] = rag_upload_result.get('ingestion', 'scheduled')

                company_db.query(CompanyDocument).filter(CompanyDocument.id == document.id).update({
                    'metadata_json': json.dumps(metadata)
                })
                company_db.commit()

                logger.info(f"✅ Document uploaded to RAG service successfully: RAG ID {rag_document_id}")

        except Exception as rag_error:
            # Don't fail the upload if RAG service fails
            logger.warning(f"⚠️ RAG service upload failed for document {document.id}: {str(rag_error)}")
            logger.warning("Document saved successfully, but advanced QA features may not be available")

        # Refresh document to ensure all attributes are loaded before session closes
        company_db.refresh(document)

        return document
        
    except Exception as e:
        print(f"❌ Upload failed with error: {str(e)}")
        company_db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
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

# Enhanced Document Management Endpoints - MUST come BEFORE wildcard routes
# Remove this - global CORS middleware handles OPTIONS requests
# @router.options("/categories")
# async def options_categories():
#     """Handle CORS preflight for categories endpoint"""
#     return {"message": "OK"}

@router.get("/categories", response_model=List[schemas.DocumentCategoryResponse])
async def list_document_categories(
    current_user = Depends(auth.get_current_user_or_system_user),
    management_db: Session = Depends(get_management_db)
):
    """List all document categories for the company"""
    # For system admins, show categories from all companies
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins need to query all company databases to get categories
        all_categories = []
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        for company in companies:
            try:
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                categories = company_db.query(DocumentCategory).filter(
                    DocumentCategory.is_active == True
                ).order_by(DocumentCategory.sort_order).all()
                
                # Add company context to categories
                for category in categories:
                    category.company_name = company.name  # type: ignore
                
                all_categories.extend(categories)
                company_db.close()
            except Exception as e:
                print(f"Error accessing company {company.id}: {str(e)}")
                continue
        
        # Convert SQLAlchemy objects to dictionaries for JSON serialization
        all_categories_dict = []
        for category in all_categories:
            category_dict = {
                "id": category.id,
                "name": category.name,
                "display_name": getattr(category, 'display_name', category.name),  # Use name as fallback if display_name is missing
                "description": getattr(category, 'description', None),
                "icon": getattr(category, 'icon', None),
                "color": getattr(category, 'color', None),
                "parent_category_id": getattr(category, 'parent_category_id', None),
                "sort_order": getattr(category, 'sort_order', 0),
                "is_active": getattr(category, 'is_active', True),
                "company_id": category.company_id,
                "company_name": getattr(category, 'company_name', None),
                "created_at": category.created_at.isoformat() if hasattr(category, 'created_at') and category.created_at else None,
                "subcategories": []  # Initialize empty subcategories list
            }
            all_categories_dict.append(category_dict)
        
        return all_categories_dict
    else:
        # For company users, show only their company's categories
        # Validate company information exists
        if not hasattr(current_user, 'company_id') or not current_user.company_id:
            raise HTTPException(status_code=400, detail="User does not have a company_id")
        
        if not hasattr(current_user, 'company') or not current_user.company:
            raise HTTPException(status_code=400, detail="User does not have company information")
        
        if not hasattr(current_user.company, 'database_url') or not current_user.company.database_url:
            raise HTTPException(status_code=400, detail="Company does not have a database URL")
        
        company_db_gen = get_company_db(str(current_user.company_id), str(current_user.company.database_url))
        company_db = next(company_db_gen)
        
        try:
            categories = company_db.query(DocumentCategory).filter(
                DocumentCategory.company_id == current_user.company_id,
                DocumentCategory.is_active == True
            ).order_by(DocumentCategory.sort_order).all()
            
            # Convert SQLAlchemy objects to dictionaries for JSON serialization
            categories_dict = []
            for category in categories:
                category_dict = {
                    "id": str(category.id),
                    "name": category.name,
                    "display_name": getattr(category, 'display_name', category.name),  # Use name as fallback if display_name is missing
                    "description": getattr(category, 'description', None),
                    "icon": getattr(category, 'icon', None),
                    "color": getattr(category, 'color', None),
                    "parent_category_id": getattr(category, 'parent_category_id', None),
                    "sort_order": getattr(category, 'sort_order', 0),
                    "is_active": getattr(category, 'is_active', True),
                    "company_id": str(category.company_id),
                    "created_at": category.created_at.isoformat() if hasattr(category, 'created_at') and category.created_at else None,
                    "subcategories": []  # Initialize empty subcategories list
                }
                categories_dict.append(category_dict)
            
            return categories_dict
        finally:
            company_db.close()

# Remove this - global CORS middleware handles OPTIONS requests
# @router.options("/enhanced")
# async def options_enhanced():
#     """Handle CORS preflight for enhanced endpoint"""
#     return {"message": "OK"}

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
    management_db: Session = Depends(get_management_db)
):
    """Enhanced document listing with advanced filtering and pagination"""
    
    # Build query
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins need to query all company databases to get documents
        all_documents = []
        all_categories = []
        all_folders = []
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        for company in companies:
            try:
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                # Get documents for this company
                query = company_db.query(CompanyDocument)
                
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
                
                # Get documents for this company
                company_documents = query.all()
                
                # Add company context to documents
                for doc in company_documents:
                    doc.company_name = company.name  # type: ignore
                
                all_documents.extend(company_documents)
                
                # Get categories and folders for this company
                categories = company_db.query(DocumentCategory).filter(
                    DocumentCategory.is_active == True
                ).all()
                for category in categories:
                    category.company_name = company.name  # type: ignore
                all_categories.extend(categories)
                
                folders = company_db.query(DocumentFolder).filter(
                    DocumentFolder.is_active == True
                ).all()
                for folder in folders:
                    folder.company_name = company.name  # type: ignore
                all_folders.extend(folders)
                
                company_db.close()
            except Exception as e:
                print(f"Error accessing company {company.id}: {str(e)}")
                continue
        
        # Apply pagination to all documents
        total_count = len(all_documents)
        offset = (page - 1) * page_size
        paginated_documents = all_documents[offset:offset + page_size]
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        # Convert SQLAlchemy objects to dictionaries for proper serialization
        documents_dict = []
        for doc in paginated_documents:
            doc_dict = {
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
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "document_category": getattr(doc, 'document_category', None),
                "document_subcategory": getattr(doc, 'document_subcategory', None),
                "tags": getattr(doc, 'tags', []),
                "description": getattr(doc, 'description', None),
                "is_public": getattr(doc, 'is_public', False),
                "access_level": getattr(doc, 'access_level', 'private'),
                "expiry_date": doc.expiry_date.isoformat() if hasattr(doc, 'expiry_date') and doc.expiry_date else None,
                "version": getattr(doc, 'version', '1.0'),
                "status": getattr(doc, 'status', 'active'),
                "category_info": None,  # Will be populated if needed
                "folder_info": None     # Will be populated if needed
            }
            documents_dict.append(doc_dict)
        
        # Convert categories to proper format
        categories_dict = []
        for category in all_categories:
            cat_dict = {
                "id": category.id,
                "name": category.name,
                "display_name": getattr(category, 'display_name', category.name),
                "description": getattr(category, 'description', None),
                "icon": getattr(category, 'icon', None),
                "color": getattr(category, 'color', None),
                "parent_category_id": getattr(category, 'parent_category_id', None),
                "company_id": category.company_id,
                "is_active": getattr(category, 'is_active', True),
                "sort_order": getattr(category, 'sort_order', 0),
                "created_at": category.created_at.isoformat() if category.created_at else None
            }
            categories_dict.append(cat_dict)
        
        # Convert folders to proper format
        folders_dict = []
        for folder in all_folders:
            folder_dict = {
                "id": folder.id,
                "name": folder.name,
                "display_name": getattr(folder, 'display_name', folder.name),
                "description": getattr(folder, 'description', None),
                "category_id": getattr(folder, 'category_id', None),
                "parent_folder_id": getattr(folder, 'parent_folder_id', None),
                "company_id": folder.company_id,
                "created_by_user_id": getattr(folder, 'created_by_user_id', None),
                "is_active": getattr(folder, 'is_active', True),
                "sort_order": getattr(folder, 'sort_order', 0),
                "created_at": folder.created_at.isoformat() if folder.created_at else None
            }
            folders_dict.append(folder_dict)
        
        return {
            "documents": documents_dict,
            "categories": categories_dict,
            "folders": folders_dict,
            "total_count": total_count,
            "current_page": page,
            "total_pages": total_pages
        }
    else:
        # Company users can only see their company's documents
        company_db_gen = get_company_db(str(current_user.company_id), str(current_user.company.database_url))
        company_db = next(company_db_gen)
        
        try:
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
            if current_user.role not in ['hr_admin', 'hr_manager']:
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
            
            # Convert SQLAlchemy objects to dictionaries for proper serialization
            documents_dict = []
            for doc in documents:
                doc_dict = {
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
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "document_category": getattr(doc, 'document_category', None),
                    "document_subcategory": getattr(doc, 'document_subcategory', None),
                    "tags": getattr(doc, 'tags', []),
                    "description": getattr(doc, 'description', None),
                    "is_public": getattr(doc, 'is_public', False),
                    "access_level": getattr(doc, 'access_level', 'private'),
                    "expiry_date": doc.expiry_date.isoformat() if hasattr(doc, 'expiry_date') and doc.expiry_date else None,
                    "version": getattr(doc, 'version', '1.0'),
                    "status": getattr(doc, 'status', 'active'),
                    "category_info": None,  # Will be populated if needed
                    "folder_info": None     # Will be populated if needed
                }
                documents_dict.append(doc_dict)
            
            # Convert categories to proper format
            categories_dict = []
            for category in categories:
                cat_dict = {
                    "id": category.id,
                    "name": category.name,
                    "display_name": getattr(category, 'display_name', category.name),
                    "description": getattr(category, 'description', None),
                    "icon": getattr(category, 'icon', None),
                    "color": getattr(category, 'color', None),
                    "parent_category_id": getattr(category, 'parent_category_id', None),
                    "company_id": category.company_id,
                    "is_active": getattr(category, 'is_active', True),
                    "sort_order": getattr(category, 'sort_order', 0),
                    "created_at": category.created_at.isoformat() if category.created_at else None
                }
                categories_dict.append(cat_dict)
            
            # Convert folders to proper format
            folders_dict = []
            for folder in folders:
                folder_dict = {
                    "id": folder.id,
                    "name": folder.name,
                    "display_name": getattr(folder, 'display_name', folder.name),
                    "description": getattr(folder, 'description', None),
                    "category_id": getattr(folder, 'category_id', None),
                    "parent_folder_id": getattr(folder, 'parent_folder_id', None),
                    "company_id": folder.company_id,
                    "created_by_user_id": getattr(folder, 'created_by_user_id', None),
                    "is_active": getattr(folder, 'is_active', True),
                    "sort_order": getattr(folder, 'sort_order', 0),
                    "created_at": folder.created_at.isoformat() if folder.created_at else None
                }
                folders_dict.append(folder_dict)
            
            return {
                "documents": documents_dict,
                "categories": categories_dict,
                "folders": folders_dict,
                "total_count": total_count,
                "current_page": page,
                "total_pages": total_pages
            }
        finally:
            company_db.close()

@router.post("/{document_id}/process-ai")
async def process_document_with_ai(
    document_id: str,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Manually process a document with AI analysis"""
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
        # Get document
        document = company_db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if already processed
        existing_analysis = company_db.query(DocumentAnalysis).filter(
            DocumentAnalysis.document_id == document_id
        ).first()
        
        if existing_analysis:
            return {
                "message": "Document already processed by AI",
                "analysis_id": existing_analysis.id,
                "already_processed": True
            }
        
        # Download file from S3
        try:
            file_content = await aws_service.download_file(
                bucket_name=company.s3_bucket_name,
                file_key=document.s3_key
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to download file from S3: {str(e)}")
        
        # Get user information
        user = company_db.query(CompanyUser).filter(
            CompanyUser.id == document.user_id
        ).first()
        
        user_name = user.full_name if user else "Unknown User"
        user_email = user.email if user else "unknown@example.com"
        
        # Process with AI
        analysis_result = await document_analysis_service.process_document_upload(
            document_id=document.id,
            file_content=file_content,
            filename=document.filename,
            folder_name=document.folder_name,
            user_id=document.user_id,
            user_name=user_name,
            user_email=user_email,
            company_db=company_db
        )
        
        if analysis_result["success"]:
            return {
                "message": "Document processed successfully with AI",
                "analysis_id": analysis_result["analysis_id"],
                "metadata": analysis_result["metadata"],
                "expiry_detected": analysis_result["expiry_detected"],
                "already_processed": False
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"AI processing failed: {analysis_result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document with AI: {str(e)}")
    finally:
        company_db.close()

@router.get("/{document_id}/ai-analysis")
async def get_document_ai_analysis(
    document_id: str,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get AI analysis for a specific document"""
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
        # Get document
        document = company_db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document has AI analysis
        analysis = company_db.query(DocumentAnalysis).filter(
            DocumentAnalysis.document_id == document_id
        ).first()
        
        if analysis:
            return {
                "document_id": document_id,
                "filename": document.filename,
                "ai_processed": True,
                "analysis": {
                    "id": analysis.id,
                    "title": analysis.title,
                    "summary": analysis.summary,
                    "document_type": analysis.document_type,
                    "expiry_detected": analysis.expiry_detected,
                    "expiry_date": analysis.expiry_date.isoformat() if analysis.expiry_date else None,
                    "urgency_level": analysis.urgency_level,
                    "key_topics": analysis.key_topics,
                    "entities": analysis.entities,
                    "keywords": analysis.keywords,
                    "language": analysis.language,
                    "word_count": analysis.word_count,
                    "sentiment": analysis.sentiment,
                    "important_notes": analysis.important_notes,
                    "compliance_requirements": analysis.compliance_requirements,
                    "extracted_text": analysis.extracted_text,
                    "ai_model": analysis.ai_model,
                    "processing_status": analysis.processing_status,
                    "created_at": analysis.created_at.isoformat()
                }
            }
        else:
            return {
                "document_id": document_id,
                "filename": document.filename,
                "ai_processed": False,
                "message": "Document has not been processed by AI yet"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking AI analysis: {str(e)}")
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
@router.options("/folders")
async def options_folders():
    """Handle CORS preflight for folders endpoint"""
    return {"message": "OK"}

@router.get("/folders", response_model=List[schemas.DocumentFolderResponse])
async def list_document_folders(
    category_id: Optional[str] = None,
    current_user = Depends(auth.get_current_user_or_system_user),
    management_db: Session = Depends(get_management_db)
):
    """List document folders, optionally filtered by category"""
    # For system admins, show folders from all companies
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins need to query all company databases to get folders
        all_folders = []
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        for company in companies:
            try:
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                query = company_db.query(DocumentFolder).filter(
                    DocumentFolder.is_active == True
                )
                
                if category_id:
                    query = query.filter(DocumentFolder.category_id == category_id)
                
                folders = query.order_by(DocumentFolder.sort_order).all()
                
                # Add company context to folders
                for folder in folders:
                    folder.company_name = company.name  # type: ignore
                
                all_folders.extend(folders)
                company_db.close()
            except Exception as e:
                print(f"Error accessing company {company.id}: {str(e)}")
                continue
        
        return all_folders
    else:
        # For company users, show only their company's folders
        company_db_gen = get_company_db(str(current_user.company_id), str(current_user.company.database_url))
        company_db = next(company_db_gen)
        
        try:
            query = company_db.query(DocumentFolder).filter(
                DocumentFolder.company_id == current_user.company_id,
                DocumentFolder.is_active == True
            )
            
            if category_id:
                query = query.filter(DocumentFolder.category_id == category_id)
            
            folders = query.order_by(DocumentFolder.sort_order).all()
            return folders
        finally:
            company_db.close()

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

@router.options("/bulk-operation")
async def options_bulk_operation():
    """Handle CORS preflight for bulk-operation endpoint"""
    return {"message": "OK"}

@router.post("/bulk-operation")
async def bulk_document_operation(
    operation: schemas.BulkDocumentOperation,
    current_user = Depends(auth.get_current_user_or_system_user),
    management_db: Session = Depends(get_management_db)
):
    """Perform bulk operations on documents"""
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins can perform bulk operations on all documents across all companies
        all_documents = []
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        for company in companies:
            try:
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                company_documents = company_db.query(CompanyDocument).filter(
                    CompanyDocument.id.in_(operation.document_ids)
                ).all()
                
                all_documents.extend(company_documents)
                company_db.close()
            except Exception as e:
                print(f"Error accessing company {company.id}: {str(e)}")
                continue
        
        documents = all_documents
    elif current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    else:
        # Company users can only perform bulk operations on their company's documents
        company_db_gen = get_company_db(str(current_user.company_id), str(current_user.company.database_url))
        company_db = next(company_db_gen)
        
        try:
            documents = company_db.query(CompanyDocument).filter(
                CompanyDocument.id.in_(operation.document_ids),
                CompanyDocument.company_id == current_user.company_id
            ).all()
        finally:
            company_db.close()
    
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
    management_db: Session = Depends(get_management_db)
):
    """Get document audit logs (HR admins, managers, and system admins only)"""
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins can see all audit logs from all companies
        all_logs = []
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        for company in companies:
            try:
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                query = company_db.query(DocumentAuditLog)
                
                if document_id:
                    query = query.filter(DocumentAuditLog.document_id == document_id)
                
                if user_id:
                    query = query.filter(DocumentAuditLog.user_id == user_id)
                
                if action:
                    query = query.filter(DocumentAuditLog.action == action)
                
                company_logs = query.order_by(DocumentAuditLog.created_at.desc()).all()
                
                # Add company context to logs
                for log in company_logs:
                    log.company_name = company.name  # type: ignore
                
                all_logs.extend(company_logs)
                company_db.close()
            except Exception as e:
                print(f"Error accessing company {company.id}: {str(e)}")
                continue
        
        # Apply pagination to all logs
        total_count = len(all_logs)
        offset = (page - 1) * page_size
        paginated_logs = all_logs[offset:offset + page_size]
        
        return paginated_logs
    elif current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    else:
        # Company users can only see their company's audit logs
        company_db_gen = get_company_db(str(current_user.company_id), str(current_user.company.database_url))
        company_db = next(company_db_gen)
        
        try:
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
        finally:
            company_db.close()

@router.get("/stats")
async def get_document_statistics(
    current_user = Depends(auth.get_current_user_or_system_user),
    management_db: Session = Depends(get_management_db)
):
    """Get document statistics for the company or all companies (for system admins)"""
    
    # Base query for documents
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admins can see stats from all companies
        all_stats = {
            'total_documents': 0,
            'category_distribution': {},
            'file_type_distribution': {},
            'recent_uploads_30_days': 0,
            'total_storage_bytes': 0
        }
        
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        for company in companies:
            try:
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                # Get company stats
                company_docs = company_db.query(CompanyDocument).all()
                company_count = len(company_docs)
                all_stats['total_documents'] += company_count
                
                # Category distribution
                category_stats = company_db.query(
                    CompanyDocument.document_category,
                    func.count(CompanyDocument.id)
                ).filter(CompanyDocument.document_category.isnot(None)).group_by(CompanyDocument.document_category).all()
                
                for category, count in category_stats:
                    if category in all_stats['category_distribution']:
                        all_stats['category_distribution'][category] += count
                    else:
                        all_stats['category_distribution'][category] = count
                
                # File type distribution
                file_type_stats = company_db.query(
                    CompanyDocument.file_type,
                    func.count(CompanyDocument.id)
                ).group_by(CompanyDocument.file_type).all()
                
                for file_type, count in file_type_stats:
                    if file_type in all_stats['file_type_distribution']:
                        all_stats['file_type_distribution'][file_type] += count
                    else:
                        all_stats['file_type_distribution'][file_type] += count
                
                # Recent uploads
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                recent_uploads = company_db.query(CompanyDocument).filter(
                    CompanyDocument.created_at >= thirty_days_ago
                ).count()
                all_stats['recent_uploads_30_days'] += recent_uploads
                
                # Storage usage
                total_size = company_db.query(func.sum(CompanyDocument.file_size)).scalar() or 0
                all_stats['total_storage_bytes'] += total_size
                
                company_db.close()
            except Exception as e:
                print(f"Error accessing company {company.id}: {str(e)}")
                continue
        
        all_stats['total_storage_mb'] = round(all_stats['total_storage_bytes'] / (1024 * 1024), 2)
        return all_stats
    else:
        # Company users can only see their company's stats
        company_db_gen = get_company_db(str(current_user.company_id), str(current_user.company.database_url))
        company_db = next(company_db_gen)
        
        try:
            base_query = company_db.query(CompanyDocument).filter(
                CompanyDocument.company_id == current_user.company_id
            )
            
            # Total documents
            total_documents = base_query.count()
            
            # Documents by category
            category_stats = company_db.query(
                CompanyDocument.document_category,
                func.count(CompanyDocument.id)
            ).filter(
                CompanyDocument.document_category.isnot(None),
                CompanyDocument.company_id == current_user.company_id
            ).group_by(CompanyDocument.document_category).all()
            
            # Documents by file type
            file_type_stats = company_db.query(
                CompanyDocument.file_type,
                func.count(CompanyDocument.id)
            ).filter(
                CompanyDocument.company_id == current_user.company_id
            ).group_by(CompanyDocument.file_type).all()
            
            # Recent uploads (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_uploads = base_query.filter(
                CompanyDocument.created_at >= thirty_days_ago
            ).count()
            
            # Storage usage
            total_size = company_db.query(func.sum(CompanyDocument.file_size)).filter(
                CompanyDocument.company_id == current_user.company_id
            ).scalar() or 0
            
            return {
                "total_documents": total_documents,
                "category_distribution": dict(category_stats),
                "file_type_distribution": dict(file_type_stats),
                "recent_uploads_30_days": recent_uploads,
                "total_storage_bytes": total_size,
                "total_storage_mb": round(total_size / (1024 * 1024), 2)
            }
        finally:
            company_db.close()

# New HR Admin and Analytics APIs
@router.get("/counts/my", response_model=schemas.DocumentCountsResponse)
async def get_my_documents_count(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db)
):
    """Get count of user's personal documents"""
    try:
        # Count user's documents
        my_count = company_db.query(CompanyDocument).filter(
            CompanyDocument.user_id == current_user.id,
            CompanyDocument.company_id == current_user.company_id
        ).count()
        
        return schemas.DocumentCountsResponse(
            my_files_count=my_count,
            org_files_count=0,
            recent_files_count=0,
            starred_files_count=0,
            logs_count=0,
            uploads_count=0,
            category_counts={}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document counts: {str(e)}")

@router.get("/counts/org", response_model=schemas.DocumentCountsResponse)
async def get_org_documents_count(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db)
):
    """Get count of organization documents"""
    try:
        # Count all company documents
        org_count = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id
        ).count()
        
        # Get category counts
        category_counts = {}
        categories = company_db.query(CompanyDocument.document_category).filter(
            CompanyDocument.company_id == current_user.company_id,
            CompanyDocument.document_category.isnot(None)
        ).distinct().all()
        
        for cat in categories:
            if cat[0]:
                count = company_db.query(CompanyDocument).filter(
                    CompanyDocument.company_id == current_user.company_id,
                    CompanyDocument.document_category == cat[0]
                ).count()
                category_counts[cat[0]] = count
        
        return schemas.DocumentCountsResponse(
            my_files_count=0,
            org_files_count=org_count,
            recent_files_count=0,
            starred_files_count=0,
            logs_count=0,
            uploads_count=0,
            category_counts=category_counts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get organization document counts: {str(e)}")

@router.get("/counts/recent", response_model=schemas.DocumentCountsResponse)
async def get_recent_documents_count(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db)
):
    """Get count of recently accessed documents"""
    try:
        # Count documents accessed in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_count = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id,
            CompanyDocument.created_at >= thirty_days_ago
        ).count()
        
        return schemas.DocumentCountsResponse(
            my_files_count=0,
            org_files_count=0,
            recent_files_count=recent_count,
            starred_files_count=0,
            logs_count=0,
            uploads_count=0,
            category_counts={}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent document counts: {str(e)}")

@router.get("/counts/starred", response_model=schemas.DocumentCountsResponse)
async def get_starred_documents_count(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db)
):
    """Get count of starred documents"""
    try:
        # For now, return 0 as starred functionality needs to be implemented
        # This would require a new table to track starred documents
        return schemas.DocumentCountsResponse(
            my_files_count=0,
            org_files_count=0,
            recent_files_count=0,
            starred_files_count=0,
            logs_count=0,
            uploads_count=0,
            category_counts={}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get starred document counts: {str(e)}")

@router.get("/counts/logs", response_model=schemas.DocumentCountsResponse)
async def get_document_activity_logs_count(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db)
):
    """Get count of document activity logs"""
    try:
        # Count document audit logs
        logs_count = company_db.query(DocumentAuditLog).filter(
            DocumentAuditLog.company_id == current_user.company_id
        ).count()
        
        return schemas.DocumentCountsResponse(
            my_files_count=0,
            org_files_count=0,
            recent_files_count=0,
            starred_files_count=0,
            logs_count=logs_count,
            uploads_count=0,
            category_counts={}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document logs count: {str(e)}")

@router.get("/counts/uploads", response_model=schemas.DocumentCountsResponse)
async def get_uploads_count(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db)
):
    """Get count of uploads"""
    try:
        # Count documents uploaded by user
        uploads_count = company_db.query(CompanyDocument).filter(
            CompanyDocument.user_id == current_user.id,
            CompanyDocument.company_id == current_user.company_id
        ).count()
        
        return schemas.DocumentCountsResponse(
            my_files_count=0,
            org_files_count=0,
            recent_files_count=0,
            starred_files_count=0,
            logs_count=0,
            uploads_count=uploads_count,
            category_counts={}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get uploads count: {str(e)}")

@router.get("/analytics/summary", response_model=schemas.DocumentAnalyticsSummaryResponse)
async def get_document_analytics_summary(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db)
):
    """Get document analytics summary for HR admin dashboard"""
    try:
        if current_user.role not in ['hr_admin', 'hr_manager']:
            raise HTTPException(status_code=403, detail="Access denied. HR role required.")
        
        # Get total documents
        total_documents = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id
        ).count()
        
        # Get documents by category
        categories = company_db.query(CompanyDocument.document_category).filter(
            CompanyDocument.company_id == current_user.company_id,
            CompanyDocument.document_category.isnot(None)
        ).distinct().all()
        
        documents_by_category = {}
        for cat in categories:
            if cat[0]:
                count = company_db.query(CompanyDocument).filter(
                    CompanyDocument.company_id == current_user.company_id,
                    CompanyDocument.document_category == cat[0]
                ).count()
                documents_by_category[cat[0]] = count
        
        # Get documents by type
        file_types = company_db.query(CompanyDocument.file_type).filter(
            CompanyDocument.company_id == current_user.company_id
        ).distinct().all()
        
        documents_by_type = {}
        for ft in file_types:
            if ft[0]:
                count = company_db.query(CompanyDocument).filter(
                    CompanyDocument.company_id == current_user.company_id,
                    CompanyDocument.file_type == ft[0]
                ).count()
                documents_by_type[ft[0]] = count
        
        # Get uploads by month (last 6 months)
        uploads_by_month = {}
        for i in range(6):
            month_date = datetime.utcnow() - timedelta(days=30*i)
            month_key = month_date.strftime("%Y-%m")
            start_date = month_date.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            count = company_db.query(CompanyDocument).filter(
                CompanyDocument.company_id == current_user.company_id,
                CompanyDocument.created_at >= start_date,
                CompanyDocument.created_at <= end_date
            ).count()
            uploads_by_month[month_key] = count
        
        # Get top viewed documents (placeholder - would need analytics table)
        top_viewed_documents = []
        
        # Get recent activity
        recent_activity = []
        recent_docs = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id
        ).order_by(CompanyDocument.created_at.desc()).limit(10).all()
        
        for doc in recent_docs:
            recent_activity.append({
                "action": "uploaded",
                "document_name": doc.original_filename,
                "user_name": doc.user.full_name if doc.user else "Unknown",
                "timestamp": doc.created_at.isoformat(),
                "document_id": doc.id
            })
        
        return schemas.DocumentAnalyticsSummaryResponse(
            total_documents=total_documents,
            total_views=0,  # Placeholder
            total_downloads=0,  # Placeholder
            total_shares=0,  # Placeholder
            documents_by_category=documents_by_category,
            documents_by_type=documents_by_type,
            uploads_by_month=uploads_by_month,
            top_viewed_documents=top_viewed_documents,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")

@router.get("/search", response_model=schemas.SearchResultResponse)
async def search_documents_and_users(
    query: str,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db)
):
    """Search for documents and users"""
    try:
        start_time = datetime.utcnow()
        
        # Search documents
        documents = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id,
            or_(
                CompanyDocument.original_filename.ilike(f"%{query}%"),
                CompanyDocument.document_category.ilike(f"%{query}%"),
                CompanyDocument.description.ilike(f"%{query}%")
            )
        ).limit(10).all()
        
        # Search users (if HR role)
        employees = []
        if current_user.role in ['hr_admin', 'hr_manager']:
            employees = company_db.query(CompanyUser).filter(
                CompanyUser.company_id == current_user.company_id,
                or_(
                    CompanyUser.full_name.ilike(f"%{query}%"),
                    CompanyUser.email.ilike(f"%{query}%"),
                    CompanyUser.role.ilike(f"%{query}%")
                )
            ).limit(10).all()
        
        search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return schemas.SearchResultResponse(
            employees=[schemas.EmployeeSummaryResponse(
                id=emp.id,
                full_name=emp.full_name,
                email=emp.email,
                role=emp.role,
                department=None,  # Would need department field
                status="active" if emp.is_active else "inactive",
                documents_count=len(emp.documents),
                last_login=None,  # Would need login tracking
                created_at=emp.created_at
            ) for emp in employees],
            documents=[schemas.DocumentSummaryResponse(
                id=doc.id,
                original_filename=doc.original_filename,
                document_category=doc.document_category,
                file_size=doc.file_size,
                file_type=doc.file_type,
                user_id=doc.user_id,
                user_full_name=doc.user.full_name if doc.user else "Unknown",
                created_at=doc.created_at,
                status=doc.status
            ) for doc in documents],
            total_results=len(employees) + len(documents),
            search_time_ms=search_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# HR Admin specific endpoints
@router.get("/hr/stats", response_model=schemas.HRDashboardStatsResponse)
async def get_hr_dashboard_stats(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db)
):
    """Get HR dashboard statistics"""
    try:
        if current_user.role not in ['hr_admin', 'hr_manager']:
            raise HTTPException(status_code=403, detail="Access denied. HR role required.")
        
        # Get employee counts
        total_employees = company_db.query(CompanyUser).filter(
            CompanyUser.company_id == current_user.company_id
        ).count()
        
        active_employees = company_db.query(CompanyUser).filter(
            CompanyUser.company_id == current_user.company_id,
            CompanyUser.is_active == True
        ).count()
        
        # Get document counts
        total_documents = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id
        ).count()
        
        # Get documents this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        documents_this_month = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id,
            CompanyDocument.created_at >= month_start
        ).count()
        
        # Calculate storage used (in GB)
        total_size_bytes = company_db.query(func.sum(CompanyDocument.file_size)).filter(
            CompanyDocument.company_id == current_user.company_id
        ).scalar() or 0
        storage_used_gb = total_size_bytes / (1024**3)
        
        # Placeholder values for features not yet implemented
        pending_approvals = 0
        compliance_alerts = 0
        storage_limit_gb = 100.0  # 100GB default limit
        
        return schemas.HRDashboardStatsResponse(
            total_employees=total_employees,
            active_employees=active_employees,
            pending_approvals=pending_approvals,
            compliance_alerts=compliance_alerts,
            total_documents=total_documents,
            documents_this_month=documents_this_month,
            storage_used_gb=round(storage_used_gb, 2),
            storage_limit_gb=storage_limit_gb
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get HR stats: {str(e)}")

@router.get("/hr/employees", response_model=List[schemas.EmployeeSummaryResponse])
async def get_hr_employees_list(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db),
    skip: int = 0,
    limit: int = 100
):
    """Get list of employees for HR admin"""
    try:
        if current_user.role not in ['hr_admin', 'hr_manager']:
            raise HTTPException(status_code=403, detail="Access denied. HR role required.")
        
        employees = company_db.query(CompanyUser).filter(
            CompanyUser.company_id == current_user.company_id
        ).offset(skip).limit(limit).all()

        # Build response with document counts
        response = []
        for emp in employees:
            # Count documents for this user
            doc_count = company_db.query(CompanyDocument).filter(
                CompanyDocument.user_id == emp.id,
                CompanyDocument.company_id == current_user.company_id
            ).count()

            response.append(schemas.EmployeeSummaryResponse(
                id=emp.id,
                full_name=emp.full_name,
                email=emp.email,
                role=emp.role,
                department=emp.department if hasattr(emp, 'department') else None,
                status="active" if emp.is_active else "inactive",
                documents_count=doc_count,
                last_login=None,  # Would need login tracking
                created_at=emp.created_at
            ))

        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get employees list: {str(e)}")

@router.get("/hr/workflows", response_model=List[schemas.WorkflowSummaryResponse])
async def get_hr_workflows_list(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db),
    skip: int = 0,
    limit: int = 100
):
    """Get list of workflows for HR admin"""
    try:
        if current_user.role not in ['hr_admin', 'hr_manager']:
            raise HTTPException(status_code=403, detail="Access denied. HR role required.")
        
        # Placeholder - workflows not yet implemented
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows list: {str(e)}")

@router.get("/hr/compliance", response_model=List[schemas.ComplianceSummaryResponse])
async def get_hr_compliance_violations(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    company_db: Session = Depends(get_company_db),
    skip: int = 0,
    limit: int = 100
):
    """Get list of compliance violations for HR admin"""
    try:
        if current_user.role not in ['hr_admin', 'hr_manager']:
            raise HTTPException(status_code=403, detail="Access denied. HR role required.")
        
        # Placeholder - compliance violations not yet implemented
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance violations: {str(e)}")

# Helper functions for Document Health Snapshot
def categorize_document(doc, doc_analysis):
    """Categorize document based on type/category/folder"""
    doc_text = " ".join([
        doc.document_category or "",
        doc.document_subcategory or "",
        doc_analysis.document_type if doc_analysis else "",
        doc.original_filename
    ]).lower()

    for cat_key, cat_info in HEALTH_CATEGORY_MAPPING.items():
        if any(keyword in doc_text for keyword in cat_info["keywords"]):
            return cat_key

    return "employee_relations"  # Default category

def calculate_compliance_status(doc, doc_analysis):
    """Calculate compliance status based on expiry and metadata"""
    from datetime import date
    today = date.today()

    # Check expiry
    if doc_analysis and doc_analysis.expiry_detected and doc_analysis.expiry_date:
        if doc_analysis.expiry_date < today:
            return "non_compliant", f"Expired on {doc_analysis.expiry_date}", doc_analysis.expiry_date

        days_until = (doc_analysis.expiry_date - today).days
        if 30 <= days_until <= 60:
            return "at_risk", f"Expiring in {days_until} days", doc_analysis.expiry_date

    # Check missing metadata
    missing = []
    if not doc.document_category:
        missing.append("category")
    if not doc.document_subcategory:
        missing.append("subcategory")
    if not doc_analysis or not doc_analysis.document_type:
        missing.append("document_type")

    if len(missing) >= 2:
        return "at_risk", "Missing metadata", None

    return "compliant", "Active", None

@router.get("/hr/health-snapshot", response_model=schemas.DocumentHealthSnapshotResponse)
async def get_hr_health_snapshot(
    user_id: Optional[str] = None,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """
    Get document health snapshot for compliance tracking

    Args:
        user_id: Optional user ID to filter documents.
                 - For regular employees: automatically filtered to their own documents (parameter ignored)
                 - For HR/Managers: can filter by any user, or see all if not specified
    """
    # Role-based access control
    is_hr_or_manager = current_user.role in ['hr_admin', 'hr_manager', 'manager']

    # Regular employees can only see their own documents
    if not is_hr_or_manager:
        user_id = current_user.id  # Force to their own ID for security

    # Get company database
    company = management_db.query(models.Company).filter(
        models.Company.id == current_user.company_id
    ).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        # Debug: Log current user and company info
        logger.info(f"📊 Document Health - User: {current_user.username}, Company: {current_user.company_id}, Role: {current_user.role}")
        logger.info(f"🔍 User filter parameter received: {user_id if user_id else 'NONE (should show ALL USERS)'}")
        logger.info(f"🆔 Current user ID: {current_user.id}")

        # First, check total documents in company WITHOUT any filters
        all_docs = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id
        ).all()
        logger.info(f"📄 Total documents in company database: {len(all_docs)}")

        # Log sample of documents and their user_ids
        if len(all_docs) > 0:
            logger.info(f"📋 Sample documents (first 5):")
            for i, doc in enumerate(all_docs[:5]):
                logger.info(f"  Doc {i+1}: ID={doc.id}, user_id={doc.user_id}, filename={doc.original_filename}")

        # Get unique user IDs from documents
        unique_user_ids = set(doc.user_id for doc in all_docs)
        logger.info(f"👥 Unique user IDs with documents: {unique_user_ids}")

        # Check how many have analysis
        all_analysis = company_db.query(DocumentAnalysis).all()
        logger.info(f"🤖 Total DocumentAnalysis records: {len(all_analysis)}")
        if len(all_analysis) > 0:
            analyzed_doc_ids = {a.document_id for a in all_analysis}
            logger.info(f"📊 Document IDs with analysis: {analyzed_doc_ids}")

        # Build query for documents with analysis
        query = company_db.query(
            CompanyDocument, DocumentAnalysis
        ).outerjoin(
            DocumentAnalysis,
            CompanyDocument.id == DocumentAnalysis.document_id
        ).filter(
            CompanyDocument.company_id == current_user.company_id
        )

        # Apply user filter if specified
        if user_id:
            logger.info(f"⚠️ APPLYING USER FILTER for user_id: {user_id}")
            query = query.filter(CompanyDocument.user_id == user_id)
        else:
            logger.info(f"✅ NO USER FILTER - should return ALL company documents")

        docs_query = query.all()
        logger.info(f"✅ Final query returned {len(docs_query)} document records")

        # Log details of what was returned
        if len(docs_query) > 0:
            logger.info(f"📝 Returned documents:")
            for i, (doc, analysis) in enumerate(docs_query[:5]):
                logger.info(f"  Result {i+1}: Doc ID={doc.id}, user_id={doc.user_id}, has_analysis={analysis is not None}")

        # Categorize and calculate status
        categorized_docs = {key: [] for key in HEALTH_CATEGORY_MAPPING.keys()}
        all_statuses = []

        for doc, analysis in docs_query:
            cat_key = categorize_document(doc, analysis)
            status, reason, expiry = calculate_compliance_status(doc, analysis)

            categorized_docs[cat_key].append({
                "doc": doc,
                "analysis": analysis,
                "status": status,
                "reason": reason,
                "expiry": expiry
            })
            all_statuses.append(status)

        # Calculate overall metrics
        total = len(docs_query)
        compliant_cnt = all_statuses.count("compliant")
        at_risk_cnt = all_statuses.count("at_risk")
        non_compliant_cnt = all_statuses.count("non_compliant")

        # Build category metrics
        categories = []
        for cat_key, cat_info in HEALTH_CATEGORY_MAPPING.items():
            cat_docs = categorized_docs[cat_key]
            cat_total = len(cat_docs)

            if cat_total == 0:
                continue  # Skip empty categories

            cat_compliant = sum(1 for d in cat_docs if d["status"] == "compliant")
            cat_at_risk = sum(1 for d in cat_docs if d["status"] == "at_risk")
            cat_non_compliant = sum(1 for d in cat_docs if d["status"] == "non_compliant")
            cat_compliance_pct = round((cat_compliant / cat_total) * 100, 1)

            # Determine status badge
            if cat_compliance_pct >= 90:
                cat_status = "Healthy"
            elif cat_compliance_pct >= 70:
                cat_status = "Watch"
            else:
                cat_status = "Critical"

            # Group by employee for drill-down
            employee_docs = {}
            for item in cat_docs:
                doc = item["doc"]
                user = company_db.query(CompanyUser).filter(
                    CompanyUser.id == doc.user_id
                ).first()

                if not user:
                    continue

                if user.id not in employee_docs:
                    employee_docs[user.id] = {
                        "user": user,
                        "documents": []
                    }

                missing_fields = []
                if not doc.document_category:
                    missing_fields.append("category")
                if not doc.document_subcategory:
                    missing_fields.append("subcategory")
                if not item["analysis"] or not item["analysis"].document_type:
                    missing_fields.append("document_type")

                employee_docs[user.id]["documents"].append({
                    "document_id": doc.id,
                    "filename": doc.original_filename,
                    "document_type": item["analysis"].document_type if item["analysis"] else None,
                    "expiry_date": item["expiry"],
                    "days_until_expiry": (item["expiry"] - date.today()).days if item["expiry"] else None,
                    "status": item["status"],
                    "missing_fields": missing_fields
                })

            # Build affected employees list
            affected = []
            for user_id, emp_data in employee_docs.items():
                user = emp_data["user"]
                affected.append(schemas.AffectedEmployee(
                    user_id=user.id,
                    full_name=user.full_name,
                    email=user.email,
                    employee_id=user.employee_id,
                    department=user.department,
                    documents=[schemas.AffectedDocument(**d) for d in emp_data["documents"]]
                ))

            categories.append(schemas.CategoryHealthMetrics(
                category_name=cat_info["display_name"],
                category_key=cat_key,
                icon=cat_info["icon"],
                total_documents=cat_total,
                compliant_count=cat_compliant,
                at_risk_count=cat_at_risk,
                non_compliant_count=cat_non_compliant,
                compliance_percentage=cat_compliance_pct,
                status=cat_status,
                affected_employees=affected
            ))

        return schemas.DocumentHealthSnapshotResponse(
            total_documents=total,
            compliant_count=compliant_cnt,
            at_risk_count=at_risk_cnt,
            non_compliant_count=non_compliant_cnt,
            compliant_percentage=round((compliant_cnt / total * 100), 1) if total > 0 else 0,
            at_risk_percentage=round((at_risk_cnt / total * 100), 1) if total > 0 else 0,
            non_compliant_percentage=round((non_compliant_cnt / total * 100), 1) if total > 0 else 0,
            categories=categories,
            last_updated=datetime.utcnow(),
            target_threshold=95.0
        )

    except Exception as e:
        logger.error(f"❌ Failed to get health snapshot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health snapshot: {str(e)}")
    finally:
        company_db.close()

@router.post("/hr/process-unanalyzed-documents")
async def process_unanalyzed_documents(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """
    Process all documents that don't have AI analysis yet.
    This is useful for existing documents that were uploaded before AI analysis was enabled.
    """
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR role required.")

    # Get company database
    company = management_db.query(models.Company).filter(
        models.Company.id == current_user.company_id
    ).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        # Log company and user info
        logger.info(f"🔧 Process Unanalyzed - User: {current_user.username}, Company: {current_user.company_id}, Role: {current_user.role}")

        # First check total documents in company
        all_docs = company_db.query(CompanyDocument).filter(
            CompanyDocument.company_id == current_user.company_id
        ).all()
        logger.info(f"📄 Total documents in company: {len(all_docs)}")

        # Check which have analysis
        all_analysis = company_db.query(DocumentAnalysis).all()
        analyzed_doc_ids = {a.document_id for a in all_analysis}
        logger.info(f"🤖 Documents with analysis: {len(analyzed_doc_ids)}")
        logger.info(f"📊 Analysis doc IDs: {analyzed_doc_ids}")

        # Find documents without analysis
        docs_without_analysis = company_db.query(CompanyDocument).outerjoin(
            DocumentAnalysis,
            CompanyDocument.id == DocumentAnalysis.document_id
        ).filter(
            CompanyDocument.company_id == current_user.company_id,
            DocumentAnalysis.id.is_(None)  # No analysis record exists
        ).all()

        logger.info(f"📊 Found {len(docs_without_analysis)} documents without AI analysis")

        if len(docs_without_analysis) > 0:
            logger.info(f"📋 Documents needing analysis:")
            for i, doc in enumerate(docs_without_analysis[:10]):
                logger.info(f"  {i+1}. Doc ID={doc.id}, user_id={doc.user_id}, file={doc.original_filename}")

        if len(docs_without_analysis) == 0:
            logger.info("✅ All documents already have analysis")
            return {
                "message": "All documents have been analyzed",
                "processed": 0,
                "total": 0
            }

        processed_count = 0
        failed_count = 0
        errors = []

        for doc in docs_without_analysis:
            try:
                logger.info(f"🤖 Processing document {doc.id}: {doc.original_filename}")

                # Download file from S3
                file_content = await aws_service.download_file_from_s3(
                    company.s3_bucket_name,
                    doc.s3_key
                )

                # Get user information
                user = company_db.query(CompanyUser).filter(
                    CompanyUser.id == doc.user_id
                ).first()

                user_name = user.full_name if user else "Unknown User"
                user_email = user.email if user else "unknown@example.com"

                # Process with AI
                analysis_result = await document_analysis_service.process_document_upload(
                    document_id=doc.id,
                    file_content=file_content,
                    filename=doc.original_filename,
                    folder_name=doc.folder_name or "",
                    user_id=doc.user_id,
                    user_name=user_name,
                    user_email=user_email,
                    company_db=company_db
                )

                if analysis_result["success"]:
                    processed_count += 1
                    logger.info(f"✅ Successfully analyzed document {doc.id}")
                else:
                    failed_count += 1
                    error_msg = f"Document {doc.id}: {analysis_result.get('error', 'Unknown error')}"
                    errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")

            except Exception as e:
                failed_count += 1
                error_msg = f"Document {doc.id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ Failed to process document {doc.id}: {str(e)}")

        return {
            "message": f"Processed {processed_count} documents successfully, {failed_count} failed",
            "processed": processed_count,
            "failed": failed_count,
            "total": len(docs_without_analysis),
            "errors": errors[:10] if errors else []  # Return first 10 errors
        }

    except Exception as e:
        logger.error(f"❌ Failed to process unanalyzed documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process documents: {str(e)}")
    finally:
        company_db.close()

# Add CORS preflight handler for upload endpoint
@router.options("/upload")
async def upload_options():
    """Handle CORS preflight for upload endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://multitenant-frontend.onrender.com",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin, User-Agent, Cache-Control, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600"
        }
    )

