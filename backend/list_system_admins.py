#!/usr/bin/env python3
"""
Script to list all system administrators
Usage: python list_system_admins.py
"""

from app.database import get_management_db
from app.models import SystemUser

def list_system_admins():
    """List all system administrators"""
    
    # Get management database session
    db_gen = get_management_db()
    db = next(db_gen)
    
    try:
        print("👥 Listing all System Administrators:")
        print("=" * 50)
        
        # Get all system users
        system_users = db.query(SystemUser).filter(
            SystemUser.role == "system_admin",
            SystemUser.is_active == True
        ).order_by(SystemUser.created_at).all()
        
        if not system_users:
            print("❌ No system administrators found!")
            return
        
        for i, admin in enumerate(system_users, 1):
            print(f"\n🔰 Admin #{i}:")
            print(f"   ID: {admin.id}")
            print(f"   Username: {admin.username}")
            print(f"   Email: {admin.email}")
            print(f"   Full Name: {admin.full_name}")
            print(f"   Role: {admin.role}")
            print(f"   S3 Bucket: {admin.s3_bucket_name or 'Not set'}")
            print(f"   S3 Folder: {admin.s3_folder or 'Not set'}")
            print(f"   Created: {admin.created_at}")
            print(f"   Active: {'✅ Yes' if bool(admin.is_active) else '❌ No'}")
        
        print(f"\n📊 Total System Administrators: {len(system_users)}")
        
    except Exception as e:
        print(f"❌ Error listing system admins: {str(e)}")
    finally:
        db.close()

def main():
    """Main function"""
    list_system_admins()

if __name__ == "__main__":
    main() 