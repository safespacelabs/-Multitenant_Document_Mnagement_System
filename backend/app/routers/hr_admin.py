from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.database import get_management_db, get_company_db
from app import models, schemas, auth
from app.models_company import (
    User as CompanyUser, 
    Document, 
    DocumentCategory, 
    DocumentFolder,
    UserLoginHistory,
    UserCredentials,
    UserActivity,
    DocumentAuditLog
)
from app.utils.permissions import get_manageable_roles
from app.services.aws_service import aws_service

router = APIRouter()

def verify_hr_admin_access(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Verify that the current user has HR admin access"""
    if current_user.role not in ["hr_admin", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. HR admin role required."
        )
    return current_user

@router.get("/company/users", response_model=List[schemas.CompanyUserDetailResponse])
async def get_all_company_users(
    current_user: CompanyUser = Depends(verify_hr_admin_access),
    management_db: Session = Depends(get_management_db),
    include_inactive: bool = Query(False, description="Include inactive users"),
    role_filter: Optional[str] = Query(None, description="Filter by specific role"),
    search: Optional[str] = Query(None, description="Search by name or email")
):
    """Get all company users with comprehensive data for HR admins"""
    
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
        query = company_db.query(CompanyUser)
        
        if not include_inactive:
            query = query.filter(CompanyUser.is_active == True)
        
        if role_filter:
            query = query.filter(CompanyUser.role == role_filter)
        
        if search:
            search_filter = or_(
                CompanyUser.full_name.ilike(f"%{search}%"),
                CompanyUser.email.ilike(f"%{search}%"),
                CompanyUser.username.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        users = query.all()
        
        # Get additional data for each user
        response_list = []
        for user in users:
            # Get document count and size
            user_docs = company_db.query(Document).filter(
                Document.user_id == user.id
            ).all()
            
            documents_count = len(user_docs)
            total_documents_size = sum(doc.file_size for doc in user_docs)
            
            # Get last login
            last_login = company_db.query(UserLoginHistory).filter(
                UserLoginHistory.user_id == user.id,
                UserLoginHistory.success == True
            ).order_by(desc(UserLoginHistory.login_timestamp)).first()
            
            # Get login count
            login_count = company_db.query(UserLoginHistory).filter(
                UserLoginHistory.user_id == user.id,
                UserLoginHistory.success == True
            ).count()
            
            response_list.append(schemas.CompanyUserDetailResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                s3_folder=user.s3_folder,
                password_set=user.password_set,
                created_at=user.created_at,
                is_active=user.is_active,
                company_id=user.company_id,
                unique_id=user.unique_id,
                created_by=user.created_by,
                last_login=last_login.login_timestamp if last_login else None,
                login_count=login_count,
                documents_count=documents_count,
                total_documents_size=total_documents_size
            ))
        
        return response_list
        
    finally:
        company_db.close()

@router.get("/company/users/{user_id}/credentials", response_model=schemas.CompanyUserCredentialsResponse)
async def get_user_credentials(
    user_id: str,
    current_user: CompanyUser = Depends(verify_hr_admin_access),
    management_db: Session = Depends(get_management_db)
):
    """Get user credentials and access information for HR admin management"""
    
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
        # Get user
        user = company_db.query(CompanyUser).filter(
            CompanyUser.id == user_id,
            CompanyUser.company_id == company_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get credentials
        credentials = company_db.query(UserCredentials).filter(
            UserCredentials.user_id == user_id
        ).first()
        
        if not credentials:
            # Create default credentials record
            credentials = UserCredentials(
                user_id=user_id,
                hashed_password=user.hashed_password or "",
                company_id=company_id
            )
            company_db.add(credentials)
            company_db.commit()
            company_db.refresh(credentials)
        
        return schemas.CompanyUserCredentialsResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            hashed_password=credentials.hashed_password,
            password_set=user.password_set,
            last_password_change=credentials.last_password_change,
            password_expires_at=credentials.password_expires_at,
            login_attempts=credentials.login_attempts,
            account_locked=credentials.account_locked,
            lock_reason=credentials.lock_reason,
            created_at=user.created_at,
            is_active=user.is_active
        )
        
    finally:
        company_db.close()

@router.get("/company/users/{user_id}/files", response_model=schemas.CompanyUserFilesResponse)
async def get_user_files(
    user_id: str,
    current_user: CompanyUser = Depends(verify_hr_admin_access),
    management_db: Session = Depends(get_management_db),
    category_filter: Optional[str] = Query(None, description="Filter by document category"),
    folder_filter: Optional[str] = Query(None, description="Filter by folder")
):
    """Get user's files and documents for HR admin access"""
    
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
        # Get user
        user = company_db.query(CompanyUser).filter(
            CompanyUser.id == user_id,
            CompanyUser.company_id == company_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build document query
        doc_query = company_db.query(Document).filter(Document.user_id == user_id)
        
        if category_filter:
            doc_query = doc_query.filter(Document.document_category == category_filter)
        
        if folder_filter:
            doc_query = doc_query.filter(Document.folder_name == folder_filter)
        
        documents = doc_query.all()
        
        # Get unique categories and folders
        categories = list(set(doc.document_category for doc in documents if doc.document_category))
        folders = list(set(doc.folder_name for doc in documents if doc.folder_name))
        
        # Get last activity
        last_activity = company_db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).order_by(desc(UserActivity.timestamp)).first()
        
        # Convert documents to response format
        doc_list = []
        for doc in documents:
            doc_list.append({
                "id": doc.id,
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "file_size": doc.file_size,
                "file_type": doc.file_type,
                "document_category": doc.document_category,
                "folder_name": doc.folder_name,
                "created_at": doc.created_at,
                "status": doc.status,
                "access_level": doc.access_level
            })
        
        return schemas.CompanyUserFilesResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            documents=doc_list,
            total_documents=len(documents),
            total_size=sum(doc.file_size for doc in documents),
            categories=categories,
            folders=folders,
            last_activity=last_activity.timestamp if last_activity else None
        )
        
    finally:
        company_db.close()

