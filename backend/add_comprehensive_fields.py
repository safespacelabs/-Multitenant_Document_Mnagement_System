#!/usr/bin/env python3
"""
Add Comprehensive Extraction Fields
This script adds new fields to the document_analysis table for comprehensive text extraction
"""

from app.database import get_management_db, get_company_db
from app import models
from sqlalchemy import text

def add_comprehensive_fields():
    """Add new fields for comprehensive text extraction to all companies"""
    
    print('🔍 Adding comprehensive extraction fields to document_analysis table...')
    
    # Get management database
    management_db = next(get_management_db())
    
    try:
        # Get ALL companies
        companies = management_db.query(models.Company).all()
        
        if not companies:
            print('❌ No companies found')
            return
            
        print(f'📊 Found {len(companies)} companies to update')
        
        for company in companies:
            print(f'\n🏢 Processing company: {company.name} (ID: {company.id})')
            
            try:
                # Get company database
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                try:
                    # Add new columns to document_analysis table
                    print(f'   🔧 Adding comprehensive extraction fields for {company.name}...')
                    
                    # Check if columns already exist
                    result = company_db.execute(text('''
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'document_analysis' 
                        AND column_name IN ('document_sections', 'key_findings', 'data_points', 'action_items')
                    ''')).fetchall()
                    
                    existing_columns = [row[0] for row in result]
                    
                    if 'document_sections' not in existing_columns:
                        company_db.execute(text('ALTER TABLE document_analysis ADD COLUMN document_sections TEXT[]'))
                        print(f'   ✅ Added document_sections column')
                    
                    if 'key_findings' not in existing_columns:
                        company_db.execute(text('ALTER TABLE document_analysis ADD COLUMN key_findings TEXT[]'))
                        print(f'   ✅ Added key_findings column')
                    
                    if 'data_points' not in existing_columns:
                        company_db.execute(text('ALTER TABLE document_analysis ADD COLUMN data_points TEXT[]'))
                        print(f'   ✅ Added data_points column')
                    
                    if 'action_items' not in existing_columns:
                        company_db.execute(text('ALTER TABLE document_analysis ADD COLUMN action_items TEXT[]'))
                        print(f'   ✅ Added action_items column')
                    
                    company_db.commit()
                    print(f'   ✅ Comprehensive fields added successfully for {company.name}!')
                    
                except Exception as e:
                    print(f'   ❌ Error adding fields for {company.name}: {e}')
                    import traceback
                    traceback.print_exc()
                finally:
                    company_db.close()
                    
            except Exception as e:
                print(f'   ❌ Error connecting to database for {company.name}: {e}')
                import traceback
                traceback.print_exc()
        
        print(f'\n🎉 Comprehensive fields addition completed for {len(companies)} companies!')
            
    except Exception as e:
        print(f'❌ Error connecting to database: {e}')
        import traceback
        traceback.print_exc()
    finally:
        management_db.close()

if __name__ == "__main__":
    add_comprehensive_fields()
