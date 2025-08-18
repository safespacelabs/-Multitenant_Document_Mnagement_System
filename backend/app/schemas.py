from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional, Any
from enum import Enum

class UserRole(str, Enum):
    hr_admin = "hr_admin" 
    hr_manager = "hr_manager"
    employee = "employee"
    customer = "customer"

class SystemRole(str, Enum):
    system_admin = "system_admin"

# Company schemas
class CompanyCreate(BaseModel):
    name: str
    email: EmailStr

class CompanyResponse(BaseModel):
    id: str
    name: str
    email: str
    database_name: str
    database_url: str
    database_host: str
    database_port: str
    created_at: datetime
    is_active: bool
    s3_bucket_name: Optional[str] = None

    class Config:
        from_attributes = True

# System User schemas (for management database)
class SystemUserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: SystemRole

class SystemUserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    s3_bucket_name: Optional[str] = None
    s3_folder: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Company User schemas (for company databases)
class CompanyUserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole

class CompanyUserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    s3_folder: str
    password_set: bool
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Legacy User schemas (for backward compatibility)
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
    company_id: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Document schemas
class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    folder_name: Optional[str]
    user_id: str
    processed: bool
    metadata_json: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True

# System Document schemas (for system admin documents)
class SystemDocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    s3_key: str
    folder_name: Optional[str]
    user_id: str
    processed: bool
    metadata_json: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True

class SystemDocumentCreate(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    s3_key: str
    folder_name: Optional[str] = None

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
    folder_name: Optional[str] = None

# User Invitation schemas
class UserInviteCreate(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole

class UserInviteResponse(BaseModel):
    id: str
    unique_id: str
    email: str
    full_name: str
    role: str
    created_by: str
    expires_at: datetime
    is_used: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Password Setup schemas
class PasswordSetupRequest(BaseModel):
    unique_id: str
    username: str
    password: str

class PasswordSetupResponse(BaseModel):
    message: str
    user_id: str

# Enhanced User Login for role-based access
class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    company: Optional[CompanyResponse] = None
    permissions: List[str]

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    company: Optional[CompanyResponse] = None
    permissions: Optional[List[str]] = None

# Database Log schemas
class DatabaseLogResponse(BaseModel):
    id: str
    company_id: str
    action: str
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Company Stats schema
class CompanyStats(BaseModel):
    company: CompanyResponse 
    stats: dict

# E-Signature Schemas
class ESignatureStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    signed = "signed"
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"

class ESignatureRecipient(BaseModel):
    email: EmailStr
    full_name: str
    role: Optional[str] = None

class ESignatureRequest(BaseModel):
    document_id: str
    title: str
    message: Optional[str] = None
    recipients: List[ESignatureRecipient]
    require_all_signatures: bool = True
    expires_in_days: int = 14

class ESignatureSignRequest(BaseModel):
    signature_text: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    recipient_email: Optional[str] = None  # For direct signing from email

class ESignatureResponse(BaseModel):
    id: str
    document_id: str
    title: str
    message: Optional[str]
    status: ESignatureStatus
    inkless_document_id: Optional[str]
    inkless_document_url: Optional[str]
    created_by_user_id: str
    recipients: List[ESignatureRecipient]
    signed_by: List[str] = []
    completed_at: Optional[datetime] = None
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class ESignatureUpdate(BaseModel):
    status: Optional[ESignatureStatus] = None
    inkless_document_id: Optional[str] = None
    inkless_document_url: Optional[str] = None
    signed_by: Optional[List[str]] = None
    completed_at: Optional[datetime] = None

class WorkflowApprovalRequest(BaseModel):
    document_id: str
    approval_type: str  # "contract_approval", "policy_acknowledgment", "budget_approval", etc.
    approvers: List[ESignatureRecipient]
    message: Optional[str] = None
    requires_sequential_approval: bool = False

class BulkESignatureRequest(BaseModel):
    document_ids: List[str]
    title: str
    message: Optional[str] = None
    recipients: List[ESignatureRecipient]
    require_all_signatures: bool = True
    expires_in_days: int = 14 

# Enhanced Document Management Schemas
class DocumentCategoryBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_category_id: Optional[str] = None
    sort_order: Optional[int] = 0

class DocumentCategoryCreate(DocumentCategoryBase):
    pass

class DocumentCategoryUpdate(DocumentCategoryBase):
    is_active: Optional[bool] = None

class DocumentCategoryResponse(DocumentCategoryBase):
    id: str
    company_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    subcategories: List['DocumentCategoryResponse'] = []
    
    class Config:
        from_attributes = True

class DocumentFolderBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    parent_folder_id: Optional[str] = None
    sort_order: Optional[int] = 0

class DocumentFolderCreate(DocumentFolderBase):
    pass

class DocumentFolderUpdate(DocumentFolderBase):
    is_active: Optional[bool] = None

class DocumentFolderResponse(DocumentFolderBase):
    id: str
    company_id: Optional[str] = None
    created_by_user_id: str
    is_active: bool
    created_at: datetime
    category: Optional[DocumentCategoryResponse] = None
    subfolders: List['DocumentFolderResponse'] = []
    
    class Config:
        from_attributes = True

class DocumentAccessBase(BaseModel):
    document_id: str
    user_id: Optional[str] = None
    role_id: Optional[str] = None
    access_type: str  # read, write, admin
    expires_at: Optional[datetime] = None

class DocumentAccessCreate(DocumentAccessBase):
    pass

class DocumentAccessUpdate(DocumentAccessBase):
    is_active: Optional[bool] = None

class DocumentAccessResponse(DocumentAccessBase):
    id: str
    company_id: Optional[str] = None
    granted_by_user_id: str
    granted_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class DocumentAuditLogResponse(BaseModel):
    id: str
    document_id: str
    user_id: str
    action: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    company_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Enhanced Document schemas
class DocumentCreateEnhanced(DocumentCreate):
    document_category: Optional[str] = None
    document_subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    is_public: Optional[bool] = False
    access_level: Optional[str] = "private"
    expiry_date: Optional[datetime] = None
    version: Optional[str] = "1.0"
    status: Optional[str] = "active"

class DocumentResponseEnhanced(DocumentResponse):
    document_category: Optional[str] = None
    document_subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    is_public: bool
    access_level: str
    expiry_date: Optional[datetime] = None
    version: str
    status: str
    category_info: Optional[DocumentCategoryResponse] = None
    folder_info: Optional[DocumentFolderResponse] = None

# Document Management Response schemas
class DocumentManagementResponse(BaseModel):
    documents: List[DocumentResponseEnhanced]
    categories: List[DocumentCategoryResponse]
    folders: List[DocumentFolderResponse]
    total_count: int
    current_page: int
    total_pages: int

class DocumentFilterRequest(BaseModel):
    category_id: Optional[str] = None
    folder_id: Optional[str] = None
    file_type: Optional[str] = None
    search_query: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[str] = None
    access_level: Optional[str] = None
    user_id: Optional[str] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 20
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"

class BulkDocumentOperation(BaseModel):
    document_ids: List[str]
    operation: str  # download, delete, move, share, archive
    target_folder_id: Optional[str] = None
    target_category_id: Optional[str] = None
    user_ids: Optional[List[str]] = None
    access_type: Optional[str] = None 