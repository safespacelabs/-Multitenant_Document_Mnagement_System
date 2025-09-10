#!/usr/bin/env python3
"""
Fix Document Analysis Table Column Order
This script recreates the document_analysis table with the correct column order
"""

from app.database import get_management_db, get_company_db
from app import models
from sqlalchemy import text

def fix_column_order():
    """Recreate the document_analysis table with correct column order for ALL companies"""
    
    print('🔍 Fixing document_analysis table column order for ALL companies...')
    
    # Get management database
    management_db = next(get_management_db())
    
    try:
        # Get ALL companies
        companies = management_db.query(models.Company).all()
        
        if not companies:
            print('❌ No companies found')
            return
            
        print(f'📊 Found {len(companies)} companies to fix')
        
        for company in companies:
            print(f'\n🏢 Processing company: {company.name} (ID: {company.id})')
            
            try:
                # Get company database
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                try:
                    print(f'   ⚠️ Dropping existing document_analysis table for {company.name}...')
                    company_db.execute(text('DROP TABLE IF EXISTS document_analysis CASCADE;'))
                    
                    print(f'   ⚠️ Dropping existing expiry_notification table for {company.name}...')
                    company_db.execute(text('DROP TABLE IF EXISTS expiry_notification CASCADE;'))
                    
                    print(f'   🔧 Creating document_analysis table with correct column order for {company.name}...')
                    company_db.execute(text('''
                        CREATE TABLE document_analysis (
                            id SERIAL PRIMARY KEY,
                            document_id VARCHAR(255) NOT NULL,
                            user_id VARCHAR(255) NOT NULL,
                            user_name VARCHAR(255),
                            user_email VARCHAR(255),
                            title TEXT,
                            summary TEXT,
                            document_type VARCHAR(100),
                            folder_name VARCHAR(255),
                            key_topics TEXT[],
                            entities JSONB,
                            keywords TEXT[],
                            language VARCHAR(50),
                            word_count INTEGER,
                            sentiment VARCHAR(20),
                            expiry_detected BOOLEAN DEFAULT FALSE,
                            expiry_date DATE,
                            expiry_type VARCHAR(50),
                            urgency_level VARCHAR(20),
                            extracted_text TEXT,
                            important_notes TEXT[],
                            compliance_requirements TEXT[],
                            extracted_at TIMESTAMP,
                            ai_model VARCHAR(100),
                            processing_status VARCHAR(20),
                            error_message TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    '''))
                    
                    print(f'   🔧 Creating expiry_notification table for {company.name}...')
                    company_db.execute(text('''
                        CREATE TABLE expiry_notification (
                            id SERIAL PRIMARY KEY,
                            document_analysis_id INTEGER NOT NULL,
                            document_id VARCHAR(255) NOT NULL,
                            user_id VARCHAR(255) NOT NULL,
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
                    '''))
                    
                    company_db.commit()
                    print(f'   ✅ Database tables recreated with correct column order for {company.name}!')
                    
                except Exception as e:
                    print(f'   ❌ Error recreating table for {company.name}: {e}')
                    import traceback
                    traceback.print_exc()
                finally:
                    company_db.close()
                    
            except Exception as e:
                print(f'   ❌ Error connecting to database for {company.name}: {e}')
                import traceback
                traceback.print_exc()
        
        print(f'\n🎉 Column order fix completed for {len(companies)} companies!')
            
    except Exception as e:
        print(f'❌ Error connecting to database: {e}')
        import traceback
        traceback.print_exc()
    finally:
        management_db.close()
    
    print('🎉 Column order fix completed!')

if __name__ == "__main__":
    fix_column_order()
