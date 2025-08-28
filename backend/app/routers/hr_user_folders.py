from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os

from app.database import get_management_db, get_company_db
from app import models, schemas, auth
from app.models_company import (
    User as CompanyUser, 
    UserFolder,
    HRManagedDocument,
    UserFolderAccess,
    UserFolderAuditLog
)
from app.utils.permissions import get_manageable_roles
from app.services.aws_service import aws_service

router = APIRouter()

def verify_hr_access(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Verify that the current user has HR admin or manager access"""
    if current_user.role not in ["hr_admin", "hr_manager", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. HR admin or manager role required."
        )
    return current_user

@router.post("/folders", response_model=schemas.UserFolderResponse)
async def create_user_folder(
    folder_data: schemas.UserFolderCreate,
    current_user: CompanyUser = Depends(verify_hr_access),
    management_db: Session = Depends(get_management_db)
):
    """Create a new folder for a specific user"""
    
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Verify the target user exists
        target_user = company_db.query(CompanyUser).filter(
            CompanyUser.id == folder_data.user_id,
            CompanyUser.company_id == company_id
        ).first()
        
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
        
        # Create S3 folder
        s3_folder_path = await aws_service.create_hr_user_folder(
            company.s3_bucket_name,
            folder_data.user_id,
            folder_data.name
        )
        
        # Create folder record in database
        db_folder = UserFolder(
            name=folder_data.name,
            display_name=folder_data.display_name,
            description=folder_data.description,
            user_id=folder_data.user_id,
            created_by_user_id=current_user.id,
            s3_folder_path=s3_folder_path,
            folder_type=folder_data.folder_type,
            sort_order=folder_data.sort_order,
            company_id=company_id
        )
        
        company_db.add(db_folder)
        company_db.commit()
        company_db.refresh(db_folder)
        
        # Log the action
        audit_log = UserFolderAuditLog(
            folder_id=db_folder.id,
            user_id=current_user.id,
            action="folder_created",
            details={
                "folder_name": folder_data.name,
                "target_user_id": folder_data.user_id,
                "target_user_name": target_user.full_name
            },
            company_id=company_id
        )
        company_db.add(audit_log)
        company_db.commit()
        
        # Convert to response format
        response = schemas.UserFolderResponse(
            id=db_folder.id,
            name=db_folder.name,
            display_name=db_folder.display_name,
            description=db_folder.description,
            user_id=db_folder.user_id,
            created_by_user_id=db_folder.created_by_user_id,
            s3_folder_path=db_folder.s3_folder_path,
            folder_type=db_folder.folder_type,
            is_active=db_folder.is_active,
            sort_order=db_folder.sort_order,
            company_id=db_folder.company_id,
            created_at=db_folder.created_at,
            updated_at=db_folder.updated_at,
            documents_count=0,
            total_size=0
        )
        
        return response
        
    finally:
        company_db.close()

@router.get("/folders", response_model=List[schemas.UserFolderResponse])
async def list_user_folders(
    user_id: Optional[str] = Query(None, description="Filter by specific user"),
    current_user: CompanyUser = Depends(verify_hr_access),
    management_db: Session = Depends(get_management_db),
    search: Optional[str] = Query(None, description="Search by folder name"),
    folder_type: Optional[str] = Query(None, description="Filter by folder type")
):
    """List all user folders accessible to the current HR user"""
    
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Build query
        query = company_db.query(UserFolder).filter(
            UserFolder.company_id == company_id,
            UserFolder.is_active == True
        )
        
        if user_id:
            query = query.filter(UserFolder.user_id == user_id)
        
        if folder_type:
            query = query.filter(UserFolder.folder_type == folder_type)
        
        if search:
            query = query.filter(
                or_(
                    UserFolder.name.ilike(f"%{search}%"),
                    UserFolder.display_name.ilike(f"%{search}%")
                )
            )
        
        folders = query.order_by(UserFolder.sort_order, UserFolder.created_at.desc()).all()
        
        # Convert to response format with document counts
        response_list = []
        for folder in folders:
            # Get document count and size for this folder
            folder_docs = company_db.query(HRManagedDocument).filter(
                HRManagedDocument.folder_id == folder.id,
                HRManagedDocument.is_active == True
            ).all()
            
            documents_count = len(folder_docs)
            total_size = sum(doc.file_size for doc in folder_docs)
            
            response = schemas.UserFolderResponse(
                id=folder.id,
                name=folder.name,
                display_name=folder.display_name,
                description=folder.description,
                user_id=folder.user_id,
                created_by_user_id=folder.created_by_user_id,
                s3_folder_path=folder.s3_folder_path,
                folder_type=folder.folder_type,
                is_active=folder.is_active,
                sort_order=folder.sort_order,
                company_id=folder.company_id,
                created_at=folder.created_at,
                updated_at=folder.updated_at,
                documents_count=documents_count,
                total_size=total_size
            )
            response_list.append(response)
        
        return response_list
        
    finally:
        company_db.close()

@router.get("/folders/{folder_id}", response_model=schemas.UserFolderWithDocumentsResponse)
async def get_user_folder_with_documents(
    folder_id: str,
    current_user: CompanyUser = Depends(verify_hr_access),
    management_db: Session = Depends(get_management_db)
):
    """Get a specific user folder with all its documents"""
    
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Get the folder
        folder = company_db.query(UserFolder).filter(
            UserFolder.id == folder_id,
            UserFolder.company_id == company_id,
            UserFolder.is_active == True
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Get all documents in this folder
        documents = company_db.query(HRManagedDocument).filter(
            HRManagedDocument.folder_id == folder_id,
            HRManagedDocument.is_active == True
        ).order_by(HRManagedDocument.created_at.desc()).all()
        
        # Convert documents to response format
        documents_response = []
        for doc in documents:
            doc_response = schemas.HRManagedDocumentResponse(
                id=doc.id,
                filename=doc.filename,
                original_filename=doc.original_filename,
                file_path=doc.file_path,
                file_size=doc.file_size,
                file_type=doc.file_type,
                s3_key=doc.s3_key,
                folder_id=doc.folder_id,
                user_id=doc.user_id,
                created_by_user_id=doc.created_by_user_id,
                document_category=doc.document_category,
                document_subcategory=doc.document_subcategory,
                tags=doc.tags,
                description=doc.description,
                is_public=doc.is_public,
                access_level=doc.access_level,
                expiry_date=doc.expiry_date,
                version=doc.version,
                status=doc.status,
                metadata_json=doc.metadata_json,
                processed=doc.processed,
                company_id=doc.company_id,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            documents_response.append(doc_response)
        
        # Convert folder to response format
        folder_response = schemas.UserFolderResponse(
            id=folder.id,
            name=folder.name,
            display_name=folder.display_name,
            description=folder.description,
            user_id=folder.user_id,
            created_by_user_id=folder.created_by_user_id,
            s3_folder_path=folder.s3_folder_path,
            folder_type=folder.folder_type,
            is_active=folder.is_active,
            sort_order=folder.sort_order,
            company_id=folder.company_id,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
            documents_count=len(documents),
            total_size=sum(doc.file_size for doc in documents)
        )
        
        # Log folder access
        audit_log = UserFolderAuditLog(
            folder_id=folder.id,
            user_id=current_user.id,
            action="folder_accessed",
            details={"access_type": "view"},
            company_id=company_id
        )
        company_db.add(audit_log)
        company_db.commit()
        
        return schemas.UserFolderWithDocumentsResponse(
            folder=folder_response,
            documents=documents_response,
            total_documents=len(documents),
            total_size=sum(doc.file_size for doc in documents)
        )
        
    finally:
        company_db.close()

@router.post("/folders/{folder_id}/documents", response_model=schemas.HRManagedDocumentResponse)
async def upload_document_to_folder(
    folder_id: str,
    file: UploadFile = File(...),
    document_data: str = Form(...),  # JSON string with document metadata
    current_user: CompanyUser = Depends(verify_hr_access),
    management_db: Session = Depends(get_management_db)
):
    """Upload a document to a specific user folder"""
    
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Parse document metadata
        try:
            metadata = json.loads(document_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid document metadata format")
        
        # Verify the folder exists and belongs to the company
        folder = company_db.query(UserFolder).filter(
            UserFolder.id == folder_id,
            UserFolder.company_id == company_id,
            UserFolder.is_active == True
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Verify file size (max 100MB)
        if file.size and file.size > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Upload file to S3
        s3_key = await aws_service.upload_file_to_hr_folder(
            company.s3_bucket_name,
            folder.user_id,
            folder.name,
            file_content,
            file.filename,
            file.content_type
        )
        
        # Create document record in database
        db_document = HRManagedDocument(
            filename=file.filename,
            original_filename=file.filename,
            file_path=s3_key,
            file_size=file_size,
            file_type=file.content_type or "application/octet-stream",
            s3_key=s3_key,
            folder_id=folder_id,
            user_id=folder.user_id,
            created_by_user_id=current_user.id,
            document_category=metadata.get("document_category"),
            document_subcategory=metadata.get("document_subcategory"),
            tags=metadata.get("tags"),
            description=metadata.get("description"),
            is_public=metadata.get("is_public", False),
            access_level=metadata.get("access_level", "private"),
            expiry_date=metadata.get("expiry_date"),
            version=metadata.get("version", "1.0"),
            status=metadata.get("status", "active"),
            metadata_json=metadata,
            company_id=company_id
        )
        
        company_db.add(db_document)
        company_db.commit()
        company_db.refresh(db_document)
        
        # Log the action
        audit_log = UserFolderAuditLog(
            folder_id=folder_id,
            document_id=db_document.id,
            user_id=current_user.id,
            action="document_uploaded",
            details={
                "filename": file.filename,
                "file_size": file_size,
                "file_type": file.content_type
            },
            company_id=company_id
        )
        company_db.add(audit_log)
        company_db.commit()
        
        # Convert to response format
        response = schemas.HRManagedDocumentResponse(
            id=db_document.id,
            filename=db_document.filename,
            original_filename=db_document.original_filename,
            file_path=db_document.file_path,
            file_size=db_document.file_size,
            file_type=db_document.file_type,
            s3_key=db_document.s3_key,
            folder_id=db_document.folder_id,
            user_id=db_document.user_id,
            created_by_user_id=db_document.created_by_user_id,
            document_category=db_document.document_category,
            document_subcategory=db_document.document_subcategory,
            tags=db_document.tags,
            description=db_document.description,
            is_public=db_document.is_public,
            access_level=db_document.access_level,
            expiry_date=db_document.expiry_date,
            version=db_document.version,
            status=db_document.status,
            metadata_json=db_document.metadata_json,
            processed=db_document.processed,
            company_id=db_document.company_id,
            created_at=db_document.created_at,
            updated_at=db_document.updated_at
        )
        
        return response
        
    finally:
        company_db.close()

@router.get("/users/{user_id}/folders", response_model=schemas.UserFoldersSummaryResponse)
async def get_user_folders_summary(
    user_id: str,
    current_user: CompanyUser = Depends(verify_hr_access),
    management_db: Session = Depends(get_management_db)
):
    """Get a summary of all folders for a specific user"""
    
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Verify the target user exists
        target_user = company_db.query(CompanyUser).filter(
            CompanyUser.id == user_id,
            CompanyUser.company_id == company_id
        ).first()
        
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
        
        # Get all folders for this user
        folders = company_db.query(UserFolder).filter(
            UserFolder.user_id == user_id,
            UserFolder.company_id == company_id,
            UserFolder.is_active == True
        ).order_by(UserFolder.sort_order, UserFolder.created_at.desc()).all()
        
        # Convert folders to response format with document counts
        folders_response = []
        total_documents = 0
        total_size = 0
        
        for folder in folders:
            # Get document count and size for this folder
            folder_docs = company_db.query(HRManagedDocument).filter(
                HRManagedDocument.folder_id == folder.id,
                HRManagedDocument.is_active == True
            ).all()
            
            documents_count = len(folder_docs)
            folder_size = sum(doc.file_size for doc in folder_docs)
            total_documents += documents_count
            total_size += folder_size
            
            folder_response = schemas.UserFolderResponse(
                id=folder.id,
                name=folder.name,
                display_name=folder.display_name,
                description=folder.description,
                user_id=folder.user_id,
                created_by_user_id=folder.created_by_user_id,
                s3_folder_path=folder.s3_folder_path,
                folder_type=folder.folder_type,
                is_active=folder.is_active,
                sort_order=folder.sort_order,
                company_id=folder.company_id,
                created_at=folder.created_at,
                updated_at=folder.updated_at,
                documents_count=documents_count,
                total_size=folder_size
            )
            folders_response.append(folder_response)
        
        return schemas.UserFoldersSummaryResponse(
            user_id=target_user.id,
            user_name=target_user.full_name,
            user_email=target_user.email,
            folders=folders_response,
            total_folders=len(folders),
            total_documents=total_documents,
            total_size=total_size
        )
        
    finally:
        company_db.close()

@router.delete("/folders/{folder_id}")
async def delete_user_folder(
    folder_id: str,
    current_user: CompanyUser = Depends(verify_hr_access),
    management_db: Session = Depends(get_management_db)
):
    """Delete a user folder and all its contents"""
    
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Get the folder
        folder = company_db.query(UserFolder).filter(
            UserFolder.id == folder_id,
            UserFolder.company_id == company_id,
            UserFolder.is_active == True
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Delete folder from S3
        await aws_service.delete_hr_user_folder(
            company.s3_bucket_name,
            folder.user_id,
            folder.name
        )
        
        # Mark folder as inactive
        folder.is_active = False
        folder.updated_at = datetime.utcnow()
        
        # Mark all documents in this folder as inactive
        company_db.query(HRManagedDocument).filter(
            HRManagedDocument.folder_id == folder_id
        ).update({
            "is_active": False,
            "updated_at": datetime.utcnow()
        })
        
        company_db.commit()
        
        # Log the action
        audit_log = UserFolderAuditLog(
            folder_id=folder_id,
            user_id=current_user.id,
            action="folder_deleted",
            details={
                "folder_name": folder.name,
                "target_user_id": folder.user_id
            },
            company_id=company_id
        )
        company_db.add(audit_log)
        company_db.commit()
        
        return {"message": "Folder and all contents deleted successfully"}
        
    finally:
        company_db.close()

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: CompanyUser = Depends(verify_hr_access),
    management_db: Session = Depends(get_management_db)
):
    """Delete a specific document from a user folder"""
    
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Get the document
        document = company_db.query(HRManagedDocument).filter(
            HRManagedDocument.id == document_id,
            HRManagedDocument.company_id == company_id,
            HRManagedDocument.is_active == True
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file from S3
        await aws_service.delete_file_from_hr_folder(
            company.s3_bucket_name,
            document.s3_key
        )
        
        # Mark document as inactive
        document.is_active = False
        document.updated_at = datetime.utcnow()
        
        company_db.commit()
        
        # Log the action
        audit_log = UserFolderAuditLog(
            folder_id=document.folder_id,
            document_id=document_id,
            user_id=current_user.id,
            action="document_deleted",
            details={
                "filename": document.filename,
                "file_size": document.file_size
            },
            company_id=company_id
        )
        company_db.add(audit_log)
        company_db.commit()
        
        return {"message": "Document deleted successfully"}
        
    finally:
        company_db.close()
