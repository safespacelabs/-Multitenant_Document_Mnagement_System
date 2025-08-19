#!/usr/bin/env python3
"""
Script to add missing document columns to existing company databases
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_management_db
from app import models

def add_missing_document_columns():
    """Add missing document columns to all company databases"""
    
    print("🔧 Adding missing document columns to company databases...")
    
    # Get management database connection
    management_db_gen = get_management_db()
    management_db = next(management_db_gen)
    
    try:
        # Get all active companies
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        print(f"📊 Found {len(companies)} active companies")
        
        for company in companies:
            print(f"\n🏢 Processing company: {company.name} ({company.id})")
            
            try:
                # Create connection to company database
                company_engine = create_engine(company.database_url)
                company_session = sessionmaker(bind=company_engine)()
                
                # Check if columns already exist
                result = company_session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'documents' 
                    AND column_name IN ('document_category', 'document_subcategory', 'tags', 'description', 'is_public', 'access_level', 'expiry_date', 'version', 'status')
                """))
                
                existing_columns = [row[0] for row in result]
                print(f"   📋 Existing columns: {existing_columns}")
                
                # Add missing columns
                missing_columns = []
                
                if 'document_category' not in existing_columns:
                    missing_columns.append("ADD COLUMN document_category VARCHAR")
                
                if 'document_subcategory' not in existing_columns:
                    missing_columns.append("ADD COLUMN document_subcategory VARCHAR")
                
                if 'tags' not in existing_columns:
                    missing_columns.append("ADD COLUMN tags JSON")
                
                if 'description' not in existing_columns:
                    missing_columns.append("ADD COLUMN description TEXT")
                
                if 'is_public' not in existing_columns:
                    missing_columns.append("ADD COLUMN is_public BOOLEAN DEFAULT FALSE")
                
                if 'access_level' not in existing_columns:
                    missing_columns.append("ADD COLUMN access_level VARCHAR DEFAULT 'private'")
                
                if 'expiry_date' not in existing_columns:
                    missing_columns.append("ADD COLUMN expiry_date TIMESTAMP")
                
                if 'version' not in existing_columns:
                    missing_columns.append("ADD COLUMN version VARCHAR DEFAULT '1.0'")
                
                if 'status' not in existing_columns:
                    missing_columns.append("ADD COLUMN status VARCHAR DEFAULT 'active'")
                
                if missing_columns:
                    print(f"   🔧 Adding missing columns: {len(missing_columns)} columns")
                    
                    # Execute ALTER TABLE statements
                    for column_def in missing_columns:
                        try:
                            alter_sql = f"ALTER TABLE documents {column_def}"
                            print(f"      Executing: {alter_sql}")
                            company_session.execute(text(alter_sql))
                            company_session.commit()
                            print(f"      ✅ Added column successfully")
                        except Exception as e:
                            print(f"      ❌ Failed to add column: {e}")
                            company_session.rollback()
                else:
                    print("   ✅ All required columns already exist")
                
                company_session.close()
                company_engine.dispose()
                
            except Exception as e:
                print(f"   ❌ Error processing company {company.name}: {e}")
                continue
        
        print("\n🎉 Finished processing all companies")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        management_db.rollback()
    finally:
        management_db.close()

if __name__ == "__main__":
    add_missing_document_columns()
