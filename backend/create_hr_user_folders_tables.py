#!/usr/bin/env python3
"""
Database migration script to create HR user folders and related tables
Run this script to add the new tables for HR-managed user folders
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database import get_management_db
from app.models_company import CompanyBase
from app.config import DATABASE_URL

def create_hr_user_folders_tables():
    """Create HR user folders tables in all company databases"""
    
    print("🚀 Starting HR user folders tables creation...")
    
    # Get management database connection
    management_db_gen = get_management_db()
    management_db = next(management_db_gen)
    
    try:
        # Get all active companies using proper SQLAlchemy syntax
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
                
                # Create tables for this company
                CompanyBase.metadata.create_all(bind=company_engine)
                
                print(f"✅ Successfully created HR user folders tables for company: {company_id}")
                
                # Close the engine
                company_engine.dispose()
                
            except Exception as e:
                print(f"❌ Error creating tables for company {company_id}: {str(e)}")
                continue
        
        print("🎉 HR user folders tables creation completed!")
        
    except Exception as e:
        print(f"❌ Error in migration: {str(e)}")
        raise
    finally:
        management_db.close()

if __name__ == "__main__":
    create_hr_user_folders_tables()
