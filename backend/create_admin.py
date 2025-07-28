#!/usr/bin/env python3
"""
Script to create initial system admin user
Usage: python create_admin.py
"""

import asyncio
import sys
from sqlalchemy.orm import Session
from app.database import get_management_db
from app.models import SystemUser
from app.auth import get_password_hash
from app.services.database_manager import db_manager

def create_system_admin():
    """Create initial system admin user"""
    
    # Get management database session
    db_gen = get_management_db()
    db = next(db_gen)
    
    try:
        # Check if any system admin already exists
        existing_admin = db.query(SystemUser).filter(
            SystemUser.role == "system_admin"
        ).first()
        
        if existing_admin:
            print(f"✅ System admin already exists: {existing_admin.username}")
            return
        
        # Create system admin user
        admin_username = "admin"
        admin_email = "admin@system.local"
        admin_password = "admin123"  # Change this in production!
        admin_full_name = "System Administrator"
        
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
        
        print("🎉 System admin user created successfully!")
        print(f"Username: {admin_username}")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print("⚠️  Please change the password after first login!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating system admin: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

def main():
    """Main function"""
    print("🚀 Creating system admin user...")
    
    # Create management database tables first
    print("📊 Creating management database tables...")
    from app.models import Base
    Base.metadata.create_all(bind=db_manager.management_engine)
    
    # Create system admin
    create_system_admin()
    
    print("✅ Setup complete!")

if __name__ == "__main__":
    main() 