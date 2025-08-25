from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# Base for company-specific tables
CompanyBase = declarative_base()

class User(CompanyBase):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:8]}")
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Can be null for pending users
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="customer")  # hr_admin, hr_manager, employee, customer
    s3_folder = Column(String, nullable=False)
    company_id = Column(String, nullable=True)  # Company ID for multi-tenancy (temporarily nullable for existing users)
    unique_id = Column(String, unique=True, nullable=True)  # For initial registration
    password_set = Column(Boolean, default=False)  # Track if password has been set
    created_by = Column(String, ForeignKey("users.id"), nullable=True)  # Who registered this user
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    documents = relationship("Document", back_populates="user")
    created_users = relationship("User", remote_side=[id])  # Users this user created

class UserInvitation(CompanyBase):
    __tablename__ = "user_invitations"
    
    id = Column(String, primary_key=True, default=lambda: f"invite_{uuid.uuid4().hex[:8]}")
    unique_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    company_id = Column(String, nullable=True)  # Company ID for multi-tenancy (temporarily nullable for existing users)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)  # user_id who created this invitation
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    creator = relationship("User")

class Document(CompanyBase):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    folder_name = Column(String, nullable=True)  # New field for folder organization
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, nullable=True)  # Company ID for multi-tenancy (temporarily nullable for existing users)
    metadata_json = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # New fields for enhanced document management
    document_category = Column(String, nullable=True)  # Career Development, Compensation, etc.
    document_subcategory = Column(String, nullable=True)  # Subcategory within main category
    tags = Column(JSON, nullable=True)  # Array of tags
    description = Column(Text, nullable=True)  # Document description
    is_public = Column(Boolean, default=False)  # Whether document is visible to all employees
    access_level = Column(String, default="private")  # private, shared, public
    expiry_date = Column(DateTime, nullable=True)  # Document expiry date
    version = Column(String, default="1.0")  # Document version
    status = Column(String, default="active")  # active, archived, expired
    
    user = relationship("User", back_populates="documents")

class ChatHistory(CompanyBase):
    __tablename__ = "chat_history"
    
    id = Column(String, primary_key=True, default=lambda: f"chat_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    context_documents = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User") 

# E-Signature Models
class ESignatureDocument(CompanyBase):
    __tablename__ = "esignature_documents"
    
    id = Column(String, primary_key=True, default=lambda: f"esign_{uuid.uuid4().hex[:8]}")
    document_id = Column(String, nullable=False, index=True)  # Reference to original document
    title = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending, sent, signed, completed, cancelled, expired
    inkless_document_id = Column(String, nullable=True)  # Inkless document ID
    inkless_document_url = Column(String, nullable=True)  # Inkless document URL
    company_id = Column(String, nullable=True)  # Company ID for multi-tenancy (temporarily nullable for existing users)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)  # User who initiated the signature request
    require_all_signatures = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Add relationships
    creator = relationship("User", foreign_keys=[created_by_user_id])

class ESignatureRecipient(CompanyBase):
    __tablename__ = "esignature_recipients"
    
    id = Column(String, primary_key=True, default=lambda: f"recipient_{uuid.uuid4().hex[:8]}")
    esignature_document_id = Column(String, ForeignKey("esignature_documents.id"), nullable=False)
    email = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    is_signed = Column(Boolean, default=False, nullable=False)
    signature_text = Column(String, nullable=True)  # Signature text or ID
    ip_address = Column(String, nullable=True)  # IP address when signed
    user_agent = Column(String, nullable=True)  # User agent when signed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    esignature_document = relationship("ESignatureDocument", backref="recipients")

class ESignatureAuditLog(CompanyBase):
    __tablename__ = "esignature_audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: f"audit_{uuid.uuid4().hex[:8]}")
    esignature_document_id = Column(String, ForeignKey("esignature_documents.id"), nullable=False)
    action = Column(String, nullable=False)  # created, sent, opened, signed, completed, cancelled
    user_email = Column(String, nullable=True)
    user_ip = Column(String, nullable=True)
    details = Column(Text, nullable=True)  # JSON string with additional details
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    esignature_document = relationship("ESignatureDocument", backref="audit_logs")

