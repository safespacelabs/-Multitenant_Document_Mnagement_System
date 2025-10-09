#!/usr/bin/env python3
"""
Script to create chunked document tables in company databases
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_management_db
from app.models import Company
from app.services.database_manager import db_manager
from app.models_chunked_documents import Base
from sqlalchemy.orm import Session


def create_chunked_tables_for_all_companies():
    """Create chunked document tables for all companies"""
    try:
        # Get management database
        management_db_gen = get_management_db()
        management_db = next(management_db_gen)
        
        try:
            # Get all companies
            companies = management_db.query(Company).filter(Company.is_active == True).all()
            
            print(f"Found {len(companies)} active companies")
            
            for company in companies:
                try:
                    print(f"Creating chunked tables for company: {company.name} ({company.id})")
                    
                    # Get company database connection
                    company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
                    company_db = next(company_db_gen)
                    
                    try:
                        # Create tables
                        Base.metadata.create_all(company_db.bind)
                        print(f"✅ Created chunked tables for company: {company.name}")
                        
                    except Exception as e:
                        print(f"❌ Error creating tables for company {company.name}: {e}")
                    finally:
                        company_db.close()
                        
                except Exception as e:
                    print(f"❌ Error processing company {company.name}: {e}")
            
            print("✅ Completed creating chunked tables for all companies")
            
        finally:
            management_db.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    create_chunked_tables_for_all_companies()
