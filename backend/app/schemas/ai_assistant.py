from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

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
