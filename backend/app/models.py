from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(String, primary_key=True, default=lambda: f"comp_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    s3_bucket_name = Column(String, nullable=False)
    database_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    users = relationship("User", back_populates="company")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:8]}")
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="employee")  # admin, employee
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    s3_folder = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    company = relationship("Company", back_populates="users")
    documents = relationship("Document", back_populates="user")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    metadata_json = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="documents")
    company = relationship("Company")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(String, primary_key=True, default=lambda: f"chat_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    context_documents = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    company = relationship("Company") 