@router.get("/company/analytics", response_model=schemas.CompanyAnalyticsResponse)
async def get_company_analytics(
    current_user: CompanyUser = Depends(verify_hr_admin_access),
    management_db: Session = Depends(get_management_db),
    date_range: int = Query(30, description="Number of days for analytics")
):
    """Get company-wide analytics for HR admin dashboard"""
    
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
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        # Get user statistics
        total_users = company_db.query(CompanyUser).count()
        active_users = company_db.query(CompanyUser).filter(CompanyUser.is_active == True).count()
        inactive_users = total_users - active_users
        
        # Get users by role
        users_by_role = {}
        roles = company_db.query(CompanyUser.role, func.count(CompanyUser.id)).group_by(CompanyUser.role).all()
        for role, count in roles:
            users_by_role[role] = count
        
        # Get document statistics
        total_documents = company_db.query(Document).count()
        total_storage_used = company_db.query(func.sum(Document.file_size)).scalar() or 0
        
        # Get recent activity
        recent_activity = company_db.query(UserActivity).filter(
            UserActivity.timestamp >= start_date
        ).order_by(desc(UserActivity.timestamp)).limit(50).all()
        
        activity_list = []
        for activity in recent_activity:
            activity_list.append({
                "user_id": activity.user_id,
                "activity_type": activity.activity_type,
                "timestamp": activity.timestamp,
                "details": activity.activity_details
            })
        
        # Get user growth over time
        user_growth = []
        for i in range(date_range):
            date = start_date + timedelta(days=i)
            user_count = company_db.query(CompanyUser).filter(
                CompanyUser.created_at <= date
            ).count()
            user_growth.append({
                "date": date.date().isoformat(),
                "user_count": user_count
            })
        
        # Get document categories
        doc_categories = company_db.query(
            Document.document_category,
            func.count(Document.id),
            func.sum(Document.file_size)
        ).filter(
            Document.document_category.isnot(None)
        ).group_by(Document.document_category).all()
        
        categories_list = []
        for category, count, size in doc_categories:
            categories_list.append({
                "category": category,
                "document_count": count,
                "total_size": size or 0
            })
        
        # Get storage by category
        storage_by_category = []
        for category, count, size in doc_categories:
            storage_by_category.append({
                "category": category,
                "storage_bytes": size or 0,
                "storage_mb": round((size or 0) / (1024 * 1024), 2)
            })
        
        return schemas.CompanyAnalyticsResponse(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            users_by_role=users_by_role,
            total_documents=total_documents,
            total_storage_used=total_storage_used,
            recent_activity=activity_list,
            user_growth=user_growth,
            document_categories=categories_list,
            storage_by_category=storage_by_category
        )
        
    finally:
        company_db.close()

