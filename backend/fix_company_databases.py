#!/usr/bin/env python3
"""
Script to fix missing company_id fields in existing company databases.
This script should be run after updating the models to add the company_id field.
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from app.database import get_management_db
from app import models

def fix_company_databases():
    """Fix missing company_id fields in all company databases"""
    
    # Load environment variables
    load_dotenv()
    
    # Get management database connection
    management_db = next(get_management_db())
    
    try:
        # Get all active companies
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        print(f"Found {len(companies)} active companies")
        
        for company in companies:
            print(f"\n🔧 Processing company: {company.name} ({company.id})")
            
            try:
                # Create engine for company database
                company_engine = create_engine(company.database_url)
                company_inspector = inspect(company_engine)
                
                # Check if tables exist and get their structure
                tables_to_check = ['users', 'documents', 'user_invitations', 'esignature_documents']
                
                for table_name in tables_to_check:
                    if company_inspector.has_table(table_name):
                        print(f"  📋 Checking table: {table_name}")
                        
                        # Check if company_id column exists
                        columns = [col['name'] for col in company_inspector.get_columns(table_name)]
                        
                        if 'company_id' not in columns:
                            print(f"    ➕ Adding company_id column to {table_name}")
                            
                            # Add company_id column
                            with company_engine.connect() as conn:
                                conn.execute(text(f"""
                                    ALTER TABLE {table_name} 
                                    ADD COLUMN company_id VARCHAR
                                """))
                                conn.commit()
                            
                            print(f"    ✅ Added company_id column to {table_name}")
                            
                            # Update existing records with company ID
                            print(f"    🔄 Updating existing records in {table_name}")
                            
                            with company_engine.connect() as conn:
                                result = conn.execute(text(f"""
                                    UPDATE {table_name} 
                                    SET company_id = '{company.id}' 
                                    WHERE company_id IS NULL
                                """))
                                conn.commit()
                                
                                print(f"    ✅ Updated {result.rowcount} records in {table_name}")
                        else:
                            print(f"    ✅ company_id column already exists in {table_name}")
                            
                            # Check if there are any NULL company_id values
                            with company_engine.connect() as conn:
                                result = conn.execute(text(f"""
                                    SELECT COUNT(*) as count 
                                    FROM {table_name} 
                                    WHERE company_id IS NULL
                                """))
                                null_count = result.fetchone()[0]
                                
                                if null_count > 0:
                                    print(f"    🔄 Updating {null_count} records with NULL company_id")
                                    conn.execute(text(f"""
                                        UPDATE {table_name} 
                                        SET company_id = '{company.id}' 
                                        WHERE company_id IS NULL
                                    """))
                                    conn.commit()
                                    print(f"    ✅ Updated {null_count} records in {table_name}")
                                else:
                                    print(f"    ✅ All records in {table_name} have company_id set")
                    else:
                        print(f"  ⚠️  Table {table_name} does not exist in {company.name}")
                
                company_engine.dispose()
                print(f"  ✅ Completed processing {company.name}")
                
            except Exception as e:
                print(f"  ❌ Error processing {company.name}: {str(e)}")
                continue
        
        print(f"\n🎉 Database migration completed for {len(companies)} companies")
        
    except Exception as e:
        print(f"❌ Error in migration: {str(e)}")
        raise
    finally:
        management_db.close()

if __name__ == "__main__":
    print("🚀 Starting company database migration...")
    fix_company_databases()
    print("✅ Migration completed successfully!") 