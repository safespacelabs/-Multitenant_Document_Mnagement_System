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
    document_id = Column(Integer, nullable=False, index=True)  # Reference to documents table
    user_id = Column(Integer, nullable=False, index=True)  # User who uploaded the document
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
    extracted_at = Column(DateTime, default=func.current_timestamp())
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
    document_id = Column(Integer, nullable=False, index=True)  # Reference to documents table
    user_id = Column(Integer, nullable=False, index=True)  # User who uploaded the document
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
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
