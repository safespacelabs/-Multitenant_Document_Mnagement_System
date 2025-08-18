# Enhanced Document Management System

This document describes the enhanced document management features that replicate the PFile interface with organizational categories, advanced filtering, and improved user experience.

## Features Overview

### 🏢 Organizational Structure
- **Document Categories**: Pre-defined categories like Career Development, Compensation, Employee Central, etc.
- **Document Folders**: Hierarchical folder organization within categories
- **Multi-tenant Support**: Each company has its own document structure

### 🔍 Advanced Filtering & Search
- **Category-based filtering**: Filter documents by organizational category
- **File type filtering**: Filter by PDF, Word, Excel, Images, etc.
- **Search functionality**: Search across document names, descriptions, and tags
- **Date range filtering**: Filter by upload date
- **Employee filtering**: Filter by document owner/creator

### 📊 Enhanced Document Management
- **Grid/List view**: Toggle between different viewing modes
- **Bulk operations**: Download, delete, move, share, or archive multiple documents
- **Document metadata**: Enhanced document information including tags, descriptions, and access levels
- **Audit logging**: Track all document activities and access
- **Access control**: Granular permissions for document access

### 🎨 Modern UI/UX
- **PFile-like interface**: Clean, professional design similar to enterprise file management systems
- **Responsive design**: Works on desktop and mobile devices
- **Intuitive navigation**: Breadcrumb navigation and sidebar organization
- **Visual indicators**: Color-coded categories and file type icons

## Backend Implementation

### New Database Models