@router.post("/company/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    current_user: CompanyUser = Depends(verify_hr_admin_access),
    management_db: Session = Depends(get_management_db)
):
    """Reset user password and send new invitation"""
    
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
        # Get user
        user = company_db.query(CompanyUser).filter(
            CompanyUser.id == user_id,
            CompanyUser.company_id == company_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Reset password
        user.hashed_password = None
        user.password_set = False
        
        # Update credentials
        credentials = company_db.query(UserCredentials).filter(
            UserCredentials.user_id == user_id
        ).first()
        
        if credentials:
            credentials.hashed_password = None
            credentials.login_attempts = 0
            credentials.account_locked = False
            credentials.lock_reason = None
            credentials.lock_timestamp = None
        
        company_db.commit()
        
        return {"message": f"Password reset for user {user.email}. User will need to set a new password."}
        
    finally:
        company_db.close()

@router.post("/company/users/{user_id}/lock-account")
async def lock_user_account(
    user_id: str,
    lock_data: dict,
    current_user: CompanyUser = Depends(verify_hr_admin_access),
    management_db: Session = Depends(get_management_db)
):
    """Lock or unlock user account"""
    
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
        # Get user
        user = company_db.query(CompanyUser).filter(
            CompanyUser.id == user_id,
            CompanyUser.company_id == company_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user status
        user.is_active = not lock_data.get("lock", True)
        
        # Update credentials
        credentials = company_db.query(UserCredentials).filter(
            UserCredentials.user_id == user_id
        ).first()
        
        if credentials:
            credentials.account_locked = lock_data.get("lock", True)
            credentials.lock_reason = lock_data.get("reason", "Account locked by HR admin")
            credentials.lock_timestamp = datetime.utcnow() if lock_data.get("lock", True) else None
        
        company_db.commit()
        
        action = "locked" if lock_data.get("lock", True) else "unlocked"
        return {"message": f"Account {action} for user {user.email}"}
        
    finally:
        company_db.close()

@router.get("/company/users/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    current_user: CompanyUser = Depends(verify_hr_admin_access),
    management_db: Session = Depends(get_management_db),
    days: int = Query(30, description="Number of days of activity to retrieve")
):
    """Get detailed user activity for HR admin monitoring"""
    
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
        # Get user
        user = company_db.query(CompanyUser).filter(
            CompanyUser.id == user_id,
            CompanyUser.company_id == company_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get login history
        login_history = company_db.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user_id,
            UserLoginHistory.login_timestamp >= start_date
        ).order_by(desc(UserLoginHistory.login_timestamp)).all()
        
        # Get user activity
        user_activities = company_db.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.timestamp >= start_date
        ).order_by(desc(UserActivity.timestamp)).all()
        
        # Get document audit logs
        document_audits = company_db.query(DocumentAuditLog).filter(
            DocumentAuditLog.user_id == user_id,
            DocumentAuditLog.created_at >= start_date
        ).order_by(desc(DocumentAuditLog.created_at)).all()
        
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            },
            "login_history": [
                {
                    "timestamp": login.login_timestamp,
                    "ip_address": login.ip_address,
                    "user_agent": login.user_agent,
                    "success": login.success,
                    "failure_reason": login.failure_reason
                } for login in login_history
            ],
            "activities": [
                {
                    "activity_type": activity.activity_type,
                    "timestamp": activity.timestamp,
                    "details": activity.activity_details,
                    "ip_address": activity.ip_address
                } for activity in user_activities
            ],
            "document_actions": [
                {
                    "action": audit.action,
                    "document_id": audit.document_id,
                    "timestamp": audit.created_at,
                    "details": audit.details,
                    "ip_address": audit.ip_address
                } for audit in document_audits
            ]
        }
        
    finally:
        company_db.close()
