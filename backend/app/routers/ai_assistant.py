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
from ..services.aws_service import aws_service
from ..services.chunked_document_service import chunked_document_service

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
@router.post("/chat/ask-about-chunked-document")
async def ask_about_chunked_document(
    payload: dict,
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Ask a question about a previously uploaded chunked document."""
    try:
        chunked_document_id = payload.get("document_id")
        question = payload.get("question")
        
        if not chunked_document_id or not question:
            raise HTTPException(status_code=400, detail="document_id and question are required")
        
        # Get company database connection
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
        company_db = next(company_db_gen)
        
        try:
            # Search across all chunks for the answer
            search_result = await chunked_document_service.search_across_chunks(
                chunked_document_id=chunked_document_id,
                query=question,
                company_db=company_db
            )
            
            if 'error' in search_result:
                raise HTTPException(status_code=404, detail=search_result['error'])
            
            # Get document info
            doc_info = chunked_document_service.get_chunked_document_info(
                chunked_document_id=chunked_document_id,
                company_db=company_db
            )
            
            return {
                "document_id": chunked_document_id,
                "answer": search_result['answer'],
                "filename": doc_info.get('filename', 'Unknown'),
                "total_pages": doc_info.get('total_pages', 0),
                "total_chunks": doc_info.get('total_chunks', 0),
                "relevant_chunks": search_result.get('relevant_chunks', []),
                "search_method": search_result.get('search_method', 'multi_chunk_search'),
                "total_chunks_searched": search_result.get('total_chunks_searched', 0),
                "relevant_chunks_found": search_result.get('relevant_chunks_found', 0)
            }
            
        finally:
            company_db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"ask_about_chunked_document failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to answer question for the chunked document")

@router.get("/chat/chunked-documents")
async def list_chunked_documents(
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """List all chunked documents for the current user's company."""
    try:
        # Get company database connection
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
        company_db = next(company_db_gen)
        
        try:
            from app.models_chunked_documents import ChunkedDocument
            
            chunked_docs = company_db.query(ChunkedDocument).filter(
                ChunkedDocument.is_active == True
            ).order_by(ChunkedDocument.created_at.desc()).all()
            
            documents = []
            for doc in chunked_docs:
                documents.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "total_pages": doc.total_pages,
                    "total_chunks": doc.total_chunks,
                    "total_characters": doc.total_characters,
                    "processing_status": doc.processing_status,
                    "created_at": doc.created_at,
                    "user_name": doc.user_name
                })
            
            return {"documents": documents}
            
        finally:
            company_db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"list_chunked_documents failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list chunked documents")

