from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_management_db, get_company_db
from app import models, schemas
from app import auth as auth_utils
from app.models_company import User as CompanyUser
from app.utils.permissions import has_permission, Permission, get_manageable_roles
from app.utils.helpers import validate_email, validate_password

router = APIRouter()

@router.get("/", response_model=List[schemas.CompanyUserResponse])
async def list_users(
    current_user: CompanyUser = Depends(auth_utils.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Only users with management permissions can list users
    user_role = str(current_user.role)
    manageable_roles = get_manageable_roles(user_role)
    can_list = len(manageable_roles) > 0 or user_role in ["hr_admin", "hr_manager"]
    
    if not can_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view users"
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
        users = company_db.query(CompanyUser).filter(
            CompanyUser.is_active == True
        ).all()
        
        return users

    finally:
        company_db.close()

@router.get("/{user_id}", response_model=schemas.CompanyUserResponse)
async def get_user(
    user_id: str,
    current_user: CompanyUser = Depends(auth_utils.get_current_company_user),
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
        user = company_db.query(CompanyUser).filter(CompanyUser.id == user_id).first()
    
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Users can only view their own profile or managers can view users they can manage
        user_role = str(current_user.role)
        manageable_roles = get_manageable_roles(user_role)
        can_view_others = len(manageable_roles) > 0 or user_role in ["hr_admin", "hr_manager"]
        
        if not can_view_others and str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return user

    finally:
        company_db.close()

@router.put("/{user_id}", response_model=schemas.CompanyUserResponse)
async def update_user(
    user_id: str,
    user_update: schemas.UserUpdate,
    current_user: CompanyUser = Depends(auth_utils.get_current_company_user),
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
        user = company_db.query(CompanyUser).filter(CompanyUser.id == user_id).first()
    
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Users can only update their own profile or managers can update users they can manage
        user_role = str(current_user.role)
        manageable_roles = get_manageable_roles(user_role)
        can_update_others = len(manageable_roles) > 0 or user_role in ["hr_admin", "hr_manager"]
        
        if not can_update_others and str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update user fields
        update_data = user_update.dict(exclude_unset=True)
        
        # Validate email if being updated
        if "email" in update_data:
            if not validate_email(update_data["email"]):
                raise HTTPException(status_code=400, detail="Invalid email format")
            
            # Check if email already exists in company
            existing_user = company_db.query(CompanyUser).filter(
                CompanyUser.email == update_data["email"],
                CompanyUser.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password if being updated
        if "password" in update_data:
            is_valid, message = validate_password(update_data["password"])
            if not is_valid:
                raise HTTPException(status_code=400, detail=message)
            update_data["hashed_password"] = auth_utils.get_password_hash(update_data["password"])
            del update_data["password"]
        
        # Only users with appropriate management permissions can update role
        if "role" in update_data:
            user_role = str(current_user.role)
            manageable_roles = get_manageable_roles(user_role)
            can_update_roles = len(manageable_roles) > 0 or user_role in ["hr_admin", "hr_manager"]
            
            if not can_update_roles:
                raise HTTPException(status_code=403, detail="You don't have permission to update user roles")
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        company_db.commit()
        company_db.refresh(user)
        
        return user
        
    finally:
        company_db.close()

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: CompanyUser = Depends(auth_utils.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Only users with management permissions can delete users
    user_role = str(current_user.role)
    manageable_roles = get_manageable_roles(user_role)
    can_delete = len(manageable_roles) > 0 or user_role in ["hr_admin", "hr_manager"]
    
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete users"
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
        user = company_db.query(CompanyUser).filter(CompanyUser.id == user_id).first()
    
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Soft delete - set is_active to False
        user.is_active = False
        company_db.commit()
        
        return {"message": "User deleted successfully"}
        
    finally:
        company_db.close()

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: CompanyUser = Depends(auth_utils.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Only users with management permissions can activate users
    user_role = str(current_user.role)
    manageable_roles = get_manageable_roles(user_role)
    can_activate = len(manageable_roles) > 0 or user_role in ["hr_admin", "hr_manager"]
    
    if not can_activate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to activate users"
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
        user = company_db.query(CompanyUser).filter(CompanyUser.id == user_id).first()
    
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = True
        company_db.commit()
        
        return {"message": "User activated successfully"}
        
    finally:
        company_db.close()

@router.get("/stats/overview")
async def get_user_stats(
    current_user: CompanyUser = Depends(auth_utils.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Only users with management permissions can view stats
    user_role = str(current_user.role)
    manageable_roles = get_manageable_roles(user_role)
    can_view_stats = len(manageable_roles) > 0 or user_role in ["hr_admin", "hr_manager"]
    
    if not can_view_stats:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view user statistics"
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
        total_users = company_db.query(CompanyUser).count()
        active_users = company_db.query(CompanyUser).filter(CompanyUser.is_active == True).count()
        inactive_users = total_users - active_users
        
        # Count by roles
        hr_admins = company_db.query(CompanyUser).filter(CompanyUser.role == 'hr_admin').count()
        hr_managers = company_db.query(CompanyUser).filter(CompanyUser.role == 'hr_manager').count()
        employees = company_db.query(CompanyUser).filter(CompanyUser.role == 'employee').count()
        customers = company_db.query(CompanyUser).filter(CompanyUser.role == 'customer').count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "roles": {
                "hr_admin": hr_admins,
                "hr_manager": hr_managers,
                "employee": employees,
                "customer": customers
            }
        }
        
    finally:
        company_db.close() 