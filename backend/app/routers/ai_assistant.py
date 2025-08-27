from fastapi import APIRouter, Depends, HTTPException, status
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
            id=response.id,
            session_id=response.session_id,
            message=response.message,
            response=response.response,
            message_type=response.message_type,
            timestamp=response.timestamp,
            ai_response_time=response.ai_response_time
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
            total_chat_sessions=stats.total_chat_sessions,
            total_messages=stats.total_messages,
            documents_analyzed=stats.documents_analyzed,
            suggestions_generated=stats.suggestions_generated,
            average_response_time=stats.average_response_time,
            most_used_features=stats.most_used_features,
            company_usage_trend=stats.company_usage_trend
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
