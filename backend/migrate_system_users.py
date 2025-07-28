#!/usr/bin/env python3
"""
Migration script to add S3 columns to system_users table
Usage: python migrate_system_users.py
"""

import sys
from sqlalchemy import text
from app.database import get_management_db
from app.services.database_manager import db_manager

def migrate_system_users_table():
    """Add S3 columns to system_users table"""
    
    # Get management database session
    db_gen = get_management_db()
    db = next(db_gen)
    
    try:
        print("🔧 Checking system_users table structure...")
        
        # Check if columns already exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'system_users' 
            AND column_name IN ('s3_bucket_name', 's3_folder')
        """))
        
        existing_columns = [row[0] for row in result.fetchall()]
        
        if 's3_bucket_name' in existing_columns and 's3_folder' in existing_columns:
            print("✅ S3 columns already exist in system_users table!")
            return
        
        print("📝 Adding missing S3 columns to system_users table...")
        
        # Add s3_bucket_name column if it doesn't exist
        if 's3_bucket_name' not in existing_columns:
            db.execute(text("""
                ALTER TABLE system_users 
                ADD COLUMN s3_bucket_name VARCHAR
            """))
            print("✅ Added s3_bucket_name column")
        
        # Add s3_folder column if it doesn't exist
        if 's3_folder' not in existing_columns:
            db.execute(text("""
                ALTER TABLE system_users 
                ADD COLUMN s3_folder VARCHAR
            """))
            print("✅ Added s3_folder column")
        
        db.commit()
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

def main():
    """Main function"""
    print("🚀 Starting system_users table migration...")
    
    # Run migration
    migrate_system_users_table()
    
    print("✅ Migration complete!")
    print("📝 You can now run create_admin2.py to create the second system admin")

if __name__ == "__main__":
    main() 