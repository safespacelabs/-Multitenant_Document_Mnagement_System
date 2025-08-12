#!/usr/bin/env python3
"""
Simple script to add company_id columns to existing company database tables.
This script handles the database migration for the new company_id field.
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from app.database import get_management_db
from app import models

def add_company_id_columns():
    """Add company_id columns to all company databases"""
    
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
                
                # Tables that need company_id column
                tables = ['users', 'documents', 'user_invitations', 'esignature_documents']
                
                for table in tables:
                    try:
                        # Check if company_id column exists
                        with company_engine.connect() as conn:
                            # Try to add company_id column (will fail if it already exists)
                            conn.execute(text(f"""
                                ALTER TABLE {table} 
                                ADD COLUMN company_id VARCHAR
                            """))
                            conn.commit()
                            print(f"  ✅ Added company_id column to {table}")
                            
                            # Update existing records
                            result = conn.execute(text(f"""
                                UPDATE {table} 
                                SET company_id = '{company.id}' 
                                WHERE company_id IS NULL
                            """))
                            conn.commit()
                            print(f"  ✅ Updated {result.rowcount} records in {table}")
                            
                    except Exception as e:
                        if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                            print(f"  ✅ company_id column already exists in {table}")
                            
                            # Still update any NULL values
                            try:
                                with company_engine.connect() as conn:
                                    result = conn.execute(text(f"""
                                        UPDATE {table} 
                                        SET company_id = '{company.id}' 
                                        WHERE company_id IS NULL
                                    """))
                                    conn.commit()
                                    if result.rowcount > 0:
                                        print(f"  ✅ Updated {result.rowcount} records in {table}")
                                    else:
                                        print(f"  ✅ All records in {table} already have company_id")
                            except Exception as update_error:
                                print(f"  ⚠️  Could not update records in {table}: {str(update_error)}")
                        else:
                            print(f"  ❌ Error with {table}: {str(e)}")
                
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
    print("🚀 Starting company_id column migration...")
    add_company_id_columns()
    print("✅ Migration completed successfully!")
