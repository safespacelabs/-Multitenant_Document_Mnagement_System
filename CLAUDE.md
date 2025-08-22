# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-tenant document management system with AI-powered features, e-signature capabilities, and true database isolation. Each company gets its own PostgreSQL database and AWS S3 bucket for complete data separation.

## Commands

### Backend Development
```bash
cd backend
python3 -m venv venv  # Create virtual environment if needed
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt  # Install dependencies
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install  # Install dependencies
npm start
```

### Local Development Setup
```bash
# Prerequisites: PostgreSQL (Docker or local), Node.js, Python 3.8+

# 1. Start PostgreSQL (if using Docker)
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=pgadmin \
  -e POSTGRES_PASSWORD=pgadminappdb \
  -e POSTGRES_DB=document_management \
  postgres:14

# 2. Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your database credentials
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Frontend setup (new terminal)
cd frontend
npm install
npm start  # Runs on http://localhost:3000
```

### Docker Development
```bash
docker-compose up --build  # Build and run all services
docker-compose logs -f      # View logs
```

### Testing
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

### Build for Production
```bash
# Frontend build
cd frontend && npm run build

# Docker production build
docker-compose -f docker-compose.prod.yml up --build
```

## Architecture

### Multi-Tenant Database Architecture
- **Management Database**: Central registry at `app/models.py` containing companies table with database URLs
- **Company Databases**: Individual databases per company defined in `app/models_company.py`
- **Database Manager**: `app/services/database_manager.py` handles dynamic database connections and routing
- **Company Context**: `app/utils/company_context.py` automatically routes requests to correct company database

### API Structure
- **Routers**: All API endpoints in `backend/app/routers/` - each router handles specific domain (auth, documents, chatbot, etc.)
- **CRUD Operations**: Database operations in `backend/app/crud.py`
- **Schemas**: Pydantic models in `backend/app/schemas.py` for request/response validation
- **Services**: External integrations in `backend/app/services/` (AWS S3, Groq AI, Neon Database)

### Frontend Architecture
- **Component Structure**: Feature-based organization in `frontend/src/components/`
- **API Service**: All backend communication through `frontend/src/services/api.js`
- **Authentication**: JWT token management in `frontend/src/utils/auth.js`
- **Routing**: React Router v6 configuration in `frontend/src/App.js`

### Authentication Flow
1. JWT tokens issued by `backend/app/auth.py`
2. Two token types: system tokens (system admins) and company tokens (company users)
3. Role-based permissions enforced via `backend/app/utils/permissions.py`
4. Frontend stores tokens and includes in API requests

## Key Technical Decisions

### Database Strategy
- **Neon Database**: Using Neon's API to dynamically create/delete PostgreSQL databases
- **Connection Pooling**: SQLAlchemy sessions with proper lifecycle management
- **Migration Pattern**: Each company database gets same schema via `models_company.py`

### File Storage
- **AWS S3**: Each company gets dedicated bucket created via `aws_service.py`
- **Bucket Naming**: `company-{company_id}-documents`
- **Access Control**: Bucket-level isolation ensures data security

### AI Integration
- **Groq Service**: Using Qwen 3-32B model for document analysis and chat
- **Document Processing**: Automatic metadata extraction on upload
- **Context Management**: Chat maintains conversation history per company

### E-Signature System
- **Dynamic Tables**: Automatic creation for new companies via `initialize_dynamic_esignature.py`
- **Role Permissions**: Configurable permissions stored in database
- **Audit Trail**: Complete signing history with timestamps and IP tracking

## Development Guidelines

### Adding New Features
1. **API Endpoint**: Create router in `backend/app/routers/`
2. **Database Model**: Add to `models_company.py` for company-specific data
3. **Schema**: Define Pydantic models in `schemas.py`
4. **Frontend Component**: Add to appropriate directory in `frontend/src/components/`
5. **API Service**: Add functions to `frontend/src/services/api.js`

### Database Changes
1. Modify `models_company.py` for company database changes
2. Run initialization scripts to update existing databases
3. Consider backward compatibility for existing companies

### Adding New Roles
1. Update role enum in `backend/app/models_company.py`
2. Add permissions in `backend/app/utils/permissions.py`
3. Update frontend role checks in components
4. Test role-based access across all endpoints

## Environment Variables

### Backend (.env)
```
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/document_management
MANAGEMENT_DATABASE_URL=postgresql://user:password@localhost:5432/document_management

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment (development/production)
ENVIRONMENT=development

# AWS Configuration (Optional for local development)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# AI Services (Optional for local development)
GROQ_API_KEY=...
NEON_API_KEY=...
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
```

## CORS Configuration

### Environment-Based CORS
The application uses environment-aware CORS configuration:

- **Development Mode** (`ENVIRONMENT=development`):
  - Allows `http://localhost:3000`, `3001`, `8080` and `127.0.0.1` variants
  - Permits any localhost port for flexibility
  - Supports file:// protocol for testing

- **Production Mode** (`ENVIRONMENT=production`):
  - Only allows `https://multitenant-frontend.onrender.com`
  - Strict origin validation for security
  - Invalid origins receive 403 Forbidden (not mismatched headers)

