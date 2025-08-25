from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app.database import get_management_db
from app.services.database_manager import db_manager
from app import models
from app.routers import auth, companies, users, documents, chatbot, user_management, esignature
from app.config import get_cors_origins, ENVIRONMENT, IS_DEVELOPMENT, IS_PRODUCTION

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Multi-Tenant Document Management System")
    
    # Create management database tables
    print("📊 Creating management database tables...")
    models.Base.metadata.create_all(bind=db_manager.management_engine)
    
    yield
    # Shutdown
    print("🛑 Shutting down...")

app = FastAPI(
    title="Multi-Tenant Document Management System",
    description="AI-powered document management with true database isolation",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware - environment-aware configuration
cors_origins = get_cors_origins()
print(f"🚀 Running in {ENVIRONMENT} mode")

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Add custom middleware to ensure CORS headers are always present
@app.middleware("http")
async def ensure_cors_headers(request, call_next):
    """Ensure CORS headers are present in all responses - Production only for Render"""
    origin = request.headers.get("origin", "")
    method = request.method
    path = request.url.path
    
    print(f"🔍 CORS Middleware - Method: {method}, Path: {path}")
    print(f"🔍 CORS Middleware - Origin: {origin}, Environment: {ENVIRONMENT}, IS_PRODUCTION: {IS_PRODUCTION}")
    print(f"🔍 Allowed CORS origins: {cors_origins}")
    
    # Handle preflight requests
    if method == "OPTIONS":
        print(f"🚀 Handling OPTIONS preflight request for path: {path}")
        # Always allow preflight for production
        if IS_PRODUCTION:
            allowed_origin = origin if origin in cors_origins else "https://multitenant-frontend.onrender.com"
            print(f"✅ Preflight: Production mode - allowing origin {allowed_origin}")
        else:
            # Check if origin is allowed
            if origin in cors_origins:
                allowed_origin = origin
                print(f"✅ Preflight: Origin {origin} is in allowed CORS origins")
            else:
                # Origin not allowed
                print(f"❌ Preflight: Origin {origin} not in allowed origins")
                allowed_origin = cors_origins[0] if cors_origins else "https://multitenant-frontend.onrender.com"
            
        headers = {
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600"
        }
        print(f"📤 Sending preflight response with headers: {headers}")
        return Response(content="", status_code=200, headers=headers)
    
    response = await call_next(request)
    
    # Ensure CORS headers are present for actual requests
    if IS_PRODUCTION:
        # Production mode - always set CORS headers
        if origin in cors_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = "https://multitenant-frontend.onrender.com"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        print(f"✅ Production mode: set CORS headers for origin {origin}")
    elif origin in cors_origins:
        # Origin is explicitly allowed
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        print(f"✅ Added CORS headers for origin {origin}")
    else:
        # Origin not allowed or development mode
        print(f"❌ Not setting CORS headers for origin: '{origin}'")
    
    print(f"📤 Final response headers: {dict(response.headers)}")
    return response

# Test endpoint to verify CORS is working
@app.get("/api/test-cors")
async def test_cors():
    """Test endpoint to verify CORS is working"""
    return {"message": "CORS test successful", "timestamp": "2024-01-01T00:00:00Z"}

# Security
security = HTTPBearer()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "Backend is running"}

# Test endpoint for CORS verification
@app.get("/test-cors")
async def test_cors():
    """Test endpoint for CORS verification"""
    return {
        "message": "CORS is working", 
        "timestamp": "2024-01-01T00:00:00Z",
        "environment": ENVIRONMENT,
        "is_production": IS_PRODUCTION,
        "cors_origins": cors_origins,
        "env_vars": {
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "NOT_SET"),
            "CORS_ORIGINS": os.getenv("CORS_ORIGINS", "NOT_SET"),
            "NODE_ENV": os.getenv("NODE_ENV", "NOT_SET")
        }
    }

