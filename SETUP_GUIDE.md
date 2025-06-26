# Environment Configuration Setup Guide

This guide will help you set up all the required environment variables and credentials for the Multi-Tenant Document Management System.

## 📋 Prerequisites

Before setting up the environment variables, make sure you have:

1. **PostgreSQL Database** - Running locally or cloud-hosted
2. **AWS Account** - For S3 file storage
3. **Anthropic API Key** - For AI-powered document processing
4. **Node.js & npm** - For the frontend
5. **Python 3.11+** - For the backend

## 🔧 Environment Files Setup

### 1. Backend Environment (.env)

Copy the `backend/env.example` to `backend/.env` and fill in your credentials:

```bash
cd backend
cp env.example .env
```

#### Required Configurations:

**Database Configuration:**
```env
DATABASE_URL=postgresql://username:password@localhost:5432/multitenant_db
```

**JWT Authentication:**
```env
SECRET_KEY=your-super-secret-jwt-key-here-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**AWS S3 Configuration:**
```env
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
```

**Anthropic AI Configuration:**
```env
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### 2. Frontend Environment (.env)

Copy the `frontend/env.example` to `frontend/.env`:

```bash
cd frontend
cp env.example .env
```

**Required Configuration:**
```env
REACT_APP_API_URL=http://localhost:8000
```

### 3. Docker Compose Environment (.env)

Copy the root `env.example` to `.env`:

```bash
cp env.example .env
```

## 🔑 Getting Your Credentials

### 1. PostgreSQL Database

**Local Setup:**
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE multitenant_db;
CREATE USER docuser WITH PASSWORD 'your-secure-db-password';
GRANT ALL PRIVILEGES ON DATABASE multitenant_db TO docuser;
\q
```

**Cloud Options:**
- AWS RDS
- Google Cloud SQL
- Heroku Postgres
- ElephantSQL

### 2. AWS S3 Setup

1. **Create IAM User:**
   - Go to AWS IAM Console
   - Create new user with programmatic access
   - Attach policy: `AmazonS3FullAccess`
   - Save Access Key ID and Secret Access Key

2. **S3 Permissions Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:DeleteBucket",
                "s3:GetBucketLocation",
                "s3:ListBucket",
                "s3:ListAllMyBuckets"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:PutObjectTagging",
                "s3:GetObjectTagging"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up/Log in
3. Navigate to API Keys
4. Create new API key
5. Copy the key (starts with `sk-ant-`)

### 4. JWT Secret Key Generation

Generate a secure secret key:

```bash
# Using OpenSSL
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

## 🚀 Running the Application

### Development Mode

1. **Start Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start Frontend:**
```bash
cd frontend
npm install
npm start
```

### Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

## 🔍 Environment Variables Reference

### Backend Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | ✅ | JWT signing key | `abc123...` |
| `AWS_ACCESS_KEY_ID` | ✅ | AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | ✅ | AWS secret key | `xyz...` |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key | `sk-ant-...` |
| `AWS_REGION` | ⚠️ | AWS region | `us-east-1` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ⚠️ | Token expiry time | `30` |
| `DEBUG` | ⚠️ | Debug mode | `False` |

### Frontend Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `REACT_APP_API_URL` | ✅ | Backend API URL | `http://localhost:8000` |
| `REACT_APP_NAME` | ⚠️ | Application name | `Doc Management` |
| `REACT_APP_MAX_FILE_SIZE` | ⚠️ | Max upload size (bytes) | `10485760` |

### Docker Compose Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `POSTGRES_DB` | ✅ | Database name | `multitenant_db` |
| `POSTGRES_USER` | ✅ | Database user | `docuser` |
| `POSTGRES_PASSWORD` | ✅ | Database password | `secure-password` |
| `BACKEND_PORT` | ⚠️ | Backend port | `8000` |
| `FRONTEND_PORT` | ⚠️ | Frontend port | `3000` |

**Legend:**
- ✅ Required
- ⚠️ Optional (has default)

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection Failed:**
   - Check if PostgreSQL is running
   - Verify connection string format
   - Ensure database exists

2. **AWS S3 Access Denied:**
   - Verify IAM user permissions
   - Check AWS credentials
   - Ensure bucket policy is correct

3. **Anthropic API Errors:**
   - Verify API key is valid
   - Check account credits/limits
   - Ensure API key starts with `sk-ant-`

4. **Frontend Can't Connect to Backend:**
   - Check if backend is running on correct port
   - Verify CORS settings
   - Check `REACT_APP_API_URL` value

### Logs and Debugging

```bash
# Backend logs
cd backend
python -m uvicorn app.main:app --log-level debug

# Docker logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

## 🔒 Security Best Practices

1. **Never commit .env files to version control**
2. **Use strong, unique passwords**
3. **Rotate API keys regularly**
4. **Use environment-specific configurations**
5. **Enable SSL/TLS in production**
6. **Set up proper firewall rules**
7. **Use IAM roles instead of root credentials**

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Anthropic API Documentation](https://docs.anthropic.com/)

## 🆘 Support

If you encounter issues:

1. Check the logs for error messages
2. Verify all environment variables are set correctly
3. Ensure all services are running
4. Check firewall and network settings
5. Review the troubleshooting section above

For additional help, please create an issue in the project repository. 