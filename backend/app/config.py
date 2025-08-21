"""
Enhanced configuration with email service settings and original constants
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Original configuration constants for backward compatibility
MANAGEMENT_DATABASE_URL = os.getenv("MANAGEMENT_DATABASE_URL", "postgresql://postgres:password@localhost:5432/document_management")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/document_management")

# Database connection settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# AI Service Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")

# Neon Database Configuration
NEON_API_KEY = os.getenv("NEON_API_KEY", "")
NEON_PROJECT_ID = os.getenv("NEON_PROJECT_ID", "")

# Email Service Configuration (NEW)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@yourcompany.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
SENDER_NAME = os.getenv("SENDER_NAME", "Document Management System")

# Application settings
APP_URL = os.getenv("APP_URL", "http://localhost:3000")

# Feature flags for email notifications (NEW)
ENABLE_EMAIL_NOTIFICATIONS = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() == "true"
ENABLE_DOCUMENT_NOTIFICATIONS = os.getenv("ENABLE_DOCUMENT_NOTIFICATIONS", "true").lower() == "true"
ENABLE_ESIGNATURE_NOTIFICATIONS = os.getenv("ENABLE_ESIGNATURE_NOTIFICATIONS", "true").lower() == "true"

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DEVELOPMENT = ENVIRONMENT == "development"

# Debug environment detection
print(f"🔍 Environment detection: ENVIRONMENT={ENVIRONMENT}, IS_PRODUCTION={IS_PRODUCTION}, IS_DEVELOPMENT={IS_DEVELOPMENT}")

# CORS origins function
def get_cors_origins():
    """Get CORS origins from environment variable"""
    # Get from environment variable first (highest priority)
    origins_str = os.getenv("CORS_ORIGINS", "")
    
    if origins_str:
        # Parse environment variable and clean up origins
        custom_origins = []
        for origin in origins_str.split(","):
            cleaned_origin = origin.strip()
            # Remove trailing slash if present
            if cleaned_origin.endswith('/'):
                cleaned_origin = cleaned_origin.rstrip('/')
            if cleaned_origin:  # Only add non-empty origins
                custom_origins.append(cleaned_origin)
        
        print(f"🔧 CORS Origins from environment variable: {custom_origins}")
        return custom_origins
    
    # Environment-specific origins (fallback)
    if IS_PRODUCTION:
        default_origins = [
            "https://multitenant-frontend.onrender.com"
        ]
        print(f"🔧 Using production CORS origins: {default_origins}")
    else:
        # Development/local origins
        default_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",  # Alternative port
            "http://127.0.0.1:3001",
            "http://localhost:8080",  # Test server
            "http://127.0.0.1:8080"
        ]
        print(f"🔧 Using development CORS origins: {default_origins}")
    
    return default_origins

# Settings class for new structured approach (optional)
class Settings:
    def __init__(self):
        # Database settings
        self.DATABASE_URL = DATABASE_URL
        self.MANAGEMENT_DATABASE_URL = MANAGEMENT_DATABASE_URL
        
        # Email settings
        self.SMTP_SERVER = SMTP_SERVER
        self.SMTP_PORT = SMTP_PORT
        self.SENDER_EMAIL = SENDER_EMAIL
        self.SENDER_PASSWORD = SENDER_PASSWORD
        self.SENDER_NAME = SENDER_NAME
        
        # Application settings
        self.APP_URL = APP_URL
        self.SECRET_KEY = SECRET_KEY
        
        # AWS settings
        self.AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
        self.AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
        self.AWS_REGION = AWS_REGION
        
        # Feature flags
        self.ENABLE_EMAIL_NOTIFICATIONS = ENABLE_EMAIL_NOTIFICATIONS
        self.ENABLE_DOCUMENT_NOTIFICATIONS = ENABLE_DOCUMENT_NOTIFICATIONS
        self.ENABLE_ESIGNATURE_NOTIFICATIONS = ENABLE_ESIGNATURE_NOTIFICATIONS

settings = Settings()