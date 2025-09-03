from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_management_db, get_company_db
from app import models, schemas, auth
from app.models_company import User as CompanyUser, ChatHistory as CompanyChatHistory
from app.services.nlp_service import nlp_service
from app.services.intelligent_ai_service import intelligent_ai_service
from app.services.document_analysis_service import document_analysis_service
from app.services.hr_admin_database_service import hr_admin_database_service

router = APIRouter()

async def process_enhanced_chat_query(query: str, current_user: CompanyUser, company_db: Session) -> tuple[str, list]:
    """Enhanced chat processing with document analysis integration and HR admin database access"""
    try:
        query_lower = query.lower()
        
        # Check if user is HR admin and provide comprehensive database access
        if current_user.role in ['hr_admin', 'hr_manager']:
            # HR admin gets access to entire company database
            hr_admin_response = await hr_admin_database_service.process_hr_admin_query(query, company_db)
            return hr_admin_response, []
        
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
        # Enhanced chatbot with document analysis integration
        answer, context_documents = await process_enhanced_chat_query(
            query=chat_request.question,
            current_user=current_user,
            company_db=company_db
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