# Dynamic E-signature System Guide

## Overview

The Dynamic E-signature System is a comprehensive, multi-tenant solution that automatically handles E-signature functionality for all companies (existing and future) with role-based permissions that adapt to new roles dynamically.

## Key Features

### 🏢 **Multi-Tenant Company Support**
- **Automatic Table Creation**: E-signature tables are automatically created for every new company
- **Existing Company Support**: All existing companies automatically get E-signature tables
- **Company Isolation**: Each company has its own isolated E-signature data
- **Auto-Cleanup**: Tables are automatically cleaned up when companies are deleted

### 🔐 **Dynamic Role-Based Permissions**
- **Base Roles**: Pre-defined roles with specific permissions (system_admin, hr_admin, hr_manager, employee, customer)
- **Custom Roles**: System administrators can create custom roles with specific permissions
- **Unknown Role Handling**: Automatically detects and assigns appropriate permissions to new/unknown roles
- **Role Hierarchy**: Supports role inheritance and permission escalation

### 🎯 **Permission Actions**
- **CREATE**: Create new signature requests
- **SEND**: Send signature requests to recipients
- **VIEW**: View signature requests
- **CANCEL**: Cancel signature requests
- **SIGN**: Sign documents
- **DOWNLOAD**: Download signed documents
- **MANAGE**: Manage all signature requests
- **APPROVE**: Approve signature requests
- **WORKFLOW_CREATE**: Create workflow templates
- **WORKFLOW_MANAGE**: Manage workflow templates
- **BULK_SEND**: Send bulk signature requests
- **AUDIT_VIEW**: View audit logs

## System Architecture

### Database Layer
```
Management Database (Global)
├── Companies Table
├── System Users Table
└── Company Configurations

Company Database (Per Company)
├── Users Table
├── Documents Table
├── E-signature Documents Table      [AUTO-CREATED]
├── E-signature Recipients Table     [AUTO-CREATED]
├── E-signature Audit Logs Table     [AUTO-CREATED]
└── Workflow Approvals Table         [AUTO-CREATED]
```

### Permission System
```
Role Permission Matrix
├── Base Permissions (Built-in)
│   ├── system_admin (Full Access)
│   ├── hr_admin (High Level)
│   ├── hr_manager (Mid Level)
│   ├── employee (Basic)
│   └── customer (Limited)
├── Custom Permissions (Dynamic)
│   ├── Created by System Admin
│   ├── Cloned from existing roles
│   └── Modified permissions
└── Unknown Role Handler
    ├── Pattern matching
    ├── Auto-assignment
    └── Fallback to employee
```

## Role Permissions Matrix

| Role | Create | Send | View | Cancel | Sign | Download | Manage | Approve | Workflow | Bulk | Audit |
|------|--------|------|------|--------|------|----------|---------|---------|----------|------|--------|
| **system_admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **hr_admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **hr_manager** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| **employee** | ✅ | ✅ | ✅ | ✅* | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **customer** | ❌ | ❌ | ✅* | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

*\*Own requests only*

## API Endpoints

### Core E-signature Operations
```
POST   /api/esignature/create-request     # Create signature request
POST   /api/esignature/{id}/send          # Send signature request
GET    /api/esignature/list               # List signature requests
GET    /api/esignature/{id}/status        # Get request status
POST   /api/esignature/{id}/cancel        # Cancel request
GET    /api/esignature/{id}/download-signed # Download signed document
```

### Permission Management
```
GET    /api/esignature/permissions/my-role        # Get current user permissions
GET    /api/esignature/permissions/all-roles      # Get all role permissions (admin)
GET    /api/user-management/roles/list-all-roles  # List all roles
POST   /api/user-management/roles/create-custom-role # Create custom role
DELETE /api/user-management/roles/delete-custom-role/{role} # Delete custom role
POST   /api/user-management/roles/clone-role      # Clone existing role
```

### Workflow Operations
```
POST   /api/esignature/workflow/contract-approval    # Contract approval workflow
POST   /api/esignature/workflow/policy-acknowledgment # Policy acknowledgment workflow
POST   /api/esignature/workflow/budget-approval      # Budget approval workflow
POST   /api/esignature/bulk-send                     # Bulk signature requests
GET    /api/esignature/audit-logs                    # View audit logs
```

## Dynamic Company Integration

### New Company Creation
When a new company is created:

1. **Database Tables**: E-signature tables are automatically created
2. **Permission Verification**: System verifies all tables exist
3. **Role Assignment**: Company users get appropriate role-based permissions
4. **Isolation**: Company data is completely isolated from other companies

### Company Deletion
When a company is deleted:

1. **Database Cleanup**: All E-signature data is cleaned up
2. **Connection Removal**: Database connections are properly closed
3. **Resource Cleanup**: All resources are freed

## Dynamic Role Management

### Creating Custom Roles
```json
POST /api/user-management/roles/create-custom-role
{
    "role_name": "project_lead",
    "permissions": {
        "create": true,
        "send": true,
        "view": true,
        "cancel": true,
        "sign": true,
        "download": true,
        "manage": false,
        "approve": true,
        "workflow_create": false,
        "workflow_manage": false,
        "bulk_send": false,
        "audit_view": false
    }
}
```

### Cloning Existing Roles
```json
POST /api/user-management/roles/clone-role
{
    "source_role": "hr_manager",
    "new_role_name": "department_head",
    "permission_modifications": {
        "bulk_send": true,
        "audit_view": true
    }
}
```

