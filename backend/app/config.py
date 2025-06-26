import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/multitenant_db")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))

# JWT Authentication
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-here-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_S3_BUCKET_PREFIX = os.getenv("AWS_S3_BUCKET_PREFIX", "company-docs")

# Anthropic AI Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Application Configuration
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://frontend:3000").split(",")

# File Upload Settings
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "pdf,docx,txt,md,csv,xlsx").split(",")

# Helper function to get allowed file extensions
def get_allowed_extensions() -> List[str]:
    return [ext.strip().lower() for ext in ALLOWED_FILE_TYPES]

# Helper function to check if file size is allowed
def is_file_size_allowed(file_size: int) -> bool:
    return file_size <= MAX_FILE_SIZE

# Helper function to get CORS origins as list
def get_cors_origins() -> List[str]:
    return [origin.strip() for origin in CORS_ORIGINS] 