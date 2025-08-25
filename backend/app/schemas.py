from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional, Any, Dict
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

# New comprehensive schemas for HR admin access
class CompanyUserDetailResponse(BaseModel):
    """Comprehensive user data accessible by HR admins"""
    id: str
    username: str
    email: str
    full_name: str
    role: str
    s3_folder: str
    password_set: bool
    created_at: datetime
    is_active: bool
    company_id: Optional[str] = None
    unique_id: Optional[str] = None
    created_by: Optional[str] = None
    hashed_password: Optional[str] = None  # For password management
    last_login: Optional[datetime] = None
    login_count: Optional[int] = 0
    documents_count: Optional[int] = 0
    total_documents_size: Optional[int] = 0

    class Config:
        from_attributes = True

# New schemas for HR admin features
class DocumentAnalyticsResponse(BaseModel):
    id: str
    document_id: str
    view_count: int
    download_count: int
    share_count: int
    last_viewed_at: Optional[datetime]
    last_downloaded_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ComplianceRuleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    rule_type: str
    category_id: Optional[str]
    retention_period_days: Optional[int]
    requires_approval: bool
    requires_signature: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ComplianceViolationResponse(BaseModel):
    id: str
    rule_id: str
    document_id: Optional[str]
    user_id: Optional[str]
    violation_type: str
    severity: str
    description: Optional[str]
    resolved: bool
    resolved_by_user_id: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentWorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    workflow_type: str
    document_id: str
    initiator_user_id: str
    current_step: int
    total_steps: int
    status: str
    priority: str
    due_date: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class WorkflowStepResponse(BaseModel):
    id: str
    workflow_id: str
    step_number: int
    step_type: str
    assigned_user_id: Optional[str]
    assigned_role: Optional[str]
    title: str
    description: Optional[str]
    required: bool
    completed: bool
    completed_by_user_id: Optional[str]
    completed_at: Optional[datetime]
    due_date: Optional[datetime]

    class Config:
        from_attributes = True

class DocumentNotificationResponse(BaseModel):
    id: str
    user_id: str
    document_id: Optional[str]
    workflow_id: Optional[str]
    notification_type: str
    title: str
    message: Optional[str]
    read: bool
    read_at: Optional[datetime]
    action_required: bool
    action_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentTagResponse(BaseModel):
    id: str
    name: str
    color: Optional[str]
    description: Optional[str]
    created_by_user_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentVersionResponse(BaseModel):
    id: str
    document_id: str
    version_number: str
    filename: str
    file_path: str
    s3_key: str
    file_size: int
    change_description: Optional[str]
    created_by_user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# HR Admin Dashboard schemas
class HRDashboardStatsResponse(BaseModel):
    total_employees: int
    active_employees: int
    pending_approvals: int
    compliance_alerts: int
    total_documents: int
    documents_this_month: int
    storage_used_gb: float
    storage_limit_gb: float

class EmployeeSummaryResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    department: Optional[str]
    status: str
    documents_count: int
    last_login: Optional[datetime]
    created_at: datetime

class DocumentSummaryResponse(BaseModel):
    id: str
    original_filename: str
    document_category: Optional[str]
    file_size: int
    file_type: str
    user_id: str
    user_full_name: str
    created_at: datetime
    status: str

class WorkflowSummaryResponse(BaseModel):
    id: str
    name: str
    workflow_type: str
    document_id: str
    document_name: str
    current_step: int
    total_steps: int
    status: str
    priority: str
    due_date: Optional[datetime]
    initiator_full_name: str
    created_at: datetime

class ComplianceSummaryResponse(BaseModel):
    id: str
    rule_name: str
    violation_type: str
    severity: str
    document_name: Optional[str]
    user_name: Optional[str]
    description: Optional[str]
    resolved: bool
    created_at: datetime

# Document count schemas for sidebar
class DocumentCountsResponse(BaseModel):
    my_files_count: int
    org_files_count: int
    recent_files_count: int
    starred_files_count: int
    logs_count: int
    uploads_count: int
    category_counts: Dict[str, int]

# Search schemas
class SearchResultResponse(BaseModel):
    employees: List[EmployeeSummaryResponse]
    documents: List[DocumentSummaryResponse]
    total_results: int
    search_time_ms: float

# Analytics schemas
class DocumentAnalyticsSummaryResponse(BaseModel):
    total_documents: int
    total_views: int
    total_downloads: int
    total_shares: int
    documents_by_category: Dict[str, int]
    documents_by_type: Dict[str, int]
    uploads_by_month: Dict[str, int]
    top_viewed_documents: List[DocumentSummaryResponse]
    recent_activity: List[Dict[str, Any]]

class CompanyUserCredentialsResponse(BaseModel):
    """User credentials and access information for HR admins"""
    id: str
    username: str
    email: str
    full_name: str
    role: str
    hashed_password: str
    password_set: bool
    last_password_change: Optional[datetime] = None
    password_expires_at: Optional[datetime] = None
    login_attempts: Optional[int] = 0
    account_locked: Optional[bool] = False
    lock_reason: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class CompanyUserFilesResponse(BaseModel):
    """User's files and documents for HR admin access"""
    id: str
    username: str
    email: str
    full_name: str
    role: str
    documents: List[dict] = []
    total_documents: int = 0
    total_size: int = 0
    categories: List[str] = []
    folders: List[str] = []
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True

class CompanyAnalyticsResponse(BaseModel):
    """Company-wide analytics for HR admins"""
    total_users: int
    active_users: int
    inactive_users: int
    users_by_role: Dict[str, int]
    total_documents: int
    total_storage_used: int
    recent_activity: List[dict]
    user_growth: List[dict]
    document_categories: List[dict]
    storage_by_category: List[dict]

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

class CompanyLoginCredentials(BaseModel):
    username: str
    password: str
    company_id: str
    database_url: Optional[str] = None

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