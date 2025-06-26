from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app import models, schemas, auth
from app.services.aws_service import aws_service
from app.services.anthropic_service import anthropic_service
from app.config import MAX_FILE_SIZE, get_allowed_extensions, is_file_size_allowed

router = APIRouter()

@router.post("/upload", response_model=schemas.DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file size
    file_content = await file.read()
    if not is_file_size_allowed(len(file_content)):
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
        )
    
    # Check file type
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    allowed_extensions = get_allowed_extensions()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type .{file_extension} not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else uuid.uuid4().hex
    
    # Create S3 key
    s3_key = f"users/{current_user.id}/{unique_filename}"
    
    try:
        # Upload to S3
        s3_url = await aws_service.upload_file(
            bucket_name=current_user.company.s3_bucket_name,
            file_key=s3_key,
            file_data=file_content,
            user_id=current_user.id,
            company_id=current_user.company_id
        )
        
        # Create document record
        document = models.Document(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=s3_url,
            file_size=len(file_content),
            file_type=file.content_type or 'application/octet-stream',
            s3_key=s3_key,
            user_id=current_user.id,
            company_id=current_user.company_id,
            processed=False
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document with Anthropic API in background
        try:
            metadata = await anthropic_service.extract_document_metadata(file_content, file.filename)
            document.metadata_json = metadata
            document.processed = True
            db.commit()
        except Exception as e:
            print(f"Failed to process document {document.id}: {str(e)}")
        
        return document
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/", response_model=List[schemas.DocumentResponse])
async def list_documents(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "admin":
        # Admin can see all company documents
        documents = db.query(models.Document).filter(
            models.Document.company_id == current_user.company_id
        ).order_by(models.Document.created_at.desc()).all()
    else:
        # Regular users can only see their own documents
        documents = db.query(models.Document).filter(
            models.Document.user_id == current_user.id
        ).order_by(models.Document.created_at.desc()).all()
    
    return documents

@router.get("/{document_id}", response_model=schemas.DocumentResponse)
async def get_document(
    document_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access permissions
    if current_user.role != "admin" and document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if document.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return document

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check access permissions
    if current_user.role != "admin" and document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if document.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Delete from S3
        await aws_service.delete_file(
            bucket_name=current_user.company.s3_bucket_name,
            file_key=document.s3_key
        )
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")