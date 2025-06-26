from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.services.aws_service import aws_service
import uuid

router = APIRouter()

@router.get("/", response_model=List[schemas.CompanyResponse])
async def list_companies(db: Session = Depends(get_db)):
    companies = db.query(models.Company).filter(models.Company.is_active == True).all()
    return companies

@router.post("/", response_model=schemas.CompanyResponse)
async def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    # Check if company email already exists
    if db.query(models.Company).filter(models.Company.email == company.email).first():
        raise HTTPException(status_code=400, detail="Company email already registered")
    
    # Create company
    company_id = f"comp_{uuid.uuid4().hex[:8]}"
    db_company = models.Company(
        id=company_id,
        name=company.name,
        email=company.email,
        database_name=f"db_{company_id}",
        s3_bucket_name=""  # Will be set after S3 bucket creation
    )
    
    # Create S3 bucket for company
    try:
        bucket_name = await aws_service.create_company_bucket(company_id)
        db_company.s3_bucket_name = bucket_name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create S3 bucket: {str(e)}")
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    return db_company

@router.get("/{company_id}", response_model=schemas.CompanyResponse)
async def get_company(company_id: str, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company 