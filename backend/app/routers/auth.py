from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_management_db, get_company_db
from app import models, schemas
from app import auth as auth_utils
from app.models_company import User as CompanyUser
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.utils.permissions import get_user_permissions
from typing import List

router = APIRouter()
security = HTTPBearer()



@router.post("/system/register", response_model=schemas.SystemUserResponse)
async def register_system_user(
    user: schemas.SystemUserCreate, 
    current_admin: models.SystemUser = Depends(auth_utils.get_current_system_user),
    db: Session = Depends(get_management_db)
):
    """Register system admin user (only system admins can create other system users)"""
    
    # Check if username already exists
    if db.query(models.SystemUser).filter(models.SystemUser.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    if db.query(models.SystemUser).filter(models.SystemUser.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create system user
    hashed_password = auth_utils.get_password_hash(user.password)
    db_user = models.SystemUser(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role.value
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create S3 bucket and folder for the new system admin
    bucket_name = f"system-admin-{db_user.id.lower()}"
    folder_name = f"system-admin-{db_user.id}"
    
    try:
        from app.services.aws_service import aws_service
        # The create_system_admin_bucket method now automatically cleans bucket names
        clean_bucket_name = await aws_service.create_system_admin_bucket(bucket_name, folder_name)
        
        # Update system user with the cleaned S3 bucket name
        db.query(models.SystemUser).filter(models.SystemUser.id == db_user.id).update({
            's3_bucket_name': clean_bucket_name,
            's3_folder': folder_name
        })
        db.commit()
        db.refresh(db_user)
        
    except Exception as e:
        print(f"Warning: Failed to create S3 storage for system admin {db_user.id}: {str(e)}")
        # Don't fail user creation if S3 setup fails
    
    return db_user

@router.post("/register", response_model=schemas.Token)
async def register_company_user(
    user: schemas.CompanyUserCreate,
    company_id: str,
    management_db: Session = Depends(get_management_db)
):
    """Register company user in their company database"""
    
    # Check if company exists
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id,
        models.Company.is_active == True
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Check if username already exists in company database
        if company_db.query(CompanyUser).filter(CompanyUser.username == user.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check if email already exists in company database
        if company_db.query(CompanyUser).filter(CompanyUser.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user in company database
        hashed_password = auth_utils.get_password_hash(user.password)
        db_user = CompanyUser(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            role=user.role.value,
            s3_folder=f"users/{user.username}/",
            company_id=company_id
        )
        
        company_db.add(db_user)
        company_db.commit()
        company_db.refresh(db_user)
        
        # Create user folder in S3
        from app.services.aws_service import aws_service
        try:
            await aws_service.create_user_folder(str(company.s3_bucket_name), str(db_user.id))
        except Exception as e:
            print(f"Warning: Failed to create S3 folder for user {db_user.id}: {str(e)}")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_utils.create_access_token(
            data={"sub": db_user.username}, expires_delta=access_token_expires
        )
        
        # Convert to response format
        user_response = schemas.CompanyUserResponse(
            id=str(db_user.id),
            username=str(db_user.username),
            email=str(db_user.email),
            full_name=str(db_user.full_name),
            role=str(db_user.role),
            s3_folder=str(db_user.s3_folder),
            password_set=bool(db_user.password_set),
            created_at=db_user.created_at,
            is_active=bool(db_user.is_active)
        )
        
        company_response = schemas.CompanyResponse(
            id=str(company.id),
            name=str(company.name),
            email=str(company.email),
            database_name=str(company.database_name),
            database_url=str(company.database_url),
            database_host=str(company.database_host),
            database_port=str(company.database_port),
            created_at=company.created_at,
            is_active=bool(company.is_active),
            s3_bucket_name=str(company.s3_bucket_name) if company.s3_bucket_name else None
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response,
            "company": company_response
        }
        
    finally:
        company_db.close()

@router.post("/login", response_model=schemas.Token)
async def login_user(
    user_credentials: schemas.UserLogin, 
    management_db: Session = Depends(get_management_db)
):
    """Login for both system users and company users"""
    
    # First check if this is a system user
    system_user = management_db.query(models.SystemUser).filter(
        models.SystemUser.username == user_credentials.username
    ).first()
    
    if system_user:
        if not auth_utils.verify_password(user_credentials.password, system_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not bool(system_user.is_active):
            raise HTTPException(status_code=400, detail="Inactive user")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_utils.create_access_token(
            data={"sub": system_user.username}, expires_delta=access_token_expires
        )
        
        # Convert to response format
        user_response = schemas.UserResponse(
            id=system_user.id,
            username=system_user.username,
            email=system_user.email,
            full_name=system_user.full_name,
            role=system_user.role,
            created_at=system_user.created_at,
            is_active=system_user.is_active
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response,
            "company": None,
            "permissions": get_user_permissions(str(system_user.role))
        }
    
    # If not a system user, check company databases
    companies = management_db.query(models.Company).filter(
        models.Company.is_active == True
    ).all()
    
    for company in companies:
        try:
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)
            
            user = company_db.query(CompanyUser).filter(
                CompanyUser.username == user_credentials.username
            ).first()
            
            if user:
                if not auth_utils.verify_password(user_credentials.password, user.hashed_password):
                    company_db.close()
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrect username or password",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                
                if not bool(user.is_active):
                    company_db.close()
                    raise HTTPException(status_code=400, detail="Inactive user")
                
                # Fix missing company_id for existing users
                if not user.company_id:
                    user.company_id = company.id
                    company_db.commit()
                    company_db.refresh(user)
                
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = auth_utils.create_access_token(
                    data={"sub": user.username}, expires_delta=access_token_expires
                )
                
                # Convert to response formats
                user_response = schemas.UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    role=user.role,
                    company_id=user.company_id or company.id,
                    created_at=user.created_at,
                    is_active=user.is_active
                )
                
                company_response = schemas.CompanyResponse(
                    id=company.id,
                    name=company.name,
                    email=company.email,
                    database_name=company.database_name,
                    database_url=company.database_url,
                    database_host=company.database_host,
                    database_port=company.database_port,
                    created_at=company.created_at,
                    is_active=company.is_active,
                    s3_bucket_name=company.s3_bucket_name
                )
                
                company_db.close()
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": user_response,
                    "company": company_response,
                    "permissions": get_user_permissions(str(user.role))
                }
            
            company_db.close()
            
        except Exception:
            continue
    
    # No user found in any database
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user = Depends(auth_utils.get_current_user)):
    """Get current user information"""
    if isinstance(current_user, models.SystemUser):
        return schemas.UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            created_at=current_user.created_at,
            is_active=current_user.is_active
        )
    else:
        # CompanyUser
        return schemas.UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            company_id=getattr(current_user, 'company_id', None),
            created_at=current_user.created_at,
            is_active=current_user.is_active
        )

