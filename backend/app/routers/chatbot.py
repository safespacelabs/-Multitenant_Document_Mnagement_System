from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_management_db, get_company_db
from app import models, schemas, auth
from app.models_company import User as CompanyUser, ChatHistory as CompanyChatHistory, Document as CompanyDocument
from app.services.nlp_service import nlp_service
from app.services.intelligent_ai_service import intelligent_ai_service
from app.services.document_analysis_service import document_analysis_service
from app.services.hr_admin_database_service import hr_admin_database_service
from app.services.rag_service import rag_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def process_enhanced_chat_query(query: str, current_user: CompanyUser, company_db: Session, company_id: str, document_ids: list = None) -> tuple[str, list]:
    """Enhanced chat processing with automatic query type detection (I9, documents, or general)"""
    try:
        query_lower = query.lower()

        # Check if user is HR admin and provide comprehensive database access
        if current_user.role in ['hr_admin', 'hr_manager']:
            # HR admin gets access to entire company database
            hr_admin_response = await hr_admin_database_service.process_hr_admin_query(query, company_db)
            return hr_admin_response, []

        # ===== AUTOMATIC I9 DETECTION =====
        # Check if query is specifically about I9 documents/forms
        i9_keywords = ['i9', 'i-9', 'form i9', 'form i-9', 'i9 form', 'i-9 form',
                       'i9 compliance', 'employment verification', 'work authorization']
        i9_actions = ['expiring', 'expired', 'invalid', 'compliance', 'verification']

        is_i9_query = any(keyword in query_lower for keyword in i9_keywords)

        # If it's an I9 query, route to I9-specific endpoints
        if is_i9_query:
            logger.info(f"🏢 Detected I9 query: {query[:100]}")
            try:
                # Check what kind of I9 query it is
                if any(action in query_lower for action in ['expiring', 'expire soon', 'about to expire', 'will expire']):
                    # Get expiring I9 documents
                    days = 30  # Default to 30 days
                    if '60 day' in query_lower or 'two month' in query_lower:
                        days = 60
                    elif '90 day' in query_lower or 'three month' in query_lower:
                        days = 90

                    expiring = await rag_service.get_expiring_i9_documents(
                        company_id=company_id,
                        days=days,
                        user_id=str(current_user.id)
                    )

                    count = expiring.get('count', 0)
                    if count > 0:
                        docs_list = "\n".join([f"- {doc['employee_name']} (expires: {doc['expiration_date']})"
                                              for doc in expiring.get('documents', [])[:10]])
                        return f"🏢 **I9 Forms Expiring in {days} Days:**\n\n{count} I9 form(s) expiring soon:\n\n{docs_list}", []
                    else:
                        return f"✅ No I9 forms expiring in the next {days} days.", []

                elif any(action in query_lower for action in ['expired', 'past due', 'overdue']):
                    # Get expired I9 documents
                    expired = await rag_service.get_expired_i9_documents(
                        company_id=company_id,
                        user_id=str(current_user.id)
                    )

                    count = expired.get('count', 0)
                    if count > 0:
                        docs_list = "\n".join([f"- {doc['employee_name']} (expired: {doc['expiration_date']})"
                                              for doc in expired.get('documents', [])[:10]])
                        return f"⚠️ **Expired I9 Forms:**\n\n{count} expired I9 form(s):\n\n{docs_list}\n\n**Action Required:** Please update these forms immediately.", []
                    else:
                        return f"✅ No expired I9 forms found.", []

                elif any(action in query_lower for action in ['invalid', 'problem', 'issue', 'missing']):
                    # Get invalid I9 documents
                    invalid = await rag_service.get_invalid_i9_documents(
                        company_id=company_id,
                        user_id=str(current_user.id)
                    )

                    count = invalid.get('count', 0)
                    if count > 0:
                        docs_list = "\n".join([f"- {doc['employee_name']} ({doc.get('issue', 'Issue detected')})"
                                              for doc in invalid.get('documents', [])[:10]])
                        return f"⚠️ **Invalid/Problem I9 Forms:**\n\n{count} I9 form(s) with issues:\n\n{docs_list}", []
                    else:
                        return f"✅ No invalid I9 forms found.", []

                else:
                    # General I9 summary
                    summary = await rag_service.get_i9_summary(
                        company_id=company_id,
                        user_id=str(current_user.id)
                    )

                    total = summary.get('total_i9_documents', 0)
                    valid = summary.get('valid_count', 0)
                    expiring = summary.get('expiring_soon_count', 0)
                    expired = summary.get('expired_count', 0)

                    return (f"🏢 **I9 Compliance Summary:**\n\n"
                           f"📊 Total I9 Forms: {total}\n"
                           f"✅ Valid: {valid}\n"
                           f"⏰ Expiring Soon: {expiring}\n"
                           f"⚠️ Expired: {expired}\n\n"
                           f"Ask me specific questions like 'show expiring I9 forms' or 'which I9s are invalid'"), []

            except Exception as i9_error:
                logger.warning(f"I9 service error: {str(i9_error)}")
                return "I couldn't fetch I9 information at this time. The I9 tracking service may still be processing documents.", []

        # ===== AUTOMATIC DOCUMENT DETECTION =====
        # Check if query mentions specific document names or asks about document content
        document_indicators = ['document', 'file', 'pdf', 'contract', 'report', 'form', 'resume',
                              'invoice', 'receipt', 'certificate', 'letter', 'agreement']
        content_questions = ['what', 'how', 'why', 'when', 'where', 'who', 'explain', 'describe',
                           'tell me about', 'summarize', 'summary', 'compare', 'difference', 'show me']

        mentions_document = any(indicator in query_lower for indicator in document_indicators)
        is_content_query = any(question in query_lower for question in content_questions)

        # Use RAG if query is about document content or mentions documents
        use_rag = (mentions_document and is_content_query) or document_ids

        if use_rag:
            try:
                logger.info(f"📄 Auto-detected DOCUMENT query: {query[:100]}")
                if document_ids:
                    logger.info(f"Using specific documents: {document_ids}")
                else:
                    logger.info(f"Searching all available documents automatically")

                # First, check if there are any documents in the RAG service
                try:
                    rag_docs = await rag_service.list_documents(
                        company_id=company_id,
                        user_id=str(current_user.id)
                    )
                    logger.info(f"Found {len(rag_docs)} documents in RAG service for company {company_id}")

                    if len(rag_docs) == 0:
                        # No documents in RAG service yet
                        logger.warning("No documents found in RAG service")
                        # Check if there are documents in the company database
                        company_docs_count = company_db.query(CompanyDocument).filter(
                            CompanyDocument.company_id == company_id
                        ).count()

                        if company_docs_count > 0:
                            return (
                                f"📄 I can see you have {company_docs_count} document(s) in the system, but they haven't been processed yet.\n\n"
                                f"⏳ **Processing Status**: Documents typically take 10-15 seconds to process.\n\n"
                                f"💡 **Tip**: Please wait a moment and try your question again. If you just uploaded a document, give it a few seconds to finish processing.",
                                []
                            )
                except Exception as list_error:
                    logger.warning(f"Failed to list RAG documents: {str(list_error)}")

                # Query using advanced RAG service with optional document filtering
                rag_result = await rag_service.query_documents(
                    question=query,
                    company_id=company_id,
                    user_id=str(current_user.id),
                    document_ids=document_ids,  # Pass selected document IDs for focused search
                    limit=12  # Get top 12 most relevant chunks
                )

                if rag_result and rag_result.get('answer'):
                    answer = f"🤖 **RAG-Powered Answer:**\n\n{rag_result['answer']}\n\n"

                    # Add context information
                    debug_info = rag_result.get('debug', {})
                    if debug_info:
                        total_chunks = debug_info.get('total_chunks', 0)
                        docs_used = debug_info.get('documents_used', {})

                        if total_chunks > 0:
                            answer += f"\n\n📊 **Sources:** Found {total_chunks} relevant sections"
                            if docs_used:
                                answer += f" across {len(docs_used)} document(s)"
                        else:
                            # No chunks found - documents might still be processing
                            answer += f"\n\n⚠️ **Note**: No specific document sections found. If you just uploaded documents, they may still be processing (takes 10-15 seconds)."

                    # Extract document IDs from contexts for reference
                    contexts = rag_result.get('contexts', [])
                    doc_ids = list(set([ctx.get('document_id') for ctx in contexts if ctx.get('document_id')]))

                    return answer, doc_ids

            except Exception as rag_error:
                logger.warning(f"RAG service error, falling back to basic search: {str(rag_error)}")
                # Fall through to basic document search if RAG fails
        
        # Check if query is about documents, folders, or expiry
        document_keywords = ['document', 'file', 'folder', 'upload', 'expiry', 'expire', 'passport', 'license', 'card']
        is_document_query = any(keyword in query_lower for keyword in document_keywords)
        
        if is_document_query:
            # Search for relevant documents
            relevant_docs = document_analysis_service.search_documents_by_content(query, company_db, limit=5)
            
            if relevant_docs:
                # Get expiring documents if asking about expiry
                if any(word in query_lower for word in ['expiry', 'expire', 'expiring']):
                    expiring_docs = document_analysis_service.get_expiring_documents(company_db, days_ahead=90)
                    if expiring_docs:
                        answer = f"📋 **Document Expiry Information**\n\n"
                        answer += f"I found {len(expiring_docs)} documents with upcoming expiry dates:\n\n"
                        
                        for doc in expiring_docs[:5]:  # Show top 5
                            urgency_emoji = "🚨" if doc.urgency_level == "high" else "⚠️" if doc.urgency_level == "medium" else "ℹ️"
                            answer += f"{urgency_emoji} **{doc.title}**\n"
                            answer += f"   • Type: {doc.document_type}\n"
                            answer += f"   • Folder: {doc.folder_name}\n"
                            answer += f"   • Expiry: {doc.expiry_date}\n"
                            answer += f"   • Urgency: {doc.urgency_level.upper()}\n\n"
                        
                        if len(expiring_docs) > 5:
                            answer += f"... and {len(expiring_docs) - 5} more documents with upcoming expiry dates.\n\n"
                        
                        answer += "💡 **Recommendation:** Please review these documents and take necessary action before they expire."
                        
                        return answer, [doc.document_id for doc in expiring_docs[:5]]
                
                # General document search response
                answer = f"📄 **Found {len(relevant_docs)} relevant documents:**\n\n"
                
                for doc in relevant_docs:
                    answer += f"📁 **{doc.title}**\n"
                    answer += f"   • Type: {doc.document_type}\n"
                    answer += f"   • Folder: {doc.folder_name}\n"
                    answer += f"   • Uploaded by: {doc.user_name}\n"
                    answer += f"   • Summary: {doc.summary[:100]}...\n"
                    
                    if doc.expiry_detected and doc.expiry_date:
                        urgency_emoji = "🚨" if doc.urgency_level == "high" else "⚠️" if doc.urgency_level == "medium" else "ℹ️"
                        answer += f"   • {urgency_emoji} Expiry: {doc.expiry_date} ({doc.urgency_level.upper()})\n"
                    
                    answer += "\n"
                
                return answer, [doc.document_id for doc in relevant_docs]
        
        # Check for folder-specific queries
        if 'folder' in query_lower:
            # Extract folder name from query (simple extraction)
            words = query.split()
            folder_name = None
            for i, word in enumerate(words):
                if word.lower() in ['folder', 'in'] and i + 1 < len(words):
                    folder_name = words[i + 1].strip('.,!?')
                    break
            
            if folder_name:
                folder_docs = document_analysis_service.get_documents_by_folder(folder_name, company_db)
                if folder_docs:
                    answer = f"📁 **Documents in '{folder_name}' folder:**\n\n"
                    for doc in folder_docs[:10]:  # Show top 10
                        answer += f"📄 **{doc.title}**\n"
                        answer += f"   • Type: {doc.document_type}\n"
                        answer += f"   • Uploaded by: {doc.user_name}\n"
                        answer += f"   • Summary: {doc.summary[:100]}...\n\n"
                    
                    if len(folder_docs) > 10:
                        answer += f"... and {len(folder_docs) - 10} more documents in this folder."
                    
                    return answer, [doc.document_id for doc in folder_docs[:10]]
        
        # Check for document type queries
        doc_types = ['passport', 'license', 'card', 'contract', 'report']
        for doc_type in doc_types:
            if doc_type in query_lower:
                type_docs = document_analysis_service.get_documents_by_type(doc_type, company_db)
                if type_docs:
                    answer = f"📋 **{doc_type.title()} Documents:**\n\n"
                    for doc in type_docs[:5]:
                        answer += f"📄 **{doc.title}**\n"
                        answer += f"   • Folder: {doc.folder_name}\n"
                        answer += f"   • Uploaded by: {doc.user_name}\n"
                        answer += f"   • Summary: {doc.summary[:100]}...\n\n"
                    
                    return answer, [doc.document_id for doc in type_docs[:5]]
        
        # Fallback to basic NLP service
        answer = nlp_service.process_query(
            query=query,
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            db=company_db
        )
        
        return answer, []
        
    except Exception as e:
        # Fallback to basic response
        answer = f"I apologize, but I encountered an error processing your question: {str(e)}"
        return answer, []

