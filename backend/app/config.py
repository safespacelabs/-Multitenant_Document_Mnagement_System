import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Management Database Configuration (Neon)
MANAGEMENT_DATABASE_URL = os.getenv(
    "MANAGEMENT_DATABASE_URL", 
    "postgresql://multitenant-db_owner:npg_X7gKCTze2PAS@ep-lively-pond-a6gik9pf-pooler.us-west-2.aws.neon.tech/multitenant-db?sslmode=require&channel_binding=require"
)

# Legacy Database URL (for backward compatibility)
DATABASE_URL = os.getenv("DATABASE_URL", MANAGEMENT_DATABASE_URL)

# Neon API Configuration
NEON_API_KEY = os.getenv("NEON_API_KEY", "napi_4i48sb5ucqaiqkg60dct8bstompozmxnmfplr5cefr3x1qb6990p57kg17vuzt42")
NEON_PROJECT_ID = os.getenv("NEON_PROJECT_ID", "black-truth-25223398")  # Correct project ID from Neon Console

# If you're having issues with project ID extraction, you can temporarily hardcode it here:
# NEON_PROJECT_ID = "your-exact-project-id-from-neon-console"

# Database Pool Configuration
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))

# JWT Authentication
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-here-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-west-1")
AWS_S3_BUCKET_PREFIX = os.getenv("AWS_S3_BUCKET_PREFIX", "company-docs")

# Groq AI Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")

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

# Helper function to extract project ID from Neon database URL
def extract_neon_project_id(database_url: str) -> str:
    """Extract Neon project ID from database URL"""
    try:
        # Neon URLs typically contain the project ID in the host
        # Format: ep-{endpoint-name}-{project-id}-pooler.{region}.aws.neon.tech
        if "neon.tech" in database_url:
            host_part = database_url.split("@")[1].split("/")[0].split(":")[0]
            # Find the part that ends with '-pooler' and extract the 8-char ID before it
            if '-pooler.' in host_part:
                # Split by '-pooler.' and take the part before it
                before_pooler = host_part.split('-pooler.')[0]
                # The project ID is the last 8-character part
                parts = before_pooler.split('-')
                # Look for the last 8-character alphanumeric part
                for part in reversed(parts):
                    if len(part) == 8 and part.isalnum():
                        return part
    except Exception:
        pass
    return NEON_PROJECT_ID or ""

# Auto-extract project ID if not explicitly set
if not NEON_PROJECT_ID and not os.getenv("NEON_PROJECT_ID"):
    NEON_PROJECT_ID = extract_neon_project_id(MANAGEMENT_DATABASE_URL) 