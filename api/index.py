from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os

# Add the backend app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

# Create a new FastAPI instance for Vercel
app = FastAPI(title="Document Management System API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/")
async def root():
    return {"message": "Document Management System API", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "document-management-api"}

# Import and include your app's routes
try:
    from main import app as backend_app
    # Include all routes from backend
    app.include_router(backend_app.router, prefix="/api")
    print("✅ Successfully imported backend app")
except ImportError as e:
    print(f"❌ Could not import backend app: {e}")
    # Add basic API endpoints for testing
    @app.get("/api/test")
    async def test():
        return {"message": "API is working", "error": "Backend not imported"}
    
    @app.get("/api/companies")
    async def companies():
        return {"message": "Companies endpoint", "error": "Backend not imported"}
    
    @app.get("/api/auth/login")
    async def login():
        return {"message": "Login endpoint", "error": "Backend not imported"} 