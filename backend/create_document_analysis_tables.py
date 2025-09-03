#!/usr/bin/env python3
"""
Create document analysis tables for each company database
This script creates tables to store AI-extracted document metadata
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import MANAGEMENT_DATABASE_URL
from app.models import Company

def create_document_analysis_table(company_db_url: str, company_name: str):
    """Create document analysis table for a specific company"""
    try:
        engine = create_engine(company_db_url)
        
        # Create the document_analysis table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS document_analysis (
            id SERIAL PRIMARY KEY,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL, -- User who uploaded the document
            user_name VARCHAR(255), -- Username for easy reference
            user_email VARCHAR(255), -- User email for notifications
            title VARCHAR(500),
            summary TEXT,
            document_type VARCHAR(100),
            folder_name VARCHAR(200),
            key_topics TEXT[], -- Array of topics
            entities JSONB, -- JSON object with people, organizations, locations, dates, etc.
            keywords TEXT[], -- Array of keywords
            language VARCHAR(50),
            word_count INTEGER,
            sentiment VARCHAR(20),
            expiry_detected BOOLEAN DEFAULT FALSE,
            expiry_date DATE,
            expiry_type VARCHAR(50),
            urgency_level VARCHAR(20) DEFAULT 'low',
            extracted_text TEXT,
            important_notes TEXT[], -- Array of important notes
            compliance_requirements TEXT[], -- Array of compliance requirements
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ai_model VARCHAR(100),
            processing_status VARCHAR(20) DEFAULT 'pending',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Create indexes for better performance
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_document_analysis_document_id ON document_analysis(document_id);",
            "CREATE INDEX IF NOT EXISTS idx_document_analysis_user_id ON document_analysis(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_document_analysis_user_name ON document_analysis(user_name);",
            "CREATE INDEX IF NOT EXISTS idx_document_analysis_folder_name ON document_analysis(folder_name);",
            "CREATE INDEX IF NOT EXISTS idx_document_analysis_document_type ON document_analysis(document_type);",
            "CREATE INDEX IF NOT EXISTS idx_document_analysis_expiry_detected ON document_analysis(expiry_detected);",
            "CREATE INDEX IF NOT EXISTS idx_document_analysis_expiry_date ON document_analysis(expiry_date);",
            "CREATE INDEX IF NOT EXISTS idx_document_analysis_urgency_level ON document_analysis(urgency_level);",
            "CREATE INDEX IF NOT EXISTS idx_document_analysis_created_at ON document_analysis(created_at);"
        ]
        
        with engine.connect() as conn:
            # Create table
            conn.execute(text(create_table_sql))
            conn.commit()
            
            # Create indexes
            for index_sql in create_indexes_sql:
                conn.execute(text(index_sql))
            conn.commit()
            
        print(f"✅ Created document_analysis table for company: {company_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating document_analysis table for {company_name}: {str(e)}")
        return False

def create_expiry_notifications_table(company_db_url: str, company_name: str):
    """Create expiry notifications table for tracking notifications sent"""
    try:
        engine = create_engine(company_db_url)
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS expiry_notifications (
            id SERIAL PRIMARY KEY,
            document_analysis_id INTEGER REFERENCES document_analysis(id) ON DELETE CASCADE,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL, -- User who uploaded the document
            user_name VARCHAR(255), -- Username for easy reference
            user_email VARCHAR(255), -- User email for notifications
            notification_type VARCHAR(50) DEFAULT 'expiry_warning',
            expiry_date DATE,
            days_until_expiry INTEGER,
            urgency_level VARCHAR(20),
            notification_sent_at TIMESTAMP,
            notification_recipients TEXT[], -- Array of email addresses
            notification_status VARCHAR(20) DEFAULT 'pending', -- pending, sent, failed
            notification_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_document_analysis_id ON expiry_notifications(document_analysis_id);",
            "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_document_id ON expiry_notifications(document_id);",
            "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_user_id ON expiry_notifications(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_user_name ON expiry_notifications(user_name);",
            "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_expiry_date ON expiry_notifications(expiry_date);",
            "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_notification_status ON expiry_notifications(notification_status);",
            "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_urgency_level ON expiry_notifications(urgency_level);"
        ]
        
        with engine.connect() as conn:
            # Create table
            conn.execute(text(create_table_sql))
            conn.commit()
            
            # Create indexes
            for index_sql in create_indexes_sql:
                conn.execute(text(index_sql))
            conn.commit()
            
        print(f"✅ Created expiry_notifications table for company: {company_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating expiry_notifications table for {company_name}: {str(e)}")
        return False

def main():
    """Main function to create tables for all companies"""
    print("🚀 Starting document analysis tables creation...")
    
    # Connect to management database
    management_engine = create_engine(MANAGEMENT_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=management_engine)
    
    try:
        session = SessionLocal()
        
        # Get all companies
        companies = session.query(Company).all()
        
        if not companies:
            print("❌ No companies found in management database")
            return
        
        print(f"📊 Found {len(companies)} companies to process")
        
        success_count = 0
        total_count = len(companies)
        
        for company in companies:
            print(f"\n📁 Processing company: {company.name} (ID: {company.id})")
            
            # Construct company database URL
            company_db_url = f"postgresql://{company.db_user}:{company.db_password}@{company.db_host}:{company.db_port}/{company.db_name}"
            
            # Create document analysis table
            analysis_success = create_document_analysis_table(company_db_url, company.name)
            
            # Create expiry notifications table
            notifications_success = create_expiry_notifications_table(company_db_url, company.name)
            
            if analysis_success and notifications_success:
                success_count += 1
                print(f"✅ Successfully created tables for {company.name}")
            else:
                print(f"❌ Failed to create some tables for {company.name}")
        
        print(f"\n🎉 Table creation completed!")
        print(f"✅ Successfully processed: {success_count}/{total_count} companies")
        
        if success_count < total_count:
            print(f"⚠️  {total_count - success_count} companies had issues")
        
    except Exception as e:
        print(f"❌ Error in main process: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
