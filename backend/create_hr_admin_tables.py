#!/usr/bin/env python3
"""
Database migration script to create HR admin monitoring tables
This script adds new tables for tracking user activity, credentials, and login history
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_management_db
from app.models import Company

def create_hr_admin_tables():
    """Create HR admin monitoring tables in all company databases"""
    
    print("🚀 Starting HR Admin tables creation...")
    
    # Get management database session
    management_db_gen = get_management_db()
    management_db = next(management_db_gen)
    
    try:
        # Get all active companies
        companies = management_db.query(Company).filter(Company.is_active == True).all()
        print(f"📋 Found {len(companies)} active companies")
        
        for company in companies:
            print(f"\n🏢 Processing company: {company.name}")
            
            try:
                # Create company database engine
                company_engine = create_engine(company.database_url)
                
                # Create tables
                create_company_hr_tables(company_engine, company.name)
                
                print(f"✅ Successfully created HR admin tables for {company.name}")
                
            except Exception as e:
                print(f"❌ Failed to create tables for {company.name}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"❌ Error accessing management database: {str(e)}")
    finally:
        management_db.close()

def create_company_hr_tables(engine, company_name):
    """Create HR admin tables in a specific company database"""
    
    # SQL statements to create the new tables
    tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS user_login_history (
            id VARCHAR PRIMARY KEY,
            user_id VARCHAR NOT NULL,
            login_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            logout_timestamp TIMESTAMP NULL,
            ip_address VARCHAR NULL,
            user_agent TEXT NULL,
            success BOOLEAN DEFAULT TRUE,
            failure_reason VARCHAR NULL,
            company_id VARCHAR NULL,
            CONSTRAINT fk_login_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_credentials (
            id VARCHAR PRIMARY KEY,
            user_id VARCHAR NOT NULL UNIQUE,
            hashed_password VARCHAR NOT NULL,
            password_set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            password_expires_at TIMESTAMP NULL,
            last_password_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            login_attempts INTEGER DEFAULT 0,
            account_locked BOOLEAN DEFAULT FALSE,
            lock_reason VARCHAR NULL,
            lock_timestamp TIMESTAMP NULL,
            company_id VARCHAR NULL,
            CONSTRAINT fk_cred_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_activity (
            id VARCHAR PRIMARY KEY,
            user_id VARCHAR NOT NULL,
            activity_type VARCHAR NOT NULL,
            activity_details JSON NULL,
            ip_address VARCHAR NULL,
            user_agent TEXT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            company_id VARCHAR NULL,
            CONSTRAINT fk_activity_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON user_login_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_login_history_timestamp ON user_login_history(login_timestamp);
        CREATE INDEX IF NOT EXISTS idx_login_history_success ON user_login_history(success);
        
        CREATE INDEX IF NOT EXISTS idx_credentials_user_id ON user_credentials(user_id);
        CREATE INDEX IF NOT EXISTS idx_credentials_locked ON user_credentials(account_locked);
        
        CREATE INDEX IF NOT EXISTS idx_activity_user_id ON user_activity(user_id);
        CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON user_activity(timestamp);
        CREATE INDEX IF NOT EXISTS idx_activity_type ON user_activity(activity_type);
        """
    ]
    
    # Execute SQL statements
    with engine.connect() as connection:
        for sql in tables_sql:
            try:
                connection.execute(text(sql))
                connection.commit()
            except SQLAlchemyError as e:
                print(f"⚠️ Warning executing SQL: {str(e)}")
                # Continue with other statements even if one fails
                continue

def populate_initial_data():
    """Populate initial data for existing users"""
    
    print("\n📊 Populating initial data for existing users...")
    
    # Get management database session
    management_db_gen = get_management_db()
    management_db = next(management_db_gen)
    
    try:
        # Get all active companies
        companies = management_db.query(Company).filter(Company.is_active == True).all()
        
        for company in companies:
            print(f"🏢 Populating data for company: {company.name}")
            
            try:
                # Create company database engine
                company_engine = create_engine(company.database_url)
                
                # Populate initial credentials for existing users
                populate_user_credentials(company_engine, company.name)
                
                print(f"✅ Successfully populated data for {company.name}")
                
            except Exception as e:
                print(f"❌ Failed to populate data for {company.name}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"❌ Error accessing management database: {str(e)}")
    finally:
        management_db.close()

def populate_user_credentials(engine, company_name):
    """Populate initial user credentials for existing users"""
    
    sql = """
    INSERT INTO user_credentials (id, user_id, hashed_password, company_id)
    SELECT 
        'cred_' || substr(md5(random()::text), 1, 8),
        u.id,
        COALESCE(u.hashed_password, ''),
        u.company_id
    FROM users u
    WHERE NOT EXISTS (
        SELECT 1 FROM user_credentials uc WHERE uc.user_id = u.id
    );
    """
    
    with engine.connect() as connection:
        try:
            result = connection.execute(text(sql))
            connection.commit()
            print(f"   📝 Created {result.rowcount} credential records")
        except SQLAlchemyError as e:
            print(f"   ⚠️ Warning creating credentials: {str(e)}")

def main():
    """Main function to run the migration"""
    
    print("=" * 60)
    print("🔧 HR Admin Tables Migration Script")
    print("=" * 60)
    
    try:
        # Create tables
        create_hr_admin_tables()
        
        # Populate initial data
        populate_initial_data()
        
        print("\n" + "=" * 60)
        print("✅ HR Admin tables migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