#### DocumentCategory
```python
class DocumentCategory(CompanyBase):
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)  # career_development, compensation, etc.
    display_name = Column(String, nullable=False)  # Career Development, Compensation, etc.
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)  # briefcase, dollar-sign, etc.
    color = Column(String, nullable=True)  # Hex color codes
    parent_category_id = Column(String, ForeignKey("document_categories.id"), nullable=True)
    company_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### DocumentFolder
```python
class DocumentFolder(CompanyBase):
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(String, ForeignKey("document_categories.id"), nullable=True)
    parent_folder_id = Column(String, ForeignKey("document_folders.id"), nullable=True)
    company_id = Column(String, nullable=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### Enhanced Document Model
```python
class Document(CompanyBase):
    # ... existing fields ...
    
    # New enhanced fields
    document_category = Column(String, nullable=True)
    document_subcategory = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    access_level = Column(String, default="private")
    expiry_date = Column(DateTime, nullable=True)
    version = Column(String, default="1.0")
    status = Column(String, default="active")
```

### New API Endpoints

#### GET /api/documents/categories
List all document categories for the company.

#### GET /api/documents/folders
List document folders, optionally filtered by category.

#### GET /api/documents/enhanced
Enhanced document listing with advanced filtering, pagination, and sorting.

**Query Parameters:**
- `category_id`: Filter by category
- `folder_id`: Filter by folder
- `file_type`: Filter by file type
- `search_query`: Search in document names and descriptions
- `tags`: Filter by tags
- `date_from` & `date_to`: Date range filtering
- `status`: Filter by document status
- `access_level`: Filter by access level
- `user_id`: Filter by document owner
- `page`: Page number for pagination
- `page_size`: Number of documents per page
- `sort_by`: Sort field
- `sort_order`: Sort direction (asc/desc)

#### POST /api/documents/bulk-operation
Perform bulk operations on multiple documents.

**Request Body:**
```json
{
  "document_ids": ["doc1", "doc2", "doc3"],
  "operation": "download|delete|move|share|archive",
  "target_folder_id": "folder_id",  // for move operation
  "target_category_id": "category_id",  // for move operation
  "user_ids": ["user1", "user2"],  // for share operation
  "access_type": "read|write|admin"  // for share operation
}
```

#### GET /api/documents/stats
Get document statistics for the company.

#### GET /api/documents/audit-logs
Get document audit logs (HR admins and managers only).

## Frontend Implementation

### EnhancedDocumentManager Component

The main component that provides the PFile-like interface:

```jsx
import EnhancedDocumentManager from './components/Documents/EnhancedDocumentManager';

// Use in your app
<EnhancedDocumentManager />
```

### Key Features

1. **Left Sidebar Navigation**
   - Company logo and branding
   - Main navigation (My Files, Org Files, Recent, etc.)
   - Organizational categories with icons
   - Collapsible sidebar

2. **Header with Search**
   - Global search bar with filters
   - User information and avatar
   - Clear search functionality

3. **Main Content Area**
   - Breadcrumb navigation
   - Advanced filtering controls
   - Action buttons (Download Files, List View, Date)
   - Document grid with metadata
   - Pagination controls

4. **Document Cards**
   - File type icons
   - Document names
   - File sizes and dates
   - Owner information
   - Hover effects and interactions

## Setup Instructions

### 1. Initialize Database Tables

Run the initialization script to create the new tables and default categories:

```bash
cd backend
python initialize_document_categories.py
```

This will:
- Create new tables for categories, folders, access control, and audit logging
- Insert default organizational categories
- Create default folders for each category
- Set up the basic structure for all companies

### 2. Update Existing Documents

If you have existing documents, you may want to update them with category information:

```sql
-- Example: Update existing documents to use a default category
UPDATE documents 
SET document_category = 'career_development' 
WHERE document_category IS NULL;
```

### 3. Frontend Integration

1. **Import the component:**
   ```jsx
   import EnhancedDocumentManager from './components/Documents/EnhancedDocumentManager';
   ```

2. **Add to your routing:**
   ```jsx
   <Route path="/documents/enhanced" element={<EnhancedDocumentManager />} />
   ```

3. **Update navigation:**
   Add a link to the enhanced document manager in your navigation menu.

## Default Categories

The system comes with these pre-configured categories:

1. **Career Development** (briefcase icon)
   - Training materials
   - Skill development documents
   - Career planning resources

2. **Compensation** (dollar sign icon)
   - Salary information
   - Benefits documentation
   - Compensation policies

3. **Employee Central** (user icon)
   - Employee records
   - Personal information
   - Employment contracts

4. **On/Offboarding** (file-text icon)
   - New hire documents
   - Exit procedures
   - Orientation materials

5. **Performance and Goals** (trending-up icon)
   - Performance reviews
   - Goal setting documents
   - Assessment materials

6. **Platform** (monitor icon)
   - System documentation
   - Technical guides
   - Platform policies

7. **Others** (more-horizontal icon)
   - Miscellaneous documents
   - General files
   - Uncategorized content

## Customization

### Adding New Categories

You can add custom categories through the API:

```bash
curl -X POST "http://localhost:8000/api/documents/categories" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_category",
    "display_name": "Custom Category",
    "description": "Description of custom category",
    "icon": "star",
    "color": "#FF6B6B",
    "sort_order": 8
  }'
```

### Customizing Icons and Colors

The system supports custom icons and colors for categories. You can use any Lucide React icon names and hex color codes.

### Folder Organization

Create custom folders within categories:

```bash
curl -X POST "http://localhost:8000/api/documents/folders" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_folder",
    "display_name": "Custom Folder",
    "description": "Description of custom folder",
    "category_id": "category_id_here",
    "sort_order": 1
  }'
```

## Security and Permissions

### Access Control

- **HR Admins & Managers**: Full access to all features
- **Regular Employees**: Can only see their own documents and public documents
- **System Admins**: Access to system-level document management

### Audit Logging

All document operations are logged with:
- User who performed the action
- Action type (view, download, edit, delete, share)
- Timestamp
- IP address and user agent
- Additional details

### Data Privacy

- Documents are isolated by company
- User access is controlled by role and permissions
- Sensitive operations require appropriate permissions

## Performance Considerations

### Pagination

The enhanced document listing uses pagination to handle large document collections efficiently:
- Default page size: 20 documents
- Configurable page size
- Optimized database queries

### Caching

Consider implementing caching for:
- Category and folder lists
- Document metadata
- Search results
- Statistics

### Database Optimization

- Indexes on frequently queried fields
- Efficient JOIN operations
- Query optimization for complex filters

## Troubleshooting

### Common Issues

1. **Categories not loading**
   - Check if the initialization script ran successfully
   - Verify database table creation
   - Check user permissions

2. **Documents not appearing**
   - Verify document category assignments
   - Check access permissions
   - Verify company_id assignments

3. **API errors**
   - Check authentication tokens
   - Verify endpoint URLs
   - Check request payload format

### Debug Mode

Enable debug logging in the backend:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Database Queries

Use these queries to debug data issues:

```sql
-- Check categories
SELECT * FROM document_categories WHERE company_id = 'your_company_id';

-- Check folders
SELECT * FROM document_folders WHERE company_id = 'your_company_id';

-- Check document assignments
SELECT d.*, dc.display_name as category_name 
FROM documents d 
LEFT JOIN document_categories dc ON d.document_category = dc.id 
WHERE d.company_id = 'your_company_id';
```

## Future Enhancements

### Planned Features

1. **Advanced Search**
   - Full-text search
   - Semantic search
   - Search within document content

2. **Document Workflows**
   - Approval processes
   - Version control
   - Collaboration features

3. **Integration**
   - Cloud storage providers
   - Document signing services
   - Email integration

4. **Analytics**
   - Usage statistics
   - Storage analytics
   - User behavior insights

### Contributing

To contribute to the enhanced document management system:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## Support

For support and questions:

1. Check the troubleshooting section
2. Review the API documentation
3. Check GitHub issues
4. Contact the development team

---

This enhanced document management system provides a professional, enterprise-grade file management experience similar to PFile, with robust backend support and a modern, intuitive frontend interface.
