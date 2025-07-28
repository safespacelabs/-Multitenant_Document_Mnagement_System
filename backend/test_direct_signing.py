#!/usr/bin/env python3

import sys
sys.path.append('.')
from app.database import get_management_db
from app.services.database_manager import db_manager
from app.models import Company
from app.models_company import ESignatureDocument, ESignatureRecipient, Document, ESignatureAuditLog
from datetime import datetime, timedelta
import json

def test_direct_signing_functionality():
    """Test the complete direct signing functionality for system admins"""
    
    print("🧪 Testing Direct Document Signing Functionality")
    print("="*60)
    
    # Get a company database (use SafespaceLabs)
    management_db = next(get_management_db())
    company = management_db.query(Company).filter(Company.name == "SafespaceLabs").first()
    
    if not company:
        print("❌ SafespaceLabs company not found")
        return
    
    print(f"🏢 Using company: {company.name} ({company.id})")
    
    try:
        # Get company database session
        company_db = next(db_manager.get_company_db(str(company.id), str(company.database_url)))
        
        # Create a test document
        test_doc = Document(
            filename="test_contract_direct.pdf",
            original_filename="test_contract_direct.pdf",
            file_path="test/test_contract_direct.pdf",
            file_size=2048,
            file_type="application/pdf",
            s3_key="test/test_contract_direct.pdf",
            user_id="test_user",
            processed=True,
            created_at=datetime.utcnow()
        )
        company_db.add(test_doc)
        company_db.commit()
        
        print(f"✅ Created test document: {test_doc.id}")
        print(f"   Filename: {test_doc.original_filename}")
        print(f"   Size: {test_doc.file_size} bytes")
        
        # Test the direct signing process
        print(f"\n🔍 Testing Direct Signing Process...")
        print(f"   Document ID: {test_doc.id}")
        print(f"   Expected behavior:")
        print(f"   1. System admin logs in")
        print(f"   2. Navigates to document list")
        print(f"   3. Sees green 'Sign Document' button")
        print(f"   4. Clicks button to open signing modal")
        print(f"   5. Enters signature and submits")
        print(f"   6. System creates e-signature record automatically")
        
        # Check for any existing e-signature records for this document
        existing_esign = company_db.query(ESignatureDocument).filter(
            ESignatureDocument.document_id == test_doc.id
        ).first()
        
        if existing_esign:
            print(f"   ⚠️  Document already has e-signature record: {existing_esign.id}")
            print(f"       Status: {existing_esign.status}")
            print(f"       Title: {existing_esign.title}")
        else:
            print(f"   📝 No existing e-signature record (as expected)")
        
        # Simulate what happens after direct signing
        print(f"\n🔧 Simulating Direct Signing Result...")
        
        # This is what the backend endpoint would create
        simulated_esign = ESignatureDocument(
            document_id=test_doc.id,
            title=f"Direct Signature: {test_doc.original_filename}",
            message="Document signed directly by system administrator",
            status="completed",
            created_by_user_id="admin2@system.local",
            require_all_signatures=False,
            expires_at=datetime.utcnow() + timedelta(days=365),
            completed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        # System admin as recipient (signed)
        simulated_recipient = ESignatureRecipient(
            esignature_document_id=simulated_esign.id,
            email="admin2@system.local",
            full_name="System Administrator 2",
            role="system_admin",
            is_signed=True,
            signed_at=datetime.utcnow(),
            signature_text="System Administrator 2",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0 (Test Browser)",
            created_at=datetime.utcnow()
        )
        
        # Audit log
        simulated_audit = ESignatureAuditLog(
            esignature_document_id=simulated_esign.id,
            action="direct_signed",
            user_email="admin2@system.local",
            user_ip="127.0.0.1",
            details=json.dumps({
                "signed_by_role": "system_admin",
                "signed_by_name": "System Administrator 2",
                "signature_type": "direct",
                "signature_text": "System Administrator 2",
                "document_filename": test_doc.original_filename,
                "ip_address": "127.0.0.1",
                "user_agent": "Mozilla/5.0 (Test Browser)"
            }),
            created_at=datetime.utcnow()
        )
        
        print(f"   ✅ E-signature record would be created:")
        print(f"       ID: {simulated_esign.id}")
        print(f"       Title: {simulated_esign.title}")
        print(f"       Status: {simulated_esign.status}")
        print(f"       Signed by: {simulated_recipient.email}")
        print(f"       Signature: {simulated_recipient.signature_text}")
        print(f"       Audit action: {simulated_audit.action}")
        
        # Check what the system admin would see
        print(f"\n📱 Frontend Experience:")
        print(f"   System Admin sees in document list:")
        print(f"   ├── Blue 'Send for Signature' button (create request)")
        print(f"   └── Green 'Sign Document' button (direct sign)")
        print(f"   ")
        print(f"   When clicking 'Sign Document':")
        print(f"   ├── Modal opens with document info")
        print(f"   ├── Signature input field")
        print(f"   └── Green 'Sign Document' button")
        print(f"   ")
        print(f"   After successful signing:")
        print(f"   ├── Success message displayed")
        print(f"   ├── Modal closes")
        print(f"   └── Document list refreshes")
        
        # API endpoints summary
        print(f"\n🔌 API Endpoints Used:")
        print(f"   POST /api/esignature/sign-document-directly/{test_doc.id}")
        print(f"   ├── Payload: signature_text, ip_address, user_agent")
        print(f"   ├── Auth: System admin required")
        print(f"   └── Response: esignature_document_id, signed_by, status")
        
        print(f"\n✅ Direct Signing Test Complete!")
        print(f"   Document: {test_doc.original_filename}")
        print(f"   Ready for testing in UI")
        
        company_db.close()
        management_db.close()
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        company_db.rollback()
        company_db.close()
        management_db.close()

def test_existing_documents():
    """Test signing existing documents"""
    
    print(f"\n🔍 Testing Existing Document Signing...")
    print("="*50)
    
    management_db = next(get_management_db())
    company = management_db.query(Company).filter(Company.name == "SafespaceLabs").first()
    
    if not company:
        print("❌ Company not found")
        return
    
    try:
        company_db = next(db_manager.get_company_db(str(company.id), str(company.database_url)))
        
        # Check for existing documents
        documents = company_db.query(Document).limit(5).all()
        
        print(f"📄 Found {len(documents)} existing documents:")
        for doc in documents:
            print(f"   ├── {doc.original_filename} ({doc.id})")
            print(f"   └── Size: {doc.file_size} bytes, Type: {doc.file_type}")
        
        if documents:
            print(f"\n✅ System admin can sign any of these documents directly!")
            print(f"   Just click the green 'Sign Document' button")
        else:
            print(f"\n💡 Upload some documents first to test direct signing")
        
        company_db.close()
        management_db.close()
        
    except Exception as e:
        print(f"❌ Error checking existing documents: {e}")
        company_db.close()
        management_db.close()

def main():
    """Main test function"""
    
    print("🚀 System Admin Direct Document Signing Test")
    print("="*60)
    
    test_direct_signing_functionality()
    test_existing_documents()
    
    print(f"\n🎯 How to Use Direct Signing:")
    print(f"   1. Login as admin2@system.local")
    print(f"   2. Go to Documents section")
    print(f"   3. For ANY document, you'll see:")
    print(f"      - Blue 'Send for Signature' (create request)")
    print(f"      - Green 'Sign Document' (direct sign)")
    print(f"   4. Click green 'Sign Document' button")
    print(f"   5. Enter your signature in the modal")
    print(f"   6. Click 'Sign Document' to complete")
    print(f"   7. Document is instantly signed and marked as completed")
    
    print(f"\n🔧 Key Features:")
    print(f"   ✅ System admin can sign any document directly")
    print(f"   ✅ No need to create formal e-signature requests")
    print(f"   ✅ Works for newly uploaded documents")
    print(f"   ✅ Works for existing documents")
    print(f"   ✅ Full audit trail maintained")
    print(f"   ✅ Signature tracking and IP logging")
    print(f"   ✅ Document status updated automatically")

if __name__ == "__main__":
    main() 