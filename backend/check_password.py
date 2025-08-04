#!/usr/bin/env python3
"""
Check password verification for Amazon HR admin
"""

from app.database import get_management_db
from app.models import Company
from app.models_company import User
from app.services.database_manager import db_manager
from app.auth import verify_password

def check_password():
    """Check password verification for Amazon HR admin"""
    
    try:
        # Get management database
        db = next(get_management_db())
        company = db.query(Company).filter(Company.id == 'comp_3e6dab46').first()
        
        if not company:
            print("❌ Company not found")
            return
        
        # Get company database
        company_db_gen = db_manager.get_company_db(company.id, company.database_url)
        company_db = next(company_db_gen)
        
        # Get user
        user = company_db.query(User).filter(User.username == 'Hradmin1_amazon').first()
        
        if not user:
            print("❌ User not found")
            return
        
        print(f"User: {user.username}")
        print(f"Role: {user.role}")
        print(f"Active: {user.is_active}")
        print(f"Password hash: {user.hashed_password[:50]}...")
        
        # Test password verification
        test_password = "hr_amazon123"
        is_valid = verify_password(test_password, user.hashed_password)
        print(f"Password verification for '{test_password}': {is_valid}")
        
        if is_valid:
            print("✅ Password verification successful!")
        else:
            print("❌ Password verification failed!")
            
        company_db.close()
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_password() 