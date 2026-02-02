"""
Document Analysis Models for AI-extracted metadata
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class DocumentAnalysis(Base):
    """Model for storing AI-extracted document metadata"""
    __tablename__ = "document_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), nullable=False, index=True)  # Reference to documents table (UUID)
    user_id = Column(String(255), nullable=False, index=True)  # User who uploaded the document (UUID)
    user_name = Column(String(255), index=True)  # Username for easy reference
    user_email = Column(String(255))  # User email for notifications
    title = Column(String(500))
    summary = Column(Text)
    document_type = Column(String(100), index=True)
    folder_name = Column(String(200), index=True)
    key_topics = Column(ARRAY(String))  # Array of topics
    entities = Column(JSON)  # JSON object with people, organizations, locations, dates, etc.
    keywords = Column(ARRAY(String))  # Array of keywords
    language = Column(String(50))
    word_count = Column(Integer)
    sentiment = Column(String(20))
    expiry_detected = Column(Boolean, default=False, index=True)
    expiry_date = Column(Date, index=True)
    expiry_type = Column(String(50))
    urgency_level = Column(String(20), default='low', index=True)
    extracted_text = Column(Text)
    important_notes = Column(ARRAY(String))  # Array of important notes
    compliance_requirements = Column(ARRAY(String))  # Array of compliance requirements
    document_sections = Column(ARRAY(String))  # Array of document sections
    key_findings = Column(ARRAY(String))  # Array of key findings
    data_points = Column(ARRAY(String))  # Array of numerical data and statistics
    action_items = Column(ARRAY(String))  # Array of action items and tasks
    compliance_analysis = Column(JSON)  # AI-generated detailed compliance analysis with reasons
    extracted_at = Column(DateTime)
    ai_model = Column(String(100))
    processing_status = Column(String(20), default='pending')
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

class ExpiryNotification(Base):
    """Model for tracking expiry notifications sent to HR admins"""
    __tablename__ = "expiry_notifications"

    id = Column(Integer, primary_key=True, index=True)
    document_analysis_id = Column(Integer, nullable=False, index=True)  # Reference to document_analysis table
    document_id = Column(String(255), nullable=False, index=True)  # Reference to documents table (UUID)
    user_id = Column(String(255), nullable=False, index=True)  # User who uploaded the document (UUID)
    user_name = Column(String(255), index=True)  # Username for easy reference
    user_email = Column(String(255))  # User email for notifications
    notification_type = Column(String(50), default='expiry_warning')
    expiry_date = Column(Date, index=True)
    days_until_expiry = Column(Integer)
    urgency_level = Column(String(20), index=True)
    notification_sent_at = Column(DateTime)
    notification_recipients = Column(ARRAY(String))  # Array of email addresses
    notification_status = Column(String(20), default='pending', index=True)  # pending, sent, failed
    notification_message = Column(Text)
    # Enhanced fields for AI agent
    ai_generated_reasons = Column(JSON, nullable=True)  # AI-generated expiry reasons
    recommended_action = Column(Text, nullable=True)  # AI-suggested action
    hr_notified = Column(Boolean, default=False)  # Whether HR was notified
    hr_notification_sent_at = Column(DateTime, nullable=True)
    reminder_count = Column(Integer, default=0)  # Number of reminders sent
    last_reminder_at = Column(DateTime, nullable=True)
    agent_run_id = Column(String(255), nullable=True, index=True)  # Link to the agent run that created this
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class ChatDocument(Base):
    """Minimal per-company table for chatbot document parsing results."""
    __tablename__ = "chat_documents"

    id = Column(String(255), primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    user_name = Column(String(255), index=True)
    filename = Column(String(500))
    content_type = Column(String(100))
    file_size = Column(Integer)
    extracted_text = Column(Text)
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class ChatMessage(Base):
    """Per-company chat history for questions/answers over a parsed document."""
    __tablename__ = "chat_messages"

    id = Column(String(255), primary_key=True, index=True)
    document_id = Column(String(255), index=True)
    user_id = Column(String(255), index=True)
    question = Column(Text)
    answer = Column(Text)
    model = Column(String(100))
    created_at = Column(DateTime, default=func.current_timestamp())


class ExpiryAgentRun(Base):
    """Track expiry agent execution runs"""
    __tablename__ = "expiry_agent_runs"

    id = Column(String(255), primary_key=True, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    run_date = Column(DateTime, default=func.current_timestamp())
    companies_processed = Column(Integer, default=0)
    documents_scanned = Column(Integer, default=0)
    notifications_sent = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    urgent_count = Column(Integer, default=0)  # Documents expiring in <=7 days
    upcoming_count = Column(Integer, default=0)  # Documents expiring in 8-30 days
    future_count = Column(Integer, default=0)  # Documents expiring in 31-90 days
    status = Column(String(50), default='pending', index=True)  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    run_type = Column(String(50), default='scheduled')  # scheduled, manual
    triggered_by = Column(String(255), nullable=True)  # User ID who triggered manual run
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    completed_at = Column(DateTime, nullable=True)


class ExpiryAgentConfig(Base):
    """Configuration for expiry agent per company"""
    __tablename__ = "expiry_agent_config"

    id = Column(String(255), primary_key=True, index=True)
    company_id = Column(String(255), nullable=False, unique=True, index=True)
    is_enabled = Column(Boolean, default=True)
    daily_run_time = Column(String(10), default='08:00')  # HH:MM format
    timezone = Column(String(50), default='UTC')
    urgent_threshold_days = Column(Integer, default=7)
    upcoming_threshold_days = Column(Integer, default=30)
    future_threshold_days = Column(Integer, default=90)
    send_user_emails = Column(Boolean, default=True)
    send_hr_summary = Column(Boolean, default=True)
    send_weekly_digest = Column(Boolean, default=True)
    hr_admin_emails = Column(ARRAY(String))  # List of HR admin emails to notify
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class HRChatAction(Base):
    """Track HR chatbot action executions"""
    __tablename__ = "hr_chat_actions"

    id = Column(String(255), primary_key=True, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    hr_user_id = Column(String(255), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)  # create_user, upload_document, bulk_create_users
    action_status = Column(String(50), default='pending', index=True)  # pending, confirmed, executed, cancelled, failed
    extracted_params = Column(JSON)  # Parameters extracted from chat query
    confirmation_message = Column(Text)  # Confirmation prompt shown to user
    user_response = Column(String(50), nullable=True)  # yes, no, modified
    execution_result = Column(JSON, nullable=True)  # Result of action execution
    error_message = Column(Text, nullable=True)
    created_resource_id = Column(String(255), nullable=True)  # ID of created user/document
    created_at = Column(DateTime, default=func.current_timestamp())
    confirmed_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Action expires if not confirmed within timeout


class BulkUserImport(Base):
    """Track bulk user import operations"""
    __tablename__ = "bulk_user_imports"

    id = Column(String(255), primary_key=True, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    hr_user_id = Column(String(255), nullable=False, index=True)
    filename = Column(String(500))
    file_type = Column(String(50))  # csv, excel
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    created_users = Column(Integer, default=0)
    skipped_users = Column(Integer, default=0)
    failed_users = Column(Integer, default=0)
    status = Column(String(50), default='pending', index=True)  # pending, validating, confirmed, processing, completed, failed
    validation_errors = Column(JSON, nullable=True)  # List of validation errors
    created_user_ids = Column(ARRAY(String), nullable=True)  # IDs of created users
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    completed_at = Column(DateTime, nullable=True)
