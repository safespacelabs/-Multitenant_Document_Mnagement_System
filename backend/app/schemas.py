from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, date
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

# New schemas for HR-managed user folders and documents
class UserFolderCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    user_id: str
    folder_type: str = "hr_managed"
    sort_order: int = 0

class UserFolderUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class UserFolderResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str]
    user_id: str
    created_by_user_id: str
    s3_folder_path: str
    folder_type: str
    is_active: bool
    sort_order: int
    company_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    documents_count: int = 0
    total_size: int = 0

    class Config:
        from_attributes = True

class HRManagedDocumentCreate(BaseModel):
    folder_id: str
    user_id: str
    document_category: Optional[str] = None
    document_subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    is_public: bool = False
    access_level: str = "private"
    expiry_date: Optional[datetime] = None
    version: str = "1.0"
    status: str = "active"

class HRManagedDocumentUpdate(BaseModel):
    document_category: Optional[str] = None
    document_subcategory: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    access_level: Optional[str] = None
    expiry_date: Optional[datetime] = None
    version: Optional[str] = None
    status: Optional[str] = None

class HRManagedDocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    s3_key: str
    folder_id: str
    user_id: str
    created_by_user_id: str
    document_category: Optional[str]
    document_subcategory: Optional[str]
    tags: Optional[List[str]]
    description: Optional[str]
    is_public: bool
    access_level: str
    expiry_date: Optional[datetime]
    version: str
    status: str
    metadata_json: Optional[Dict[str, Any]]
    processed: bool
    company_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserFolderWithDocumentsResponse(BaseModel):
    folder: UserFolderResponse
    documents: List[HRManagedDocumentResponse]
    total_documents: int
    total_size: int