### Testing CORS
```bash
# Test CORS configuration locally
curl -X OPTIONS "http://localhost:8000/api/documents/categories" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Test CORS in production
curl -X OPTIONS "https://multitenant-backend.onrender.com/api/companies" \
  -H "Origin: https://multitenant-frontend.onrender.com" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

## Production Deployment

### Critical Environment Variables for Production

**Backend Environment Variables (Render.com):**
```env
# CRITICAL: Must be set to "production" for correct CORS behavior
ENVIRONMENT=production

# Database (auto-generated by Render)
DATABASE_URL=postgresql://...
MANAGEMENT_DATABASE_URL=postgresql://... (same as DATABASE_URL)

# Security
SECRET_KEY=<use-openssl-rand-hex-32-to-generate>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS Configuration
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# AI Services
GROQ_API_KEY=...
NEON_API_KEY=...
NEON_PROJECT_ID=...

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=...
SENDER_PASSWORD=...
SENDER_NAME=Document Management System

# Application
APP_URL=https://multitenant-frontend.onrender.com

# Feature Flags
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_DOCUMENT_NOTIFICATIONS=true
ENABLE_ESIGNATURE_NOTIFICATIONS=true
```

**Frontend Environment Variables (Render.com):**
```env
REACT_APP_API_URL=https://multitenant-backend.onrender.com
CI=false
```

### Deployment Checklist

1. **Before Deployment:**
   - [ ] Generate strong SECRET_KEY using `openssl rand -hex 32`
   - [ ] Obtain all API keys (AWS, Groq, Neon)
   - [ ] Set up email credentials (use App Password for Gmail)
   - [ ] Commit latest changes to repository

2. **Backend Deployment:**
   - [ ] Set `ENVIRONMENT=production` in environment variables
   - [ ] Configure all required environment variables
   - [ ] Deploy backend service
   - [ ] Verify health endpoint: `https://your-backend.onrender.com/health`

3. **Frontend Deployment:**
   - [ ] Set `REACT_APP_API_URL` to backend URL
   - [ ] Set `CI=false` to prevent build warnings from failing
   - [ ] Deploy frontend static site
   - [ ] Verify frontend loads correctly

4. **Post-Deployment:**
   - [ ] Initialize system admin: `POST /init-admin`
   - [ ] Test CORS with curl command
   - [ ] Verify login functionality
   - [ ] Test document upload
   - [ ] Check email notifications

### Common Production Issues

**CORS Errors:**
- **Cause**: `ENVIRONMENT` not set to `production` or set incorrectly
- **Fix**: Set `ENVIRONMENT=production` in backend environment variables and restart service

**Database Connection Failed:**
- **Cause**: Missing or incorrect database URLs
- **Fix**: Ensure both `DATABASE_URL` and `MANAGEMENT_DATABASE_URL` are set

**Authentication Issues:**
- **Cause**: SECRET_KEY mismatch or not set
- **Fix**: Ensure SECRET_KEY is set and consistent across deployments

## Common Workflows

### Creating New Company
1. System admin logs in
2. POST to `/api/companies/` creates Neon database and S3 bucket
3. Database URL stored in management database
4. Company admin user created with credentials

### Document Upload Flow
1. File uploaded to S3 via `/api/documents/upload`
2. Groq AI processes document for metadata
3. Document record created with extracted data
4. File retrievable via presigned S3 URLs

### Multi-Tenant Request Flow
1. JWT token includes company_id
2. `company_context.py` extracts company_id
3. `database_manager.py` gets correct database connection
4. CRUD operations execute on company-specific database

## Debugging Tips

### Database Connection Issues
- Check Neon database status in dashboard
- Verify DATABASE_URL in management database companies table
- Check `database_manager.py` connection pool status

### Authentication Problems
- Verify JWT token includes correct company_id
- Check role permissions in `permissions.py`
- Ensure frontend includes token in Authorization header

### File Upload Issues
- Verify AWS credentials and bucket permissions
- Check S3 bucket naming convention
- Ensure file size limits in both frontend and backend

### CORS Issues
- Check `ENVIRONMENT` variable in backend/.env (development/production)
- Verify frontend URL is in allowed origins list
- For local development, use http://localhost:3000 (not file://)
- Test with: `curl -X OPTIONS http://localhost:8000/api/endpoint -H "Origin: http://localhost:3000" -v`

## Dependencies & Compatibility

### Python Dependencies
- Python 3.8+ required (3.11+ recommended)
- Key packages: FastAPI, SQLAlchemy, Pydantic, psycopg2, boto3, spacy
- For spacy: Run `python -m spacy download en_core_web_sm` after installation
- If issues with psycopg2-binary, install PostgreSQL locally first

### Frontend Dependencies
- Node.js 16+ and npm 8+
- React 18 with TypeScript
- Key packages: React Router v6, Axios, Material-UI

## Testing Approach

### Backend Testing
- Use pytest with async support for FastAPI
- Mock external services (Groq, AWS, Neon)
- Test multi-tenant isolation explicitly

### Frontend Testing
- Component testing with React Testing Library
- Mock API responses in tests
- Test role-based UI rendering
- 1. Set the ENVIRONMENT variable on your Render backend:
    - Go to your Render backend service dashboard
    - Add environment variable: ENVIRONMENT=production
    - This ensures the backend knows it's in production mode
  2. Deploy the updated code:
    - Commit and push the changes
    - Render will automatically redeploy

  The fix ensures that:
  - In production mode, only https://multitenant-frontend.onrender.com is allowed
  - Invalid origins get rejected with a 403 instead of returning mismatched headers
  - The CORS configuration properly distinguishes between development and production environments