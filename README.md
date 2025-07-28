# Multi-Tenant Document Management System

🚀 A modern, AI-powered document management system with multi-tenant architecture, built with FastAPI and React.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Local Development Setup](#local-development-setup)
- [Docker Setup](#docker-setup)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🏢 Multi-Tenant Architecture
- **Company Isolation**: Each company has its own data space
- **AWS S3 Integration**: Automatic bucket creation per company
- **Role-Based Access**: Admin and Employee roles with different permissions

### 📄 Document Management
- **File Upload**: Drag & drop interface with progress tracking
- **AI Processing**: Automatic document analysis using Anthropic Claude
- **Metadata Extraction**: Title, summary, topics, entities, and more
- **Search & Chat**: AI-powered document search and chat interface

### 🔐 Security & Authentication
- **JWT Authentication**: Secure token-based authentication
- **Password Validation**: Strong password requirements
- **Multi-Factor Ready**: Extensible for MFA implementation

### 🎨 Modern UI/UX
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Tailwind CSS**: Beautiful, modern interface
- **Real-time Updates**: Live document processing status
- **Dark Mode Ready**: Prepared for theme switching

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **SQLAlchemy** - ORM and database toolkit
- **Anthropic Claude** - AI document processing
- **AWS S3** - File storage
- **JWT** - Authentication tokens
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI framework
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icons
- **Axios** - HTTP client

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Production web server
- **Redis** - Caching (optional)

## 📋 Prerequisites

### For Local Development
- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL 14+**
- **Git**

### For Docker Setup
- **Docker** 20.10+
- **Docker Compose** 2.0+

### External Services
- **AWS Account** with S3 access
- **Anthropic API Key** for Claude AI

## 🔧 Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/multitenant-document-management.git
cd multitenant-document-management
```

### 2. Set Up Environment Variables

Copy the example environment files:
```bash
# Backend environment
cp backend/env.example backend/.env

# Frontend environment
cp frontend/env.example frontend/.env

# Docker Compose environment
cp env.example .env
```

### 3. Configure Environment Variables

#### Backend Configuration (`backend/.env`)
```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/multitenant_db

# JWT Authentication
SECRET_KEY=your-super-secret-jwt-key-here-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-west-1

# Anthropic AI
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

#### Frontend Configuration (`frontend/.env`)
```env
REACT_APP_API_URL=http://localhost:8000
```

#### Docker Configuration (`.env`)
```env
# Database
POSTGRES_DB=multitenant_db
POSTGRES_USER=docuser
POSTGRES_PASSWORD=your-secure-db-password

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
DB_PORT=5432
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

Install and start PostgreSQL:
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

# Download spaCy model
python -m spacy download en_core_web_sm

# Run database migrations (if using Alembic)
# alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at `http://localhost:3000`

### 4. Verify Setup

1. Open `http://localhost:3000` in your browser
2. You should see the company selection page
3. API documentation available at `http://localhost:8000/docs`

## 🐳 Docker Setup

### 1. Environment Variables

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

### 3. Access the Application

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Database**: `localhost:5432`

### 4. Docker Commands

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

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Clean up
docker-compose down -v  # Remove volumes
docker system prune     # Clean up unused containers/images
```

## 🚀 Usage

### 1. Company Registration

1. Visit the application homepage
2. Click "Register New Company"
3. Fill in company details
4. AWS S3 bucket will be created automatically
5. You'll be redirected to create your admin account

### 2. User Management

**As an Admin:**
- Register new employees
- Manage user roles and permissions
- View company statistics
- Access all company documents

**As an Employee:**
- Upload and manage personal documents
- Chat with AI assistant about documents
- View document analytics

### 3. Document Upload

1. Go to the Documents section
2. Drag & drop files or click to select
3. Supported formats: PDF, DOCX, TXT, MD, CSV, XLSX
4. AI processing will extract metadata automatically

### 4. AI Chat Assistant

1. Navigate to AI Assistant
2. Ask questions about your documents
3. Get intelligent responses based on document content
4. View chat history

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user

### Company Endpoints
- `GET /api/companies` - List all companies
- `POST /api/companies` - Create new company
- `GET /api/companies/{id}` - Get company details

### Document Endpoints
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List user documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document

### Chat Endpoints
- `POST /api/chat` - Send message to AI
- `GET /api/chat/history` - Get chat history

### Full API Documentation
Visit `http://localhost:8000/docs` for interactive Swagger documentation.

## 📁 Project Structure

```
multitenant-document-management/
├── backend/
│   ├── app/
│   │   ├── routers/          # API route handlers
│   │   ├── services/         # External service integrations
│   │   ├── utils/           # Utility functions
│   │   ├──         # Database models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── database.py      # Database configuration
│   │   ├── auth.py          # Authentication utilities
│   │   └── main.py          # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Backend Docker configuration
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
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
```

#### 2. AWS S3 Permission Error
```bash
# Verify AWS credentials
aws s3 ls

# Check IAM permissions for S3 operations
# Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are correct
```

#### 3. Anthropic API Error
```bash
# Verify API key is valid
# Check API key starts with 'sk-ant-'
# Ensure you have sufficient credits
```

#### 4. Frontend Build Error
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### 5. Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up

# Check container logs
docker-compose logs backend
docker-compose logs frontend
```

### Environment-Specific Issues

#### Development Environment
- Ensure all services are running on correct ports
- Check firewall settings
- Verify Python virtual environment is activated

#### Production Environment
- Check Nginx configuration
- Verify SSL certificates
- Monitor resource usage
- Check application logs

### Getting Help

1. Check the [Issues](https://github.com/your-username/multitenant-document-management/issues) page
2. Search existing issues for similar problems
3. Create a new issue with:
   - Detailed error description
   - Steps to reproduce
   - Environment information
   - Log files (remove sensitive data)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

### 1. Development Setup
```bash
# Fork the repository
git clone https://github.com/your-username/multitenant-document-management.git
cd multitenant-document-management

# Create a new branch
git checkout -b feature/your-feature-name

# Make your changes
# Add tests for new features
# Update documentation
```

### 2. Code Standards

#### Backend (Python)
- Follow PEP 8 style guidelines
- Use type hints
- Write docstrings for functions
- Add unit tests with pytest

#### Frontend (React)
- Use functional components with hooks
- Follow ESLint configuration
- Write component tests with Jest
- Use Tailwind CSS for styling

### 3. Commit Guidelines
```bash
# Use conventional commit format
git commit -m "feat: add document sharing feature"
git commit -m "fix: resolve authentication bug"
git commit -m "docs: update API documentation"
```

### 4. Pull Request Process
1. Update documentation
2. Add tests for new features
3. Ensure all tests pass
4. Submit pull request with clear description
5. Respond to code review feedback

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing Python web framework
- [React](https://reactjs.org/) for the frontend framework
- [Tailwind CSS](https://tailwindcss.com/) for the utility-first CSS framework
- [Anthropic](https://www.anthropic.com/) for the Claude AI API
- [Lucide](https://lucide.dev/) for the beautiful icons

## 📞 Support

For support and questions:
- 📧 Email: support@yourcompany.com
- 💬 Discord: [Join our server](https://discord.gg/your-server)
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/multitenant-document-management/issues)

---

**Made with ❤️ by [Your Team Name]** 



Here are all the user-related URLs in your system:
Login: http://localhost:3000/login
Register: http://localhost:3000/register
Password Setup: http://localhost:3000/setup-password/[unique-id]
Dashboard: http://localhost:3000/dashboard
Companies: http://localhost:3000/companies
Company Registration: http://localhost:3000/companies/new