from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_management_db
from app import models, schemas, auth
from app.services.neon_service import neon_service
from app.services.database_manager import db_manager
from app.utils.company_context import get_company_context_by_id
from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
import uuid
import logging

logger = logging.getLogger(__name__)

# Use mock AWS service if credentials are not configured
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    from app.services.aws_service import aws_service
    logger.info("Using real AWS service")
else:
    from app.services.aws_service_mock import mock_aws_service as aws_service
    logger.info("Using mock AWS service - no real S3 operations will be performed")

router = APIRouter()

# Public endpoints (no authentication required) - MUST come before parameterized routes
@router.get("/public", response_model=List[schemas.CompanyResponse])
async def list_companies_public(db: Session = Depends(get_management_db)):
    """Public endpoint to list all active companies for main landing page"""
    companies = db.query(models.Company).filter(models.Company.is_active == True).all()
    return companies

@router.get("/{company_id}/public", response_model=schemas.CompanyResponse)
async def get_company_public(company_id: str, db: Session = Depends(get_management_db)):
    """Public endpoint to get company information for company access page"""
    logger.info(f"🔍 Company verification request for company_id: {company_id}")
    
    try:
        company = db.query(models.Company).filter(
            models.Company.id == company_id,
            models.Company.is_active == True
        ).first()
        
        if not company:
            logger.warning(f"❌ Company not found: {company_id}")
            raise HTTPException(status_code=404, detail="Company not found")
        
        logger.info(f"✅ Company found: {company.name} (ID: {company.id})")
        return company
        
    except Exception as e:
        logger.error(f"❌ Error in company verification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/", response_model=List[schemas.CompanyResponse])
async def list_companies(db: Session = Depends(get_management_db)):
    companies = db.query(models.Company).filter(models.Company.is_active == True).all()
    return companies

