from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
from contextlib import asynccontextmanager

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        "architecture": "true_database_isolation"
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