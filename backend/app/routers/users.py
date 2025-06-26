from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, auth
from app.utils.helpers import validate_email, validate_password

router = APIRouter()

@router.get("/", response_model=List[schemas.UserResponse])
async def list_users(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Only admins can list all users in their company
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list users"
        )
    
    users = db.query(models.User).filter(
        models.User.company_id == current_user.company_id,
        models.User.is_active == True
    ).all()
    
    return users

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Users can only view their own profile or admins can view any user in their company
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return user

@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: str,
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Users can only update their own profile or admins can update any user in their company
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    
    # Validate email if being updated
    if "email" in update_data:
        if not validate_email(update_data["email"]):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Check if email already exists
        existing_user = db.query(models.User).filter(
            models.User.email == update_data["email"],
            models.User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password if being updated
    if "password" in update_data:
        is_valid, message = validate_password(update_data["password"])
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        update_data["hashed_password"] = auth.get_password_hash(update_data["password"])
        del update_data["password"]
    
    # Only admins can update role
    if "role" in update_data and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can update user roles")
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Only admins can delete users
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Soft delete - set is_active to False
    user.is_active = False
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Only admins can activate users
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can activate users"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user.is_active = True
    db.commit()
    
    return {"message": "User activated successfully"}

@router.get("/stats/company")
async def get_company_user_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Only admins can view stats
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view user statistics"
        )
    
    total_users = db.query(models.User).filter(
        models.User.company_id == current_user.company_id
    ).count()
    
    active_users = db.query(models.User).filter(
        models.User.company_id == current_user.company_id,
        models.User.is_active == True
    ).count()
    
    admin_users = db.query(models.User).filter(
        models.User.company_id == current_user.company_id,
        models.User.role == "admin",
        models.User.is_active == True
    ).count()
    
    employee_users = db.query(models.User).filter(
        models.User.company_id == current_user.company_id,
        models.User.role == "employee",
        models.User.is_active == True
    ).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "employee_users": employee_users
    } 