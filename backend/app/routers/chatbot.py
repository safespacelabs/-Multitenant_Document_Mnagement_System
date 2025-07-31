from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_management_db, get_company_db
from app import models, schemas, auth
from app.models_company import User as CompanyUser, ChatHistory as CompanyChatHistory
from app.services.nlp_service import nlp_service
from app.services.intelligent_ai_service import intelligent_ai_service

router = APIRouter()

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
        # Process the question using NLP service
        answer = nlp_service.process_query(
            query=chat_request.question,
            user_id=str(current_user.id),
            company_id=str(company_id),
            db=company_db
        )
        
        # Save chat history in company database
        chat_history = CompanyChatHistory(
            user_id=current_user.id,
            question=chat_request.question,
            answer=answer,
            context_documents=[]  # Could be populated with relevant doc IDs
        )
        
        company_db.add(chat_history)
        company_db.commit()
        company_db.refresh(chat_history)
        
        return {
            "answer": answer,
            "context_documents": [],
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