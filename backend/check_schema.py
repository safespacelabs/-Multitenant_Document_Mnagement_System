#!/usr/bin/env python3
"""
Check Database Schema
This script checks the current database schema to see the exact column positions
"""

from app.database import get_management_db, get_company_db
from app import models
from sqlalchemy import text

def check_schema():
    """Check the current database schema"""
    
    print('🔍 Checking current database schema...')
    
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
                # Get the actual column order from the database
                print('\n📋 Current Database Schema:')
                result = company_db.execute(text('''
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'document_analysis' 
                    ORDER BY ordinal_position
                ''')).fetchall()
                
                for i, (name, dtype) in enumerate(result):
                    print(f'{i:2d}. {name:<25} ({dtype})')
                
                # Get the latest record to see what's actually stored
                print('\n📊 Latest Record Sample:')
                latest = company_db.execute(text('SELECT * FROM document_analysis ORDER BY id DESC LIMIT 1')).fetchone()
                
                if latest:
                    print(f'Total columns: {len(latest)}')
                    print(f'ID: {latest[0]}')
                    print(f'Title: {latest[5]}')
                    print(f'Summary: {latest[6][:100]}...')
                    print(f'Extracted Text: {latest[19][:100]}...')
                    
                    # Check if comprehensive fields exist
                    if len(latest) > 22:
                        print(f'Document Sections: {latest[22] if len(latest) > 22 else "N/A"}')
                        print(f'Key Findings: {latest[23] if len(latest) > 23 else "N/A"}')
                        print(f'Data Points: {latest[24] if len(latest) > 24 else "N/A"}')
                        print(f'Action Items: {latest[25] if len(latest) > 25 else "N/A"}')
                    else:
                        print('❌ Comprehensive fields not found in database')
                
            except Exception as e:
                print(f'❌ Error checking schema: {e}')
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

if __name__ == "__main__":
    check_schema()
