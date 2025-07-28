#!/usr/bin/env python3
"""
Script to create second system admin user
Usage: python create_admin2.py
"""

import asyncio
import sys
from sqlalchemy.orm import Session
from app.database import get_management_db
from app.models import SystemUser
from app.auth import get_password_hash
from app.services.database_manager import db_manager
from app.services.aws_service import aws_service

async def create_system_admin2():
    """Create second system admin user"""
    
    # Get management database session
    db_gen = get_management_db()
    db = next(db_gen)
    
    try:
        # Check if this specific admin already exists
        existing_admin = db.query(SystemUser).filter(
            SystemUser.username == "admin2"
        ).first()
        
        if existing_admin:
            print(f"✅ System admin 'admin2' already exists!")
            return
        
        # Create system admin user
        admin_username = "admin2"
        admin_email = "admin2@system.local"
        admin_password = "admin@61"
        admin_full_name = "System Administrator 2"
        
        hashed_password = get_password_hash(admin_password)
        
        admin_user = SystemUser(
            username=admin_username,
            email=admin_email,
            hashed_password=hashed_password,
            full_name=admin_full_name,
            role="system_admin"
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("🎉 System admin user 'admin2' created successfully!")
        print(f"Username: {admin_username}")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print(f"Full Name: {admin_full_name}")
        
        # Create S3 bucket and folder for the new system admin
        print("📦 Setting up S3 storage for system admin...")
        bucket_name = f"system-admin-{admin_user.id.lower()}"
        folder_name = f"system-admin-{admin_user.id}"
        
        try:
            await aws_service.create_system_admin_bucket(bucket_name, folder_name)
            
            # Update system user with S3 info
            db.query(SystemUser).filter(SystemUser.id == admin_user.id).update({
                's3_bucket_name': bucket_name,
                's3_folder': folder_name
            })
            db.commit()
            db.refresh(admin_user)
            
            print(f"✅ S3 storage created: {bucket_name}")
            print(f"✅ S3 folder created: {folder_name}")
            
        except Exception as s3_error:
            print(f"⚠️ Warning: Failed to create S3 storage: {str(s3_error)}")
            print("📝 S3 storage can be created later when the admin uploads their first document")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating system admin: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

async def main():
    """Main function"""
    print("🚀 Creating second system admin user...")
    
    # Create management database tables first (if not already created)
    print("📊 Ensuring management database tables exist...")
    from app.models import Base
    Base.metadata.create_all(bind=db_manager.management_engine)
    
    # Create second system admin
    await create_system_admin2()
    
    print("✅ Setup complete!")
    print("🔐 The new system admin can now log in and:")
    print("   • Access the system admin dashboard")
    print("   • Create and manage companies")
    print("   • Upload and manage system documents")
    print("   • Create other system administrators")

if __name__ == "__main__":
    asyncio.run(main()) 