@router.post("/system-admin/login", response_model=schemas.Token)
async def system_admin_login(
    user_credentials: schemas.UserLogin, 
    management_db: Session = Depends(get_management_db)
):
    """Dedicated login endpoint for system administrators"""
    
    print(f"🔐 System admin login attempt for username: {user_credentials.username}")
    
    # Check if this is a system user
    system_user = management_db.query(models.SystemUser).filter(
        models.SystemUser.username == user_credentials.username
    ).first()
    
    if not system_user:
        print(f"❌ System admin login failed: User '{user_credentials.username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid system administrator credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify this is actually a system admin
    if str(system_user.role) != "system_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. System administrator privileges required.",
        )
    
    if not auth_utils.verify_password(user_credentials.password, system_user.hashed_password):
        print(f"❌ System admin login failed: Invalid password for user '{user_credentials.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid system administrator credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not bool(system_user.is_active):
        raise HTTPException(status_code=400, detail="System administrator account is inactive")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": system_user.username}, expires_delta=access_token_expires
    )
    
    # Convert to response format
    user_response = schemas.UserResponse(
        id=system_user.id,
        username=system_user.username,
        email=system_user.email,
        full_name=system_user.full_name,
        role=system_user.role,
        created_at=system_user.created_at,
        is_active=system_user.is_active
    )
    
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response,
        "company": None,
        "permissions": get_user_permissions(str(system_user.role))
    }
    
    print(f"✅ System admin login successful for {user_credentials.username}")
    print(f"📤 Sending response: {response_data}")
    
    return response_data

