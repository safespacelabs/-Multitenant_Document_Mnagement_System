# HR User Folders Feature

## Overview

The HR User Folders feature provides HR administrators and managers with the ability to create and manage folders for specific users within their company. This feature allows HR personnel to organize and store documents for individual employees in a structured manner, with each user having their own set of folders managed by HR.

## Features

### 1. User Folder Management
- **Create Folders**: HR admins can create folders for specific users
- **Folder Organization**: Folders can be categorized by type (HR managed, user created, system)
- **Custom Naming**: Each folder has a display name and description for better organization
- **Sorting**: Folders can be ordered using sort order values

### 2. Document Storage
- **Upload Documents**: HR can upload documents directly to user folders
- **Document Metadata**: Support for document categories, subcategories, tags, and descriptions
- **File Management**: Upload, view, and delete documents within folders
- **File Size Limits**: Maximum file size of 100MB per document

### 3. Access Control
- **Role-Based Access**: Only HR admins, HR managers, and system admins can access this feature
- **Company Isolation**: Users can only access folders within their own company
- **Audit Logging**: All folder and document operations are logged for compliance

### 4. Search and Filtering
- **Search Folders**: Search folders by name or display name
- **Filter by User**: Filter folders by specific user
- **Filter by Type**: Filter folders by folder type (HR managed, user created, system)

## Technical Implementation

### Backend Components

#### 1. Database Models (`backend/app/models_company.py`)
- **UserFolder**: Stores folder information and metadata
- **HRManagedDocument**: Stores document information and metadata
- **UserFolderAccess**: Manages access control for folders
- **UserFolderAuditLog**: Tracks all folder and document operations

#### 2. API Endpoints (`backend/app/routers/hr_user_folders.py`)
- `POST /api/hr-user-folders/folders` - Create new user folder
- `GET /api/hr-user-folders/folders` - List all user folders with filters
- `GET /api/hr-user-folders/folders/{folder_id}` - Get folder with documents
- `POST /api/hr-user-folders/folders/{folder_id}/documents` - Upload document to folder
- `GET /api/hr-user-folders/users/{user_id}/folders` - Get all folders for a specific user
- `DELETE /api/hr-user-folders/folders/{folder_id}` - Delete folder and contents
- `DELETE /api/hr-user-folders/documents/{document_id}` - Delete specific document

#### 3. AWS S3 Integration (`backend/app/services/aws_service.py`)
- **Folder Creation**: Creates S3 folders with proper tagging
- **File Upload**: Uploads files to specific user folders
- **File Management**: Lists, copies, and deletes files from S3
- **Security**: Implements proper access controls and encryption

#### 4. Schemas (`backend/app/schemas.py`)
- **UserFolderCreate**: Schema for creating new folders
- **UserFolderResponse**: Schema for folder responses
- **HRManagedDocumentCreate**: Schema for creating documents
- **HRManagedDocumentResponse**: Schema for document responses

### Frontend Components

#### 1. Main Component (`frontend/src/components/Features/HRUserFolders.js`)
- **Folder Management**: Create, view, and delete folders
- **Document Management**: Upload, view, and delete documents
- **Search and Filtering**: Advanced search and filter capabilities
- **Responsive Design**: Mobile-friendly interface

#### 2. Integration
- **Routing**: Added to main App.js routing
- **Navigation**: Integrated into sidebar navigation
- **Permissions**: Role-based access control

## Usage

### For HR Administrators and Managers

#### 1. Creating User Folders
1. Navigate to "User Folders" in the sidebar
2. Click "Create Folder" button
3. Fill in folder details:
   - Folder Name (internal name)
   - Display Name (user-friendly name)
   - Description (optional)
   - Select User (who the folder belongs to)
4. Click "Create Folder"

#### 2. Uploading Documents
1. Select a folder by clicking the "View" button
2. Click "Upload Document" button
3. Choose a file (max 100MB)
4. Fill in document metadata:
   - Category (Career Development, Compensation, etc.)
   - Description (optional)
5. Click "Upload"

#### 3. Managing Folders and Documents
- **View Folders**: See all folders with document counts and sizes
- **View Documents**: Click on a folder to see all documents inside
- **Delete Items**: Use the delete buttons to remove folders or documents
- **Search**: Use the search bar to find specific folders or documents

### For Users
- Users can see folders created for them by HR
- Access to documents is controlled by HR permissions
- Users can view but not modify HR-managed content

## Security Features

### 1. Authentication
- JWT token-based authentication required for all operations
- Role-based access control (HR admin, HR manager, system admin only)

### 2. Data Isolation
- Company-level isolation ensures users can only access their company's data
- User-level isolation ensures HR can only manage folders for users in their company

### 3. Audit Logging
- All folder and document operations are logged
- Includes user ID, action type, and metadata
- Supports compliance and security auditing

### 4. S3 Security
- Private S3 buckets with no public access
- Server-side encryption enabled
- Proper tagging for access control

## Database Schema