class WorkflowApproval(CompanyBase):
    __tablename__ = "workflow_approvals"
    
    id = Column(String, primary_key=True, default=lambda: f"workflow_{uuid.uuid4().hex[:8]}")
    document_id = Column(String, nullable=False, index=True)
    approval_type = Column(String, nullable=False)  # contract_approval, policy_acknowledgment, etc.
    esignature_document_id = Column(String, ForeignKey("esignature_documents.id"), nullable=False)
    requires_sequential_approval = Column(Boolean, default=False, nullable=False)
    current_step = Column(Integer, default=0, nullable=False)
    total_steps = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    esignature_document = relationship("ESignatureDocument", backref="workflow_approval") 

# New models for enhanced document management
class DocumentCategory(CompanyBase):
    __tablename__ = "document_categories"
    
    id = Column(String, primary_key=True, default=lambda: f"cat_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)  # Career Development, Compensation, etc.
    display_name = Column(String, nullable=False)  # User-friendly display name
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)  # Icon identifier (briefcase, dollar, etc.)
    color = Column(String, nullable=True)  # Color code for UI
    parent_category_id = Column(String, ForeignKey("document_categories.id"), nullable=True)  # For subcategories
    company_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent_category = relationship("DocumentCategory", remote_side=[id])
    subcategories = relationship("DocumentCategory", back_populates="parent_category")