class UserFoldersSummaryResponse(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    folders: List[UserFolderResponse]
    total_folders: int
    total_documents: int
    total_size: int

class UserFolderAccessCreate(BaseModel):
    folder_id: str
    user_id: Optional[str] = None
    role_id: Optional[str] = None
    access_type: str  # read, write, admin
    expires_at: Optional[datetime] = None

class UserFolderAccessResponse(BaseModel):
    id: str
    folder_id: str
    user_id: Optional[str]
    role_id: Optional[str]
    access_type: str
    granted_by_user_id: str
    granted_at: datetime
    expires_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

class UserFolderAuditLogResponse(BaseModel):
    id: str
    folder_id: str
    document_id: Optional[str]
    user_id: str
    action: str
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
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

# Document Health Snapshot schemas
class ComplianceReason(BaseModel):
    """Detailed compliance reason for a document"""
    reason_type: str  # "expiry", "missing_metadata", "incomplete_data", "no_analysis"
    reason_message: str  # Human-readable description
    severity: str  # "high", "medium", "low"
    details: Optional[Dict[str, Any]] = None  # Additional context

class AffectedDocument(BaseModel):
    document_id: str
    filename: str
    document_type: Optional[str]
    expiry_date: Optional[date]
    days_until_expiry: Optional[int]
    status: str  # "compliant", "at_risk", "non_compliant"
    missing_fields: List[str]
    reasons: List[ComplianceReason] = []  # Detailed list of compliance issues

class AffectedEmployee(BaseModel):
    user_id: str
    full_name: str
    email: str
    employee_id: Optional[str]
    department: Optional[str]
    documents: List[AffectedDocument]

class CategoryHealthMetrics(BaseModel):
    category_name: str
    category_key: str
    icon: str
    total_documents: int
    compliant_count: int
    at_risk_count: int
    non_compliant_count: int
    compliance_percentage: float
    status: str  # "Healthy" (>=90%), "Watch" (70-89%), "Critical" (<70%)
    affected_employees: List[AffectedEmployee]

class DocumentHealthSnapshotResponse(BaseModel):
    total_documents: int
    compliant_count: int
    at_risk_count: int
    non_compliant_count: int
    compliant_percentage: float
    at_risk_percentage: float
    non_compliant_percentage: float
    categories: List[CategoryHealthMetrics]
    last_updated: datetime
    target_threshold: float = 95.0

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
    session_id: Optional[str] = None  # Chat session ID - creates new session if not provided
    document_ids: Optional[List[str]] = None  # Optional (rarely used) - chatbot auto-detects query type

class ChatResponse(BaseModel):
    answer: str
    context_documents: Optional[List[str]]
    created_at: datetime
    session_id: Optional[str] = None  # Session ID for linking messages

# User update schema
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None

    class Config:
        from_attributes = True

# Extended User Schemas for comprehensive user management

class UserCreateExtended(BaseModel):
    """Extended user creation schema with all fields from usertable.csv"""

    # Basic Identity (Required)
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    gender: str  # M, F, Male, Female, Other, Not Specified

    # Employment (Required)
    employee_id: str
    hire_date: date
    title: str
    division: str
    department: str
    location: str
    job_code: str
    manager: str = "NO_MANAGER"  # Username of manager or 'NO_MANAGER'

    # Address (Required)
    address_line1: str
    city: str
    state: str
    zip_code: str
    country: str = "United States"

    # System (Auto-populated or defaults)
    role: UserRole  # hr_admin, hr_manager, employee, customer
    timezone: str = "US/Pacific"
    default_locale: str = "en_US"
    status: str = "active"

    # Optional Fields
    middle_initial: Optional[str] = None
    display_name: Optional[str] = None
    address_line2: Optional[str] = None
    business_phone: Optional[str] = None
    business_fax: Optional[str] = None
    hr: Optional[str] = None
    business_unit: Optional[str] = None
    matrix_manager: Optional[str] = None
    second_manager: Optional[str] = None
    custom_manager: Optional[str] = None
    review_frequency: Optional[str] = None
    last_review_date: Optional[date] = None

    # Custom Fields (Optional)
    custom01: Optional[str] = None  # Career Level
    custom02: Optional[str] = None  # Eligibility Flag
    custom03: Optional[str] = None  # L04 Org Unit
    custom04: Optional[str] = None  # L05 Org Unit
    custom05: Optional[str] = None  # L06 Org Unit
    custom06: Optional[str] = None  # L07 Org Unit
    custom07: Optional[str] = None  # L08 Org Unit
    custom08: Optional[str] = None  # Company
    custom09: Optional[str] = None  # EESubgroup
    custom10: Optional[str] = None  # Union
    custom11: Optional[str] = None
    custom12: Optional[str] = None
    custom13: Optional[str] = None
    custom14: Optional[str] = None
    custom15: Optional[str] = None

    # Auth & Access (Optional)
    login_method: Optional[str] = None
    proxy: Optional[str] = None
    assignment_id_external: Optional[str] = None

    @validator('email')
    def email_must_be_lowercase(cls, v):
        return v.lower()

    @validator('gender')
    def gender_must_be_valid(cls, v):
        valid = ['M', 'F', 'Male', 'Female', 'Other', 'Not Specified']
        if v not in valid:
            raise ValueError(f'Gender must be one of: {valid}')
        return v

    class Config:
        from_attributes = True


class UserResponseExtended(BaseModel):
    """Extended user response schema with all fields"""

    # Existing fields
    id: str
    username: str
    email: str
    full_name: str
    role: str
    company_id: Optional[str] = None
    created_at: datetime
    is_active: bool

    # Phase 1: Core Identity & Employment
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    gender: Optional[str] = None
    employee_id: Optional[str] = None
    status: Optional[str] = None
    hire_date: Optional[date] = None
    timezone: Optional[str] = None
    default_locale: Optional[str] = None
    display_name: Optional[str] = None

    # Phase 2: Organizational Hierarchy
    manager: Optional[str] = None
    division: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    job_code: Optional[str] = None
    title: Optional[str] = None
    hr: Optional[str] = None
    business_unit: Optional[str] = None
    matrix_manager: Optional[str] = None
    second_manager: Optional[str] = None
    custom_manager: Optional[str] = None

    # Phase 3: Contact & Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    business_phone: Optional[str] = None
    business_fax: Optional[str] = None

    # Phase 4: Review & Performance
    review_frequency: Optional[str] = None
    last_review_date: Optional[date] = None
    assignment_uuid: Optional[str] = None

    # Phase 5: Custom Fields
    custom01: Optional[str] = None
    custom02: Optional[str] = None
    custom03: Optional[str] = None
    custom04: Optional[str] = None
    custom05: Optional[str] = None
    custom06: Optional[str] = None
    custom07: Optional[str] = None
    custom08: Optional[str] = None
    custom09: Optional[str] = None
    custom10: Optional[str] = None
    custom11: Optional[str] = None
    custom12: Optional[str] = None
    custom13: Optional[str] = None
    custom14: Optional[str] = None
    custom15: Optional[str] = None

    # Phase 6: Auth & Access
    login_method: Optional[str] = None
    proxy: Optional[str] = None
    assignment_id_external: Optional[str] = None

    # Additional fields
    s3_folder: Optional[str] = None
    password_set: Optional[bool] = None
    created_by: Optional[str] = None
    unique_id: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdateExtended(BaseModel):
    """Extended user update schema - all fields optional"""

    # Basic fields
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None

    # Core Identity
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    gender: Optional[str] = None
    employee_id: Optional[str] = None
    status: Optional[str] = None
    hire_date: Optional[date] = None
    timezone: Optional[str] = None
    default_locale: Optional[str] = None
    display_name: Optional[str] = None

    # Organizational
    manager: Optional[str] = None
    division: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    job_code: Optional[str] = None
    title: Optional[str] = None
    hr: Optional[str] = None
    business_unit: Optional[str] = None
    matrix_manager: Optional[str] = None
    second_manager: Optional[str] = None
    custom_manager: Optional[str] = None

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    business_phone: Optional[str] = None
    business_fax: Optional[str] = None

    # Review & Performance
    review_frequency: Optional[str] = None
    last_review_date: Optional[date] = None

    # Custom Fields
    custom01: Optional[str] = None
    custom02: Optional[str] = None
    custom03: Optional[str] = None
    custom04: Optional[str] = None
    custom05: Optional[str] = None
    custom06: Optional[str] = None
    custom07: Optional[str] = None
    custom08: Optional[str] = None
    custom09: Optional[str] = None
    custom10: Optional[str] = None
    custom11: Optional[str] = None
    custom12: Optional[str] = None
    custom13: Optional[str] = None
    custom14: Optional[str] = None
    custom15: Optional[str] = None

    # Auth & Access
    login_method: Optional[str] = None
    proxy: Optional[str] = None
    assignment_id_external: Optional[str] = None

    # Activity status
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class BulkUserImportResponse(BaseModel):
    """Response for bulk user import operation"""
    imported_count: int
    imported_users: List[str]
    errors: List[str]

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

# AI Assistant Schemas
class MessageType(str, Enum):
    TEXT = "text"
    DOCUMENT = "document"
    IMAGE = "image"
    VOICE = "voice"

class AnalysisType(str, Enum):
    SUMMARY = "summary"
    KEY_POINTS = "key_points"
    SENTIMENT = "sentiment"
    COMPLIANCE = "compliance"
    ACTION_ITEMS = "action_items"
    RISK_ASSESSMENT = "risk_assessment"

class SuggestionType(str, Enum):
    DOCUMENT_ORGANIZATION = "document_organization"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    COMPLIANCE_IMPROVEMENT = "compliance_improvement"
    SECURITY_ENHANCEMENT = "security_enhancement"
    PRODUCTIVITY_TIPS = "productivity_tips"
    TRAINING_RECOMMENDATIONS = "training_recommendations"

# Chat Session Schemas
class ChatSessionCreate(BaseModel):
    session_name: str = Field(..., description="Name of the chat session")
    context: Optional[str] = Field(None, description="Context or description of the session")

class ChatSessionResponse(BaseModel):
    id: str
    session_name: str
    created_at: datetime
    last_activity: datetime
    message_count: int

    class Config:
        from_attributes = True

# Chat Message Schemas
class ChatMessageCreate(BaseModel):
    session_id: str = Field(..., description="ID of the chat session")
    message: str = Field(..., description="User's message content")
    message_type: MessageType = Field(MessageType.TEXT, description="Type of message")
    attachments: Optional[List[str]] = Field(None, description="List of attachment IDs")

class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    message: str
    response: str
    message_type: MessageType
    timestamp: datetime
    ai_response_time: float
    attachments: Optional[List[str]] = None

    class Config:
        from_attributes = True

# Document Analysis Schemas
class DocumentAnalysisRequest(BaseModel):
    document_id: str = Field(..., description="ID of the document to analyze")
    analysis_type: AnalysisType = Field(..., description="Type of analysis to perform")
    specific_questions: Optional[List[str]] = Field(None, description="Specific questions for analysis")

class DocumentAnalysisResponse(BaseModel):
    document_id: str
    analysis_type: AnalysisType
    insights: List[str]
    summary: str
    recommendations: List[str]
    confidence_score: float
    analysis_timestamp: datetime
    processing_time: Optional[float] = None

    class Config:
        from_attributes = True

# Smart Suggestions Schemas
class SmartSuggestionRequest(BaseModel):
    suggestion_type: SuggestionType = Field(..., description="Type of suggestions to generate")
    context: Optional[str] = Field(None, description="Additional context for suggestions")
    user_role: Optional[str] = Field(None, description="User's role for role-specific suggestions")

class SmartSuggestionResponse(BaseModel):
    suggestions: List[str]
    reasoning: str
    priority: str
    category: SuggestionType
    generated_at: datetime
    estimated_impact: Optional[str] = None

    class Config:
        from_attributes = True

# AI Assistant Statistics Schemas
class AIAssistantStats(BaseModel):
    total_chat_sessions: int
    total_messages: int
    documents_analyzed: int
    suggestions_generated: int
    average_response_time: float
    most_used_features: List[str]
    company_usage_trend: Dict[str, Any]

    class Config:
        from_attributes = True

# Enhanced Chat Interface Schemas
class ChatContext(BaseModel):
    company_name: str
    user_role: str
    current_topic: Optional[str] = None
    recent_documents: Optional[List[str]] = None
    user_preferences: Optional[Dict[str, Any]] = None

class EnhancedChatMessage(BaseModel):
    id: str
    session_id: str
    message: str
    response: str
    message_type: MessageType
    timestamp: datetime
    ai_response_time: float
    context: Optional[ChatContext] = None
    follow_up_questions: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    sources: Optional[List[str]] = None

    class Config:
        from_attributes = True

# AI Assistant Configuration Schemas
class AIAssistantConfig(BaseModel):
    company_id: str
    ai_model: str = Field(default="gpt-4", description="AI model to use")
    max_context_length: int = Field(default=4000, description="Maximum context length")
    response_style: str = Field(default="professional", description="Response style preference")
    language: str = Field(default="en", description="Preferred language")
    industry_specific: bool = Field(default=True, description="Use industry-specific knowledge")
    compliance_focus: bool = Field(default=False, description="Focus on compliance aspects")

    class Config:
        from_attributes = True

# Quick Actions Schema
class QuickAction(BaseModel):
    id: str
    title: str
    description: str
    action_type: str
    icon: str
    category: str
    requires_context: bool = False

# AI Assistant Dashboard Schema
class AIAssistantDashboard(BaseModel):
    recent_sessions: List[ChatSessionResponse]
    quick_actions: List[QuickAction]
    recent_insights: List[str]
    pending_suggestions: List[SmartSuggestionResponse]
    usage_stats: AIAssistantStats
    company_context: ChatContext 