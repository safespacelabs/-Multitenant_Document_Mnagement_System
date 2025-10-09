"""
Database models for chunked document storage
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

# Base for company-specific database tables
Base = declarative_base()

class ChunkedDocument(Base):
    """Master document record for chunked documents"""
    __tablename__ = "chunked_documents"
    
    id = Column(String, primary_key=True, default=lambda: f"chunkdoc_{uuid.uuid4().hex[:8]}")
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    folder_name = Column(String, nullable=True)
    user_id = Column(Integer, nullable=False)
    user_name = Column(String, nullable=False)
    user_email = Column(String, nullable=False)
    
    # Document statistics
    total_pages = Column(Integer, nullable=False)
    total_chunks = Column(Integer, nullable=False)
    total_characters = Column(Integer, nullable=False)
    
    # Processing status
    processing_status = Column(String, nullable=False, default="processing")
    processing_started_at = Column(DateTime, default=datetime.utcnow)
    processing_completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class DocumentChunk(Base):
    """Individual chunk of a chunked document"""
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, default=lambda: f"chunk_{uuid.uuid4().hex[:8]}")
    chunked_document_id = Column(String, ForeignKey("chunked_documents.id"), nullable=False)
    
    # Chunk identification
    chunk_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    chunk_id = Column(String, nullable=False)  # UUID for the chunk
    
    # Page information
    start_page = Column(Integer, nullable=False)
    end_page = Column(Integer, nullable=False)
    page_count = Column(Integer, nullable=False)
    
    # Content
    extracted_text = Column(Text, nullable=False)
    character_count = Column(Integer, nullable=False)
    word_count = Column(Integer, nullable=False)
    
    # AI processing
    metadata_json = Column(JSON, nullable=True)
    processing_status = Column(String, nullable=False, default="pending")
    processed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class ChunkedDocumentAnalysis(Base):
    """Analysis results for chunked documents"""
    __tablename__ = "chunked_document_analyses"
    
    id = Column(String, primary_key=True, default=lambda: f"analysis_{uuid.uuid4().hex[:8]}")
    chunked_document_id = Column(String, ForeignKey("chunked_documents.id"), nullable=False)
    
    # Analysis metadata
    analysis_type = Column(String, nullable=False)  # 'full_document', 'chunk_specific', 'cross_chunk'
    chunk_id = Column(String, nullable=True)  # If analysis is chunk-specific
    
    # Results
    analysis_results = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=True)
    
    # Processing info
    model_used = Column(String, nullable=False)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class ChunkedDocumentChat(Base):
    """Chat history for chunked documents"""
    __tablename__ = "chunked_document_chats"
    
    id = Column(String, primary_key=True, default=lambda: f"chat_{uuid.uuid4().hex[:8]}")
    chunked_document_id = Column(String, ForeignKey("chunked_documents.id"), nullable=False)
    
    # Chat information
    user_id = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    
    # Context information
    relevant_chunks = Column(JSON, nullable=True)  # List of chunk IDs that were relevant
    search_method = Column(String, nullable=False)  # 'full_search', 'chunk_specific', 'semantic_search'
    
    # AI processing info
    model_used = Column(String, nullable=False)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