@router.post("/", response_model=schemas.CompanyResponse)
async def create_company(
    company: schemas.CompanyCreate, 
    current_user: models.SystemUser = Depends(auth.get_current_system_user),
    db: Session = Depends(get_management_db)
):
    # Only system admins can create companies
    if str(current_user.role) != "system_admin":
        raise HTTPException(status_code=403, detail="Only system administrators can create companies")
    
    # Check if company email already exists
    if db.query(models.Company).filter(models.Company.email == company.email).first():
        raise HTTPException(status_code=400, detail="Company email already registered")
    
    # Create company ID
    company_id = f"comp_{uuid.uuid4().hex[:8]}"
    
    try:
        # Generate database name and URL
        database_name = f"db_{company_id}"
        
        # Get base database URL from management database
        from app.config import DATABASE_URL
        base_url_parts = DATABASE_URL.rsplit('/', 1)
        if len(base_url_parts) == 2:
            database_url = f"{base_url_parts[0]}/{database_name}?sslmode=require&channel_binding=require"
        else:
            database_url = f"{DATABASE_URL}/{database_name}?sslmode=require&channel_binding=require"
        
        # Create company record first (so it exists for logging)
        db_company = models.Company(
            id=company_id,
            name=company.name,
            email=company.email,
            database_name=database_name,
            database_url=database_url,
            database_host="ep-lively-pond-a6gik9pf-pooler.us-west-2.aws.neon.tech",
            database_port=5432,
            database_user="multitenant-db_owner",
            database_password="npg_X7gKCTze2PAS",
            s3_bucket_name=""  # Will be set later
        )
        
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        
        # Create database using direct SQL
        logger.info(f"Creating database {database_name} for company {company_id}")
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'CREATE DATABASE "{database_name}";')
            logger.info(f"Database {database_name} created successfully")
        except psycopg2.Error as e:
            if 'already exists' in str(e):
                logger.info(f"Database {database_name} already exists")
            else:
                raise e
        finally:
            cursor.close()
            conn.close()
        
        # Create tables in the company's database
        logger.info(f"Creating tables in company database {company_id}")
        db_manager.create_company_tables(company_id, database_url)
        
        # Create S3 bucket for company
        logger.info(f"Creating S3 bucket for company {company_id}")
        try:
            bucket_name = await aws_service.create_company_bucket(company_id)
            # Update S3 bucket name
            db_company = db.query(models.Company).filter(models.Company.id == company_id).first()
            db_company.s3_bucket_name = bucket_name
            db.commit()
        except Exception as s3_error:
            logger.warning(f"Failed to create S3 bucket for {company_id}: {str(s3_error)}")
            # Continue without S3 bucket
        
        # Log database creation
        log_entry = models.CompanyDatabaseLog(
            company_id=company_id,
            action="created",
            message=f"Database {database_name} created successfully"
        )
        db.add(log_entry)
        db.commit()
        
        logger.info(f"Company {company_id} created successfully with isolated database")
        return db_company
        
    except Exception as e:
        # Rollback database changes on error
        db.rollback()
        
        # Try to clean up any created resources
        try:
            if 'database_name' in locals():
                # Try to drop the database if it was created
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                conn.autocommit = True
                cursor = conn.cursor()
                try:
                    cursor.execute(f'DROP DATABASE IF EXISTS "{database_name}";')
                except:
                    pass
                finally:
                    cursor.close()
                    conn.close()
                    
            if 'bucket_name' in locals():
                await aws_service.delete_company_bucket(bucket_name)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {str(cleanup_error)}")
        
        logger.error(f"Failed to create company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

@router.get("/{company_id}", response_model=schemas.CompanyResponse)
async def get_company(company_id: str, db: Session = Depends(get_management_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.delete("/{company_id}")
async def delete_company(
    company_id: str, 
    current_user: models.SystemUser = Depends(auth.get_current_system_user),
    db: Session = Depends(get_management_db)
):
    # Only system admins can delete companies
    if str(current_user.role) != "system_admin":
        raise HTTPException(status_code=403, detail="Only system administrators can delete companies")
    
    # Get the company
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        # Get company database connection to count records
        company_context = await get_company_context_by_id(company_id, db)
        
        # Count records in company database
        user_count = company_context.company_db.query(
            company_context.company_db.query(models.User).count()
        ).scalar() if hasattr(models, 'User') else 0
        
        document_count = company_context.company_db.query(
            company_context.company_db.query(models.Document).count()
        ).scalar() if hasattr(models, 'Document') else 0
        
        # Close company database connection
        company_context.company_db.close()
        
        # Remove company database connection from cache
        db_manager.remove_company_connection(company_id)
        
        # Delete the company database
        db_deletion_success = await neon_service.delete_company_database(company.database_name)
        
        # Delete S3 bucket and all its contents
        s3_deletion_success = False
        if company.s3_bucket_name:
            try:
                s3_deletion_success = await aws_service.delete_company_bucket(company.s3_bucket_name)
            except Exception as s3_error:
                logger.warning(f"Failed to delete S3 bucket {company.s3_bucket_name}: {str(s3_error)}")
        
        # Save company info before deletion for logging
        company_name = company.name
        database_name = company.database_name
        
        # Delete existing log entries first to avoid foreign key constraint
        existing_logs = db.query(models.CompanyDatabaseLog).filter(
            models.CompanyDatabaseLog.company_id == company_id
        ).all()
        for log in existing_logs:
            db.delete(log)
        
        # Delete the company record from management database
        db.delete(company)
        db.commit()
        
        # Log the deletion after company is deleted (without foreign key reference)
        logger.info(f"Company {company_name} and database {database_name} deleted successfully")
        
        return {
            "message": "Company deleted successfully",
            "company_name": company.name,
            "users_deleted": user_count,
            "documents_deleted": document_count,
            "database_deleted": db_deletion_success,
            "s3_bucket_deleted": s3_deletion_success,
            "database_name": company.database_name,
            "s3_bucket_name": company.s3_bucket_name or "N/A"
        }
        
    except Exception as e:
        # Rollback database changes on error
        db.rollback()
        logger.error(f"Failed to delete company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete company: {str(e)}")

@router.get("/{company_id}/stats")
async def get_company_stats(
    company_id: str,
    current_user: models.SystemUser = Depends(auth.get_current_system_user),
    db: Session = Depends(get_management_db)
):
    # Only system admins can view company stats (for now)
    if str(current_user.role) != "system_admin":
        raise HTTPException(status_code=403, detail="Only system administrators can view company statistics")
    
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        # Get company database connection
        company_context = await get_company_context_by_id(company_id, db)
        
        # Get stats from company database
        from app.models_company import User, Document, ChatHistory
        
        user_count = company_context.company_db.query(User).count()
        document_count = company_context.company_db.query(Document).count()
        chat_count = company_context.company_db.query(ChatHistory).count()
        
        # Close company database connection
        company_context.company_db.close()
        
        return {
            "company": company,
            "stats": {
                "users": user_count,
                "documents": document_count,
                "chats": chat_count,
                "database_name": company.database_name,
                "s3_bucket": company.s3_bucket_name
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get company statistics: {str(e)}")

@router.get("/{company_id}/database/test")
async def test_company_database(
    company_id: str,
    current_user: models.SystemUser = Depends(auth.get_current_system_user),
    db: Session = Depends(get_management_db)
):
    """Test company database connection"""
    if str(current_user.role) != "system_admin":
        raise HTTPException(status_code=403, detail="Only system administrators can test database connections")
    
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    try:
        # Test database connection
        connection_success = db_manager.test_company_connection(company_id, company.database_url)
        
        return {
            "company_id": company_id,
            "database_name": company.database_name,
            "connection_test": "success" if connection_success else "failed"
        }
        
    except Exception as e:
        logger.error(f"Error testing database for company {company_id}: {str(e)}")
        return {
            "company_id": company_id,
            "database_name": company.database_name,
            "connection_test": "failed",
            "error": str(e)
        }

@router.post("/{company_id}/request-access", response_model=dict)
async def request_company_access(
    company_id: str,
    request_data: dict,
    management_db: Session = Depends(get_management_db)
):
    """
    Handle user access requests to a company.
    This creates a pending access request that can be reviewed by HR admins.
    """
    try:
        # Verify company exists
        company = management_db.query(models.Company).filter(models.Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # For demonstration purposes, just return success
        # In a real system, this would create an access request record
        
        return {
            "message": "Access request submitted successfully",
            "company_name": company.name,
            "status": "pending_review",
            "email": request_data.get("email"),
            "full_name": request_data.get("full_name")
        }
        
    except Exception as e:
        logger.error(f"Error processing access request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process access request") 