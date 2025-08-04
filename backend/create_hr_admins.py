#!/usr/bin/env python3
"""
Script to create HR admin users for each company
Usage: python create_hr_admins.py
"""

import asyncio
import sys
import uuid
from sqlalchemy.orm import Session
from app.database import get_management_db, get_company_db
from app.models import Company
from app.models_company import User
from app.auth import get_password_hash
from app.services.database_manager import db_manager

def create_hr_admin_for_company(company_id: str, company_name: str, company_email: str, database_url: str):
    """Create HR admin user for a specific company"""
    
    try:
        # Get company database session
        company_db_gen = db_manager.get_company_db(company_id, database_url)
        company_db = next(company_db_gen)
        if not company_db:
            print(f"❌ Could not connect to database for company {company_name}")
            return None
        
        # Check if HR admin already exists for this company
        existing_hr_admin = company_db.query(User).filter(
            User.role == "hr_admin"
        ).first()
        
        if existing_hr_admin:
            print(f"✅ HR admin already exists for {company_name}: {existing_hr_admin.username}")
            return existing_hr_admin
        
        # Generate HR admin credentials
        hr_admin_username = f"hr_admin_{company_name.lower()}"
        hr_admin_email = f"hr_admin@{company_name.lower()}.com"
        hr_admin_password = f"hr_{company_name.lower()}123"  # Change this in production!
        hr_admin_full_name = f"HR Admin - {company_name}"
        
        # Hash password
        hashed_password = get_password_hash(hr_admin_password)
        
        # Create HR admin user
        hr_admin_user = User(
            username=hr_admin_username,
            email=hr_admin_email,
            hashed_password=hashed_password,
            full_name=hr_admin_full_name,
            role="hr_admin",
            s3_folder=f"company_{company_id}/users/{hr_admin_username}",
            password_set=True,
            is_active=True
        )
        
        company_db.add(hr_admin_user)
        company_db.commit()
        company_db.refresh(hr_admin_user)
        
        print(f"🎉 HR admin created for {company_name}!")
        print(f"  Username: {hr_admin_username}")
        print(f"  Email: {hr_admin_email}")
        print(f"  Password: {hr_admin_password}")
        print(f"  Full Name: {hr_admin_full_name}")
        print(f"  Role: hr_admin")
        print("  ⚠️  Please change the password after first login!")
        print()
        
        return hr_admin_user
        
    except Exception as e:
        print(f"❌ Error creating HR admin for {company_name}: {str(e)}")
        return None
    finally:
        if 'company_db' in locals():
            company_db.close()

def main():
    """Main function"""
    print("🚀 Creating HR Admin Users for All Companies")
    print("=" * 50)
    
    # Get management database session
    management_db = get_management_db()
    db = next(management_db)
    
    try:
        # Get all companies
        companies = db.query(Company).all()
        
        if not companies:
            print("❌ No companies found in the system")
            return
        
        print(f"Found {len(companies)} companies:")
        for company in companies:
            print(f"  - {company.name} (ID: {company.id})")
        print()
        
        # Create HR admin for each company
        created_admins = []
        for company in companies:
            print(f"Processing {company.name}...")
            hr_admin = create_hr_admin_for_company(
                company.id, 
                company.name, 
                company.email,
                company.database_url
            )
            if hr_admin:
                created_admins.append({
                    'company': company.name,
                    'username': hr_admin.username,
                    'email': hr_admin.email,
                    'password': f"hr_{company.name.lower()}123"
                })
        
        print("\n" + "=" * 50)
        print("📋 SUMMARY - HR Admin Credentials")
        print("=" * 50)
        
        if created_admins:
            for admin in created_admins:
                print(f"\n🏢 {admin['company']}")
                print(f"   Username: {admin['username']}")
                print(f"   Email: {admin['email']}")
                print(f"   Password: {admin['password']}")
                print(f"   Login URL: http://localhost:3000/login")
        else:
            print("No new HR admins were created (they may already exist)")
        
        print("\n" + "=" * 50)
        print("✅ HR Admin Creation Complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main() 