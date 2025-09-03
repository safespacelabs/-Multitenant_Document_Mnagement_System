#!/usr/bin/env python3
"""
Setup script for AI-powered document processing system
This script initializes the document analysis tables and verifies the setup
"""

import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import MANAGEMENT_DATABASE_URL, ANTHROPIC_API_KEY
from app.models import Company
from app.services.anthropic_service import anthropic_service
from app.services.document_analysis_service import document_analysis_service

def check_anthropic_api():
    """Check if Anthropic API is properly configured"""
    print("🔍 Checking Anthropic API configuration...")
    
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not found in environment variables")
        print("   Please set ANTHROPIC_API_KEY in your .env file")
        return False
    
    print(f"✅ ANTHROPIC_API_KEY found: {ANTHROPIC_API_KEY[:10]}...")
    
    # Test API connection
    try:
        test_result = anthropic_service.test_connection()
        if test_result["success"]:
            print(f"✅ Anthropic API connection successful")
            print(f"   Model: {test_result['model']}")
            print(f"   Response: {test_result['response']}")
            return True
        else:
            print(f"❌ Anthropic API connection failed: {test_result['error']}")
            return False
    except Exception as e:
        print(f"❌ Error testing Anthropic API: {str(e)}")
        return False

def create_document_analysis_tables():
    """Create document analysis tables for all companies"""
    print("\n📊 Creating document analysis tables...")
    
    # Connect to management database
    management_engine = create_engine(MANAGEMENT_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=management_engine)
    
    try:
        session = SessionLocal()
        
        # Get all companies
        companies = session.query(Company).all()
        
        if not companies:
            print("❌ No companies found in management database")
            return False
        
        print(f"📁 Found {len(companies)} companies to process")
        
        success_count = 0
        
        for company in companies:
            print(f"\n📁 Processing company: {company.name} (ID: {company.id})")
            
            # Construct company database URL
            company_db_url = f"postgresql://{company.db_user}:{company.db_password}@{company.db_host}:{company.db_port}/{company.db_name}"
            
            try:
                engine = create_engine(company_db_url)
                
                # Create document_analysis table
                create_analysis_table_sql = """
                CREATE TABLE IF NOT EXISTS document_analysis (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR(255) NOT NULL,
                    user_id INTEGER NOT NULL,
                    user_name VARCHAR(255),
                    user_email VARCHAR(255),
                    title VARCHAR(500),
                    summary TEXT,
                    document_type VARCHAR(100),
                    folder_name VARCHAR(200),
                    key_topics TEXT[],
                    entities JSONB,
                    keywords TEXT[],
                    language VARCHAR(50),
                    word_count INTEGER,
                    sentiment VARCHAR(20),
                    expiry_detected BOOLEAN DEFAULT FALSE,
                    expiry_date DATE,
                    expiry_type VARCHAR(50),
                    urgency_level VARCHAR(20) DEFAULT 'low',
                    extracted_text TEXT,
                    important_notes TEXT[],
                    compliance_requirements TEXT[],
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ai_model VARCHAR(100),
                    processing_status VARCHAR(20) DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                
                # Create expiry_notifications table
                create_notifications_table_sql = """
                CREATE TABLE IF NOT EXISTS expiry_notifications (
                    id SERIAL PRIMARY KEY,
                    document_analysis_id INTEGER REFERENCES document_analysis(id) ON DELETE CASCADE,
                    document_id VARCHAR(255) NOT NULL,
                    user_id INTEGER NOT NULL,
                    user_name VARCHAR(255),
                    user_email VARCHAR(255),
                    notification_type VARCHAR(50) DEFAULT 'expiry_warning',
                    expiry_date DATE,
                    days_until_expiry INTEGER,
                    urgency_level VARCHAR(20),
                    notification_sent_at TIMESTAMP,
                    notification_recipients TEXT[],
                    notification_status VARCHAR(20) DEFAULT 'pending',
                    notification_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                
                # Create indexes
                create_indexes_sql = [
                    "CREATE INDEX IF NOT EXISTS idx_document_analysis_document_id ON document_analysis(document_id);",
                    "CREATE INDEX IF NOT EXISTS idx_document_analysis_user_id ON document_analysis(user_id);",
                    "CREATE INDEX IF NOT EXISTS idx_document_analysis_user_name ON document_analysis(user_name);",
                    "CREATE INDEX IF NOT EXISTS idx_document_analysis_folder_name ON document_analysis(folder_name);",
                    "CREATE INDEX IF NOT EXISTS idx_document_analysis_document_type ON document_analysis(document_type);",
                    "CREATE INDEX IF NOT EXISTS idx_document_analysis_expiry_detected ON document_analysis(expiry_detected);",
                    "CREATE INDEX IF NOT EXISTS idx_document_analysis_expiry_date ON document_analysis(expiry_date);",
                    "CREATE INDEX IF NOT EXISTS idx_document_analysis_urgency_level ON document_analysis(urgency_level);",
                    "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_document_analysis_id ON expiry_notifications(document_analysis_id);",
                    "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_document_id ON expiry_notifications(document_id);",
                    "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_user_id ON expiry_notifications(user_id);",
                    "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_user_name ON expiry_notifications(user_name);",
                    "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_expiry_date ON expiry_notifications(expiry_date);",
                    "CREATE INDEX IF NOT EXISTS idx_expiry_notifications_notification_status ON expiry_notifications(notification_status);"
                ]
                
                with engine.connect() as conn:
                    # Create tables
                    conn.execute(text(create_analysis_table_sql))
                    conn.execute(text(create_notifications_table_sql))
                    conn.commit()
                    
                    # Create indexes
                    for index_sql in create_indexes_sql:
                        conn.execute(text(index_sql))
                    conn.commit()
                
                print(f"✅ Created document analysis tables for {company.name}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ Error creating tables for {company.name}: {str(e)}")
        
        print(f"\n🎉 Table creation completed!")
        print(f"✅ Successfully processed: {success_count}/{len(companies)} companies")
        
        return success_count == len(companies)
        
    except Exception as e:
        print(f"❌ Error in table creation process: {str(e)}")
        return False
    finally:
        session.close()

async def test_document_processing():
    """Test document processing with a sample document"""
    print("\n🧪 Testing document processing...")
    
    try:
        # Create a sample document content
        sample_content = """
        PASSPORT
        United States of America
        
        Name: John Doe
        Date of Birth: 01/15/1985
        Passport Number: A12345678
        Issue Date: 01/15/2020
        Expiry Date: 01/15/2030
        
        This passport is valid for travel to most countries.
        Please ensure to renew before expiry date.
        """
        
        # Test document analysis
        metadata = await anthropic_service.extract_document_metadata(
            file_content=sample_content.encode('utf-8'),
            filename="sample_passport.txt",
            folder_name="TestFolder"
        )
        
        print("✅ Document analysis test successful!")
        print(f"   Title: {metadata.get('title')}")
        print(f"   Document Type: {metadata.get('document_type')}")
        print(f"   Expiry Detected: {metadata.get('expiry_detected')}")
        print(f"   Expiry Date: {metadata.get('expiry_date')}")
        print(f"   Urgency Level: {metadata.get('urgency_level')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document processing test failed: {str(e)}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up AI-powered Document Processing System")
    print("=" * 60)
    
    # Check Anthropic API
    api_ok = check_anthropic_api()
    if not api_ok:
        print("\n❌ Setup failed: Anthropic API not properly configured")
        return False
    
    # Create database tables
    tables_ok = create_document_analysis_tables()
    if not tables_ok:
        print("\n❌ Setup failed: Could not create all database tables")
        return False
    
    # Test document processing
    print("\n🧪 Running document processing test...")
    test_ok = asyncio.run(test_document_processing())
    if not test_ok:
        print("\n⚠️  Setup completed but document processing test failed")
        print("   The system is configured but may need troubleshooting")
        return False
    
    print("\n🎉 AI Document Processing System Setup Complete!")
    print("=" * 60)
    print("✅ Anthropic API configured and tested")
    print("✅ Database tables created for all companies")
    print("✅ Document processing tested successfully")
    print("\n📋 Next Steps:")
    print("1. Upload documents through the web interface")
    print("2. Documents will be automatically analyzed with AI")
    print("3. Expiry dates will be detected and notifications sent")
    print("4. Use the chatbot to query your documents")
    print("\n💡 Example chatbot queries:")
    print("   - 'Show me expiring documents'")
    print("   - 'What documents are in the HR folder?'")
    print("   - 'Find all passport documents'")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
