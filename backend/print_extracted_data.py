#!/usr/bin/env python3
"""
Print All Extracted Data from AI Processing
This script fetches and displays all the AI-extracted data from documents
"""

from app.database import get_management_db, get_company_db
from app import models
from sqlalchemy import text
import json
from datetime import datetime

def print_extracted_data():
    """Print all extracted data from AI processing"""
    
    print('🔍 Fetching all AI-extracted data from documents...')
    print('=' * 80)
    
    # Get management database
    management_db = next(get_management_db())
    
    try:
        # Get company
        company = management_db.query(models.Company).filter(
            models.Company.id == 'comp_3e6dab46'
        ).first()
        
        if company:
            print(f'✅ Company: {company.name} (ID: {company.id})')
            
            # Get company database
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)
            
            try:
                # Get all document analysis records
                print(f'\n📊 Fetching all document analysis records...')
                result = company_db.execute(text('''
                    SELECT * FROM document_analysis 
                    ORDER BY created_at DESC
                ''')).fetchall()
                
                if not result:
                    print('❌ No document analysis records found')
                    return
                
                print(f'📈 Found {len(result)} document analysis records\n')
                
                # Display each record
                for i, record in enumerate(result, 1):
                    print(f'📄 DOCUMENT ANALYSIS #{i}')
                    print('-' * 60)
                    print(f'🆔 Analysis ID: {record[0]}')
                    print(f'📋 Document ID: {record[1]}')
                    print(f'👤 User: {record[3]} ({record[4]})')
                    print(f'📅 Created: {record[26]}')
                    print()
                    
                    # Basic Information
                    print('📝 BASIC INFORMATION:')
                    print(f'   Title: {record[5]}')
                    print(f'   Summary: {record[6]}')
                    print(f'   Document Type: {record[7]}')
                    print(f'   Folder: {record[8]}')
                    print()
                    
                    # AI Analysis Results
                    print('🤖 AI ANALYSIS RESULTS:')
                    print(f'   Key Topics: {record[9]}')
                    print(f'   Keywords: {record[11]}')
                    print(f'   Language: {record[12]}')
                    print(f'   Word Count: {record[13]}')
                    print(f'   Sentiment: {record[14]}')
                    print()
                    
                    # Entities (formatted nicely)
                    print('🏷️ ENTITIES:')
                    entities = record[10]
                    if entities:
                        for entity_type, entity_list in entities.items():
                            if entity_list:
                                print(f'   {entity_type.title()}: {entity_list}')
                    else:
                        print('   No entities found')
                    print()
                    
                    # Expiry Information
                    print('⏰ EXPIRY INFORMATION:')
                    print(f'   Expiry Detected: {record[15]}')
                    print(f'   Expiry Date: {record[16]}')
                    print(f'   Expiry Type: {record[17]}')
                    print(f'   Urgency Level: {record[18]}')
                    print()
                    
                    # Extracted Content
                    print('📄 EXTRACTED CONTENT:')
                    print(f'   Extracted Text: {record[19][:200]}{"..." if len(str(record[19])) > 200 else ""}')
                    print()
                    
                    # Important Notes and Compliance
                    print('📌 IMPORTANT NOTES:')
                    if record[20]:
                        for note in record[20]:
                            print(f'   • {note}')
                    else:
                        print('   No important notes')
                    print()
                    
                    print('⚖️ COMPLIANCE REQUIREMENTS:')
                    if record[21]:
                        for req in record[21]:
                            print(f'   • {req}')
                    else:
                        print('   No compliance requirements')
                    print()
                    
                    # Technical Information
                    print('🔧 TECHNICAL INFORMATION:')
                    print(f'   AI Model: {record[23]}')
                    print(f'   Processing Status: {record[24]}')
                    print(f'   Extracted At: {record[22]}')
                    print(f'   Error Message: {record[25] if record[25] else "None"}')
                    print()
                    
                    print('=' * 80)
                    print()
                
                # Summary Statistics
                print('📊 SUMMARY STATISTICS:')
                print('-' * 40)
                
                # Count by document type
                type_counts = {}
                for record in result:
                    doc_type = record[7] or 'Unknown'
                    type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                
                print('📋 Document Types:')
                for doc_type, count in type_counts.items():
                    print(f'   {doc_type}: {count}')
                print()
                
                # Count by processing status
                status_counts = {}
                for record in result:
                    status = record[24] or 'Unknown'
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print('🔄 Processing Status:')
                for status, count in status_counts.items():
                    print(f'   {status}: {count}')
                print()
                
                # Count by AI model
                model_counts = {}
                for record in result:
                    model = record[23] or 'Unknown'
                    model_counts[model] = model_counts.get(model, 0) + 1
                
                print('🤖 AI Models Used:')
                for model, count in model_counts.items():
                    print(f'   {model}: {count}')
                print()
                
                # Expiry statistics
                expiry_detected = sum(1 for record in result if record[15])
                print(f'⏰ Documents with Expiry: {expiry_detected}/{len(result)}')
                
                # Recent activity
                recent_count = sum(1 for record in result if record[26] and (datetime.now() - record[26]).days < 1)
                print(f'🕐 Recent Activity (last 24h): {recent_count} documents')
                
            except Exception as e:
                print(f'❌ Error fetching data: {e}')
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
    
    print('\n🎉 Data extraction display completed!')

if __name__ == "__main__":
    print_extracted_data()
