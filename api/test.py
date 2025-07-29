from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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