### Unknown Role Handling
The system automatically handles unknown roles by:

1. **Pattern Matching**: Analyzes role name patterns
   - `*admin*` → Admin-level permissions
   - `*manager*`, `*supervisor*`, `*lead*` → Manager-level permissions
   - `*employee*`, `*staff*`, `*user*` → Employee-level permissions
   - `*customer*`, `*client*`, `*guest*` → Customer-level permissions

2. **Fallback**: Defaults to employee permissions for unrecognized patterns

3. **Logging**: Logs unknown roles for system administrator review

## Security Features

### Role-Based Access Control
- **Permission Validation**: Every API call validates user permissions
- **Ownership Checks**: Users can only access their own data (except admins)
- **Audit Logging**: All actions are logged with user details and timestamps
- **Company Isolation**: Users can only access data within their company

### Data Protection
- **Database Isolation**: Each company has separate database tables
- **Connection Security**: Secure database connections with proper authentication
- **Input Validation**: All inputs are validated before processing
- **Error Handling**: Proper error handling without exposing sensitive information

## Usage Examples

### Creating a Signature Request
```javascript
// Employee creating a signature request
const response = await api.post('/api/esignature/create-request', {
    document_id: 'doc_123',
    title: 'Employment Contract',
    message: 'Please sign this employment contract',
    recipients: [
        {
            email: 'john.doe@company.com',
            full_name: 'John Doe',
            role: 'employee'
        }
    ],
    expires_in_days: 14
});
```

### Checking Role Permissions
```javascript
// Check current user's permissions
const permissions = await api.get('/api/esignature/permissions/my-role');
console.log(permissions.data.permissions.can_create); // true/false
```

### Creating a Custom Role
```javascript
// System admin creating a custom role
const customRole = await api.post('/api/user-management/roles/create-custom-role', {
    role_name: 'contract_manager',
    permissions: {
        create: true,
        send: true,
        view: true,
        cancel: true,
        sign: true,
        download: true,
        manage: true,
        approve: true,
        workflow_create: true,
        workflow_manage: false,
        bulk_send: true,
        audit_view: true
    }
});
```

## Implementation Details

### Database Manager Integration
```python
# Automatic table creation for new companies
def create_company_tables(self, company_id: str, database_url: str):
    """Create all company tables including E-signature tables dynamically"""
    # Creates all tables including E-signature tables
    # Verifies table creation
    # Handles errors gracefully
```

### Permission System Integration
```python
# Dynamic permission checking
def has_permission(role: str, action: PermissionAction) -> bool:
    """Check if a role has permission for a specific action"""
    # Handles base roles
    # Handles custom roles
    # Handles unknown roles
    # Returns safe defaults
```

### API Integration
```python
# Permission validation in API endpoints
@router.post("/create-request")
async def create_signature_request(
    request_data: ESignatureRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_company_db_session)
):
    # Check permissions dynamically
    user_role = getattr(current_user, 'role', 'customer')
    if not can_create_esignature_request(user_role):
        raise HTTPException(status_code=403, detail="Permission denied")
```

## Monitoring and Maintenance

### Audit Logs
All E-signature actions are logged with:
- User information
- Action performed
- Timestamp
- Additional context (role, company, etc.)

### System Health
- **Database Connections**: Monitored for all companies
- **Table Integrity**: Verified during startup and periodically
- **Permission Validation**: Logged for security monitoring
- **Error Tracking**: Comprehensive error logging and tracking

## Future Enhancements

### Planned Features
1. **Role Templates**: Pre-defined role templates for common use cases
2. **Permission Inheritance**: More sophisticated role hierarchy
3. **Time-based Permissions**: Permissions that expire or activate at specific times
4. **Geographic Permissions**: Location-based permission restrictions
5. **Integration APIs**: External system integration for role management

### Scalability Considerations
- **Database Sharding**: Support for database sharding across companies
- **Caching Layer**: Redis-based caching for permissions
- **Event-Driven Architecture**: Event-based permission updates
- **Microservices**: Breaking down into smaller, focused services

## Troubleshooting

### Common Issues

1. **Missing E-signature Tables**
   - Run: `python backend/initialize_dynamic_esignature.py`
   - Check: Company database connection
   - Verify: Table creation permissions

2. **Permission Denied Errors**
   - Check: User role assignment
   - Verify: Permission matrix
   - Review: Custom role configurations

3. **New Role Not Working**
   - Check: Role pattern matching
   - Verify: Custom role creation
   - Review: Permission assignments

### Diagnostic Commands
```bash
# Initialize system
python backend/initialize_dynamic_esignature.py

# Check E-signature tables
python backend/create_esignature_tables.py

# Test system
python backend/test_system.py
```

## Conclusion

The Dynamic E-signature System provides a robust, scalable solution for multi-tenant E-signature operations with comprehensive role-based permissions. It automatically adapts to new companies and roles while maintaining security and data isolation.

**Key Benefits:**
- ✅ **Automatic Setup**: New companies get E-signature tables automatically
- ✅ **Dynamic Permissions**: Roles and permissions adapt to business needs
- ✅ **Security**: Comprehensive access control and audit logging
- ✅ **Scalability**: Supports unlimited companies and custom roles
- ✅ **Maintainability**: Easy to manage and extend

The system is now ready for production use and will automatically handle all future companies and roles! 