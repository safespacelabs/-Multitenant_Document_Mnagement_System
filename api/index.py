from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os

# Add the backend app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

# Import your FastAPI app
from main import app

# Create a new FastAPI instance for Vercel
api = FastAPI(title="Document Management System API")

# Add CORS middleware
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your app's routes
api.include_router(app.router, prefix="/api")

# Health check endpoint
@api.get("/")
async def root():
    return {"message": "Document Management System API"}

# Export for Vercel
app = api 