@router.get("/system/admins", response_model=List[schemas.SystemUserResponse])
async def list_system_admins(
    current_admin: models.SystemUser = Depends(auth_utils.get_current_system_user),
    db: Session = Depends(get_management_db)
):
    """List all system administrators (only accessible by system admins)"""
    
    # Get all system users
    system_users = db.query(models.SystemUser).filter(
        models.SystemUser.role == "system_admin",
        models.SystemUser.is_active == True
    ).order_by(models.SystemUser.created_at.desc()).all()
    
    return system_users

@router.delete("/system/admins/{admin_id}")
async def delete_system_admin(
    admin_id: str,
    current_admin: models.SystemUser = Depends(auth_utils.get_current_system_user),
    db: Session = Depends(get_management_db)
):
    """Delete a system administrator and cleanup their S3 resources (only accessible by system admins)"""
    from app.services.aws_service import aws_service
    
    # Prevent self-deletion
    if current_admin.id == admin_id:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete your own admin account"
        )
    
    # Check if admin to delete exists
    admin_to_delete = db.query(models.SystemUser).filter(
        models.SystemUser.id == admin_id,
        models.SystemUser.role == "system_admin",
        models.SystemUser.is_active == True
    ).first()
    
    if not admin_to_delete:
        raise HTTPException(status_code=404, detail="System administrator not found")
    
    # Ensure at least one admin remains
    active_admin_count = db.query(models.SystemUser).filter(
        models.SystemUser.role == "system_admin",
        models.SystemUser.is_active == True
    ).count()
    
    if active_admin_count <= 1:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete the last system administrator. At least one admin must remain."
        )
    
    try:
        # Clean up S3 resources if they exist
        if admin_to_delete.s3_bucket_name:
            try:
                success = await aws_service.delete_company_bucket(admin_to_delete.s3_bucket_name)
                if success:
                    print(f"Successfully deleted S3 bucket: {admin_to_delete.s3_bucket_name}")
                else:
                    print(f"Warning: Failed to delete S3 bucket: {admin_to_delete.s3_bucket_name}")
            except Exception as s3_error:
                print(f"Warning: S3 cleanup failed for bucket {admin_to_delete.s3_bucket_name}: {str(s3_error)}")
                # Continue with deletion even if S3 cleanup fails
        
        # Delete any system documents associated with this admin
        system_documents = db.query(models.SystemDocument).filter(
            models.SystemDocument.user_id == admin_id
        ).all()
        
        for doc in system_documents:
            db.delete(doc)
        
        # Delete any system chat history
        chat_history = db.query(models.SystemChatHistory).filter(
            models.SystemChatHistory.user_id == admin_id
        ).all()
        
        for chat in chat_history:
            db.delete(chat)
        
        # Finally, delete the admin user
        db.delete(admin_to_delete)
        db.commit()
        
        return {
            "message": f"System administrator '{admin_to_delete.username}' has been successfully deleted",
            "deleted_admin": {
                "id": admin_to_delete.id,
                "username": admin_to_delete.username,
                "email": admin_to_delete.email,
                "full_name": admin_to_delete.full_name
            },
            "s3_cleanup": bool(admin_to_delete.s3_bucket_name),
            "documents_deleted": len(system_documents),
            "chat_history_deleted": len(chat_history)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete system administrator: {str(e)}"
        )