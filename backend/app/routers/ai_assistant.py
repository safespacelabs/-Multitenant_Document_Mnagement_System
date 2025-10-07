from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging
from datetime import datetime

from ..database import get_db
from ..models import Company
from ..models_company import User
from ..schemas import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    SmartSuggestionRequest,
    SmartSuggestionResponse,
    AIAssistantStats
)
from ..auth import get_current_user, get_current_company_user
from ..services.ai_service import AIService
from ..services.anthropic_service import anthropic_service
from ..services.document_analysis_service import document_analysis_service
from ..services.database_manager import db_manager

router = APIRouter(prefix="/api/ai-assistant", tags=["AI Assistant"])

# Initialize AI Service
ai_service = AIService()

@router.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Create a new AI chat session for company users"""
    try:
        # Get company from user's company_id
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        session = ai_service.create_chat_session(
            user_id=current_user.id,
            company_id=company.id,
            session_name=session_data.session_name,
            context=session_data.context
        )
        return ChatSessionResponse(
            id=session.id,
            session_name=session.session_name,
            created_at=session.created_at,
            last_activity=session.last_activity,
            message_count=session.message_count
        )
    except Exception as e:
        logging.error(f"Failed to create chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )

@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for the current user in their company"""
    try:
        # Get company from user's company_id
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        sessions = ai_service.get_user_chat_sessions(
            user_id=current_user.id,
            company_id=company.id
        )
        return sessions
    except Exception as e:
        logging.error(f"Failed to get chat sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat sessions"
        )

