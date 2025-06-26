from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth
from app.services.nlp_service import nlp_service

router = APIRouter()

@router.post("/", response_model=schemas.ChatResponse)
async def chat_with_bot(
    chat_request: schemas.ChatRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Process the question using NLP service
        answer = nlp_service.process_query(
            query=chat_request.question,
            user_id=current_user.id,
            company_id=current_user.company_id,
            db=db
        )
        
        # Save chat history
        chat_history = models.ChatHistory(
            user_id=current_user.id,
            company_id=current_user.company_id,
            question=chat_request.question,
            answer=answer,
            context_documents=[]  # Could be populated with relevant doc IDs
        )
        
        db.add(chat_history)
        db.commit()
        
        return schemas.ChatResponse(
            answer=answer,
            context_documents=[],
            created_at=chat_history.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/history")
async def get_chat_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    history = db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == current_user.id
    ).order_by(models.ChatHistory.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": chat.id,
            "question": chat.question,
            "answer": chat.answer,
            "created_at": chat.created_at
        }
        for chat in history
    ]