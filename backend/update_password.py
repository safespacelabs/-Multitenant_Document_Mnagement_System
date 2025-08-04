#!/usr/bin/env python3
"""
Update password hash for Amazon HR admin to ensure compatibility
"""

from app.database import get_management_db
from app.models import Company
from app.models_company import User
from app.services.database_manager import db_manager
from app.auth import get_password_hash, verify_password

def update_password():
    """Update password hash for Amazon HR admin"""
    
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
        print(f"Current password hash: {user.hashed_password[:50]}...")
        
        # Test current password verification
        test_password = "hr_amazon123"
        is_valid = verify_password(test_password, user.hashed_password)
        print(f"Current password verification: {is_valid}")
        
        if not is_valid:
            print("🔄 Updating password hash...")
            # Create new password hash
            new_hash = get_password_hash(test_password)
            user.hashed_password = new_hash
            company_db.commit()
            print(f"New password hash: {new_hash[:50]}...")
            
            # Verify new hash
            is_valid_new = verify_password(test_password, new_hash)
            print(f"New password verification: {is_valid_new}")
            
            if is_valid_new:
                print("✅ Password hash updated successfully!")
            else:
                print("❌ Password hash update failed!")
        else:
            print("✅ Password verification already works!")
            
        company_db.close()
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    update_password() 