@router.post("/chat/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Send a message to AI Assistant and get response"""
    try:
        # Get company from user's company_id
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        # Get company context for AI
        company_context = {
            "company_name": company.name,
            "company_industry": getattr(company, 'industry', 'General'),
            "user_role": current_user.role,
            "user_department": getattr(current_user, 'department', 'General')
        }
        
        # Process message with AI service
        response = ai_service.process_chat_message(
            user_id=current_user.id,
            company_id=company.id,
            session_id=message_data.session_id,
            message=message_data.message,
            message_type=message_data.message_type,
            company_context=company_context
        )
        
        return ChatMessageResponse(
            id=response.get("id"),
            session_id=response.get("session_id"),
            message=response.get("message"),
            response=response.get("response"),
            message_type=response.get("message_type"),
            timestamp=response.get("timestamp"),
            ai_response_time=response.get("ai_response_time")
        )
    except Exception as e:
        logging.error(f"Failed to process chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )

@router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: str,
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Get all messages for a specific chat session"""
    try:
        # Get company from user's company_id
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        messages = ai_service.get_chat_session_messages(
            session_id=session_id,
            user_id=current_user.id,
            company_id=company.id
        )
        return messages
    except Exception as e:
        logging.error(f"Failed to get chat messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat messages"
        )

@router.post("/chat/ask-about-document")
async def ask_about_document(
    file: UploadFile = File(...),
    question: str = Form(...),
    read_content: bool = Form(False),
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Upload a document and ask a question grounded in its content using Anthropic.
    Returns a simple JSON with the assistant's answer and minimal metadata.
    """
    try:
        content = await file.read()
        result = await anthropic_service.answer_question_about_file(content, file.filename, question, read_content=read_content)
        return {
            "answer": result.get("answer"),
            "filename": file.filename,
            "metadata": result.get("metadata")
        }
    except Exception as e:
        logging.error(f"ask_about_document failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the uploaded document"
        )

@router.post("/documents/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    analysis_request: DocumentAnalysisRequest,
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Analyze a document using AI for company-specific insights"""
    try:
        # Get company from user's company_id
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        analysis = ai_service.analyze_document(
            document_id=analysis_request.document_id,
            analysis_type=analysis_request.analysis_type,
            company_context={
                "company_name": company.name,
                "industry": getattr(company, 'industry', 'General'),
                "user_role": current_user.role
            }
        )
        
        return DocumentAnalysisResponse(
            document_id=analysis.document_id,
            analysis_type=analysis.analysis_type,
            insights=analysis.insights,
            summary=analysis.summary,
            recommendations=analysis.recommendations,
            confidence_score=analysis.confidence_score,
            analysis_timestamp=analysis.analysis_timestamp
        )
    except Exception as e:
        logging.error(f"Failed to analyze document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze document"
        )

@router.post("/suggestions", response_model=SmartSuggestionResponse)
async def get_smart_suggestions(
    suggestion_request: SmartSuggestionRequest,
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered smart suggestions for company operations"""
    try:
        # Get company from user's company_id
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        suggestions = ai_service.generate_smart_suggestions(
            user_id=current_user.id,
            company_id=company.id,
            suggestion_type=suggestion_request.suggestion_type,
            context=suggestion_request.context
        )
        
        return SmartSuggestionResponse(
            suggestions=suggestions.suggestions,
            reasoning=suggestions.reasoning,
            priority=suggestions.priority,
            category=suggestions.category,
            generated_at=suggestions.generated_at
        )
    except Exception as e:
        logging.error(f"Failed to generate suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions"
        )

@router.get("/stats", response_model=AIAssistantStats)
async def get_ai_assistant_stats(
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Get AI Assistant usage statistics for the company"""
    try:
        # Get company from user's company_id
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        stats = ai_service.get_company_ai_stats(
            company_id=company.id,
            user_id=current_user.id
        )
        
        return AIAssistantStats(
            total_chat_sessions=stats.get("total_chat_sessions", 0),
            total_messages=stats.get("total_messages", 0),
            documents_analyzed=stats.get("documents_analyzed", 0),
            suggestions_generated=stats.get("suggestions_generated", 0),
            average_response_time=stats.get("average_response_time", 0.0),
            most_used_features=stats.get("most_used_features", []),
            company_usage_trend=stats.get("company_usage_trend", {})
        )
    except Exception as e:
        logging.error(f"Failed to get AI stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI statistics"
        )

@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages"""
    try:
        # Get company from user's company_id
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
        ai_service.delete_chat_session(
            session_id=session_id,
            user_id=current_user.id,
            company_id=company.id
        )
        return {"message": "Chat session deleted successfully"}
    except Exception as e:
        logging.error(f"Failed to delete chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session"
        )

@router.post("/chat/ask-about-document-id")
async def ask_about_document_id(
    payload: dict,
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Answer a question grounded in a previously uploaded document using stored extracted text.
    Body: { "document_id": str, "question": str }
    """
    try:
        document_id = payload.get("document_id")
        question = payload.get("question")
        if not document_id or not question:
            raise HTTPException(status_code=400, detail="document_id and question are required")

        # Resolve company DB url
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        # Open company database session
        company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
        company_db = next(company_db_gen)
        try:
            answer = await document_analysis_service.chat_with_document(document_id, question, company_db)
            return {"answer": answer, "document_id": document_id}
        finally:
            company_db.close()
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"ask_about_document_id failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to answer question for the document")

@router.post("/chat/upload-and-ask")
async def upload_and_ask(
    file: UploadFile = File(...),
    question: str = Form(...),
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Upload any document, parse locally, store as ChatDocument, and answer question using stored text only."""
    try:
        content = await file.read()
        # Enforce backend size limit up to 200MB
        if len(content) > 200 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 200MB")
        filename = file.filename or "uploaded"
        content_type = file.content_type or "application/octet-stream"

        # Extract using existing service (text/pdf/ocr/vision)
        metadata = await anthropic_service.extract_document_metadata(content, filename)
        extracted_text = (metadata or {}).get("extracted_text") or ""

        # Store in per-company ChatDocument
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
        company_db = next(company_db_gen)
        try:
            chat_doc = await document_analysis_service.upsert_chat_document(
                user_id=current_user.id,
                user_name=getattr(current_user, "username", ""),
                filename=filename,
                content_type=content_type,
                file_size=len(content or b"") or 0,
                extracted_text=extracted_text,
                metadata=metadata,
                company_db=company_db
            )

            # Answer and store message
            msg = await document_analysis_service.answer_and_store_chat(
                document_id=chat_doc.id,
                user_id=current_user.id,
                question=question,
                company_db=company_db
            )
            return {
                "document_id": chat_doc.id,
                "answer": msg.answer,
                "question": msg.question,
                "model": msg.model
            }
        finally:
            company_db.close()
    except Exception as e:
        logging.error(f"upload_and_ask failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process document and answer question")