@router.post("/", response_model=schemas.ChatResponse)
async def chat_with_bot(
    chat_request: schemas.ChatRequest,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Enhanced chatbot with RAG service, document analysis integration
        answer, context_documents = await process_enhanced_chat_query(
            query=chat_request.question,
            current_user=current_user,
            company_db=company_db,
            company_id=str(company.id),
            document_ids=chat_request.document_ids  # Pass selected document IDs for context-aware responses
        )
        
        # Save chat history in company database
        chat_history = CompanyChatHistory(
            user_id=current_user.id,
            question=chat_request.question,
            answer=answer,
            context_documents=context_documents
        )
        
        company_db.add(chat_history)
        company_db.commit()
        company_db.refresh(chat_history)
        
        return {
            "answer": answer,
            "context_documents": context_documents,
            "created_at": chat_history.created_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")
    finally:
        company_db.close()

@router.get("/history")
async def get_chat_history(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        history = company_db.query(CompanyChatHistory).filter(
            CompanyChatHistory.user_id == current_user.id
        ).order_by(CompanyChatHistory.created_at.desc()).limit(50).all()
        
        return [
            {
                "id": chat.id,
                "question": chat.question,
                "answer": chat.answer,
                "created_at": chat.created_at
            }
            for chat in history
        ]
        
    finally:
        company_db.close()

@router.post("/document/{document_id}/chat")
async def chat_with_document(
    document_id: str,
    chat_request: schemas.ChatRequest,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Chat with a specific document using AI analysis"""
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        # Chat with the specific document
        answer = await document_analysis_service.chat_with_document(
            document_id=document_id,
            query=chat_request.question,
            company_db=company_db
        )
        
        return {
            "answer": answer,
            "document_id": document_id,
            "created_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document chat failed: {str(e)}")
    finally:
        company_db.close()

@router.get("/expiring-documents")
async def get_expiring_documents(
    days_ahead: int = 30,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get documents expiring within specified days"""
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        expiring_docs = document_analysis_service.get_expiring_documents(company_db, days_ahead)
        
        result = []
        for doc in expiring_docs:
            result.append({
                "document_id": doc.document_id,
                "title": doc.title,
                "document_type": doc.document_type,
                "folder_name": doc.folder_name,
                "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
                "urgency_level": doc.urgency_level,
                "summary": doc.summary
            })
        
        return {
            "expiring_documents": result,
            "count": len(result),
            "days_ahead": days_ahead
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get expiring documents: {str(e)}")
    finally:
        company_db.close()

# System Admin Chat Endpoints
@router.post("/system", response_model=schemas.ChatResponse)
async def system_chat_with_bot(
    chat_request: schemas.ChatRequest,
    current_user: models.SystemUser = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """System administrator chat endpoint."""
    try:
        # Process the question using intelligent AI service
        ai_result = await intelligent_ai_service.process_system_query(
            query=chat_request.question,
            user_id=str(current_user.id),
            management_db=management_db
        )
        
        # Save chat history in management database
        chat_history = models.SystemChatHistory(
            user_id=current_user.id,
            question=chat_request.question,
            answer=ai_result["response"],
            context_data={
                "task_executed": ai_result["task_executed"],
                "task_result": ai_result["task_result"],
                "actions_available": ai_result["actions_available"]
            }
        )
        
        management_db.add(chat_history)
        management_db.commit()
        management_db.refresh(chat_history)
        
        return {
            "answer": ai_result["response"],
            "context_documents": [],  # System admins don't have documents
            "created_at": chat_history.created_at,
            "task_executed": ai_result["task_executed"],
            "task_result": ai_result["task_result"],
            "actions_available": ai_result["actions_available"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System chat processing failed: {str(e)}")

@router.get("/system/history")
async def get_system_chat_history(
    current_user: models.SystemUser = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """Get system administrator chat history."""
    try:
        history = management_db.query(models.SystemChatHistory).filter(
            models.SystemChatHistory.user_id == current_user.id
        ).order_by(models.SystemChatHistory.created_at.desc()).limit(50).all()
        
        return [
            {
                "id": str(chat.id),
                "question": chat.question,
                "answer": chat.answer,
                "created_at": chat.created_at
            }
            for chat in history
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system chat history: {str(e)}")

# HR Admin Database Access Endpoints
@router.get("/hr-admin/company-overview")
async def get_company_overview(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get comprehensive company overview for HR admins"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")
    
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        overview = hr_admin_database_service.get_company_overview(company_db)
        return overview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get company overview: {str(e)}")
    finally:
        company_db.close()

@router.get("/hr-admin/users/search")
async def search_users(
    query: str,
    limit: int = 20,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Search users for HR admins"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")
    
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        users = hr_admin_database_service.search_users(query, company_db, limit)
        return {"users": users, "query": query, "count": len(users)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search users: {str(e)}")
    finally:
        company_db.close()

@router.get("/hr-admin/users/{user_id}")
async def get_user_details(
    user_id: str,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get detailed user information for HR admins"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")
    
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        user_details = hr_admin_database_service.get_user_details(user_id, company_db)
        return user_details
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user details: {str(e)}")
    finally:
        company_db.close()

@router.get("/hr-admin/analytics")
async def get_document_analytics(
    days: int = 30,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get document analytics for HR admins"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")
    
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        analytics = hr_admin_database_service.get_document_analytics(company_db, days)
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document analytics: {str(e)}")
    finally:
        company_db.close()

@router.get("/hr-admin/compliance")
async def get_compliance_status(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get compliance status for HR admins"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")
    
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        compliance = hr_admin_database_service.get_compliance_status(company_db)
        return compliance
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance status: {str(e)}")
    finally:
        company_db.close()

@router.get("/hr-admin/esignatures")
async def get_esignature_status(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get e-signature status for HR admins"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")
    
    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")
    
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    try:
        esignatures = hr_admin_database_service.get_esignature_status(company_db)
        return esignatures
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get e-signature status: {str(e)}")
    finally:
        company_db.close()

@router.get("/hr-admin/documents/search")
async def search_documents(
    query: str,
    limit: int = 20,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Search documents across all tables for HR admins"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")

    # Get company information
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        documents = hr_admin_database_service.search_documents(query, company_db, limit)
        return {"documents": documents, "query": query, "count": len(documents)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search documents: {str(e)}")
    finally:
        company_db.close()

# RAG-Specific Endpoints

@router.post("/rag/query")
async def rag_query(
    chat_request: schemas.ChatRequest,
    document_ids: list[str] = None,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """
    Advanced RAG query with vector similarity search, hybrid search, and re-ranking.

    This endpoint uses the deployed document extraction service for:
    - Semantic vector search with embeddings
    - Hybrid search (BM25 + vector)
    - Cross-encoder re-ranking for better accuracy
    - Multi-document queries
    """
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    try:
        # Query using RAG service
        rag_result = await rag_service.query_documents(
            question=chat_request.question,
            company_id=str(company_id),
            user_id=str(current_user.id),
            document_ids=document_ids,
            limit=12
        )

        return {
            "answer": rag_result.get('answer'),
            "contexts": rag_result.get('contexts', []),
            "debug": rag_result.get('debug', {}),
            "created_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

@router.get("/rag/i9/summary")
async def get_i9_summary(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get I9 compliance summary from RAG service"""
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    try:
        summary = await rag_service.get_i9_summary(
            company_id=str(company_id),
            user_id=str(current_user.id)
        )
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get I9 summary: {str(e)}")

@router.get("/rag/i9/expiring")
async def get_expiring_i9(
    days: int = 30,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get expiring I9 documents from RAG service"""
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    try:
        expiring = await rag_service.get_expiring_i9_documents(
            company_id=str(company_id),
            days=days,
            user_id=str(current_user.id)
        )
        return expiring

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get expiring I9 documents: {str(e)}")

@router.get("/rag/i9/expired")
async def get_expired_i9(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get expired I9 documents from RAG service"""
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    try:
        expired = await rag_service.get_expired_i9_documents(
            company_id=str(company_id),
            user_id=str(current_user.id)
        )
        return expired

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get expired I9 documents: {str(e)}")

@router.get("/rag/i9/invalid")
async def get_invalid_i9(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get invalid I9 documents from RAG service"""
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    try:
        invalid = await rag_service.get_invalid_i9_documents(
            company_id=str(company_id),
            user_id=str(current_user.id)
        )
        return invalid

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get invalid I9 documents: {str(e)}")

@router.get("/rag/health")
async def rag_health_check():
    """Check RAG service health"""
    try:
        health = await rag_service.health_check()
        models_health = await rag_service.models_health_check()

        return {
            "service": health,
            "models": models_health,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@router.get("/rag/documents")
async def list_rag_documents(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """
    List all documents in RAG service for debugging.

    This helps verify that documents are properly synced to the RAG service.
    """
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    try:
        # Get documents from RAG service
        rag_docs = await rag_service.list_documents(
            company_id=str(company_id),
            user_id=str(current_user.id)
        )

        # Get documents from company database for comparison
        company = management_db.query(models.Company).filter(
            models.Company.id == company_id
        ).first()

        if company:
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)

            try:
                company_docs = company_db.query(CompanyDocument).filter(
                    CompanyDocument.company_id == company_id
                ).all()

                company_doc_list = [
                    {
                        "id": doc.id,
                        "filename": doc.original_filename,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None,
                        "metadata": doc.metadata_json
                    }
                    for doc in company_docs
                ]
            finally:
                company_db.close()
        else:
            company_doc_list = []

        return {
            "rag_documents": rag_docs,
            "rag_document_count": len(rag_docs),
            "company_documents": company_doc_list,
            "company_document_count": len(company_doc_list),
            "sync_status": "synced" if len(rag_docs) == len(company_doc_list) else "out_of_sync",
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list RAG documents: {str(e)}")

@router.post("/rag/documents/{document_id}/re-upload")
async def re_upload_document_to_rag(
    document_id: str,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """
    Re-upload a specific document to the RAG service.

    Use this if a document failed to sync or you want to force a re-upload.
    """
    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        # Get document from database
        document = company_db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id,
            CompanyDocument.company_id == company_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get file from S3
        from app.services.aws_service import aws_service
        file_content = await aws_service.get_file_from_s3(
            bucket_name=company.s3_bucket_name,
            s3_key=document.s3_key
        )

        # Re-upload to RAG service
        logger.info(f"Re-uploading document {document_id} to RAG service")
        rag_upload_result = await rag_service.upload_document(
            file_content=file_content,
            filename=document.original_filename,
            company_id=str(company_id),
            user_id=str(current_user.id),
            metadata={
                "document_id": document.id,
                "folder_name": document.folder_name,
                "uploaded_by": current_user.username,
                "company_name": company.name,
                "re_upload": True
            }
        )

        # Update document metadata
        import json
        metadata = json.loads(document.metadata_json or '{}')
        metadata['rag_document_id'] = rag_upload_result.get("document_id")
        metadata['rag_ingestion_status'] = rag_upload_result.get('ingestion', 'scheduled')
        metadata['rag_re_uploaded_at'] = datetime.utcnow().isoformat()

        company_db.query(CompanyDocument).filter(CompanyDocument.id == document.id).update({
            'metadata_json': json.dumps(metadata)
        })
        company_db.commit()

        return {
            "success": True,
            "message": "Document re-uploaded to RAG service successfully",
            "document_id": document_id,
            "rag_document_id": rag_upload_result.get("document_id"),
            "rag_status": rag_upload_result
        }

    except Exception as e:
        logger.error(f"Failed to re-upload document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to re-upload document: {str(e)}")

    finally:
        company_db.close()