class DocumentFolder(CompanyBase):
    __tablename__ = "document_folders"
    
    id = Column(String, primary_key=True, default=lambda: f"folder_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(String, ForeignKey("document_categories.id"), nullable=True)
    parent_folder_id = Column(String, ForeignKey("document_folders.id"), nullable=True)
    company_id = Column(String, nullable=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    category = relationship("DocumentCategory")
    parent_folder = relationship("DocumentFolder", remote_side=[id])
    subfolders = relationship("DocumentFolder", back_populates="parent_folder")
    creator = relationship("User")

class DocumentAccess(CompanyBase):
    __tablename__ = "document_access"
    
    id = Column(String, primary_key=True, default=lambda: f"access_{uuid.uuid4().hex[:8]}")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Null for role-based access
    role_id = Column(String, nullable=True)  # For role-based access
    access_type = Column(String, nullable=False)  # read, write, admin
    granted_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    document = relationship("Document")
    user = relationship("User", foreign_keys=[user_id])
    granted_by = relationship("User", foreign_keys=[granted_by_user_id])

class DocumentAuditLog(CompanyBase):
    __tablename__ = "document_audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: f"audit_{uuid.uuid4().hex[:8]}")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # view, download, edit, delete, share
    details = Column(JSON, nullable=True)  # Additional action details
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    company_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document")
    user = relationship("User")

# New models for HR admin monitoring and access control
class UserLoginHistory(CompanyBase):
    __tablename__ = "user_login_history"
    
    id = Column(String, primary_key=True, default=lambda: f"login_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    login_timestamp = Column(DateTime, default=datetime.utcnow)
    logout_timestamp = Column(DateTime, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    success = Column(Boolean, default=True)
    failure_reason = Column(String, nullable=True)
    company_id = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", backref="login_history")

class UserCredentials(CompanyBase):
    __tablename__ = "user_credentials"
    
    id = Column(String, primary_key=True, default=lambda: f"cred_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    password_set_at = Column(DateTime, default=datetime.utcnow)
    password_expires_at = Column(DateTime, nullable=True)
    last_password_change = Column(DateTime, default=datetime.utcnow)
    login_attempts = Column(Integer, default=0)
    account_locked = Column(Boolean, default=False)
    lock_reason = Column(String, nullable=True)
    lock_timestamp = Column(DateTime, nullable=True)
    company_id = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", backref="credentials")

class UserActivity(CompanyBase):
    __tablename__ = "user_activity"
    
    id = Column(String, primary_key=True, default=lambda: f"activity_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String, nullable=False)  # login, logout, document_view, document_upload, etc.
    activity_details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    company_id = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", backref="activities")

# New models for HR admin analytics and compliance
class DocumentAnalytics(CompanyBase):
    __tablename__ = "document_analytics"
    
    id = Column(String, primary_key=True, default=lambda: f"analytics_{uuid.uuid4().hex[:8]}")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime, nullable=True)
    last_downloaded_at = Column(DateTime, nullable=True)
    company_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", backref="analytics")

class ComplianceRule(CompanyBase):
    __tablename__ = "compliance_rules"
    
    id = Column(String, primary_key=True, default=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String, nullable=False)  # retention, access_control, audit, etc.
    category_id = Column(String, ForeignKey("document_categories.id"), nullable=True)
    retention_period_days = Column(Integer, nullable=True)
    requires_approval = Column(Boolean, default=False)
    requires_signature = Column(Boolean, default=False)
    company_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    category = relationship("DocumentCategory")

class ComplianceViolation(CompanyBase):
    __tablename__ = "compliance_violations"
    
    id = Column(String, primary_key=True, default=lambda: f"violation_{uuid.uuid4().hex[:8]}")
    rule_id = Column(String, ForeignKey("compliance_rules.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    violation_type = Column(String, nullable=False)  # retention_expired, unauthorized_access, etc.
    severity = Column(String, default="medium")  # low, medium, high, critical
    description = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    company_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rule = relationship("ComplianceRule")
    document = relationship("Document")
    user = relationship("User", foreign_keys=[user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])

class DocumentWorkflow(CompanyBase):
    __tablename__ = "document_workflows"
    
    id = Column(String, primary_key=True, default=lambda: f"workflow_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    workflow_type = Column(String, nullable=False)  # approval, review, signature, etc.
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    initiator_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=1)
    status = Column(String, default="pending")  # pending, in_progress, completed, cancelled
    priority = Column(String, default="normal")  # low, normal, high, urgent
    due_date = Column(DateTime, nullable=True)
    company_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    document = relationship("Document")
    initiator = relationship("User")

class WorkflowStep(CompanyBase):
    __tablename__ = "workflow_steps"
    
    id = Column(String, primary_key=True, default=lambda: f"step_{uuid.uuid4().hex[:8]}")
    workflow_id = Column(String, ForeignKey("document_workflows.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    step_type = Column(String, nullable=False)  # approval, review, signature, notification
    assigned_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    assigned_role = Column(String, nullable=True)  # For role-based assignments
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    required = Column(Boolean, default=True)
    completed = Column(Boolean, default=False)
    completed_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    company_id = Column(String, nullable=True)
    
    # Relationships
    workflow = relationship("DocumentWorkflow", backref="steps")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    completed_by = relationship("User", foreign_keys=[completed_by_user_id])

class DocumentNotification(CompanyBase):
    __tablename__ = "document_notifications"
    
    id = Column(String, primary_key=True, default=lambda: f"notification_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    workflow_id = Column(String, ForeignKey("document_workflows.id"), nullable=True)
    notification_type = Column(String, nullable=False)  # approval_required, document_shared, workflow_completed, etc.
    title = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    action_required = Column(Boolean, default=False)
    action_url = Column(String, nullable=True)
    company_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="notifications")
    document = relationship("Document")
    workflow = relationship("DocumentWorkflow")

class DocumentTag(CompanyBase):
    __tablename__ = "document_tags"
    
    id = Column(String, primary_key=True, default=lambda: f"tag_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)  # Hex color code
    description = Column(Text, nullable=True)
    company_id = Column(String, nullable=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("User")

class DocumentTagMapping(CompanyBase):
    __tablename__ = "document_tag_mappings"
    
    id = Column(String, primary_key=True, default=lambda: f"tagmap_{uuid.uuid4().hex[:8]}")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    tag_id = Column(String, ForeignKey("document_tags.id"), nullable=False)
    company_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document")
    tag = relationship("DocumentTag")

class DocumentVersion(CompanyBase):
    __tablename__ = "document_versions"
    
    id = Column(String, primary_key=True, default=lambda: f"version_{uuid.uuid4().hex[:8]}")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    version_number = Column(String, nullable=False)  # 1.0, 1.1, 2.0, etc.
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    change_description = Column(Text, nullable=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", backref="versions")
    creator = relationship("User") 