from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import secrets

# Base for management database tables
Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(String, primary_key=True, default=lambda: f"comp_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    s3_bucket_name = Column(String, nullable=False)
    database_name = Column(String, nullable=False)
    database_url = Column(String, nullable=False)  # Connection string for company's database
    database_host = Column(String, nullable=False)
    database_port = Column(String, nullable=False, default="5432")
    database_user = Column(String, nullable=False)
    database_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
class SystemUser(Base):
    __tablename__ = "system_users"
    
    id = Column(String, primary_key=True, default=lambda: f"sysuser_{uuid.uuid4().hex[:8]}")
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="system_admin")  # Only system_admin for management db
    s3_bucket_name = Column(String, nullable=True)  # System-level S3 bucket
    s3_folder = Column(String, nullable=True)  # System admin's folder in S3
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class SystemDocument(Base):
    __tablename__ = "system_documents"
    
    id = Column(String, primary_key=True, default=lambda: f"sysdoc_{uuid.uuid4().hex[:8]}")
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # S3 key/path
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    folder_name = Column(String, nullable=True)  # System admin folder organization
    user_id = Column(String, ForeignKey("system_users.id"), nullable=False)
    processed = Column(Boolean, default=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("SystemUser", backref="documents")
    
class CompanyDatabaseLog(Base):
    __tablename__ = "company_database_logs"
    
    id = Column(String, primary_key=True, default=lambda: f"dblog_{uuid.uuid4().hex[:8]}")
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    action = Column(String, nullable=False)  # created, connected, error, deleted
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company")

class SystemChatHistory(Base):
    __tablename__ = "system_chat_history"
    
    id = Column(String, primary_key=True, default=lambda: f"chat_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("system_users.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    context_data = Column(JSON, nullable=True)  # Store system context like companies, stats, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("SystemUser", backref="chat_history") 