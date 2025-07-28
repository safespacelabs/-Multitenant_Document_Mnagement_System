from typing import Optional, Generator
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_management_db, get_company_db
from app import models
from app.models_company import User as CompanyUser
import logging

logger = logging.getLogger(__name__)

class CompanyContext:
    def __init__(self, company: models.Company, company_db: Session):
        self.company = company
        self.company_db = company_db

async def get_company_from_user(user_id: str, management_db: Session) -> Optional[models.Company]:
    """Get company information from a user in any company database"""
    try:
        # First, check if this is a system user (in management database)
        system_user = management_db.query(models.SystemUser).filter(
            models.SystemUser.id == user_id
        ).first()
        
        if system_user:
            # System users don't belong to a specific company
            return None
            
        # Find which company this user belongs to by checking all companies
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        for company in companies:
            try:
                # Check if user exists in this company's database
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                user = company_db.query(CompanyUser).filter(
                    CompanyUser.id == user_id
                ).first()
                
                company_db.close()
                
                if user:
                    return company
                    
            except Exception as e:
                logger.warning(f"Error checking user {user_id} in company {company.id}: {str(e)}")
                continue
                
        return None
        
    except Exception as e:
        logger.error(f"Error finding company for user {user_id}: {str(e)}")
        return None

async def get_company_context_by_id(
    company_id: str,
    management_db: Session = Depends(get_management_db)
) -> CompanyContext:
    """Get company context by company ID"""
    company = management_db.query(models.Company).filter(
        models.Company.id == company_id,
        models.Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get company database session
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    return CompanyContext(company, company_db)

async def get_company_context_from_user(
    user_id: str,
    management_db: Session = Depends(get_management_db)
) -> Optional[CompanyContext]:
    """Get company context from user ID"""
    company = await get_company_from_user(user_id, management_db)
    
    if not company:
        return None
    
    # Get company database session
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)
    
    return CompanyContext(company, company_db)

def get_user_from_company_db(user_id: str, company_db: Session) -> Optional[CompanyUser]:
    """Get user from company database"""
    try:
        return company_db.query(CompanyUser).filter(
            CompanyUser.id == user_id,
            CompanyUser.is_active == True
        ).first()
    except Exception as e:
        logger.error(f"Error getting user {user_id} from company database: {str(e)}")
        return None

def close_company_context(context: CompanyContext):
    """Close company database session"""
    if context and context.company_db:
        context.company_db.close() 