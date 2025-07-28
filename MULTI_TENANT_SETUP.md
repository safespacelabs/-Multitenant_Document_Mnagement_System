# Multi-Tenant Document Management System - Database Isolation Setup

## Overview
This system now implements **true database isolation** where each company gets their own completely separate database. The architecture consists of:

- **Management Database**: Stores company registrations, system users, and database connection information
- **Company Databases**: Each company has its own isolated database for users, documents, and chat history

## Architecture Components

### 1. Management Database (Neon - multitenant-db)
- **Purpose**: Central registry for companies and system administration
- **Tables**: 
  - `companies` - Company information and database connection details
  - `system_users` - System administrators
  - `company_database_logs` - Database operation logs

### 2. Company Databases (Neon - Auto-created)
- **Purpose**: Isolated data storage for each company
- **Tables**:
  - `users` - Company users (HR admins, managers, employees, customers)
  - `documents` - Company documents
  - `chat_history` - Chat interactions
  - `user_invitations` - User invitation system

### 3. Services
- **Neon Service**: Manages database creation and deletion via Neon API
- **Database Manager**: Handles multiple database connections and routing
- **Company Context**: Routes requests to the correct company database

## Setup Instructions

### 1. Environment Configuration
Update your environment variables:

```bash
# Management Database (Neon)
MANAGEMENT_DATABASE_URL=postgresql://multitenant-db_owner:npg_X7gKCTze2PAS@ep-lively-pond-a6gik9pf-pooler.us-west-2.aws.neon.tech/multitenant-db?sslmode=require&channel_binding=require

# Neon API Configuration
NEON_API_KEY=napi_4i48sb5ucqaiqkg60dct8bstompozmxnmfplr5cefr3x1qb6990p57kg17vuzt42

# AWS S3 Configuration (if using S3)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-west-1
AWS_S3_BUCKET_PREFIX=company-docs

# Other configurations...
```

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Initialize System Admin User
```bash
cd backend
python create_admin.py
```
This creates:
- Username: `admin`
- Password: `admin123`
- Email: `admin@system.local`

**⚠️ Change the password after first login!**

### 4. Start the Application
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Test the System
Check system status:
```bash
curl http://localhost:8000/api/system/status
```

## API Endpoints

### System Administration
- `GET /api/system/status` - System health and statistics
- `GET /health` - Basic health check

### Company Management (System Admin Only)
- `POST /api/companies/` - Create new company (creates isolated database)
- `GET /api/companies/` - List all companies
- `GET /api/companies/{id}/stats` - Company statistics
- `GET /api/companies/{id}/database/test` - Test company database connection
- `DELETE /api/companies/{id}` - Delete company and its database

### Authentication
- `POST /api/auth/login` - Login (system users or company users)
- `POST /api/auth/token` - Get access token

## Company Creation Process

When a new company is created:

1. **Neon Database Creation**: A new database is created via Neon API
2. **Table Initialization**: Company-specific tables are created
3. **S3 Bucket Creation**: AWS S3 bucket for document storage
4. **Management Record**: Company information stored in management database
5. **Connection Caching**: Database connection cached for performance

## Database Isolation Benefits

1. **True Isolation**: No data mixing between companies
2. **Scalability**: Each company database can be scaled independently
3. **Security**: Physical data separation
4. **Compliance**: Easier to meet data residency requirements
5. **Performance**: Company-specific optimizations possible

## Monitoring

### Database Connections
- Active company database connections: `GET /api/system/status`
- Test specific company database: `GET /api/companies/{id}/database/test`

### Logs
- Database operation logs stored in `company_database_logs` table
- Application logs show database creation/deletion activities

## Security Notes

1. **System Admin Access**: Only system admins can create/delete companies
2. **Database Isolation**: Companies cannot access each other's data
3. **Connection Security**: All database connections use SSL
4. **Password Security**: Passwords are hashed using bcrypt

## Troubleshooting

### Database Connection Issues
1. Check Neon API key validity
2. Verify database URLs in company records
3. Test connection using the test endpoint
4. Check database logs in management database

### Company Creation Failures
1. Check Neon API quota and limits
2. Verify S3 permissions (if using S3)
3. Check management database connection
4. Review application logs for specific errors

## Migration from Previous Version

If migrating from the previous multi-tenant setup:
1. Export existing company and user data
2. Run the new setup
3. Create companies using the new API
4. Import users into respective company databases
5. Migrate documents to company-specific S3 buckets

## Support

For issues or questions:
1. Check application logs
2. Verify environment configuration
3. Test database connections
4. Review Neon API documentation 