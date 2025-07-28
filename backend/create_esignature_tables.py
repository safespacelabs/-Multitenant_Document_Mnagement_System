#!/usr/bin/env python3
"""
Script to create E-signature database tables
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_management_db
from app.models_company import ESignatureDocument, ESignatureRecipient, ESignatureAuditLog
from app.services.database_manager import db_manager
from app import models
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import traceback

def create_esignature_tables():
    """Create E-signature tables in the database"""
    try:
        print("🔍 Checking E-signature tables...")
        
        # Get management database to find companies
        management_db = next(get_management_db())
        
        # Get all active companies
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        if not companies:
            print("❌ No active companies found!")
            return False
        
        success_count = 0
        
        for company in companies:
            print(f"\n🏢 Processing company: {company.name} (ID: {company.id})")
            
            try:
                # Get company database connection
                company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                # Check if tables exist
                inspector = inspect(company_db.bind)
                existing_tables = inspector.get_table_names()
                
                esignature_tables = [
                    'esignature_documents',
                    'esignature_recipients', 
                    'esignature_audit_logs'
                ]
                
                missing_tables = [table for table in esignature_tables if table not in existing_tables]
                
                if missing_tables:
                    print(f"❌ Missing E-signature tables: {missing_tables}")
                    print("✅ Creating E-signature tables...")
                    
                    # Import the models to register them
                    from app.models_company import CompanyBase
                    
                    # Create the tables
                    CompanyBase.metadata.create_all(bind=company_db.bind)
                    
                    print("✅ E-signature tables created successfully!")
                    
                    # Verify creation
                    inspector = inspect(company_db.bind)
                    new_tables = inspector.get_table_names()
                    created_tables = [table for table in esignature_tables if table in new_tables]
                    print(f"✅ Verified tables: {created_tables}")
                    
                else:
                    print("✅ All E-signature tables already exist!")
                    
                # Test table structure
                for table_name in esignature_tables:
                    if table_name in inspector.get_table_names():
                        columns = inspector.get_columns(table_name)
                        print(f"📋 Table {table_name} has {len(columns)} columns")
                        
                company_db.close()
                success_count += 1
                
            except Exception as e:
                print(f"❌ Error processing company {company.name}: {str(e)}")
                traceback.print_exc()
                continue
        
        management_db.close()
        
        print(f"\n🎉 E-signature database setup complete! Processed {success_count}/{len(companies)} companies")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error creating E-signature tables: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_esignature_tables()
    sys.exit(0 if success else 1) 