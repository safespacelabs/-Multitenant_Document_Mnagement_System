from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
from contextlib import asynccontextmanager

from app.database import engine, get_db
from app import models
from app.routers import auth, companies, users, documents, chatbot
from app.config import get_cors_origins

# Create tables
models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Multi-Tenant Document Management System")
    yield
    # Shutdown
    print("🛑 Shutting down...")

app = FastAPI(
    title="Multi-Tenant Document Management System",
    description="AI-powered document management with multi-tenant architecture",
    version="1.0.0",
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

@app.get("/")
async def root():
    return {
        "message": "Multi-Tenant Document Management System API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)