### UserFolder Table
```sql
CREATE TABLE user_folders (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    display_name VARCHAR NOT NULL,
    description TEXT,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    created_by_user_id VARCHAR NOT NULL REFERENCES users(id),
    s3_folder_path VARCHAR NOT NULL,
    folder_type VARCHAR DEFAULT 'hr_managed',
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    company_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### HRManagedDocument Table
```sql
CREATE TABLE hr_managed_documents (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR NOT NULL,
    original_filename VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR NOT NULL,
    s3_key VARCHAR NOT NULL,
    folder_id VARCHAR NOT NULL REFERENCES user_folders(id),
    user_id VARCHAR NOT NULL REFERENCES users(id),
    created_by_user_id VARCHAR NOT NULL REFERENCES users(id),
    document_category VARCHAR,
    document_subcategory VARCHAR,
    tags JSON,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    access_level VARCHAR DEFAULT 'private',
    expiry_date TIMESTAMP,
    version VARCHAR DEFAULT '1.0',
    status VARCHAR DEFAULT 'active',
    metadata_json JSON,
    processed BOOLEAN DEFAULT FALSE,
    company_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## API Response Examples

### Create Folder Response
```json
{
  "id": "ufolder_abc123",
  "name": "performance_reviews",
  "display_name": "Performance Reviews",
  "description": "Annual performance review documents",
  "user_id": "user_xyz789",
  "created_by_user_id": "hr_admin_123",
  "s3_folder_path": "users/user_xyz789/hr_folders/performance_reviews/",
  "folder_type": "hr_managed",
  "is_active": true,
  "sort_order": 0,
  "company_id": "comp_456",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "documents_count": 0,
  "total_size": 0
}
```

### Folder with Documents Response
```json
{
  "folder": {
    "id": "ufolder_abc123",
    "name": "performance_reviews",
    "display_name": "Performance Reviews",
    "description": "Annual performance review documents",
    "user_id": "user_xyz789",
    "created_by_user_id": "hr_admin_123",
    "s3_folder_path": "users/user_xyz789/hr_folders/performance_reviews/",
    "folder_type": "hr_managed",
    "is_active": true,
    "sort_order": 0,
    "company_id": "comp_456",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "documents_count": 2,
    "total_size": 2048576
  },
  "documents": [
    {
      "id": "hrdoc_def456",
      "filename": "performance_review_2024.pdf",
      "original_filename": "performance_review_2024.pdf",
      "file_path": "users/user_xyz789/hr_folders/performance_reviews/performance_review_2024.pdf",
      "file_size": 1024288,
      "file_type": "application/pdf",
      "s3_key": "users/user_xyz789/hr_folders/performance_reviews/performance_review_2024.pdf",
      "folder_id": "ufolder_abc123",
      "user_id": "user_xyz789",
      "created_by_user_id": "hr_admin_123",
      "document_category": "Performance",
      "document_subcategory": "Annual Review",
      "tags": ["performance", "annual", "2024"],
      "description": "Annual performance review for 2024",
      "is_public": false,
      "access_level": "private",
      "expiry_date": null,
      "version": "1.0",
      "status": "active",
      "metadata_json": {
        "category": "Performance",
        "subcategory": "Annual Review",
        "tags": ["performance", "annual", "2024"]
      },
      "processed": false,
      "company_id": "comp_456",
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  ],
  "total_documents": 2,
  "total_size": 2048576
}
```

## Setup and Installation

### 1. Database Migration
Run the migration script to create the new tables:
```bash
cd backend
python create_hr_user_folders_tables.py
```

### 2. Backend Setup
The new router is automatically included in the main application. No additional setup required.

### 3. Frontend Setup
The new component is automatically included in the routing. No additional setup required.

### 4. S3 Configuration
Ensure your AWS S3 credentials are properly configured in the environment variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## Best Practices

### 1. Folder Naming
- Use descriptive names that clearly indicate the folder's purpose
- Follow a consistent naming convention across the organization
- Include the year or period in folder names when relevant

### 2. Document Organization
- Use appropriate categories and subcategories for better organization
- Add meaningful descriptions to help users understand document content
- Tag documents with relevant keywords for easier searching

### 3. Access Management
- Regularly review folder access permissions
- Remove access for users who no longer need it
- Monitor audit logs for unusual activity

### 4. Storage Management
- Regularly review and archive old documents
- Monitor storage usage to prevent excessive costs
- Implement document retention policies

## Troubleshooting

### Common Issues

#### 1. Folder Creation Fails
- Check if the target user exists in the company
- Verify S3 bucket permissions
- Check company database connection

#### 2. Document Upload Fails
- Verify file size is under 100MB limit
- Check S3 bucket permissions
- Ensure folder exists and is active

#### 3. Access Denied Errors
- Verify user has appropriate role (HR admin, HR manager, or system admin)
- Check if user belongs to the correct company
- Verify JWT token is valid and not expired

### Debug Steps
1. Check backend logs for detailed error messages
2. Verify database connections and table existence
3. Test S3 connectivity and permissions
4. Check frontend console for JavaScript errors

## Future Enhancements

### 1. Advanced Features
- **Document Versioning**: Support for multiple versions of the same document
- **Workflow Integration**: Integration with approval workflows
- **Advanced Search**: Full-text search within documents
- **Bulk Operations**: Upload multiple documents at once

### 2. Integration Features
- **Email Notifications**: Notify users when documents are added to their folders
- **Calendar Integration**: Link documents to calendar events
- **Mobile App**: Native mobile application for document access

### 3. Compliance Features
- **Retention Policies**: Automatic document archiving and deletion
- **Compliance Reporting**: Generate compliance reports
- **Audit Trail**: Enhanced audit logging and reporting

## Support

For technical support or questions about this feature:
1. Check the backend logs for error details
2. Review the API documentation
3. Contact the development team
4. Check the troubleshooting section above

## Changelog

### Version 1.0.0 (Initial Release)
- Basic folder creation and management
- Document upload and storage
- Role-based access control
- Search and filtering capabilities
- Audit logging
- S3 integration
- Responsive web interface
