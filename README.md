# Multi-Tenant Document Management System

🚀 A modern, AI-powered document management system with true multi-tenant architecture, built with FastAPI and React. Features comprehensive document management, AI chatbot, e-signature system, and role-based access control.

## 📋 Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Local Development Setup](#local-development-setup)
- [Docker Setup](#docker-setup)
- [Multi-Tenant Database Isolation](#multi-tenant-database-isolation)
- [User Roles and Administration](#user-roles-and-administration)
- [Email Service System](#email-service-system)
- [E-Signature System](#e-signature-system)
- [Dynamic E-Signature System](#dynamic-e-signature-system)
- [Deployment Guides](#deployment-guides)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🏢 Multi-Tenant Architecture
- **True Database Isolation**: Each company has its own dedicated PostgreSQL database
- **Automatic Database Creation**: New companies get isolated databases automatically
- **AWS S3 Integration**: Automatic bucket creation per company with proper isolation
- **Company Management**: System administrators can create, manage, and delete companies
- **Cross-Company Analytics**: System-level insights across all companies

### 📄 Document Management
- **Advanced File Upload**: Drag & drop interface with progress tracking
- **AI-Powered Processing**: Automatic document analysis using Groq AI (Qwen 3-32B)
- **Metadata Extraction**: Title, summary, topics, entities, and sentiment analysis
- **Folder Organization**: Create and manage document folders
- **Search & Filter**: Advanced document search with multiple filters
- **File Type Support**: PDF, DOCX, TXT, MD, CSV, XLSX, and more
- **Document Analytics**: Usage statistics and insights

### 🤖 AI Chatbot & Assistant
- **Intelligent Document Chat**: Ask questions about your documents
- **Context-Aware Responses**: AI understands document content and company context
- **Multi-Role Support**: Different AI assistants for system admins and company users
- **Chat History**: Persistent conversation history
- **Real-time Processing**: Instant responses with loading indicators
- **Document Integration**: Direct access to document content and metadata

### 🔐 Complete E-Signature System
- **Full Digital Signatures**: Complete e-signature workflow with role-based permissions
- **Dynamic Role Management**: Custom roles with specific e-signature permissions
- **Multi-Tenant Support**: Automatic e-signature tables for all companies
- **Workflow Templates**: Pre-built templates for common use cases
- **Comprehensive Audit Trail**: Complete signing history with IP tracking
- **Bulk Operations**: Send signature requests to multiple recipients
- **Document Integration**: Direct e-signature from document management
- **Status Tracking**: Real-time signature request status

### 👥 User Management & Roles
- **Multi-Level Role System**: System Admin, HR Admin, HR Manager, Employee, Customer
- **Custom Role Creation**: System admins can create roles with specific permissions
- **Invitation System**: Secure user invitation with email verification
- **Password Management**: Strong password requirements and secure setup
- **Permission Matrix**: Granular permissions for each role
- **Company Isolation**: Users only access their company's data
- **Profile Management**: User profile and settings management

### 📧 Comprehensive Email Service
- **User Invitations**: Automatic emails when users are invited
- **E-Signature Requests**: Automatic signature request notifications
- **Document Notifications**: HR admins notified when documents uploaded
- **System Admin Notifications**: System-wide alerts and notifications
- **Company-Specific Branding**: Customized email templates per company
- **Role-Based Email Permissions**: Different email capabilities per role

### 🔐 Security & Authentication
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Comprehensive permission system
- **Password Validation**: Strong password requirements
- **Session Management**: Secure session handling
- **Audit Logging**: Complete activity tracking
- **Multi-Factor Ready**: Extensible for MFA implementation

### 🎨 Modern UI/UX
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Tailwind CSS**: Beautiful, modern interface
- **Real-time Updates**: Live status updates and notifications
- **Dark Mode Ready**: Prepared for theme switching
- **Intuitive Navigation**: Role-based sidebar and navigation
- **Loading States**: Smooth loading indicators and progress bars

## 🏗️ System Architecture

### Database Architecture
```
Management Database (Global)
├── Companies Table - Company registry with database URLs
├── System Users Table - System administrators
└── Company Database Logs - Operation tracking

Company Database (Per Company)
├── Users Table - Company users with roles
├── Documents Table - Company documents with metadata
├── Chat History Table - AI conversation history
├── E-Signature Documents Table - Signature requests
├── E-Signature Recipients Table - Signature recipients
├── E-Signature Audit Logs Table - Signature activity
└── Workflow Approvals Table - Approval workflows
```

### Multi-Tenant Isolation
- **Database Level**: Each company has isolated PostgreSQL database
- **Storage Level**: Each company has isolated AWS S3 bucket
- **User Level**: Users can only access their company's data
- **API Level**: All endpoints respect company boundaries

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework with automatic API docs
- **PostgreSQL** - Primary database with multi-tenant architecture
- **SQLAlchemy** - ORM and database toolkit
- **Groq AI** - High-performance AI processing (Qwen 3-32B)
- **AWS S3** - Scalable file storage
- **JWT** - Secure authentication tokens
- **Pydantic** - Data validation and serialization
- **Neon Database** - Serverless PostgreSQL hosting

### Frontend
- **React 18** - Modern UI framework with hooks
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful, consistent icons
- **Axios** - HTTP client with interceptors
- **React Markdown** - Markdown rendering for AI responses

### Infrastructure
- **Docker** - Containerization for consistent deployment
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Production web server
- **Railway** - Full-stack deployment platform
- **Render** - Alternative deployment platform

## 📋 Prerequisites

### For Local Development
- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL 14+** (or Neon database)
- **Git**

### For Docker Setup
- **Docker** 20.10+
- **Docker Compose** 2.0+

### External Services
- **AWS Account** with S3 access
- **Groq API Key** for AI processing
- **Neon Database** for PostgreSQL hosting

## 🔧 Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/multitenant-document-management.git
cd multitenant-document-management
```

### 2. Set Up Environment Variables

Create environment files:
```bash
# Backend environment
cp backend/env.example backend/.env

# Frontend environment
cp frontend/env.example frontend/.env
```

### 3. Configure Environment Variables

#### Backend Configuration (`backend/.env`)
```env
# Database (Neon)
MANAGEMENT_DATABASE_URL=postgresql://user:password@host/database
NEON_API_KEY=your-neon-api-key
NEON_PROJECT_ID=your-project-id

# JWT Authentication
SECRET_KEY=your-super-secret-jwt-key-here-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-west-1

# Groq AI
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=qwen/qwen3-32b

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-company@gmail.com
SENDER_PASSWORD=your-app-password
SENDER_NAME=Your Company Document Management

# Application
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://frontend:3000
APP_URL=http://localhost:3000

# Feature Flags
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_DOCUMENT_NOTIFICATIONS=true
ENABLE_ESIGNATURE_NOTIFICATIONS=true
```

#### Frontend Configuration (`frontend/.env`)
```env
REACT_APP_API_URL=http://localhost:8000
```

### 4. Generate JWT Secret Key
```bash
# Using OpenSSL
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## 💻 Local Development Setup

### 1. Database Setup

#### Option A: Local PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS with Homebrew
brew install postgresql
brew services start postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE multitenant_db;
CREATE USER docuser WITH PASSWORD 'your-secure-db-password';
GRANT ALL PRIVILEGES ON DATABASE multitenant_db TO docuser;
\q
```

#### Option B: Neon Database (Recommended)
1. Create account at [neon.tech](https://neon.tech)
2. Create new project
3. Get connection string and API key
4. Update environment variables

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install missing email validator dependency
pip install pydantic[email]

# Run database migrations and initialization
python create_admin.py
python create_esignature_tables.py
python initialize_dynamic_esignature.py

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### 4. Access the Application

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`

## 🐳 Docker Setup

### 1. Environment Configuration
Ensure you have configured the `.env` file in the project root with your credentials.

### 2. Build and Run with Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Run in background (detached mode)
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Docker Commands
```bash
# View running containers
docker-compose ps

# Restart a specific service
docker-compose restart backend

# Run commands inside containers
docker-compose exec backend bash
docker-compose exec frontend bash

# View service logs
docker-compose logs backend
docker-compose logs frontend

# Clean up
docker-compose down -v  # Remove volumes
docker system prune     # Clean up unused containers/images
```

## 🏢 Multi-Tenant Database Isolation

### Architecture Overview
The system implements **true database isolation** where each company gets their own completely separate database. The architecture consists of:

- **Management Database**: Stores company registrations, system users, and database connection information
- **Company Databases**: Each company has its own isolated database for users, documents, and chat history

### Database Architecture Components

#### 1. Management Database (Neon - multitenant-db)
- **Purpose**: Central registry for companies and system administration
- **Tables**: 
  - `companies` - Company information and database connection details
  - `system_users` - System administrators
  - `company_database_logs` - Database operation logs

#### 2. Company Databases (Neon - Auto-created)
- **Purpose**: Isolated data storage for each company
- **Tables**:
  - `users` - Company users (HR admins, managers, employees, customers)
  - `documents` - Company documents
  - `chat_history` - Chat interactions
  - `user_invitations` - User invitation system
  - E-signature tables (auto-created)

#### 3. Services
- **Neon Service**: Manages database creation and deletion via Neon API
- **Database Manager**: Handles multiple database connections and routing
- **Company Context**: Routes requests to the correct company database

### Company Creation Process

When a new company is created:

1. **Neon Database Creation**: A new database is created via Neon API
2. **Table Initialization**: Company-specific tables are created including e-signature tables
3. **S3 Bucket Creation**: AWS S3 bucket for document storage
4. **Management Record**: Company information stored in management database
5. **Connection Caching**: Database connection cached for performance

### Database Isolation Benefits

1. **True Isolation**: No data mixing between companies
2. **Scalability**: Each company database can be scaled independently
3. **Security**: Physical data separation
4. **Compliance**: Easier to meet data residency requirements
5. **Performance**: Company-specific optimizations possible

## 👥 User Roles and Administration

### User Roles Overview
The system implements database isolation while maintaining the same user management and role-based access control.

#### System Level
- **system_admin**: Can create/delete companies and manage the entire system

#### Company Level
- **hr_admin**: Can invite users, manage all company users, access all documents
- **hr_manager**: Can invite users, manage employees and customers, access documents  
- **employee**: Can manage customers, access limited documents
- **customer**: Basic access, can view own documents only

### Authentication System
- **System Users**: Stored in management database (for system admins)
- **Company Users**: Stored in company-specific databases
- **Login**: Automatically detects if user is system admin or company user
- **Same login endpoint**: `/api/auth/login` works for both types

### User Management Flow

#### Company Registration Flow:
1. **System Admin** creates company → Creates isolated database + S3 bucket
2. **HR Admin** invited during company setup
3. **HR Admin** logs in and can invite hr_managers, employees, customers
4. **All users** exist only in their company's database

#### Invitation System:
- HR admins can invite hr_managers, employees, customers
- HR managers can invite employees, customers  
- Employees can invite customers
- Same unique ID system for password setup
- Same 7-day expiration

#### Role Permissions:
```python
# Permission system
hr_admin:    [MANAGE_COMPANY_USERS, UPLOAD_DOCUMENTS, VIEW_ALL_DOCUMENTS]
hr_manager:  [MANAGE_USERS, UPLOAD_DOCUMENTS, VIEW_DOCUMENTS]  
employee:    [MANAGE_CUSTOMERS, UPLOAD_DOCUMENTS, VIEW_OWN_DOCUMENTS]
customer:    [VIEW_OWN_DOCUMENTS]
```

### Security & Isolation

#### Data Isolation
- **Complete separation**: Companies cannot see each other's data
- **Database level**: Each company has own PostgreSQL database
- **S3 isolation**: Each company has own S3 bucket
- **Authentication**: Users can only access their company's resources

#### Role-Based Access
- Same permission checks as before
- Same role hierarchy: hr_admin > hr_manager > employee > customer
- Same document access patterns
- Same user management restrictions

## 📧 Email Service System

### Email Features
The system includes a comprehensive email service that works across the entire application:

#### 1. **User Invitations** (Enhanced)
- Automatic emails when users are invited
- Company-specific branding
- Beautiful HTML templates

#### 2. **E-Signature Requests**
- Automatic emails when signature requests are sent
- Custom messages included
- Professional signing notifications

#### 3. **Document Notifications**
- HR admins notified when documents uploaded
- Document sharing notifications
- Update/delete notifications

#### 4. **System Admin Notifications**
- System-wide alerts
- Company creation notifications
- User registration alerts

### Email Service Architecture

#### Core Components:
- `EmailService` - Basic invitation emails
- `ExtendedEmailService` - Full feature set (inherits from EmailService)
- Company-specific email instances
- Role-based email permissions

#### Integration Points:
- User Management Router
- E-Signature Router  
- Documents Router
- System Admin Functions

### Email Configuration

#### Gmail Setup (Recommended for Testing):
1. Enable 2-Factor Authentication
2. Generate App Password:
   - Google Account → Security → 2-Step Verification → App Passwords
   - Select "Mail" → Generate password
   - Use generated password (not your regular Gmail password)

#### Other Email Providers:
```bash
# Outlook
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587

# Yahoo
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587

# Custom SMTP
SMTP_SERVER=mail.yourcompany.com
SMTP_PORT=587
```

### Role-Based Email Permissions

| Role | User Invites | E-Signature | Document Notifications | System Notifications |
|------|-------------|-------------|----------------------|-------------------|
| **System Admin** | ✅ All | ✅ All | ✅ All | ✅ All |
| **HR Admin** | ✅ Company | ✅ Company | ✅ Receive | ❌ No |
| **HR Manager** | ✅ Limited | ✅ Company | ✅ Receive | ❌ No |
| **Employee** | ❌ No | ✅ Limited | ❌ No | ❌ No |
| **Customer** | ❌ No | ❌ No | ❌ No | ❌ No |

### Email Templates
All emails include:
- ✅ **Responsive HTML design**
- ✅ **Plain text fallbacks**
- ✅ **Company branding**
- ✅ **Call-to-action buttons**
- ✅ **Mobile-friendly layout**
- ✅ **Professional styling**

## 🔐 E-Signature System

### E-Signature Overview
The system provides a comprehensive e-signature functionality integrated with Inkless.com, offering free, unlimited e-signature capabilities for all user roles with role-specific workflows.

### User Role E-Signature Capabilities

#### System Admin
- **Permissions**: Full access to all e-signature functions
- **Use Cases**: System-wide policy acknowledgments, executive contract approvals, critical document workflows, bulk signature management

#### HR Admin (Company Level - Full Access)
- **Permissions**: All company e-signature functions
- **Use Cases**: Company-wide policy acknowledgments, executive contract approvals, HR policy updates, bulk employee agreement processing

#### HR Manager (Department Level)
- **Permissions**: Department-level e-signature management
- **Use Cases**: Department contract approvals, employee performance review agreements, budget approval workflows

#### Employee (Limited Management)
- **Permissions**: Customer document signatures and own documents
- **Use Cases**: Customer service agreements, project approval documents, client contract processing

#### Customer (Basic Access)
- **Permissions**: Sign documents and view own signature status
- **Use Cases**: Service agreement acceptance, terms and conditions acknowledgment, order confirmations

### E-Signature Database Models

#### ESignatureDocument
- document_id: Reference to original document
- title: Signature request title
- status: pending/sent/signed/completed/cancelled/expired
- inkless_document_id: Inkless platform ID
- created_by_user_id: User who created request
- expires_at: Expiration date

#### ESignatureRecipient
- esignature_document_id: Link to signature document
- email: Recipient email
- full_name: Recipient name
- is_signed: Signature status
- signature_text: Stores the signature text
- ip_address: Stores signing IP address
- user_agent: Stores browser information

#### ESignatureAuditLog
- action: created/sent/opened/signed/completed
- user_email: User who performed action
- details: JSON with additional info

### E-Signature API Endpoints
- `POST /api/esignature/create-request` - Create signature request
- `POST /api/esignature/{id}/send` - Send request to recipients
- `GET /api/esignature/list` - List signature requests (role-filtered)
- `GET /api/esignature/{id}/status` - Get detailed status
- `POST /api/esignature/{id}/sign` - Sign document electronically
- `POST /api/esignature/{id}/cancel` - Cancel request
- `GET /api/esignature/{id}/download-signed` - Download completed document

### E-Signature Security Features

#### Role-Based Access Control
- Document access verification before signature creation
- Role hierarchy enforcement for workflow approvals
- Permission checks on all endpoints

#### Audit Trail
- Complete logging of all signature actions
- User identification and timestamp tracking
- IP address logging for security
- JSON details for comprehensive records

#### Legal Compliance
- ESIGN Act and UETA compliance through Inkless
- Complete audit trails for legal requirements
- Tamper-evident signature process
- Court-admissible documentation

### E-Signature Workflow Examples

#### Policy Acknowledgment (HR Admin)
1. HR Admin uploads policy document
2. Clicks "Policy Acknowledgment" in e-signature interface
3. System automatically adds all employees as recipients
4. Bulk signature request created and sent
5. Employees receive email notifications
6. HR Admin tracks completion status
7. Completed documents stored with audit trail

#### Contract Approval (HR Manager)
1. HR Manager uploads contract document
2. Clicks "Contract Approval" workflow
3. System suggests approval hierarchy: Legal → Finance → HR Admin
4. Sequential approval process initiated
5. Each approver signs in sequence
6. Final signed document available for download

## 🎯 Dynamic E-Signature System

### Dynamic System Overview
The Dynamic E-signature System is a comprehensive, multi-tenant solution that automatically handles E-signature functionality for all companies (existing and future) with role-based permissions that adapt to new roles dynamically.

### Key Dynamic Features

#### 🏢 Multi-Tenant Company Support
- **Automatic Table Creation**: E-signature tables are automatically created for every new company
- **Existing Company Support**: All existing companies automatically get E-signature tables
- **Company Isolation**: Each company has its own isolated E-signature data
- **Auto-Cleanup**: Tables are automatically cleaned up when companies are deleted

#### 🔐 Dynamic Role-Based Permissions
- **Base Roles**: Pre-defined roles with specific permissions (system_admin, hr_admin, hr_manager, employee, customer)
- **Custom Roles**: System administrators can create custom roles with specific permissions
- **Unknown Role Handling**: Automatically detects and assigns appropriate permissions to new/unknown roles
- **Role Hierarchy**: Supports role inheritance and permission escalation

#### 🎯 Permission Actions
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

### Dynamic Role Permissions Matrix

| Role | Create | Send | View | Cancel | Sign | Download | Manage | Approve | Workflow | Bulk | Audit |
|------|--------|------|------|--------|------|----------|---------|---------|----------|------|--------|
| **system_admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **hr_admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **hr_manager** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| **employee** | ✅ | ✅ | ✅ | ✅* | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **customer** | ❌ | ❌ | ✅* | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

*\*Own requests only*

### Dynamic Role Management

#### Creating Custom Roles
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

#### Unknown Role Handling
The system automatically handles unknown roles by:

1. **Pattern Matching**: Analyzes role name patterns
   - `*admin*` → Admin-level permissions
   - `*manager*`, `*supervisor*`, `*lead*` → Manager-level permissions
   - `*employee*`, `*staff*`, `*user*` → Employee-level permissions
   - `*customer*`, `*client*`, `*guest*` → Customer-level permissions

2. **Fallback**: Defaults to employee permissions for unrecognized patterns

3. **Logging**: Logs unknown roles for system administrator review

### Dynamic Company Integration

#### New Company Creation
When a new company is created:

1. **Database Tables**: E-signature tables are automatically created
2. **Permission Verification**: System verifies all tables exist
3. **Role Assignment**: Company users get appropriate role-based permissions
4. **Isolation**: Company data is completely isolated from other companies

#### Company Deletion
When a company is deleted:

1. **Database Cleanup**: All E-signature data is cleaned up
2. **Connection Removal**: Database connections are properly closed
3. **Resource Cleanup**: All resources are freed

## 📚 Deployment Guides

### Railway Deployment

Railway provides an excellent platform for deploying full-stack applications with automatic deployments from GitHub.

#### Prerequisites
1. Railway account (sign up at [railway.app](https://railway.app))
2. GitHub repository with your code
3. Database credentials (Neon PostgreSQL or Railway PostgreSQL)
4. AWS credentials for S3 storage
5. Groq API key for AI features
6. Email service credentials (Gmail/SMTP)

#### Deployment Steps

##### 1. Deploy Backend Service
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Navigate to project root
cd multitenant-document-management

# Create new Railway project
railway create multitenant-backend

# Deploy backend from backend directory
cd backend
railway up
```

##### 2. Set Backend Environment Variables
Go to Railway dashboard → Your Project → Backend Service → Variables

Add these variables:
```env
DATABASE_URL=your_neon_database_url
MANAGEMENT_DATABASE_URL=your_neon_database_url
SECRET_KEY=your_super_secret_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
GROQ_API_KEY=your_groq_key
SENDER_EMAIL=your_email@domain.com
SENDER_PASSWORD=your_email_password
PORT=8000
```

##### 3. Deploy Frontend Service
```bash
# From project root
cd frontend
railway create multitenant-frontend
railway up
```

##### 4. Set Frontend Environment Variables
```env
REACT_APP_API_URL=https://your-backend-service.railway.app
PORT=3000
CI=false
```

##### 5. Update CORS Configuration
After both services are deployed:

1. Get your frontend URL: `https://your-frontend.railway.app`
2. Update backend environment variables:
   ```env
   APP_URL=https://your-frontend.railway.app
   CORS_ORIGINS=https://your-frontend.railway.app
   ```

### Render.com Deployment

Render.com offers a generous free tier perfect for full-stack applications.

#### Why Render.com?
✅ **750 hours/month free** (enough for 24/7 uptime)  
✅ **Free PostgreSQL database** (1GB, 90-day retention)  
✅ **Auto-deploy from GitHub**  
✅ **HTTPS included**  
✅ **No credit card required**  
✅ **Perfect for full-stack apps**

#### Quick Deployment Steps

##### Step 1: Deploy Backend Service
1. **Create Web Service:**
   - Click "New +" → "Web Service"
   - Connect repository: Your GitHub repository
   - Branch: `development`
   - Root Directory: `backend`

2. **Service Configuration:**
   ```
   Name: multitenant-backend
   Environment: Python 3
   Build Command: pip install -r requirements.txt && python -m spacy download en_core_web_sm
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Set Environment Variables:**
   ```env
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   AWS_ACCESS_KEY_ID=your-aws-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret
   GROQ_API_KEY=your-groq-key
   SENDER_EMAIL=your-email@domain.com
   SENDER_PASSWORD=your-email-password
   ```

##### Step 2: Create PostgreSQL Database
1. **Create Database:**
   - Click "New +" → "PostgreSQL"
   - Name: `multitenant-db`
   - Free tier selected

2. **Connect to Backend:**
   - Database will auto-generate `DATABASE_URL`
   - Add to backend environment variables:
   ```env
   DATABASE_URL=<auto-generated>
   MANAGEMENT_DATABASE_URL=<same-as-above>
   ```

##### Step 3: Deploy Frontend
1. **Create Static Site:**
   - Click "New +" → "Static Site"
   - Same repository
   - Branch: `development`
   - Root Directory: `frontend`

2. **Build Configuration:**
   ```
   Build Command: npm install && npm run build
   Publish Directory: build
   ```

3. **Environment Variables:**
   ```env
   REACT_APP_API_URL=https://multitenant-backend.onrender.com
   CI=false
   ```

##### Step 4: Update CORS Settings
After both services are deployed, update backend environment variables:
```env
CORS_ORIGINS=https://multitenant-frontend.onrender.com
APP_URL=https://multitenant-frontend.onrender.com
```

### Free Tier Limits
- **Web Services**: 750 hours/month
- **Static Sites**: Unlimited
- **PostgreSQL**: 1GB storage, 90-day retention
- **Bandwidth**: 100GB/month
- **Build Time**: 90 minutes/month

## 🚀 Usage Guide

### 1. System Administration

#### Creating Your First Company
1. **Login as System Admin**: Use the system admin login
2. **Create Company**: Navigate to Companies → Create New Company
3. **Company Setup**: Enter company details (name, email, etc.)
4. **Automatic Setup**: System creates isolated database and S3 bucket
5. **Invite HR Admin**: Send invitation to company administrator

#### Managing Companies
- **View All Companies**: Dashboard shows all companies with statistics
- **Company Details**: Click on company to view detailed information
- **Delete Company**: Remove company and all associated data
- **System Analytics**: View system-wide statistics and health

### 2. Company Administration

#### HR Admin Setup
1. **Receive Invitation**: Check email for invitation link
2. **Set Password**: Create secure password
3. **Access Dashboard**: Login to company dashboard
4. **Invite Users**: Send invitations to employees and customers

#### User Management
- **Invite Users**: Send secure invitations with role assignment
- **Manage Roles**: Assign appropriate permissions to users
- **User Analytics**: View user activity and document statistics
- **Password Management**: Help users with password issues

### 3. Document Management

#### Uploading Documents
1. **Navigate to Documents**: Click Documents in sidebar
2. **Upload Files**: Drag & drop or click to select files
3. **AI Processing**: Documents are automatically analyzed
4. **View Metadata**: See extracted information and insights
5. **Organize**: Create folders and organize documents

#### Document Features
- **Search**: Find documents by content, title, or metadata
- **Filter**: Filter by type, date, user, or status
- **Preview**: View document content in browser
- **Download**: Download original or processed documents
- **Share**: Generate shareable links (if enabled)

### 4. AI Chatbot Assistant

#### Using the AI Assistant
1. **Navigate to AI Assistant**: Click AI Assistant in sidebar
2. **Ask Questions**: Type questions about your documents
3. **Get Responses**: AI provides context-aware answers
4. **View History**: Access previous conversations
5. **Document Integration**: AI can reference specific documents

#### AI Capabilities
- **Document Analysis**: Ask about document content and insights
- **Company Information**: Get information about company data
- **General Assistance**: Ask general questions and get help
- **Context Awareness**: AI understands your role and permissions

### 5. E-Signature System

#### Creating Signature Requests
1. **Select Document**: Choose document from document list
2. **Click E-Signature**: Use the e-signature integration button
3. **Add Recipients**: Enter recipient emails and names
4. **Configure Settings**: Set expiration and message
5. **Send Request**: Send signature request to recipients

#### Managing Signatures
- **Track Status**: Monitor signature request progress
- **Send Reminders**: Send follow-up emails to recipients
- **Download Signed**: Download completed documents
- **View Audit Trail**: See complete signing history

#### Role-Based E-Signature
- **System Admin**: Full access to all signature functions
- **HR Admin**: Company-wide signature management
- **HR Manager**: Department-level signature management
- **Employee**: Customer document signatures
- **Customer**: Sign documents they're recipients of

### 6. User Roles and Permissions

#### System Administrator
- **Full System Access**: Manage all companies and users
- **Company Creation**: Create and delete companies
- **System Analytics**: View system-wide statistics
- **Cross-Company Access**: Access any company's data

#### HR Administrator
- **Company Management**: Manage company users and settings
- **Document Access**: Access all company documents
- **E-Signature Management**: Full e-signature capabilities
- **User Invitations**: Invite and manage company users

#### HR Manager
- **Department Management**: Manage department users
- **Document Management**: Upload and manage documents
- **E-Signature**: Department-level signature management
- **Limited Analytics**: View department statistics

#### Employee
- **Personal Documents**: Upload and manage own documents
- **Customer Documents**: Access customer documents
- **E-Signature**: Sign documents they're recipients of
- **AI Chat**: Use AI assistant for document help

#### Customer
- **Own Documents**: View and manage own documents
- **Document Signing**: Sign documents they're recipients of
- **Limited Access**: Restricted to own data only

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login (system or company)
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user information
- `POST /api/auth/logout` - User logout

### Company Management (System Admin)
- `GET /api/companies` - List all companies
- `POST /api/companies` - Create new company
- `GET /api/companies/{id}` - Get company details
- `DELETE /api/companies/{id}` - Delete company

### User Management
- `POST /api/user-management/invite` - Invite new user
- `GET /api/user-management/users` - List company users
- `POST /api/user-management/setup-password` - Setup password from invitation
- `GET /api/user-management/invitations` - List pending invitations
- `GET /api/user-management/roles/list-all-roles` - List all roles
- `POST /api/user-management/roles/create-custom-role` - Create custom role
- `DELETE /api/user-management/roles/delete-custom-role/{role}` - Delete custom role
- `POST /api/user-management/roles/clone-role` - Clone existing role

### Document Management
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List documents (role-filtered)
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document
- `GET /api/documents/search` - Search documents

### AI Chatbot
- `POST /api/chat` - Send message to AI assistant
- `GET /api/chat/history` - Get chat history
- `POST /api/chat/system` - System admin chat (separate endpoint)

### E-Signature System
- `POST /api/esignature/create-request` - Create signature request
- `POST /api/esignature/{id}/send` - Send signature request
- `GET /api/esignature/list` - List signature requests
- `GET /api/esignature/{id}/status` - Get request status
- `POST /api/esignature/{id}/sign` - Sign document
- `POST /api/esignature/{id}/cancel` - Cancel request
- `GET /api/esignature/{id}/download-signed` - Download signed document
- `GET /api/esignature/permissions/my-role` - Get current user permissions
- `GET /api/esignature/permissions/all-roles` - Get all role permissions (admin)

### E-Signature Workflows
- `POST /api/esignature/workflow/contract-approval` - Contract approval workflow
- `POST /api/esignature/workflow/policy-acknowledgment` - Policy acknowledgment workflow
- `POST /api/esignature/workflow/budget-approval` - Budget approval workflow
- `POST /api/esignature/bulk-send` - Bulk signature requests
- `GET /api/esignature/audit-logs` - View audit logs

### System Administration
- `GET /api/system/status` - System health and statistics
- `GET /health` - Basic health check

### Full API Documentation
Visit `http://localhost:8000/docs` for interactive Swagger documentation with all endpoints, request/response schemas, and testing capabilities.

## 📁 Project Structure

```
multitenant-document-management/
├── backend/
│   ├── app/
│   │   ├── routers/          # API route handlers
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── companies.py  # Company management
│   │   │   ├── documents.py  # Document management
│   │   │   ├── chatbot.py    # AI chat endpoints
│   │   │   ├── esignature.py # E-signature endpoints
│   │   │   └── user_management.py # User management
│   │   ├── services/         # External service integrations
│   │   │   ├── aws_service.py # AWS S3 integration
│   │   │   ├── groq_service.py # Groq AI integration
│   │   │   ├── inkless_service.py # E-signature service
│   │   │   ├── email_service.py # Email service
│   │   │   ├── email_extensions.py # Extended email features
│   │   │   ├── database_manager.py # Multi-tenant database manager
│   │   │   └── nlp_service.py # Natural language processing
│   │   ├── utils/           # Utility functions
│   │   │   ├── permissions.py # Role-based permissions
│   │   │   ├── company_context.py # Company context routing
│   │   │   └── helpers.py   # Helper functions
│   │   ├── models.py        # Database models
│   │   ├── models_company.py # Company-specific models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── database.py      # Database configuration
│   │   ├── auth.py          # Authentication utilities
│   │   └── main.py          # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Backend Docker configuration
│   ├── create_admin.py     # Initial admin setup
│   ├── create_esignature_tables.py # E-signature setup
│   ├── initialize_dynamic_esignature.py # Dynamic e-signature initialization
│   ├── railway.toml        # Railway deployment config
│   └── nixpacks.toml       # Build configuration
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Auth/        # Authentication components
│   │   │   ├── Dashboard/   # Dashboard components
│   │   │   ├── Documents/   # Document management
│   │   │   ├── ESignature/  # E-signature components
│   │   │   ├── Chat/        # AI chatbot components
│   │   │   ├── Features/    # Feature components
│   │   │   └── Layout/      # Layout components
│   │   ├── services/        # API service functions
│   │   ├── utils/          # Utility functions
│   │   ├── App.js          # Main React component
│   │   └── index.js        # React entry point
│   ├── package.json        # Node.js dependencies
│   ├── Dockerfile         # Frontend Docker configuration
│   ├── railway.toml       # Railway deployment config
│   └── nixpacks.toml      # Build configuration
├── docker-compose.yml     # Multi-container configuration
├── railway.toml           # Monorepo Railway config
├── .env.example           # Environment variables template
└── README.md             # This comprehensive documentation
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check database credentials in .env file
# Ensure database exists and user has permissions

# For Neon database
# Verify NEON_API_KEY and NEON_PROJECT_ID are correct
```

#### 2. AWS S3 Permission Error
```bash
# Verify AWS credentials
aws s3 ls

# Check IAM permissions for S3
# Ensure bucket creation permissions
```

#### 3. AI Service Error
```bash
# Verify Groq API key
# Check GROQ_API_KEY in environment
# Ensure sufficient API credits
```

#### 4. Frontend Connection Error
```bash
# Check backend is running on port 8000
# Verify REACT_APP_API_URL in frontend .env
# Check CORS settings in backend
```

#### 5. E-Signature Issues
```bash
# Run e-signature setup scripts
python create_esignature_tables.py
python initialize_dynamic_esignature.py

# Check database tables exist
# Verify permissions are set correctly
```

#### 6. Email Service Issues
**Gmail "Less Secure Apps" Error:**
- Solution: Use App Password, not regular password

**SMTP Connection Timeout:**
- Solution: Check firewall, try different SMTP port (465 for SSL)

**Authentication Failed:**
- Solution: Verify email/password, enable 2FA for Gmail

**Emails Going to Spam:**
- Solution: Use company domain, configure SPF/DKIM records

#### 7. Missing Dependencies
```bash
# Install missing email validator dependency
pip install pydantic[email]

# Install missing dependencies
pip install email-validator
```

#### 8. Virtual Environment Issues
```bash
# If venv is corrupted, recreate it
# Remove corrupted virtual environment
Remove-Item -Recurse -Force venv

# Create new virtual environment
python -m venv venv

# Activate the new virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Performance Optimization

#### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_documents_company_id ON documents(company_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_chat_history_user_id ON chat_history(user_id);
```

#### File Upload Optimization
```python
# Increase file size limits in backend/app/config.py
MAX_FILE_SIZE = 104857600  # 100MB
```

#### AI Processing Optimization
```python
# Configure AI model in backend/app/config.py
GROQ_MODEL = "qwen/qwen3-32b"  # Fast and accurate
```

### Diagnostic Commands

#### System Initialization
```bash
# Initialize dynamic e-signature system
python backend/initialize_dynamic_esignature.py

# Check E-signature tables
python backend/create_esignature_tables.py

# Create system admin
python backend/create_admin.py
```

#### Health Checks
- Backend health: `http://localhost:8000/health`
- System status: `http://localhost:8000/api/system/status`
- Frontend: `http://localhost:3000`

#### Logs and Debugging
```bash
# Backend logs (if using Railway)
railway logs --service=backend

# Frontend logs (if using Railway)
railway logs --service=frontend

# Docker logs
docker-compose logs backend
docker-compose logs frontend
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

### Code Style
- **Backend**: Follow PEP 8 Python style guide
- **Frontend**: Use ESLint and Prettier
- **Documentation**: Update README for new features

### Testing
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **React** for the powerful UI library
- **Tailwind CSS** for the beautiful styling
- **Groq** for high-performance AI processing
- **Neon** for serverless PostgreSQL hosting
- **AWS** for scalable cloud infrastructure
- **Railway** for seamless deployment
- **Render** for free-tier hosting

---

**Built with ❤️ for modern document management**

## Quick Reference URLs

### Login URLs
- **Main Login**: `http://localhost:3000/login`
- **System Admin Login**: `http://localhost:3000/system-admin-login`
- **Company Login**: `http://localhost:3000/company-login`

### Setup URLs
- **User Registration**: `http://localhost:3000/register`
- **Password Setup**: `http://localhost:3000/setup-password/[unique-id]`
- **Company Registration**: `http://localhost:3000/companies/new`

### Dashboard URLs
- **Main Dashboard**: `http://localhost:3000/dashboard`
- **Companies Management**: `http://localhost:3000/companies`
- **User Management**: `http://localhost:3000/user-management`
- **Documents**: `http://localhost:3000/documents`
- **E-Signature**: `http://localhost:3000/esignature`
- **AI Assistant**: `http://localhost:3000/chat`