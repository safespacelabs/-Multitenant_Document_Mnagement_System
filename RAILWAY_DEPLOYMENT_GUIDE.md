# Railway Deployment Guide

This guide will help you deploy your Multi-Tenant Document Management System to Railway.

## Prerequisites

1. Railway account (sign up at [railway.app](https://railway.app))
2. GitHub repository with your code
3. Database credentials (Neon PostgreSQL or Railway PostgreSQL)
4. AWS credentials for S3 storage
5. Groq API key for AI features
6. Email service credentials (Gmail/SMTP)

## Deployment Steps

### 1. Prepare Your Repository

Ensure all Railway configuration files are in place:
- `railway.toml` (root level - for monorepo)
- `backend/railway.toml` (backend service config)
- `frontend/railway.toml` (frontend service config)
- `backend/nixpacks.toml` (build configuration)
- `frontend/nixpacks.toml` (build configuration)

### 2. Deploy Backend Service

1. **Connect to Railway:**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   ```

2. **Create Backend Service:**
   ```bash
   # Navigate to project root
   cd multitenant-document-management
   
   # Create new Railway project
   railway create multitenant-backend
   
   # Deploy backend from backend directory
   cd backend
   railway up
   ```

3. **Set Environment Variables:**
   Go to Railway dashboard → Your Project → Backend Service → Variables
   
   Add these variables (use `railway-env-template.txt` as reference):
   ```
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

### 3. Deploy Frontend Service

1. **Create Frontend Service:**
   ```bash
   # From project root
   cd frontend
   railway create multitenant-frontend
   railway up
   ```

2. **Set Environment Variables:**
   ```
   REACT_APP_API_URL=https://your-backend-service.railway.app
   PORT=3000
   CI=false
   ```

### 4. Update CORS Configuration

After both services are deployed:

1. Get your frontend URL: `https://your-frontend.railway.app`
2. Update backend environment variables:
   ```
   APP_URL=https://your-frontend.railway.app
   CORS_ORIGINS=https://your-frontend.railway.app
   ```

### 5. Database Setup Options

#### Option A: Use Railway PostgreSQL
1. Add PostgreSQL service in Railway dashboard
2. Copy the DATABASE_URL from Railway PostgreSQL service
3. Update both DATABASE_URL and MANAGEMENT_DATABASE_URL

#### Option B: Continue with Neon
1. Keep your existing Neon database URLs
2. Ensure Neon allows connections from Railway IPs

### 6. Domain Configuration (Optional)

1. **Custom Domain for Frontend:**
   - Railway Dashboard → Frontend Service → Settings → Domains
   - Add your custom domain

2. **Custom Domain for Backend:**
   - Railway Dashboard → Backend Service → Settings → Domains
   - Add your API domain (e.g., api.yourdomain.com)

## Environment Variables Reference

### Backend Service Variables
```env
# Required
DATABASE_URL=postgresql://user:pass@host:port/db
MANAGEMENT_DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-secret-key-here
PORT=8000

# AWS (Required for file storage)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1

# AI Services (Required for chatbot)
GROQ_API_KEY=your-groq-api-key

# Email (Required for notifications)
SENDER_EMAIL=your-email@domain.com
SENDER_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# CORS (Update after frontend deployment)
CORS_ORIGINS=https://your-frontend.railway.app
APP_URL=https://your-frontend.railway.app
```

### Frontend Service Variables
```env
REACT_APP_API_URL=https://your-backend.railway.app
PORT=3000
CI=false
GENERATE_SOURCEMAP=false
```

## Troubleshooting

### Common Issues

1. **Build Failures:**
   - Check Nixpacks configuration
   - Verify all dependencies in requirements.txt/package.json

2. **Database Connection:**
   - Verify DATABASE_URL format
   - Check database credentials
   - Ensure database allows external connections

3. **CORS Errors:**
   - Update CORS_ORIGINS after frontend deployment
   - Ensure both services are deployed and URLs are correct

4. **Environment Variables:**
   - Double-check all required variables are set
   - Verify sensitive data like API keys

### Logs and Debugging

```bash
# View backend logs
railway logs --service=backend

# View frontend logs  
railway logs --service=frontend
```

### Health Checks

- Backend health: `https://your-backend.railway.app/health`
- Frontend: `https://your-frontend.railway.app`

## Post-Deployment

1. Test all functionality:
   - User registration/login
   - Document upload
   - AI chatbot
   - Email notifications
   - E-signature features

2. Set up monitoring and alerts in Railway dashboard

3. Configure backup strategies for your database

4. Update DNS records if using custom domains

## Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- GitHub Issues: Create issues in your repository

## Security Notes

- Use environment variables for all sensitive data
- Regularly rotate API keys and passwords  
- Enable Railway's security features
- Use HTTPS for all connections
- Implement proper CORS policies