from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Document Management System API", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "document-management-api"}

@app.get("/api/test")
async def test():
    return {"message": "API is working", "status": "success"}

@app.get("/api/companies")
async def companies():
    # Mock response for testing
    return {
        "companies": [
            {"id": 1, "name": "SafespaceLabs", "is_active": True},
            {"id": 2, "name": "Microsoft", "is_active": True},
            {"id": 3, "name": "Amazon", "is_active": True}
        ]
    }

@app.get("/api/companies/public")
async def companies_public():
    # Mock response for testing
    return {
        "companies": [
            {"id": 1, "name": "SafespaceLabs", "is_active": True},
            {"id": 2, "name": "Microsoft", "is_active": True},
            {"id": 3, "name": "Amazon", "is_active": True}
        ]
    }

@app.post("/api/auth/login")
async def login():
    return {"message": "Login endpoint", "status": "mock"}

@app.post("/api/auth/system-admin/login")
async def system_admin_login():
    return {"message": "System admin login endpoint", "status": "mock"}

# Vercel serverless function handler
def handler(request, context):
    """Vercel serverless function entry point"""
    return app(request, context) 