#!/usr/bin/env python3

import sys
sys.path.append('.')
from app.database import get_management_db
from app.services.database_manager import db_manager
from app.models import Company
from app.models_company import ESignatureDocument, ESignatureRecipient, User, Document
from datetime import datetime, timedelta
import json

def create_test_signature_request():
    """Create a test e-signature request to test system admin signing"""
    
    print("🧪 Creating Test E-Signature Request...")
    print("="*50)
    
    # Get a company database (use SafespaceLabs)
    management_db = next(get_management_db())
    companies = management_db.query(Company).filter(Company.name == "SafespaceLabs").first()
    
    if not companies:
        print("❌ SafespaceLabs company not found")
        return
    
    company = companies
    print(f"🏢 Using company: {company.name} ({company.id})")
    
    try:
        # Get company database session
        company_db = next(db_manager.get_company_db(str(company.id), str(company.database_url)))
        
        # Create a test document first
        test_doc = Document(
            filename="test_contract.pdf",
            original_filename="test_contract.pdf",
            file_path="test/test_contract.pdf",
            file_size=1024,
            file_type="application/pdf",
            s3_key="test/test_contract.pdf",
            user_id="test_user",
            processed=True,
            created_at=datetime.utcnow()
        )
        company_db.add(test_doc)
        company_db.flush()
        
        # Create e-signature request
        esign_doc = ESignatureDocument(
            document_id=test_doc.id,
            title="Test Contract for System Admin Signing",
            message="This is a test contract to verify system admin signing functionality",
            status="sent",
            created_by_user_id="test_user",
            require_all_signatures=True,
            expires_at=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow()
        )
        company_db.add(esign_doc)
        company_db.flush()
        
        # Add a regular recipient (not system admin)
        recipient = ESignatureRecipient(
            esignature_document_id=esign_doc.id,
            email="test@example.com",
            full_name="Test User",
            role="employee",
            is_signed=False,
            created_at=datetime.utcnow()
        )
        company_db.add(recipient)
        
        # Commit the changes
        company_db.commit()
        
        print(f"✅ Created e-signature request: {esign_doc.id}")
        print(f"   Document: {test_doc.filename}")
        print(f"   Title: {esign_doc.title}")
        print(f"   Status: {esign_doc.status}")
        print(f"   Recipients: {len([recipient])}")
        print(f"   └── {recipient.email} ({recipient.full_name})")
        
        # Test the signing functionality
        print(f"\n🔍 Testing System Admin Signing...")
        print(f"   Admin email: admin2@system.local")
        print(f"   Document ID: {esign_doc.id}")
        print(f"   Expected: System admin should be able to sign this document")
        print(f"   Backend will automatically add admin as recipient")
        
        company_db.close()
        management_db.close()
        
        return esign_doc.id
        
    except Exception as e:
        print(f"❌ Error creating test request: {e}")
        company_db.rollback()
        company_db.close()
        management_db.close()
        return None

def check_document_can_be_signed(esign_doc_id):
    """Check if the document can be signed by system admin"""
    
    print(f"\n🔍 Checking Document Signing Status...")
    print("="*50)
    
    management_db = next(get_management_db())
    company = management_db.query(Company).filter(Company.name == "SafespaceLabs").first()
    
    if not company:
        print("❌ Company not found")
        return
    
    try:
        company_db = next(db_manager.get_company_db(str(company.id), str(company.database_url)))
        
        # Get the document
        esign_doc = company_db.query(ESignatureDocument).filter(
            ESignatureDocument.id == esign_doc_id
        ).first()
        
        if not esign_doc:
            print(f"❌ Document {esign_doc_id} not found")
            return
        
        print(f"📄 Document: {esign_doc.title}")
        print(f"   Status: {esign_doc.status}")
        can_sign = str(esign_doc.status) in ['sent', 'signed']
        print(f"   Can be signed: {can_sign}")
        
        # Check recipients
        recipients = company_db.query(ESignatureRecipient).filter(
            ESignatureRecipient.esignature_document_id == esign_doc_id
        ).all()
        
        print(f"   Recipients: {len(recipients)}")
        for recipient in recipients:
            print(f"   ├── {recipient.email} ({recipient.full_name})")
            print(f"   └── Signed: {recipient.is_signed}")
        
        # Check if admin2@system.local is a recipient
        admin_recipient = company_db.query(ESignatureRecipient).filter(
            ESignatureRecipient.esignature_document_id == esign_doc_id,
            ESignatureRecipient.email == "admin2@system.local"
        ).first()
        
        if admin_recipient:
            print(f"   System admin is recipient: Yes")
            print(f"   Admin signed: {admin_recipient.is_signed}")
        else:
            print(f"   System admin is recipient: No")
            print(f"   ✅ System admin can still sign (will be added as recipient)")
        
        company_db.close()
        management_db.close()
        
    except Exception as e:
        print(f"❌ Error checking document: {e}")
        company_db.close()
        management_db.close()

def main():
    """Main test function"""
    
    print("🧪 System Admin Signing Test")
    print("="*50)
    
    # Create test signature request
    esign_doc_id = create_test_signature_request()
    
    if esign_doc_id:
        # Check if document can be signed
        check_document_can_be_signed(esign_doc_id)
        
        print(f"\n💡 To test the signing functionality:")
        print(f"   1. Start the backend server")
        print(f"   2. Login as admin2@system.local")
        print(f"   3. Go to E-signature management")
        print(f"   4. You should see the green pen icon for document {esign_doc_id}")
        print(f"   5. Click the pen icon to sign the document")
        print(f"   6. The system will automatically add you as a recipient and process the signature")
        
        print(f"\n🔧 Frontend changes made:")
        print(f"   - System admins can now see signing button for any document in 'sent' or 'signed' status")
        print(f"   - No need to be explicitly added as a recipient")
        
        print(f"\n🔧 Backend changes made:")
        print(f"   - System admins are automatically added as recipients when signing")
        print(f"   - Maintains audit trail and signature tracking")
        print(f"   - Updates document status correctly")
    
    else:
        print(f"❌ Failed to create test signature request")

if __name__ == "__main__":
    main() 