#!/usr/bin/env python3
"""
Script to fix company databases by adding missing columns and ensuring all tables exist
Usage: python fix_company_databases.py
"""

import sys
from sqlalchemy import text
from app.database import get_management_db
from app.models import Company
from app.services.database_manager import db_manager

def fix_company_database(company_id: str, company_name: str, database_url: str):
    """Fix a company database by adding missing columns and ensuring all tables exist"""
    
    try:
        print(f"🔧 Fixing database for {company_name}...")
        
        # Get company database engine
        engine = db_manager.get_company_engine(company_id, database_url)
        
        # Check if folder_name column exists in documents table
        with engine.connect() as conn:
            # Check if documents table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'documents'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print(f"  ❌ Documents table doesn't exist for {company_name}")
                return False
            
            # Check if folder_name column exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'documents' 
                    AND column_name = 'folder_name'
                );
            """))
            column_exists = result.scalar()
            
            if not column_exists:
                print(f"  ➕ Adding folder_name column to documents table...")
                conn.execute(text("ALTER TABLE documents ADD COLUMN folder_name VARCHAR;"))
                conn.commit()
                print(f"  ✅ Added folder_name column to {company_name}")
            else:
                print(f"  ✅ folder_name column already exists for {company_name}")
            
            # Check if all required tables exist
            required_tables = [
                'users', 'documents', 'chat_history', 
                'esignature_documents', 'esignature_recipients', 
                'esignature_audit_logs', 'workflow_approvals',
                'user_invitations'
            ]
            
            missing_tables = []
            for table in required_tables:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    );
                """))
                if not result.scalar():
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"  ⚠️  Missing tables for {company_name}: {missing_tables}")
                print(f"  🔄 Creating missing tables...")
                
                # Create all tables using SQLAlchemy
                from app.models_company import CompanyBase
                CompanyBase.metadata.create_all(bind=engine)
                print(f"  ✅ Created missing tables for {company_name}")
            else:
                print(f"  ✅ All required tables exist for {company_name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error fixing database for {company_name}: {str(e)}")
        return False

def main():
    """Main function"""
    print("🔧 Fixing Company Databases")
    print("=" * 50)
    
    # Get management database session
    management_db = get_management_db()
    db = next(management_db)
    
    try:
        # Get all companies
        companies = db.query(Company).all()
        
        if not companies:
            print("❌ No companies found in the system")
            return
        
        print(f"Found {len(companies)} companies:")
        for company in companies:
            print(f"  - {company.name} (ID: {company.id})")
        print()
        
        # Fix each company database
        fixed_count = 0
        for company in companies:
            success = fix_company_database(
                company.id, 
                company.name, 
                company.database_url
            )
            if success:
                fixed_count += 1
            print()
        
        print("=" * 50)
        print(f"✅ Fixed {fixed_count}/{len(companies)} company databases")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main() 