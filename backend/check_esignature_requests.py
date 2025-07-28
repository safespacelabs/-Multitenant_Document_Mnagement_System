#!/usr/bin/env python3

import sys
sys.path.append('.')
from app.database import get_management_db
from app.services.database_manager import db_manager
from app.models import Company
from app.models_company import ESignatureDocument, ESignatureRecipient

def check_signature_requests():
    """Check all signature requests across all companies"""
    
    print("🔍 Checking E-Signature Requests...")
    print("="*50)
    
    # Get all companies from management database
    management_db = next(get_management_db())
    companies = management_db.query(Company).filter(Company.is_active == True).all()
    
    print(f"🏢 Found {len(companies)} active companies")
    
    total_requests = 0
    
    for company in companies:
        print(f"\n🏢 Company: {company.name} ({company.id})")
        print(f"   Database URL: {company.database_url}")
        
        try:
            # Get company database session
            company_db = next(db_manager.get_company_db(str(company.id), str(company.database_url)))
            
            # Query signature requests
            requests = company_db.query(ESignatureDocument).all()
            
            print(f"   📄 Signature Requests: {len(requests)}")
            
            for request in requests:
                print(f"   ├── ID: {request.id}")
                print(f"   ├── Title: {request.title}")
                print(f"   ├── Status: {request.status}")
                print(f"   ├── Created by: {request.created_by_user_id}")
                print(f"   └── Recipients:")
                
                for recipient in request.recipients:
                    print(f"       ├── {recipient.email} ({recipient.full_name})")
                    print(f"       └── Signed: {recipient.is_signed}")
                print()
            
            total_requests += len(requests)
            company_db.close()
            
        except Exception as e:
            print(f"   ❌ Error accessing database: {e}")
    
    print(f"\n📊 Total E-Signature Requests: {total_requests}")
    
    # Also check if admin2@system.local is a recipient of any requests
    print(f"\n🔍 Checking if admin2@system.local can sign any documents...")
    signable_requests = 0
    
    for company in companies:
        try:
            company_db = next(db_manager.get_company_db(str(company.id), str(company.database_url)))
            
            # Query requests where admin2@system.local is a recipient
            requests = company_db.query(ESignatureDocument).join(ESignatureRecipient).filter(
                ESignatureRecipient.email == "admin2@system.local",
                ESignatureRecipient.is_signed == False,
                ESignatureDocument.status.in_(['sent', 'signed'])
            ).all()
            
            if requests:
                print(f"   🏢 {company.name}: {len(requests)} signable requests")
                signable_requests += len(requests)
            
            company_db.close()
            
        except Exception as e:
            print(f"   ❌ Error checking {company.name}: {e}")
    
    management_db.close()
    
    print(f"\n✅ Total signable requests for admin2@system.local: {signable_requests}")
    
    if signable_requests == 0:
        print(f"\n💡 To test signing functionality:")
        print(f"   1. Login as admin2@system.local")
        print(f"   2. Create a new e-signature request")
        print(f"   3. Add yourself (admin2@system.local) as a recipient")
        print(f"   4. Send the request")
        print(f"   5. You should then see the green pen icon to sign")

if __name__ == "__main__":
    check_signature_requests() 