@router.get("/chat/chunked-document/{document_id}/info")
async def get_chunked_document_info(
    document_id: str,
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific chunked document."""
    try:
        # Get company database connection
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
        company_db = next(company_db_gen)
        
        try:
            doc_info = chunked_document_service.get_chunked_document_info(
                chunked_document_id=document_id,
                company_db=company_db
            )
            
            if 'error' in doc_info:
                raise HTTPException(status_code=404, detail=doc_info['error'])
            
            return doc_info
            
        finally:
            company_db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"get_chunked_document_info failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chunked document info")

@router.post("/chat/upload-and-ask")
async def upload_and_ask(
    file: UploadFile = File(...),
    question: str = Form(...),
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Upload any document, automatically chunk if large, and answer question using all available content."""
    try:
        content = await file.read()
        # Enforce backend size limit up to 1GB
        if len(content) > 1024 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 1GB")
        filename = file.filename or "uploaded"
        content_type = file.content_type or "application/octet-stream"

        # Store in per-company database
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
        company_db = next(company_db_gen)
        
        try:
            # Check if this is a large document that needs chunking
            import PyPDF2
            import io
            
            is_large_document = False
            if filename.lower().endswith('.pdf'):
                try:
                    pdf_file = io.BytesIO(content)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    page_count = len(pdf_reader.pages)
                    
                    # Estimate if document is large (more than ~30 pages or 50k characters)
                    if page_count > 30:
                        is_large_document = True
                        print(f"🔍 Large document detected: {filename} ({page_count} pages)")
                except Exception as e:
                    print(f"⚠️ Could not determine PDF size: {e}")
            
            if is_large_document:
                # Process as chunked document
                result = await chunked_document_service.process_large_document_upload(
                    file_content=content,
                    filename=filename,
                    folder_name=None,
                    user_id=current_user.id,
                    user_name=getattr(current_user, "username", ""),
                    user_email=getattr(current_user, "email", ""),
                    company_db=company_db
                )
                
                if result.get('success', False):
                    chunked_document_id = result.get('chunked_document_id')
                    total_pages = result.get('total_pages', 0)
                    total_chunks = result.get('total_chunks', 0)
                    
                    # Search across all chunks for the answer
                    search_result = await chunked_document_service.search_across_chunks(
                        chunked_document_id=chunked_document_id,
                        query=question,
                        company_db=company_db
                    )
                    
                    if 'error' in search_result:
                        return {"error": search_result['error']}
                    
                    return {
                        "document_id": chunked_document_id,
                        "answer": search_result['answer'],
                        "is_chunked_document": True,
                        "total_pages": total_pages,
                        "total_chunks": total_chunks,
                        "relevant_chunks": search_result.get('relevant_chunks', []),
                        "search_method": search_result.get('search_method', 'multi_chunk_search')
                    }
                else:
                    return {"error": result.get('error', 'Failed to process large document')}
            else:
                # Process as regular document (existing logic)
                extracted_text = anthropic_service.extract_plain_text(content, filename)
                metadata = {"title": filename, "processing_status": "plain_text", "extracted_at": datetime.utcnow().isoformat()}

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

                # Answer from extracted text only and store
                answer_text = await anthropic_service.answer_question(chat_doc.extracted_text or "", question)
                msg = await document_analysis_service.answer_and_store_chat(document_id=chat_doc.id, user_id=current_user.id, question=question, company_db=company_db)
                msg.answer = answer_text
                company_db.commit()
                
                return {
                    "document_id": chat_doc.id, 
                    "answer": answer_text,
                    "is_chunked_document": False
                }
                
        finally:
            company_db.close()
            
    except Exception as e:
        logging.error(f"upload_and_ask failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process document and answer question")

@router.post("/chat/multipart/initiate")
async def initiate_multipart_upload(
    filename: str = Form(...),
    content_type: str = Form(None),
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """Initiate a multipart upload to S3 for very large files and return upload parameters."""
    try:
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        if not company.s3_bucket_name:
            # You may create bucket on demand here if desired
            raise HTTPException(status_code=400, detail="Company S3 bucket not configured")

        # Sanitize and generate a key
        import uuid
        file_id = str(uuid.uuid4())
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        s3_key = f"company-documents/{company.id}/chat-uploads/{file_id}.{ext}" if ext else f"company-documents/{company.id}/chat-uploads/{file_id}"

        init = await aws_service.create_multipart_upload(company.s3_bucket_name, s3_key, content_type)
        return {"uploadId": init["UploadId"], "key": init["Key"], "bucket": company.s3_bucket_name}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"initiate_multipart_upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate multipart upload")

@router.get("/chat/multipart/part-url")
async def get_multipart_part_url(
    key: str,
    uploadId: str,
    partNumber: int,
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    try:
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        url = await aws_service.generate_presigned_part_url(company.s3_bucket_name, key, uploadId, partNumber)
        return {"url": url}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"get_multipart_part_url failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get part URL")

@router.post("/chat/multipart/complete")
async def complete_multipart(
    key: str = Form(...),
    uploadId: str = Form(...),
    parts_json: str = Form(...),  # JSON: [{"ETag":"...","PartNumber":1},...]
    question: str = Form(...),
    current_user: User = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    try:
        import json as _json
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        parts = _json.loads(parts_json)
        await aws_service.complete_multipart_upload(company.s3_bucket_name, key, uploadId, parts)

        # Download the object to process
        file_bytes = await aws_service.download_file(company.s3_bucket_name, key)
        filename = key.split('/')[-1]
        extracted_text = anthropic_service.extract_plain_text(file_bytes, filename)
        metadata = {"title": filename, "processing_status": "plain_text", "extracted_at": datetime.utcnow().isoformat()}

        # Store and answer
        company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
        company_db = next(company_db_gen)
        try:
            chat_doc = await document_analysis_service.upsert_chat_document(
                user_id=current_user.id,
                user_name=getattr(current_user, "username", ""),
                filename=filename,
                content_type=None,
                file_size=len(file_bytes or b""),
                extracted_text=extracted_text,
                metadata=metadata,
                company_db=company_db
            )
            answer_text = await anthropic_service.answer_question(chat_doc.extracted_text or "", question)
            msg = await document_analysis_service.answer_and_store_chat(document_id=chat_doc.id, user_id=current_user.id, question=question, company_db=company_db)
            msg.answer = answer_text
            company_db.commit()
            return {"document_id": chat_doc.id, "answer": answer_text}
        finally:
            company_db.close()
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"complete_multipart failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete upload and process document")
