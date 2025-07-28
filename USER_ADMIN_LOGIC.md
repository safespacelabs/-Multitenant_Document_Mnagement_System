# User/Admin Logic with Database Isolation

## Overview
The system now implements **database isolation** while maintaining the **exact same user management and role-based access control** as before. Here's how it works:

## User Roles (Same as Before)

### System Level
- **system_admin**: Can create/delete companies and manage the entire system

### Company Level (Same as Original)
- **hr_admin**: Can invite users, manage all company users, access all documents
- **hr_manager**: Can invite users, manage employees and customers, access documents  
- **employee**: Can manage customers, access limited documents
- **customer**: Basic access, can view own documents only

## Key Changes for Database Isolation

### 1. Authentication
- **System Users**: Stored in management database (for system admins)
- **Company Users**: Stored in company-specific databases
- **Login**: Automatically detects if user is system admin or company user
- **Same login endpoint**: `/api/auth/login` works for both types

### 2. User Management (Same Logic, Different Databases)

#### Company Registration Flow:
1. **System Admin** creates company → Creates isolated database + S3 bucket
2. **HR Admin** invited during company setup
3. **HR Admin** logs in and can invite hr_managers, employees, customers
4. **All users** exist only in their company's database

#### Invitation System (Unchanged):
- HR admins can invite hr_managers, employees, customers
- HR managers can invite employees, customers  
- Employees can invite customers
- Same unique ID system for password setup
- Same 7-day expiration

#### Role Permissions (Unchanged):
```python
# Same permission system as before
hr_admin:    [MANAGE_COMPANY_USERS, UPLOAD_DOCUMENTS, VIEW_ALL_DOCUMENTS]
hr_manager:  [MANAGE_USERS, UPLOAD_DOCUMENTS, VIEW_DOCUMENTS]  
employee:    [MANAGE_CUSTOMERS, UPLOAD_DOCUMENTS, VIEW_OWN_DOCUMENTS]
customer:    [VIEW_OWN_DOCUMENTS]
```

## Database Architecture

### Management Database (multitenant-db)
```sql
-- System administration
companies           -- Company registry with database URLs
system_users        -- System administrators only
company_database_logs -- Database operation logs
```

### Company Databases (company_<id>)
```sql
-- Same tables as before, per company
users               -- HR admins, managers, employees, customers
user_invitations    -- Invitation system
documents           -- Company documents  
chat_history        -- Chat interactions
```

## API Endpoints (Same Logic)

### Authentication (Works for Both)
- `POST /api/auth/login` - Login system or company user
- `GET /api/auth/me` - Get current user info

### Company Management (System Admin Only)
- `POST /api/companies/` - Create company with isolated database
- `GET /api/companies/` - List companies
- `DELETE /api/companies/{id}` - Delete company and its database

### User Management (Company Users - Same as Before)
- `POST /api/user-management/invite` - Invite users (HR admin/manager)
- `GET /api/user-management/users` - List company users
- `POST /api/user-management/setup-password` - Setup password from invitation
- `GET /api/user-management/invitations` - List pending invitations

### Documents (Company Users - Same as Before)
- `POST /api/documents/upload` - Upload documents
- `GET /api/documents/` - List documents (based on role)
- `DELETE /api/documents/{id}` - Delete documents

## Example Workflows

### 1. System Admin Creates Company
```python
# System admin logs in
POST /api/auth/login
{
  "username": "admin", 
  "password": "admin123"
}

# Creates company with isolated database
POST /api/companies/
{
  "name": "Acme Corp",
  "email": "admin@acme.com"
}
# → Creates: company_comp_12345678 database
# → Creates: acme-corp-docs-12345678 S3 bucket
```

### 2. HR Admin Invited and Manages Users
```python
# HR admin invited through separate process
# HR admin logs in to company database
POST /api/auth/login  
{
  "username": "hr_admin",
  "password": "password123"
}

# Invites employees (same as before)
POST /api/user-management/invite
{
  "email": "employee@acme.com",
  "full_name": "John Employee", 
  "role": "employee"
}
```

### 3. Employee Manages Customers (Same as Before)
```python
# Employee logs in
POST /api/auth/login
{
  "username": "employee1", 
  "password": "password123"
}

# Can invite customers (same permission logic)
POST /api/user-management/invite
{
  "email": "customer@external.com",
  "full_name": "Jane Customer",
  "role": "customer"  
}
```

## Security & Isolation

### Data Isolation
- **Complete separation**: Companies cannot see each other's data
- **Database level**: Each company has own PostgreSQL database
- **S3 isolation**: Each company has own S3 bucket
- **Authentication**: Users can only access their company's resources

### Role-Based Access (Unchanged)
- Same permission checks as before
- Same role hierarchy: hr_admin > hr_manager > employee > customer
- Same document access patterns
- Same user management restrictions

## Migration Notes

### From Previous System
1. **Existing companies** → Migrate to isolated databases
2. **User roles** → Remain exactly the same
3. **Permissions** → No changes needed
4. **Frontend** → Minimal changes (same API contracts)

### Benefits Gained
1. **True isolation** → Companies completely separated
2. **Scalability** → Each company database scales independently  
3. **Compliance** → Easier data residency/privacy compliance
4. **Performance** → Company-specific optimizations possible
5. **Security** → Physical data separation

## Key Points

✅ **Same user roles and permissions as before**  
✅ **Same invitation and password setup flow**  
✅ **Same role-based document access**  
✅ **Same API endpoints and contracts**  
✅ **Added true database isolation**  
✅ **Added company-level S3 buckets**  
✅ **Added system admin capabilities**  

The user experience and admin workflows remain **identical** to the previous system, but now with the security and scalability benefits of true database isolation. 