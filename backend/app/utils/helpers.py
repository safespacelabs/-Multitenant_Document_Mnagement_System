import re
import uuid
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import secrets

def generate_unique_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix"""
    unique_id = uuid.uuid4().hex[:12]
    return f"{prefix}_{unique_id}" if prefix else unique_id

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Limit length
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = f"{name[:95]}.{ext}" if ext else name[:100]
    
    return filename

def generate_s3_key(user_id: str, filename: str) -> str:
    """Generate S3 key for file storage"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    sanitized_filename = sanitize_filename(filename)
    unique_id = uuid.uuid4().hex[:8]
    return f"users/{user_id}/{timestamp}_{unique_id}_{sanitized_filename}"

def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA-256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def generate_api_key() -> str:
    """Generate secure API key"""
    return secrets.token_urlsafe(32)

def is_allowed_file_type(filename: str, allowed_extensions: list) -> bool:
    """Check if file type is allowed"""
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in [ext.lower() for ext in allowed_extensions]

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

class TokenGenerator:
    """Generate various types of tokens"""
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate password reset token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate email verification token"""
        return secrets.token_urlsafe(24)
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate session ID"""
        return secrets.token_urlsafe(16) 