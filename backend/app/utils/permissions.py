"""
Dynamic Role-based Permission System for E-signature and other features
This system handles existing roles and future roles dynamically
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PermissionAction(str, Enum):
    """E-signature permission actions"""
    CREATE = "create"
    SEND = "send"
    VIEW = "view"
    CANCEL = "cancel"
    SIGN = "sign"
    DOWNLOAD = "download"
    MANAGE = "manage"
    APPROVE = "approve"
    WORKFLOW_CREATE = "workflow_create"
    WORKFLOW_MANAGE = "workflow_manage"
    BULK_SEND = "bulk_send"
    AUDIT_VIEW = "audit_view"

class ESignaturePermissions:
    """Dynamic E-signature permissions for all roles"""
    
    # Base role permissions - these are the defaults
    BASE_PERMISSIONS = {
        # System Admin - Full access to everything
        "system_admin": {
            PermissionAction.CREATE: True,
            PermissionAction.SEND: True,
            PermissionAction.VIEW: True,
            PermissionAction.CANCEL: True,
            PermissionAction.SIGN: True,
            PermissionAction.DOWNLOAD: True,
            PermissionAction.MANAGE: True,
            PermissionAction.APPROVE: True,
            PermissionAction.WORKFLOW_CREATE: True,
            PermissionAction.WORKFLOW_MANAGE: True,
            PermissionAction.BULK_SEND: True,
            PermissionAction.AUDIT_VIEW: True,
        },
        
        # HR Admin - High level access
        "hr_admin": {
            PermissionAction.CREATE: True,
            PermissionAction.SEND: True,
            PermissionAction.VIEW: True,
            PermissionAction.CANCEL: True,
            PermissionAction.SIGN: True,
            PermissionAction.DOWNLOAD: True,
            PermissionAction.MANAGE: True,
            PermissionAction.APPROVE: True,
            PermissionAction.WORKFLOW_CREATE: True,
            PermissionAction.WORKFLOW_MANAGE: True,
            PermissionAction.BULK_SEND: True,
            PermissionAction.AUDIT_VIEW: True,
        },
        
        # HR Manager - Mid level access
        "hr_manager": {
            PermissionAction.CREATE: True,
            PermissionAction.SEND: True,
            PermissionAction.VIEW: True,
            PermissionAction.CANCEL: True,  # Can cancel own requests
            PermissionAction.SIGN: True,
            PermissionAction.DOWNLOAD: True,
            PermissionAction.MANAGE: False,  # Cannot manage all requests
            PermissionAction.APPROVE: True,
            PermissionAction.WORKFLOW_CREATE: True,
            PermissionAction.WORKFLOW_MANAGE: False,
            PermissionAction.BULK_SEND: True,
            PermissionAction.AUDIT_VIEW: False,
        },
        
        # Employee - Basic access
        "employee": {
            PermissionAction.CREATE: True,
            PermissionAction.SEND: True,
            PermissionAction.VIEW: True,  # Can view own requests
            PermissionAction.CANCEL: True,  # Can cancel own requests
            PermissionAction.SIGN: True,
            PermissionAction.DOWNLOAD: True,
            PermissionAction.MANAGE: False,
            PermissionAction.APPROVE: False,
            PermissionAction.WORKFLOW_CREATE: False,
            PermissionAction.WORKFLOW_MANAGE: False,
            PermissionAction.BULK_SEND: False,
            PermissionAction.AUDIT_VIEW: False,
        },
        
        # Customer - Limited access
        "customer": {
            PermissionAction.CREATE: False,
            PermissionAction.SEND: False,
            PermissionAction.VIEW: True,  # Can view own requests only
            PermissionAction.CANCEL: False,
            PermissionAction.SIGN: True,
            PermissionAction.DOWNLOAD: True,
            PermissionAction.MANAGE: False,
            PermissionAction.APPROVE: False,
            PermissionAction.WORKFLOW_CREATE: False,
            PermissionAction.WORKFLOW_MANAGE: False,
            PermissionAction.BULK_SEND: False,
            PermissionAction.AUDIT_VIEW: False,
        },
    }
    
    # Dynamic role hierarchy - higher roles inherit permissions from lower roles
    ROLE_HIERARCHY = {
        "system_admin": ["hr_admin", "hr_manager", "employee", "customer"],
        "hr_admin": ["hr_manager", "employee", "customer"],
        "hr_manager": ["employee", "customer"],
        "employee": ["customer"],
        "customer": []
    }
    
    # Custom permissions for specific roles (can be extended dynamically)
    CUSTOM_PERMISSIONS = {}
    
    @classmethod
    def get_role_permissions(cls, role: str) -> Dict[PermissionAction, bool]:
        """Get permissions for a specific role (handles existing and future roles)"""
        try:
            # Check if role has custom permissions
            if role in cls.CUSTOM_PERMISSIONS:
                return cls.CUSTOM_PERMISSIONS[role]
            
            # Check if role exists in base permissions
            if role in cls.BASE_PERMISSIONS:
                return cls.BASE_PERMISSIONS[role]
            
            # For unknown roles, apply default permissions based on role name patterns
            return cls._get_default_permissions_for_unknown_role(role)
            
        except Exception as e:
            logger.error(f"Error getting permissions for role {role}: {str(e)}")
            # Return minimal permissions for safety
            return cls._get_minimal_permissions()
    
    @classmethod
    def _get_default_permissions_for_unknown_role(cls, role: str) -> Dict[PermissionAction, bool]:
        """Get default permissions for unknown roles based on naming patterns"""
        role_lower = role.lower()
        
        # Admin-like roles
        if "admin" in role_lower or "administrator" in role_lower:
            if "system" in role_lower or "super" in role_lower:
                return cls.BASE_PERMISSIONS["system_admin"]
            elif "hr" in role_lower:
                return cls.BASE_PERMISSIONS["hr_admin"]
            else:
                return cls.BASE_PERMISSIONS["hr_manager"]
        
        # Manager-like roles
        elif "manager" in role_lower or "supervisor" in role_lower or "lead" in role_lower:
            return cls.BASE_PERMISSIONS["hr_manager"]
        
        # Employee-like roles
        elif "employee" in role_lower or "staff" in role_lower or "user" in role_lower:
            return cls.BASE_PERMISSIONS["employee"]
        
        # Customer-like roles
        elif "customer" in role_lower or "client" in role_lower or "guest" in role_lower:
            return cls.BASE_PERMISSIONS["customer"]
        
        # Default to employee permissions for unknown roles
        else:
            logger.warning(f"Unknown role pattern '{role}', defaulting to employee permissions")
            return cls.BASE_PERMISSIONS["employee"]
    
    @classmethod
    def _get_minimal_permissions(cls) -> Dict[PermissionAction, bool]:
        """Get minimal permissions for safety"""
        return {
            PermissionAction.CREATE: False,
            PermissionAction.SEND: False,
            PermissionAction.VIEW: True,
            PermissionAction.CANCEL: False,
            PermissionAction.SIGN: True,
            PermissionAction.DOWNLOAD: True,
            PermissionAction.MANAGE: False,
            PermissionAction.APPROVE: False,
            PermissionAction.WORKFLOW_CREATE: False,
            PermissionAction.WORKFLOW_MANAGE: False,
            PermissionAction.BULK_SEND: False,
            PermissionAction.AUDIT_VIEW: False,
        }
    
    @classmethod
    def has_permission(cls, role: str, action: PermissionAction) -> bool:
        """Check if a role has permission for a specific action"""
        try:
            permissions = cls.get_role_permissions(role)
            return permissions.get(action, False)
        except Exception as e:
            logger.error(f"Error checking permission for role {role}, action {action}: {str(e)}")
            return False
    
    @classmethod
    def can_create_request(cls, role: str) -> bool:
        """Check if role can create signature requests"""
        return cls.has_permission(role, PermissionAction.CREATE)
    
    @classmethod
    def can_send_request(cls, role: str) -> bool:
        """Check if role can send signature requests"""
        return cls.has_permission(role, PermissionAction.SEND)
    
    @classmethod
    def can_view_request(cls, role: str, request_creator_id: str = None, user_id: str = None, user_email: str = None) -> bool:
        """Check if role can view signature requests (with ownership logic)"""
        base_permission = cls.has_permission(role, PermissionAction.VIEW)
        
        # System admin and HR admin can view all requests
        if role in ["system_admin", "hr_admin"]:
            return True
        
        # HR managers can view all requests in their company
        if role == "hr_manager":
            return True
        
        # Employees and customers can only view their own requests or requests they're recipients of
        if role in ["employee", "customer"]:
            return base_permission  # Frontend will handle ownership filtering
        
        return base_permission
    
    @classmethod
    def can_cancel_request(cls, role: str, request_creator_id: str = None, user_id: str = None) -> bool:
        """Check if role can cancel signature requests"""
        base_permission = cls.has_permission(role, PermissionAction.CANCEL)
        
        # System admin and HR admin can cancel any request
        if role in ["system_admin", "hr_admin"]:
            return True
        
        # HR managers can cancel any request in their company
        if role == "hr_manager":
            return True
        
        # Employees can only cancel their own requests
        if role == "employee" and request_creator_id and user_id:
            return base_permission and (request_creator_id == user_id)
        
        return base_permission
    
    @classmethod
    def can_manage_workflows(cls, role: str) -> bool:
        """Check if role can manage workflows"""
        return cls.has_permission(role, PermissionAction.WORKFLOW_MANAGE)
    
    @classmethod
    def can_send_bulk_requests(cls, role: str) -> bool:
        """Check if role can send bulk signature requests"""
        return cls.has_permission(role, PermissionAction.BULK_SEND)
    
    @classmethod
    def can_view_audit_logs(cls, role: str) -> bool:
        """Check if role can view audit logs"""
        return cls.has_permission(role, PermissionAction.AUDIT_VIEW)
    
    @classmethod
    def add_custom_role(cls, role: str, permissions: Dict[PermissionAction, bool]):
        """Add custom permissions for a new role"""
        cls.CUSTOM_PERMISSIONS[role] = permissions
        logger.info(f"✅ Added custom permissions for role: {role}")
    
    @classmethod
    def remove_custom_role(cls, role: str):
        """Remove custom permissions for a role"""
        if role in cls.CUSTOM_PERMISSIONS:
            del cls.CUSTOM_PERMISSIONS[role]
            logger.info(f"🗑️ Removed custom permissions for role: {role}")
    
    @classmethod
    def get_all_roles(cls) -> List[str]:
        """Get all available roles"""
        base_roles = list(cls.BASE_PERMISSIONS.keys())
        custom_roles = list(cls.CUSTOM_PERMISSIONS.keys())
        return base_roles + custom_roles
    
    @classmethod
    def get_role_summary(cls, role: str) -> Dict[str, Any]:
        """Get a summary of permissions for a role"""
        permissions = cls.get_role_permissions(role)
        return {
            "role": role,
            "permissions": permissions,
            "can_create": cls.can_create_request(role),
            "can_send": cls.can_send_request(role),
            "can_manage": cls.has_permission(role, PermissionAction.MANAGE),
            "can_bulk_send": cls.can_send_bulk_requests(role),
            "can_view_audit": cls.can_view_audit_logs(role),
            "is_custom_role": role in cls.CUSTOM_PERMISSIONS
        }

# Convenience functions for easy access
def has_esignature_permission(role: str, action: PermissionAction) -> bool:
    """Check if a role has E-signature permission for a specific action"""
    return ESignaturePermissions.has_permission(role, action)

def get_esignature_permissions(role: str) -> Dict[PermissionAction, bool]:
    """Get all E-signature permissions for a role"""
    return ESignaturePermissions.get_role_permissions(role)

def can_create_esignature_request(role: str) -> bool:
    """Check if role can create E-signature requests"""
    return ESignaturePermissions.can_create_request(role)

def can_send_esignature_request(role: str) -> bool:
    """Check if role can send E-signature requests"""
    return ESignaturePermissions.can_send_request(role)

def can_view_esignature_request(role: str, request_creator_id: str = None, user_id: str = None, user_email: str = None) -> bool:
    """Check if role can view E-signature requests"""
    return ESignaturePermissions.can_view_request(role, request_creator_id, user_id, user_email)

def can_cancel_esignature_request(role: str, request_creator_id: str = None, user_id: str = None) -> bool:
    """Check if role can cancel E-signature requests"""
    return ESignaturePermissions.can_cancel_request(role, request_creator_id, user_id)

def add_custom_esignature_role(role: str, permissions: Dict[PermissionAction, bool]):
    """Add custom E-signature permissions for a new role"""
    ESignaturePermissions.add_custom_role(role, permissions)

# Legacy compatibility functions for existing imports
def get_user_permissions(role: str) -> List[str]:
    """Get user permissions as a list of strings (legacy compatibility)"""
    try:
        permissions = ESignaturePermissions.get_role_permissions(role)
        permission_list = []
        
        for action, has_perm in permissions.items():
            if has_perm:
                permission_list.append(action.value)
        
        return permission_list
    except Exception:
        return []

def has_permission(role: str, permission: str) -> bool:
    """Check if role has a specific permission (legacy compatibility)"""
    try:
        perm_action = PermissionAction(permission)
        return ESignaturePermissions.has_permission(role, perm_action)
    except (ValueError, Exception):
        return False

def can_manage_role(role: str) -> bool:
    """Check if role can manage other roles (legacy compatibility)"""
    return role in ["system_admin", "hr_admin"]

class Permission:
    """Legacy Permission class for compatibility"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    def __str__(self):
        return self.name 