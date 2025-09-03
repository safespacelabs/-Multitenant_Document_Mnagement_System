#!/usr/bin/env python3
"""
Script to check if documents have been processed by AI
"""

import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_management_db, get_company_db
from app import models
from app.models_company import Document as CompanyDocument
from app.models_document_analysis import DocumentAnalysis

def check_document_processing():
    """Check if documents have been processed by AI"""
    print("🔍 Checking Document AI Processing Status")
    print("=" * 50)
    
    # Get management database
    management_db = next(get_management_db())
    
    try:
        # Get all companies
        companies = management_db.query(models.Company).all()
        
        for company in companies:
            print(f"\n📊 Company: {company.name} (ID: {company.id})")
            
            # Get company database
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)
            
            try:
                # Get all documents
                all_documents = company_db.query(CompanyDocument).all()
                print(f"   Total Documents: {len(all_documents)}")
                
                # Get processed documents
                processed_documents = company_db.query(DocumentAnalysis).all()
                print(f"   AI Processed Documents: {len(processed_documents)}")
                
                # Show recent documents
                recent_docs = company_db.query(CompanyDocument).order_by(
                    CompanyDocument.created_at.desc()
                ).limit(5).all()
                
                print(f"\n   📄 Recent Documents:")
                for doc in recent_docs:
                    # Check if processed
                    analysis = company_db.query(DocumentAnalysis).filter(
                        DocumentAnalysis.document_id == doc.id
                    ).first()
                    
                    status = "✅ AI Processed" if analysis else "❌ Not Processed"
                    print(f"      - {doc.filename} ({doc.file_size} bytes) - {status}")
                    
                    if analysis:
                        print(f"        Title: {analysis.title}")
                        print(f"        Type: {analysis.document_type}")
                        print(f"        Expiry Detected: {analysis.expiry_detected}")
                        if analysis.expiry_date:
                            print(f"        Expiry Date: {analysis.expiry_date}")
                        print(f"        Summary: {analysis.summary[:100]}...")
                        print(f"        AI Model: {analysis.ai_model}")
                        print(f"        Processing Status: {analysis.processing_status}")
                        print()
                
                # Show unprocessed documents
                unprocessed_docs = []
                for doc in all_documents:
                    analysis = company_db.query(DocumentAnalysis).filter(
                        DocumentAnalysis.document_id == doc.id
                    ).first()
                    if not analysis:
                        unprocessed_docs.append(doc)
                
                if unprocessed_docs:
                    print(f"\n   ⚠️  Unprocessed Documents ({len(unprocessed_docs)}):")
                    for doc in unprocessed_docs:
                        print(f"      - {doc.filename} (Uploaded: {doc.created_at})")
                
            except Exception as e:
                print(f"   ❌ Error accessing company database: {str(e)}")
            finally:
                company_db.close()
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        management_db.close()

def check_specific_document(document_filename):
    """Check processing status of a specific document"""
    print(f"\n🔍 Checking Document: {document_filename}")
    print("=" * 50)
    
    management_db = next(get_management_db())
    
    try:
        companies = management_db.query(models.Company).all()
        
        for company in companies:
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)
            
            try:
                # Find the document
                document = company_db.query(CompanyDocument).filter(
                    CompanyDocument.filename.ilike(f"%{document_filename}%")
                ).first()
                
                if document:
                    print(f"📄 Found Document: {document.filename}")
                    print(f"   ID: {document.id}")
                    print(f"   Size: {document.file_size} bytes")
                    print(f"   Uploaded: {document.created_at}")
                    print(f"   Folder: {document.folder_name}")
                    print(f"   User ID: {document.user_id}")
                    
                    # Check AI analysis
                    analysis = company_db.query(DocumentAnalysis).filter(
                        DocumentAnalysis.document_id == document.id
                    ).first()
                    
                    if analysis:
                        print(f"\n✅ AI Analysis Found:")
                        print(f"   Analysis ID: {analysis.id}")
                        print(f"   Title: {analysis.title}")
                        print(f"   Document Type: {analysis.document_type}")
                        print(f"   Summary: {analysis.summary}")
                        print(f"   Expiry Detected: {analysis.expiry_detected}")
                        if analysis.expiry_date:
                            print(f"   Expiry Date: {analysis.expiry_date}")
                            print(f"   Urgency Level: {analysis.urgency_level}")
                        print(f"   AI Model: {analysis.ai_model}")
                        print(f"   Processing Status: {analysis.processing_status}")
                        print(f"   Created: {analysis.created_at}")
                        
                        # Print full JSON metadata
                        print(f"\n📋 Full AI Analysis JSON:")
                        print(f"   Key Topics: {analysis.key_topics}")
                        print(f"   Entities: {analysis.entities}")
                        print(f"   Keywords: {analysis.keywords}")
                        print(f"   Language: {analysis.language}")
                        print(f"   Word Count: {analysis.word_count}")
                        print(f"   Sentiment: {analysis.sentiment}")
                        print(f"   Important Notes: {analysis.important_notes}")
                        print(f"   Compliance Requirements: {analysis.compliance_requirements}")
                        print(f"   Extracted Text: {analysis.extracted_text[:200]}...")
                        
                    else:
                        print(f"\n❌ No AI Analysis Found")
                        print(f"   This document has not been processed by Anthropic AI yet.")
                        
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
            finally:
                company_db.close()
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        management_db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Check specific document
        document_name = sys.argv[1]
        check_specific_document(document_name)
    else:
        # Check all documents
        check_document_processing()
    
    print("\n✨ Check completed!")
