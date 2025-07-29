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

### 🔐 E-Signature System
- **Complete Digital Signatures**: Full e-signature workflow with Inkless integration
- **Role-Based Permissions**: Different signing capabilities per user role
- **Workflow Templates**: Pre-built templates for common use cases
- **Audit Trail**: Complete signing history with IP tracking
- **Bulk Operations**: Send signature requests to multiple recipients
- **Document Integration**: Direct e-signature from document management
- **Status Tracking**: Real-time signature request status

### 👥 User Management & Roles
- **Multi-Level Role System**: System Admin, HR Admin, HR Manager, Employee, Customer
- **Invitation System**: Secure user invitation with email verification
- **Password Management**: Strong password requirements and secure setup
- **Permission Matrix**: Granular permissions for each role
- **Company Isolation**: Users only access their company's data
- **Profile Management**: User profile and settings management

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
- **Vercel** - Frontend deployment platform

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

# Application
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://frontend:3000
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

# Run database migrations
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
│   │   │   └── nlp_service.py # Natural language processing
│   │   ├── utils/           # Utility functions
│   │   │   ├── permissions.py # Role-based permissions
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
│   └── initialize_dynamic_esignature.py # E-signature initialization
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
│   └── Dockerfile         # Frontend Docker configuration
├── docker-compose.yml     # Multi-container configuration
├── .env.example           # Environment variables template
└── README.md             # This file
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

---

**Built with ❤️ for modern document management** 



Here are all the user-related URLs in your system:
Login: http://localhost:3000/login
Register: http://localhost:3000/register
Password Setup: http://localhost:3000/setup-password/[unique-id]
Dashboard: http://localhost:3000/dashboard
Companies: http://localhost:3000/companies
Company Registration: http://localhost:3000/companies/new