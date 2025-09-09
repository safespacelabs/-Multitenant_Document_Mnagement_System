#!/usr/bin/env python3
"""
Fix Document Analysis Table Issue
This script creates the missing document_analysis table in the company database
"""

from app.database import get_management_db, get_company_db
from app import models
from app.models_document_analysis import DocumentAnalysis, ExpiryNotification
from sqlalchemy import text

def fix_document_analysis_table():
    """Create the missing document_analysis table in the company database"""
    
    print('🔍 Starting database table fix...')
    
    # Get management database
    management_db = next(get_management_db())
    
    try:
        # Get company
        company = management_db.query(models.Company).filter(
            models.Company.id == 'comp_3e6dab46'
        ).first()
        
        if company:
            print(f'✅ Company found: {company.name}')
            
            # Get company database
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)
            
            try:
                # Check if table exists
                result = company_db.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'document_analysis'
                    );
                """))
                
                table_exists = result.scalar()
                print(f'📊 Document analysis table exists: {table_exists}')
                
                if not table_exists:
                    print('🔧 Creating document_analysis table...')
                    # Create the table
                    DocumentAnalysis.__table__.create(company_db.bind, checkfirst=True)
                    print('✅ Document analysis table created successfully')
                    
                    # Also create the expiry_notification table
                    print('🔧 Creating expiry_notification table...')
                    ExpiryNotification.__table__.create(company_db.bind, checkfirst=True)
                    print('✅ Expiry notification table created successfully')
                else:
                    print('✅ Document analysis table already exists')
                    
            except Exception as e:
                print(f'❌ Error creating table: {e}')
                import traceback
                traceback.print_exc()
            finally:
                company_db.close()
        else:
            print('❌ Company not found')
            
    except Exception as e:
        print(f'❌ Error connecting to database: {e}')
        import traceback
        traceback.print_exc()
    finally:
        management_db.close()
    
    print('🎉 Database table fix completed!')

if __name__ == "__main__":
    fix_document_analysis_table()
