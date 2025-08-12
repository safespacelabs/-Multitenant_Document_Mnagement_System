#!/usr/bin/env python3
"""
Script to fix missing company_id fields in existing company databases.
This script should be run after updating the models to add the company_id field.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_management_db
from app import models

def fix_company_databases():
    """Fix missing company_id fields in all company databases"""
    
    print("🔧 Starting company_id field fix...")
    
    # Get management database session
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
                # Connect to company database
                company_engine = create_engine(company.database_url)
                company_session = sessionmaker(bind=company_engine)()
                
                # Check if company_id column exists in users table
                result = company_session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'company_id'
                """))
                
                if not result.fetchone():
                    print(f"  ➕ Adding company_id column to users table...")
                    company_session.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN company_id VARCHAR NOT NULL DEFAULT %s
                    """), (company.id,))
                    
                    # Update existing users with the company ID
                    company_session.execute(text("""
                        UPDATE users 
                        SET company_id = %s 
                        WHERE company_id = %s
                    """), (company.id, company.id))
                    
                    company_session.commit()
                    print(f"  ✅ Added company_id column and updated existing users")
                else:
                    print(f"  ℹ️  company_id column already exists")
                
                # Check if company_id column exists in documents table
                result = company_session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'documents' AND column_name = 'company_id'
                """))
                
                if not result.fetchone():
                    print(f"  ➕ Adding company_id column to documents table...")
                    company_session.execute(text("""
                        ALTER TABLE documents 
                        ADD COLUMN company_id VARCHAR NOT NULL DEFAULT %s
                    """), (company.id,))
                    
                    # Update existing documents with the company ID
                    company_session.execute(text("""
                        UPDATE documents 
                        SET company_id = %s 
                        WHERE company_id = %s
                    """), (company.id, company.id))
                    
                    company_session.commit()
                    print(f"  ✅ Added company_id column and updated existing documents")
                else:
                    print(f"  ℹ️  company_id column already exists")
                
                # Check if company_id column exists in user_invitations table
                result = company_session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_invitations' AND column_name = 'company_id'
                """))
                
                if not result.fetchone():
                    print(f"  ➕ Adding company_id column to user_invitations table...")
                    company_session.execute(text("""
                        ALTER TABLE user_invitations 
                        ADD COLUMN company_id VARCHAR NOT NULL DEFAULT %s
                    """), (company.id,))
                    
                    # Update existing invitations with the company ID
                    company_session.execute(text("""
                        UPDATE user_invitations 
                        SET company_id = %s 
                        WHERE company_id = %s
                    """), (company.id, company.id))
                    
                    company_session.commit()
                    print(f"  ✅ Added company_id column and updated existing invitations")
                else:
                    print(f"  ℹ️  company_id column already exists")
                
                # Check if company_id column exists in esignature_documents table
                result = company_session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'esignature_documents' AND column_name = 'company_id'
                """))
                
                if not result.fetchone():
                    print(f"  ➕ Adding company_id column to esignature_documents table...")
                    company_session.execute(text("""
                        ALTER TABLE esignature_documents 
                        ADD COLUMN company_id VARCHAR NOT NULL DEFAULT %s
                    """), (company.id,))
                    
                    # Update existing e-signature documents with the company ID
                    company_session.execute(text("""
                        UPDATE esignature_documents 
                        SET company_id = %s 
                        WHERE company_id = %s
                    """), (company.id, company.id))
                    
                    company_session.commit()
                    print(f"  ✅ Added company_id column and updated existing e-signature documents")
                else:
                    print(f"  ℹ️  company_id column already exists")
                
                company_session.close()
                company_engine.dispose()
                
            except Exception as e:
                print(f"  ❌ Error processing company {company.name}: {str(e)}")
                continue
        
        print("\n✅ Company_id field fix completed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        management_db.close()

if __name__ == "__main__":
    load_dotenv()
    fix_company_databases()
