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