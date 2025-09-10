#!/usr/bin/env python3
"""
Debug Field Mapping - Check exact database vs SQLAlchemy field mapping
"""

from app.database import get_management_db, get_company_db
from app import models
from app.models_document_analysis import DocumentAnalysis
from sqlalchemy import text

def debug_field_mapping():
    """Debug the exact field mapping between SQLAlchemy model and database"""
    
    print('🔍 Debugging field mapping between SQLAlchemy model and database...')
    
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
                # Get the latest record from the database
                print('\n📥 Fetching latest record from database...')
                result = company_db.execute(text('SELECT * FROM document_analysis ORDER BY id DESC LIMIT 1')).fetchone()
                
                if result:
                    print(f'\n📊 Raw Database Record (ID: {result[0]}):')
                    print(f'   Column 0  (id): {result[0]}')
                    print(f'   Column 1  (document_id): {result[1]}')
                    print(f'   Column 2  (user_id): {result[2]}')
                    print(f'   Column 3  (user_name): {result[3]}')
                    print(f'   Column 4  (user_email): {result[4]}')
                    print(f'   Column 5  (title): {result[5]}')
                    print(f'   Column 6  (summary): {result[6]}')
                    print(f'   Column 7  (document_type): {result[7]}')
                    print(f'   Column 8  (folder_name): {result[8]}')
                    print(f'   Column 9  (key_topics): {result[9]}')
                    print(f'   Column 10 (entities): {result[10]}')
                    print(f'   Column 11 (keywords): {result[11]}')
                    print(f'   Column 12 (language): {result[12]}')
                    print(f'   Column 13 (word_count): {result[13]}')
                    print(f'   Column 14 (sentiment): {result[14]}')
                    print(f'   Column 15 (expiry_detected): {result[15]}')
                    print(f'   Column 16 (expiry_date): {result[16]}')
                    print(f'   Column 17 (expiry_type): {result[17]}')
                    print(f'   Column 18 (urgency_level): {result[18]}')
                    print(f'   Column 19 (extracted_text): {result[19]}')
                    print(f'   Column 20 (important_notes): {result[20]}')
                    print(f'   Column 21 (compliance_requirements): {result[21]}')
                    print(f'   Column 22 (extracted_at): {result[22]}')
                    print(f'   Column 23 (ai_model): {result[23]}')
                    print(f'   Column 24 (processing_status): {result[24]}')
                    print(f'   Column 25 (error_message): {result[25]}')
                    print(f'   Column 26 (created_at): {result[26]}')
                    print(f'   Column 27 (updated_at): {result[27]}')
                    
                    # Now let's check what SQLAlchemy thinks the field order should be
                    print('\n📋 SQLAlchemy Model Field Order:')
                    model_columns = DocumentAnalysis.__table__.columns
                    for i, (name, column) in enumerate(model_columns.items()):
                        print(f'   Field {i:2d}: {name:<25} -> Column {i}')
                    
                    # Check if there's a mismatch
                    print('\n🔍 Field Mapping Analysis:')
                    print(f'   Database Column 9  (key_topics): {result[9]}')
                    print(f'   Database Column 10 (entities): {result[10]}')
                    print(f'   Database Column 11 (keywords): {result[11]}')
                    print(f'   Database Column 12 (language): {result[12]}')
                    print(f'   Database Column 13 (word_count): {result[13]}')
                    print(f'   Database Column 14 (sentiment): {result[14]}')
                    
                    # Check if the data is in the wrong columns
                    if isinstance(result[9], list) and 'immigration' in str(result[9]):
                        print('✅ Key Topics: CORRECT position')
                    else:
                        print('❌ Key Topics: WRONG position')
                    
                    if isinstance(result[10], dict) and 'dates' in result[10]:
                        print('✅ Entities: CORRECT position')
                    else:
                        print('❌ Entities: WRONG position')
                    
                    if isinstance(result[11], list) and 'green card' in str(result[11]):
                        print('✅ Keywords: CORRECT position')
                    else:
                        print('❌ Keywords: WRONG position')
                    
                    if isinstance(result[12], str) and result[12] in ['english', 'en']:
                        print('✅ Language: CORRECT position')
                    else:
                        print('❌ Language: WRONG position')
                    
                    if isinstance(result[13], int):
                        print('✅ Word Count: CORRECT position')
                    else:
                        print('❌ Word Count: WRONG position')
                    
                    if isinstance(result[14], str) and result[14] in ['neutral', 'positive', 'negative']:
                        print('✅ Sentiment: CORRECT position')
                    else:
                        print('❌ Sentiment: WRONG position')
                
            except Exception as e:
                print(f'❌ Error during field mapping debug: {e}')
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
    
    print('\n🎉 Field mapping debug completed!')

if __name__ == "__main__":
    debug_field_mapping()
