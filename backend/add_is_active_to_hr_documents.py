#!/usr/bin/env python3
"""
Database migration script to add missing is_active column to hr_managed_documents table
Run this script to fix the missing is_active field that's causing 500 errors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database import get_management_db
from app.config import DATABASE_URL

def add_is_active_to_hr_documents():
    """Add is_active column to hr_managed_documents table in all company databases"""
    
    print("🚀 Starting migration to add is_active column to hr_managed_documents...")
    
    # Get management database connection
    management_db_gen = get_management_db()
    management_db = next(management_db_gen)
    
    try:
        # Get all active companies
        companies_query = text("SELECT id, database_url FROM companies WHERE is_active = true")
        companies_result = management_db.execute(companies_query)
        companies_list = companies_result.fetchall()
        
        print(f"📊 Found {len(companies_list)} active companies")
        
        for company in companies_list:
            company_id = company[0]
            database_url = company[1]
            
            print(f"🏢 Processing company: {company_id}")
            
            try:
                # Create company database engine
                company_engine = create_engine(database_url)
                
                # Check if is_active column already exists
                check_column_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'hr_managed_documents' 
                    AND column_name = 'is_active'
                """)
                
                with company_engine.connect() as connection:
                    result = connection.execute(check_column_query)
                    column_exists = result.fetchone() is not None
                    
                    if column_exists:
                        print(f"✅ Column is_active already exists for company: {company_id}")
                    else:
                        # Add the missing is_active column
                        add_column_query = text("""
                            ALTER TABLE hr_managed_documents 
                            ADD COLUMN is_active BOOLEAN DEFAULT TRUE
                        """)
                        
                        connection.execute(add_column_query)
                        connection.commit()
                        print(f"✅ Successfully added is_active column for company: {company_id}")
                
                # Close the engine
                company_engine.dispose()
                
            except Exception as e:
                print(f"❌ Error processing company {company_id}: {str(e)}")
                continue
        
        print("🎉 Migration completed!")
        
    except Exception as e:
        print(f"❌ Error in migration: {str(e)}")
        raise
    finally:
        management_db.close()

if __name__ == "__main__":
    add_is_active_to_hr_documents()
