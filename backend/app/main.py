from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app.database import get_management_db
from app.services.database_manager import db_manager
from app import models
from app.routers import auth, companies, users, documents, chatbot, user_management, esignature
from app.config import get_cors_origins

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

# CORS middleware - using environment variable
cors_origins = get_cors_origins()
print(f"🔧 CORS Origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)



# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chatbot.router, prefix="/api/chat", tags=["Chatbot"])
app.include_router(user_management.router, prefix="/api/user-management", tags=["User Management"])
app.include_router(esignature.router, prefix="/api", tags=["E-Signature"])

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

@app.get("/health")
async def health_check():
    try:
        # Test management database connection
        db_gen = get_management_db()
        db = next(db_gen)
        
        # Simple query to test connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy", 
            "management_db": "connected",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "management_db": "disconnected", 
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

@app.get("/debug-cors")
async def debug_cors():
    """Debug endpoint to check CORS configuration"""
    from app.config import get_cors_origins
    import os
    
    return {
        "cors_origins": get_cors_origins(),
        "environment": os.getenv("NODE_ENV", "development"),
        "frontend_url": "https://multitenant-frontend.onrender.com",
        "message": "CORS debug endpoint"
    }
    
    return {
        "cors_origins": get_cors_origins(),
        "cors_origins_env": os.getenv("CORS_ORIGINS", "NOT_SET"),
        "app_url_env": os.getenv("APP_URL", "NOT_SET"),
        "frontend_url": "https://multitenant-frontend.onrender.com",
        "backend_url": "https://multitenant-backend-mlap.onrender.com",
        "status": "CORS configuration loaded"
    }

@app.options("/test-cors")
async def test_cors():
    """Test CORS preflight request"""
    return {"message": "CORS preflight successful"}

@app.get("/test-cors")
async def test_cors_get():
    """Test CORS GET request"""
    return {
        "message": "CORS GET request successful",
        "timestamp": "2024-01-01T00:00:00Z",
        "cors_enabled": True,
        "frontend_url": "https://multitenant-frontend.onrender.com"
    }

@app.post("/test-cors")
async def test_cors_post():
    """Test CORS POST request"""
    return {
        "message": "CORS POST request successful",
        "timestamp": "2024-01-01T00:00:00Z",
        "cors_enabled": True
    }

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