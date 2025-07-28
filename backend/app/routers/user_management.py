from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from datetime import datetime, timedelta
import secrets

from app.database import get_management_db, get_company_db
from app import models, schemas, auth
from app.models_company import User as CompanyUser, UserInvitation as CompanyUserInvitation
from app.utils.permissions import Permission, has_permission, can_manage_role, get_user_permissions
from app.services.aws_service import aws_service

# Add these imports at the top if not already present
from ..utils.permissions import ESignaturePermissions, PermissionAction, add_custom_esignature_role

router = APIRouter()

def get_current_user_with_company_context(
    company_id: Optional[str] = Header(None, alias="X-Company-ID"),
    current_user = Depends(auth.get_current_user),
    management_db: Session = Depends(get_management_db)
):
    """Allow both system admins and company users to access user management"""
    
    # Check if this is a system admin
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        # System admin must provide company ID
        if not company_id:
            raise HTTPException(
                status_code=400, 
                detail="System admin must specify company ID in X-Company-ID header"
            )
        return current_user
    
    # For regular company users, use the existing logic
    try:
        company_user = auth.get_current_company_user(
            token=auth.get_current_user(management_db=management_db),
            management_db=management_db
        )
        return company_user
    except:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Must be a system admin or company user."
        )

@router.post("/invite", response_model=schemas.UserInviteResponse)
async def invite_user(
    invite_data: schemas.UserInviteCreate,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """HR admins and managers can invite new users to their company"""
    
    # Check if current user can manage the target role
    current_role = str(current_user.role)
    target_role = str(invite_data.role.value)
    if not can_manage_role(current_role, target_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to create users with role: {target_role}"
        )
    
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
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
        # Check if email already exists in company
        existing_user = company_db.query(CompanyUser).filter(
            CompanyUser.email == invite_data.email
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if invitation already exists
        existing_invite = company_db.query(CompanyUserInvitation).filter(
            CompanyUserInvitation.email == invite_data.email,
            CompanyUserInvitation.is_used == False
        ).first()
        if existing_invite:
            raise HTTPException(status_code=400, detail="Invitation already sent to this email")
        
        # Create invitation in company database
        invitation = CompanyUserInvitation(
            email=invite_data.email,
            full_name=invite_data.full_name,
            role=invite_data.role.value,
            created_by=current_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),  # 7 days to set password
            unique_id=secrets.token_urlsafe(16)
        )
        
        company_db.add(invitation)
        company_db.commit()
        company_db.refresh(invitation)
        
        # Convert to response format
        response = schemas.UserInviteResponse(
            id=invitation.id,
            unique_id=invitation.unique_id,
            email=invitation.email,
            full_name=invitation.full_name,
            role=invitation.role,
            created_by=invitation.created_by,
            expires_at=invitation.expires_at,
            is_used=invitation.is_used,
            created_at=invitation.created_at
        )
        
        return response
        
    finally:
        company_db.close()

@router.post("/setup-password", response_model=schemas.PasswordSetupResponse)
async def setup_password(
    setup_data: schemas.PasswordSetupRequest,
    management_db: Session = Depends(get_management_db)
):
    """New users set their password using unique ID"""
    
    # Find the invitation in all company databases
    companies = management_db.query(models.Company).filter(
        models.Company.is_active == True
    ).all()
    
    invitation = None
    company_db = None
    target_company = None
    
    for company in companies:
        try:
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)
            
            invitation = company_db.query(CompanyUserInvitation).filter(
                CompanyUserInvitation.unique_id == setup_data.unique_id,
                CompanyUserInvitation.is_used == False
            ).first()
            
            if invitation:
                target_company = company
                break
            
            company_db.close()
            company_db = None
            
        except Exception:
            if company_db:
                company_db.close()
            continue
    
    if not invitation or not company_db or not target_company:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
    
    try:
        # Check if invitation is expired
        if invitation.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invitation has expired")
        
        # Check if username already exists in company
        existing_user = company_db.query(CompanyUser).filter(
            CompanyUser.username == setup_data.username
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create the user in company database
        hashed_password = auth.get_password_hash(setup_data.password)
        user = CompanyUser(
            username=setup_data.username,
            email=invitation.email,
            hashed_password=hashed_password,
            full_name=invitation.full_name,
            role=invitation.role,
            created_by=invitation.created_by,
            s3_folder=f"users/{setup_data.username}/",
            password_set=True,
            unique_id=invitation.unique_id
        )
        
        company_db.add(user)
        
        # Mark invitation as used
        invitation.is_used = True
        
        company_db.commit()
        company_db.refresh(user)
        
        # Create user folder in S3
        try:
            if target_company.s3_bucket_name:
                await aws_service.create_user_folder(str(target_company.s3_bucket_name), str(user.id))
        except Exception as e:
            print(f"Warning: Failed to create S3 folder for user {user.id}: {str(e)}")
        
        return schemas.PasswordSetupResponse(
            message="Password set successfully! You can now login.",
            user_id=user.id
        )
        
    finally:
        if company_db:
            company_db.close()

@router.get("/invitations", response_model=List[schemas.UserInviteResponse])
async def list_invitations(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """List pending invitations for current company"""
    
    user_role = str(current_user.role)
    can_list_invitations = (
        has_permission(user_role, Permission.MANAGE_ALL_COMPANY_USERS) or
        has_permission(user_role, Permission.MANAGE_EMPLOYEES_CUSTOMERS) or
        has_permission(user_role, Permission.MANAGE_CUSTOMERS_ONLY)
    )
    if not can_list_invitations:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
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
        invitations = company_db.query(CompanyUserInvitation).filter(
            CompanyUserInvitation.is_used == False
        ).all()
        
        # Convert to response format
        response_list = []
        for inv in invitations:
            response_list.append(schemas.UserInviteResponse.model_validate(inv))
        
        return response_list
        
    finally:
        company_db.close()

@router.get("/users", response_model=List[schemas.CompanyUserResponse])
async def list_company_users(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """List users in company based on permissions"""
    
    user_role = str(current_user.role)
    can_list_users = (
        has_permission(user_role, Permission.MANAGE_ALL_COMPANY_USERS) or
        has_permission(user_role, Permission.MANAGE_EMPLOYEES_CUSTOMERS) or
        has_permission(user_role, Permission.MANAGE_CUSTOMERS_ONLY)
    )
    if not can_list_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
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
        # Get manageable roles for current user
        from app.utils.permissions import get_manageable_roles
        manageable_roles = get_manageable_roles(current_user.role)
        
        # Get users with manageable roles
        users = company_db.query(CompanyUser).filter(
            CompanyUser.role.in_(manageable_roles),
            CompanyUser.is_active == True
        ).all()
        
        # Convert to response format
        response_list = []
        for user in users:
            response_list.append(schemas.CompanyUserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                s3_folder=user.s3_folder,
                password_set=user.password_set,
                created_at=user.created_at,
                is_active=user.is_active
            ))
        
        return response_list
        
    finally:
        company_db.close()

@router.delete("/invitations/{invitation_id}")
async def cancel_invitation(
    invitation_id: str,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Cancel a pending invitation"""
    
    user_role = str(current_user.role)
    can_cancel_invitations = (
        has_permission(user_role, Permission.MANAGE_ALL_COMPANY_USERS) or
        has_permission(user_role, Permission.MANAGE_EMPLOYEES_CUSTOMERS) or
        has_permission(user_role, Permission.MANAGE_CUSTOMERS_ONLY)
    )
    if not can_cancel_invitations:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
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
        invitation = company_db.query(CompanyUserInvitation).filter(
            CompanyUserInvitation.id == invitation_id
        ).first()
        
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        if invitation.is_used:
            raise HTTPException(status_code=400, detail="Cannot cancel used invitation")
        
        company_db.delete(invitation)
        company_db.commit()
        
        return {"message": "Invitation cancelled successfully"}
        
    finally:
        company_db.close()

@router.put("/users/{user_id}", response_model=schemas.CompanyUserResponse)
async def update_user(
    user_id: str,
    user_update: schemas.UserUpdate,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Update user role and status"""
    
    user_role = str(current_user.role)
    can_update_users = (
        has_permission(user_role, Permission.MANAGE_ALL_COMPANY_USERS) or
        has_permission(user_role, Permission.MANAGE_EMPLOYEES_CUSTOMERS) or
        has_permission(user_role, Permission.MANAGE_CUSTOMERS_ONLY)
    )
    if not can_update_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
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
        # Get the user to update
        target_user = company_db.query(CompanyUser).filter(
            CompanyUser.id == user_id
        ).first()
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Can't update self
        if target_user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot update your own account")
        
        # Check if current user can manage target user's current role
        if not can_manage_role(current_user.role, target_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have permission to manage users with role: {target_user.role}"
            )
        
        # If updating role, check if current user can assign the new role
        if user_update.role and user_update.role != target_user.role:
            if not can_manage_role(current_user.role, user_update.role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You don't have permission to assign role: {user_update.role}"
                )
            target_user.role = user_update.role
        
        # Update other fields if provided
        if user_update.is_active is not None:
            target_user.is_active = user_update.is_active
            
        if user_update.full_name:
            target_user.full_name = user_update.full_name
            
        if user_update.email:
            # Check if email already exists
            existing_user = company_db.query(CompanyUser).filter(
                CompanyUser.email == user_update.email,
                CompanyUser.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already in use")
            target_user.email = user_update.email
            
        if user_update.username:
            # Check if username already exists
            existing_user = company_db.query(CompanyUser).filter(
                CompanyUser.username == user_update.username,
                CompanyUser.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already in use")
            target_user.username = user_update.username
        
        company_db.commit()
        company_db.refresh(target_user)
        
        # Return updated user
        return schemas.CompanyUserResponse(
            id=target_user.id,
            username=target_user.username,
            email=target_user.email,
            full_name=target_user.full_name,
            role=target_user.role,
            s3_folder=target_user.s3_folder,
            password_set=target_user.password_set,
            created_at=target_user.created_at,
            is_active=target_user.is_active
        )
        
    finally:
        company_db.close()

@router.get("/permissions", response_model=List[str])
async def get_my_permissions(
    current_user = Depends(auth.get_current_user)
):
    """Get current user permissions"""
    # Handle both system users and company users
    if hasattr(current_user, 'role') and current_user.role == 'system_admin':
        return ["manage_all", "manage_companies", "manage_users", "manage_documents"]
    else:
        return get_user_permissions(str(current_user.role))

@router.get("/invitation/{unique_id}")
async def get_invitation_details(
    unique_id: str,
    management_db: Session = Depends(get_management_db)
):
    """Get invitation details for password setup"""
    
    # Find the invitation in all company databases
    companies = management_db.query(models.Company).filter(
        models.Company.is_active == True
    ).all()
    
    for company in companies:
        try:
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)
            
            invitation = company_db.query(CompanyUserInvitation).filter(
                CompanyUserInvitation.unique_id == unique_id,
                CompanyUserInvitation.is_used == False
            ).first()
            
            if invitation:
                # Check if expired
                if invitation.expires_at < datetime.utcnow():
                    company_db.close()
                    raise HTTPException(status_code=400, detail="Invitation has expired")
                
                result = {
                    "email": invitation.email,
                    "full_name": invitation.full_name,
                    "role": invitation.role,
                    "company_name": company.name,
                    "expires_at": invitation.expires_at.isoformat()
                }
                company_db.close()
                return result
            
            company_db.close()
            
        except Exception:
            continue
    
    raise HTTPException(status_code=404, detail="Invalid invitation")

# System Admin endpoints for cross-company user management

@router.get("/admin/companies/{company_id}/users", response_model=List[schemas.CompanyUserResponse])
async def admin_list_company_users(
    company_id: str,
    current_user = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """System admin endpoint to list users in any company"""
    
    # Get company information
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
        users = company_db.query(CompanyUser).all()
        
        # Convert to response format
        user_responses = []
        for user in users:
            user_response = schemas.CompanyUserResponse(
                id=str(user.id),
                username=str(user.username),
                email=str(user.email),
                full_name=str(user.full_name),
                role=str(user.role),
                s3_folder=str(user.s3_folder),
                password_set=bool(user.password_set),
                created_at=user.created_at,
                is_active=bool(user.is_active)
            )
            user_responses.append(user_response)
        
        return user_responses
        
    finally:
        company_db.close()

@router.get("/admin/companies/{company_id}/invitations", response_model=List[schemas.UserInviteResponse])
async def admin_list_invitations(
    company_id: str,
    current_user = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """System admin endpoint to list invitations for any company"""
    
    # Get company information
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
        invitations = company_db.query(CompanyUserInvitation).filter(
            CompanyUserInvitation.is_used == False
        ).all()
        
        # Convert to response format
        invitation_responses = []
        for invitation in invitations:
            response = schemas.UserInviteResponse(
                id=str(invitation.id),
                unique_id=str(invitation.unique_id),
                email=str(invitation.email),
                full_name=str(invitation.full_name),
                role=str(invitation.role),
                created_by=str(invitation.created_by),
                expires_at=invitation.expires_at,
                is_used=bool(invitation.is_used),
                created_at=invitation.created_at
            )
            invitation_responses.append(response)
        
        return invitation_responses
        
    finally:
        company_db.close()

@router.get("/admin/permissions", response_model=List[str])
async def admin_get_permissions(
    current_user = Depends(auth.get_current_system_user)
):
    """System admin permissions"""
    return ["manage_all", "manage_companies", "manage_users", "manage_documents"] 

# Add these new endpoints for role management

@router.post("/roles/create-custom-role")
async def create_custom_role(
    role_data: dict,
    current_user = Depends(get_current_user_with_company_context),
    management_db: Session = Depends(get_management_db)
):
    """
    Create a custom role with specific permissions (System Admin only)
    """
    try:
        # Check if user is system admin
        if not hasattr(current_user, 'role') or current_user.role != "system_admin":
            raise HTTPException(
                status_code=403,
                detail="Only system administrators can create custom roles"
            )
        
        # Validate role data
        if not role_data.get("role_name"):
            raise HTTPException(status_code=400, detail="Role name is required")
        
        if not role_data.get("permissions"):
            raise HTTPException(status_code=400, detail="Permissions are required")
        
        role_name = role_data["role_name"]
        permissions = role_data["permissions"]
        
        # Validate permissions format
        valid_permissions = {}
        for action, value in permissions.items():
            try:
                # Convert string to PermissionAction enum
                perm_action = PermissionAction(action)
                valid_permissions[perm_action] = bool(value)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid permission action: {action}"
                )
        
        # Add the custom role
        add_custom_esignature_role(role_name, valid_permissions)
        
        # logger.info(f"✅ Custom role '{role_name}' created by system admin: {current_user.email}") # Original code had this line commented out
        
        return {
            "message": f"Custom role '{role_name}' created successfully",
            "role_name": role_name,
            "permissions": valid_permissions,
            "created_by": current_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"❌ Error creating custom role: {str(e)}") # Original code had this line commented out
        raise HTTPException(status_code=500, detail=f"Failed to create custom role: {str(e)}")

@router.get("/roles/list-all-roles")
async def list_all_roles(
    current_user = Depends(get_current_user_with_company_context),
    management_db: Session = Depends(get_management_db)
):
    """
    List all available roles with their permissions
    """
    try:
        # Check permissions
        user_role = getattr(current_user, 'role', 'customer')
        
        # Only system admin and HR admin can view all roles
        if user_role not in ["system_admin", "hr_admin"]:
            raise HTTPException(
                status_code=403,
                detail="Only system administrators and HR administrators can view all roles"
            )
        
        # Get all roles
        all_roles = ESignaturePermissions.get_all_roles()
        role_summaries = {}
        
        for role in all_roles:
            role_summaries[role] = ESignaturePermissions.get_role_summary(role)
        
        return {
            "all_roles": role_summaries,
            "total_roles": len(all_roles),
            "base_roles": list(ESignaturePermissions.BASE_PERMISSIONS.keys()),
            "custom_roles": list(ESignaturePermissions.CUSTOM_PERMISSIONS.keys()),
            "requested_by": user_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"❌ Error listing all roles: {str(e)}") # Original code had this line commented out
        raise HTTPException(status_code=500, detail=f"Failed to list roles: {str(e)}")

@router.delete("/roles/delete-custom-role/{role_name}")
async def delete_custom_role(
    role_name: str,
    current_user = Depends(get_current_user_with_company_context),
    management_db: Session = Depends(get_management_db)
):
    """
    Delete a custom role (System Admin only)
    """
    try:
        # Check if user is system admin
        if not hasattr(current_user, 'role') or current_user.role != "system_admin":
            raise HTTPException(
                status_code=403,
                detail="Only system administrators can delete custom roles"
            )
        
        # Check if role exists and is custom
        if role_name not in ESignaturePermissions.CUSTOM_PERMISSIONS:
            raise HTTPException(
                status_code=404,
                detail=f"Custom role '{role_name}' not found"
            )
        
        # Don't allow deletion of base roles
        if role_name in ESignaturePermissions.BASE_PERMISSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete base role '{role_name}'"
            )
        
        # Check if any users are currently using this role
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        users_with_role = []
        for company in companies:
            try:
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                from app.models_company import User as CompanyUser
                users = company_db.query(CompanyUser).filter(
                    CompanyUser.role == role_name
                ).all()
                
                users_with_role.extend([f"{user.email} (Company: {company.name})" for user in users])
                company_db.close()
                
            except Exception:
                continue
        
        if users_with_role:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete role '{role_name}'. It is currently assigned to users: {', '.join(users_with_role)}"
            )
        
        # Delete the custom role
        ESignaturePermissions.remove_custom_role(role_name)
        
        # logger.info(f"🗑️ Custom role '{role_name}' deleted by system admin: {current_user.email}") # Original code had this line commented out
        
        return {
            "message": f"Custom role '{role_name}' deleted successfully",
            "deleted_by": current_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"❌ Error deleting custom role: {str(e)}") # Original code had this line commented out
        raise HTTPException(status_code=500, detail=f"Failed to delete custom role: {str(e)}")

@router.get("/roles/permission-actions")
async def get_permission_actions(
    current_user = Depends(get_current_user_with_company_context)
):
    """
    Get all available permission actions for creating custom roles
    """
    try:
        # Check permissions
        user_role = getattr(current_user, 'role', 'customer')
        
        if user_role not in ["system_admin", "hr_admin"]:
            raise HTTPException(
                status_code=403,
                detail="Only system administrators and HR administrators can view permission actions"
            )
        
        # Get all permission actions
        permission_actions = {
            action.value: {
                "name": action.value,
                "description": _get_permission_description(action)
            }
            for action in PermissionAction
        }
        
        return {
            "permission_actions": permission_actions,
            "total_actions": len(permission_actions),
            "requested_by": user_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"❌ Error getting permission actions: {str(e)}") # Original code had this line commented out
        raise HTTPException(status_code=500, detail=f"Failed to get permission actions: {str(e)}")

def _get_permission_description(action: PermissionAction) -> str:
    """Get human-readable description for permission actions"""
    descriptions = {
        PermissionAction.CREATE: "Create new signature requests",
        PermissionAction.SEND: "Send signature requests to recipients",
        PermissionAction.VIEW: "View signature requests",
        PermissionAction.CANCEL: "Cancel signature requests",
        PermissionAction.SIGN: "Sign documents",
        PermissionAction.DOWNLOAD: "Download signed documents",
        PermissionAction.MANAGE: "Manage all signature requests",
        PermissionAction.APPROVE: "Approve signature requests",
        PermissionAction.WORKFLOW_CREATE: "Create workflow templates",
        PermissionAction.WORKFLOW_MANAGE: "Manage workflow templates",
        PermissionAction.BULK_SEND: "Send bulk signature requests",
        PermissionAction.AUDIT_VIEW: "View audit logs",
    }
    return descriptions.get(action, "Unknown permission")

@router.post("/roles/clone-role")
async def clone_role(
    clone_data: dict,
    current_user = Depends(get_current_user_with_company_context),
    management_db: Session = Depends(get_management_db)
):
    """
    Clone an existing role with modifications (System Admin only)
    """
    try:
        # Check if user is system admin
        if not hasattr(current_user, 'role') or current_user.role != "system_admin":
            raise HTTPException(
                status_code=403,
                detail="Only system administrators can clone roles"
            )
        
        # Validate clone data
        if not clone_data.get("source_role"):
            raise HTTPException(status_code=400, detail="Source role is required")
        
        if not clone_data.get("new_role_name"):
            raise HTTPException(status_code=400, detail="New role name is required")
        
        source_role = clone_data["source_role"]
        new_role_name = clone_data["new_role_name"]
        permission_modifications = clone_data.get("permission_modifications", {})
        
        # Get permissions from source role
        source_permissions = ESignaturePermissions.get_role_permissions(source_role)
        
        # Apply modifications
        new_permissions = source_permissions.copy()
        for action, value in permission_modifications.items():
            try:
                perm_action = PermissionAction(action)
                new_permissions[perm_action] = bool(value)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid permission action: {action}"
                )
        
        # Add the cloned role
        add_custom_esignature_role(new_role_name, new_permissions)
        
        # logger.info(f"✅ Role '{new_role_name}' cloned from '{source_role}' by system admin: {current_user.email}") # Original code had this line commented out
        
        return {
            "message": f"Role '{new_role_name}' cloned successfully from '{source_role}'",
            "source_role": source_role,
            "new_role_name": new_role_name,
            "permissions": new_permissions,
            "modifications": permission_modifications,
            "created_by": current_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # logger.error(f"❌ Error cloning role: {str(e)}") # Original code had this line commented out
        raise HTTPException(status_code=500, detail=f"Failed to clone role: {str(e)}") 