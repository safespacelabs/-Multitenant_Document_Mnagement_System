from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional, Any
from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    employee = "employee"

# Company schemas
class CompanyCreate(BaseModel):
    name: str
    email: EmailStr

class CompanyResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    company_id: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    company_id: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Document schemas
class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    processed: bool
    metadata_json: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True

# Chat schemas
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    context_documents: Optional[List[str]]
    created_at: datetime

# User update schema
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None

    class Config:
        from_attributes = True

# Document create schema
class DocumentCreate(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    s3_key: str

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    company: CompanyResponse 