# Test authentication endpoint
@app.get("/test-auth")
async def test_auth():
    """Test authentication endpoint - returns mock user data for testing"""
    return {
        "message": "Authentication test successful",
        "user": {
            "id": "test-user-123",
            "username": "testuser",
            "role": "hr_admin",
            "company_id": "test-company-456"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Test login endpoint for debugging
@app.post("/test-login")
async def test_login():
    """Test login endpoint - returns real JWT authentication data for testing"""
    from app.auth import create_access_token
    
    # Create a real JWT token for testing
    test_user_data = {
        "sub": "testuser",
        "username": "testuser",
        "role": "hr_admin",
        "company_id": "test-company-456"
    }
    
    # Create real access token
    access_token = create_access_token(data=test_user_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": "test-user-123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "hr_admin",
            "company_id": "test-company-456",
            "is_active": True
        },
        "company": {
            "id": "test-company-456",
            "name": "Test Company",
            "database_url": "postgresql://test:test@localhost:5432/testdb"
        }
    }

# Test document endpoints (no authentication required)
@app.get("/test-documents/categories")
async def test_document_categories():
    """Test endpoint for document categories without authentication"""
    return {
        "message": "Categories test successful",
        "categories": [
            {"id": "cat1", "name": "HR Documents", "sort_order": 1},
            {"id": "cat2", "name": "Finance", "sort_order": 2},
            {"id": "cat3", "name": "Legal", "sort_order": 3}
        ]
    }

@app.get("/test-documents/enhanced")
async def test_document_enhanced():
    """Test endpoint for enhanced documents without authentication"""
    return {
        "message": "Enhanced documents test successful",
        "documents": [
            {"id": "doc1", "filename": "test1.pdf", "created_at": "2024-01-01T00:00:00Z"},
            {"id": "doc2", "filename": "test2.docx", "created_at": "2024-01-02T00:00:00Z"}
        ],
        "categories": [
            {"id": "cat1", "name": "HR Documents"},
            {"id": "cat2", "name": "Finance"}
        ],
        "folders": [
            {"id": "folder1", "name": "General"},
            {"id": "folder2", "name": "Important"}
        ],
        "total_count": 2,
        "current_page": 1,
        "total_pages": 1
    }

# Include routers
print("🔧 Including API routers...")
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
print("✅ Auth router included")
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
print("✅ Companies router included")
app.include_router(users.router, prefix="/api/users", tags=["Users"])
print("✅ Users router included")
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
print("✅ Documents router included")
app.include_router(chatbot.router, prefix="/api/chat", tags=["Chatbot"])
print("✅ Chatbot router included")
app.include_router(user_management.router, prefix="/api/user-management", tags=["User Management"])
print("✅ User Management router included")
app.include_router(esignature.router, prefix="/api", tags=["E-Signature"])
print("✅ E-Signature router included")

# Import and include HR admin router
from app.routers import hr_admin
app.include_router(hr_admin.router, prefix="/api/hr-admin", tags=["HR Admin"])
print("✅ HR Admin router included")
print("🔧 All routers included successfully!")

@app.get("/")
async def root():
    return {
        "message": "Multi-Tenant Document Management System API",
        "version": "2.0.0",
        "status": "running",
        "architecture": "true_database_isolation",
        "cors_enabled": True,
        "frontend_url": "https://multitenant-frontend.onrender.com"
    }

@app.get("/debug-cors")
async def debug_cors():
    """Debug endpoint to check CORS configuration"""
    return {
        "cors_origins": cors_origins,
        "environment": os.getenv("ENVIRONMENT", "production"),
        "frontend_url": "https://multitenant-frontend.onrender.com",
        "cors_enabled": True
    }

@app.get("/test-hr-admin")
async def test_hr_admin():
    """Test endpoint to verify HR admin router is working"""
    return {
        "message": "HR Admin router is working!",
        "endpoints": [
            "/api/hr-admin/company/users",
            "/api/hr-admin/company/analytics",
            "/api/hr-admin/company/users/{user_id}/credentials",
            "/api/hr-admin/company/users/{user_id}/files",
            "/api/hr-admin/company/users/{user_id}/activity"
        ],
        "status": "active"
    }

@app.get("/test-companies-router")
async def test_companies_router():
    """Test endpoint to verify companies router is working"""
    return {
        "message": "Companies router is working!",
        "endpoints": [
            "/api/companies/",
            "/api/companies/public",
            "/api/companies/{company_id}/public"
        ],
        "status": "active",
        "environment": ENVIRONMENT,
        "cors_origins": cors_origins
    }

# Remove this conflicting route - it's interfering with API routing
# @app.options("/{full_path:path}")
# async def options_handler(full_path: str):
#     """Handle OPTIONS requests for CORS preflight"""
#     return {
#         "message": "OPTIONS request handled",
#         "path": full_path,
#         "cors_enabled": True
#     }

@app.post("/init-admin")
async def initialize_first_admin(db: Session = Depends(get_management_db)):
    """One-time endpoint to create the first system admin (no auth required)"""
    
    try:
        # Check if any system admin already exists
        existing_admin = db.query(models.SystemUser).filter(
            models.SystemUser.role == "system_admin"
        ).first()
        
        if existing_admin:
            return {
                "status": "admin_exists",
                "message": f"System admin already exists: {existing_admin.username}",
                "username": existing_admin.username
            }
        
        # Create first system admin user
        from app.auth import get_password_hash
        
        admin_username = "admin"
        admin_email = "admin@system.local"  
        admin_password = "admin123"
        admin_full_name = "System Administrator"
        
        hashed_password = get_password_hash(admin_password)
        
        admin_user = models.SystemUser(
            username=admin_username,
            email=admin_email,
            hashed_password=hashed_password,
            full_name=admin_full_name,
            role="system_admin",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        return {
            "status": "success",
            "message": "First system admin created successfully!",
            "credentials": {
                "username": admin_username,
                "password": admin_password,
                "email": admin_email
            },
            "warning": "Please change the password after first login and remove this endpoint!"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating system admin: {str(e)}")

@app.post("/reset-admin-password")
async def reset_admin_password(db: Session = Depends(get_management_db)):
    """Temporary endpoint to reset admin password (remove after use!)"""
    
    try:
        # Find the existing admin
        admin = db.query(models.SystemUser).filter(
            models.SystemUser.role == "system_admin"
        ).first()
        
        if not admin:
            raise HTTPException(status_code=404, detail="No system admin found")
        
        # Reset password to known value
        from app.auth import get_password_hash
        new_password = "admin123"
        admin.hashed_password = get_password_hash(new_password)
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Admin password reset successfully!",
            "username": admin.username,
            "new_password": new_password,
            "warning": "Please change this password immediately and remove this endpoint!"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting password: {str(e)}")

@app.get("/api/system/status")
async def system_status():
    """Get system status including database connections"""
    try:
        # Get management database connection
        db_gen = get_management_db()
        db = next(db_gen)
        
        # Count companies
        company_count = db.query(models.Company).filter(models.Company.is_active == True).count()
        system_user_count = db.query(models.SystemUser).filter(models.SystemUser.is_active == True).count()
        
        db.close()
        
        return {
            "system_status": "operational",
            "management_database": "connected",
            "companies_registered": company_count,
            "system_users": system_user_count,
            "company_database_connections": len(db_manager._company_engines),
            "version": "2.0.0"
        }
        
    except Exception as e:
        return {
            "system_status": "error",
            "management_database": "error",
            "error": str(e),
            "version": "2.0.0"
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)