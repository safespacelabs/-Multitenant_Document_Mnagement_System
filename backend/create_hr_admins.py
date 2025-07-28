#!/usr/bin/env python3
"""
Script to create default HR Admin users for existing companies.
This ensures that each company has at least one HR Admin for testing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_management_db
from app.services.database_manager import db_manager
from app import models
from app.models_company import User as CompanyUser
from app import auth as auth_utils
from sqlalchemy.orm import Session
import uuid

def create_hr_admin_for_company(management_db: Session, company: models.Company):
    """Create a default HR Admin for a company if none exists."""
    
    print(f"\n📋 Processing company: {str(company.name)} (ID: {str(company.id)})")
    
    try:
        # Get company database connection
        company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
        company_db = next(company_db_gen)
        
        # Check if any HR Admin already exists
        existing_hr_admin = company_db.query(CompanyUser).filter(
            CompanyUser.role == 'hr_admin'
        ).first()
        
        if existing_hr_admin:
            print(f"   ✅ HR Admin already exists: {existing_hr_admin.username}")
            company_db.close()
            return existing_hr_admin
        
        # Create default HR Admin
        hr_admin_username = f"hradmin_{str(company.id)}"
        hr_admin_email = f"hradmin@{str(company.email).split('@')[1]}"
        default_password = "HRAdmin123!"
        
        # Check if username/email already exists
        existing_user = company_db.query(CompanyUser).filter(
            (CompanyUser.username == hr_admin_username) |
            (CompanyUser.email == hr_admin_email)
        ).first()
        
        if existing_user:
            print(f"   ⚠️  User with similar credentials already exists: {existing_user.username}")
            company_db.close()
            return existing_user
        
        # Create the HR Admin user
        hashed_password = auth_utils.get_password_hash(default_password)
        
        hr_admin = CompanyUser(
            id=str(uuid.uuid4()),
            username=hr_admin_username,
            email=hr_admin_email,
            hashed_password=hashed_password,
            full_name=f"HR Admin - {str(company.name)}",
            role="hr_admin",
            s3_folder=f"users/{hr_admin_username}/",
            password_set=True,
            is_active=True
        )
        
        company_db.add(hr_admin)
        company_db.commit()
        company_db.refresh(hr_admin)
        
        print(f"   ✅ Created HR Admin: {hr_admin_username}")
        print(f"      📧 Email: {hr_admin_email}")
        print(f"      🔑 Password: {default_password}")
        print(f"      👤 Full Name: {hr_admin.full_name}")
        
        company_db.close()
        return hr_admin
        
    except Exception as e:
        print(f"   ❌ Error creating HR Admin for {str(company.name)}: {str(e)}")
        return None

def main():
    """Main function to create HR Admins for all companies."""
    
    print("🚀 Creating default HR Admins for existing companies...")
    print("=" * 60)
    
    # Get management database connection
    management_db_gen = get_management_db()
    management_db = next(management_db_gen)
    
    try:
        # Get all active companies
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        if not companies:
            print("❌ No active companies found!")
            return
        
        print(f"📊 Found {len(companies)} active companies")
        
        success_count = 0
        error_count = 0
        
        for company in companies:
            hr_admin = create_hr_admin_for_company(management_db, company)
            if hr_admin:
                success_count += 1
            else:
                error_count += 1
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📈 Total companies: {len(companies)}")
        
        if success_count > 0:
            print("\n🎉 HR Admins created successfully!")
            print("📝 Default credentials created:")
            print("   Username format: hradmin_{company_id}")
            print("   Email format: hradmin@{company_domain}")
            print("   Default password: HRAdmin123!")
            print("\n🔐 IMPORTANT: Change these default passwords in production!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        management_db.close()

if __name__ == "__main__":
    main() 