#!/usr/bin/env python3

"""
Test script to verify e-signature signing functionality
This demonstrates that system admins can now sign documents
"""

import os
import sys
import json
import requests
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

def test_esignature_signing():
    """Test the complete e-signature signing workflow"""
    
    print("🚀 Testing E-signature Signing Workflow...")
    
    # Step 1: Login as system admin
    print("\n🔑 Step 1: Login as system admin")
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    auth_data = login_response.json()
    token = auth_data["access_token"]
    user_info = auth_data["user"]
    
    print(f"✅ Login successful for user: {user_info['username']} (role: {user_info['role']})")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Check e-signature permissions
    print("\n🔍 Step 2: Check e-signature permissions")
    perms_response = requests.get(f"{BASE_URL}/esignature/permissions/my-role", headers=headers)
    
    if perms_response.status_code == 200:
        perms_data = perms_response.json()
        print(f"✅ Current role: {perms_data['user_role']}")
        print(f"✅ Can sign documents: {perms_data['permissions'].get('sign', False)}")
        print(f"✅ Can create requests: {perms_data['permissions'].get('create', False)}")
    else:
        print(f"⚠️  Could not check permissions: {perms_response.status_code}")
    
    # Step 3: Create a test e-signature request
    print("\n📝 Step 3: Create test e-signature request")
    
    # Use system admin's email as recipient so they can sign their own request
    system_admin_email = user_info.get("email", "admin@system.com")
    
    create_request = {
        "document_id": "test_doc_001",
        "title": "Test Document Signing",
        "message": "This is a test document for signing by system admin",
        "recipients": [
            {
                "email": system_admin_email,
                "full_name": "System Administrator",
                "role": "system_admin"
            }
        ],
        "require_all_signatures": True,
        "expires_in_days": 7
    }
    
    create_response = requests.post(f"{BASE_URL}/esignature/create-request", 
                                   json=create_request, headers=headers)
    
    if create_response.status_code != 200:
        print(f"❌ Create request failed: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return False
    
    esign_data = create_response.json()
    esign_id = esign_data["id"]
    
    print(f"✅ E-signature request created successfully: {esign_id}")
    print(f"✅ Status: {esign_data['status']}")
    print(f"✅ Auto-sent: {esign_data.get('auto_sent', False)}")
    
    # Step 4: Sign the document
    print(f"\n✍️  Step 4: Sign the document (ID: {esign_id})")
    
    sign_request = {
        "signature_text": "System Administrator",
        "ip_address": "127.0.0.1",
        "user_agent": "TestScript/1.0"
    }
    
    sign_response = requests.post(f"{BASE_URL}/esignature/{esign_id}/sign", 
                                 json=sign_request, headers=headers)
    
    if sign_response.status_code != 200:
        print(f"❌ Signing failed: {sign_response.status_code}")
        print(f"Response: {sign_response.text}")
        return False
    
    sign_data = sign_response.json()
    print(f"✅ Document signed successfully!")
    print(f"✅ Message: {sign_data['message']}")
    print(f"✅ Signed by: {sign_data['signed_by']} ({sign_data['signed_by_role']})")
    print(f"✅ Document status: {sign_data['document_status']}")
    print(f"✅ Progress: {sign_data['progress']}")
    
    # Step 5: Check final status
    print(f"\n📊 Step 5: Check final document status")
    
    status_response = requests.get(f"{BASE_URL}/esignature/{esign_id}/status", headers=headers)
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"✅ Final status: {status_data['status']}")
        print(f"✅ Recipients:")
        for recipient in status_data['recipients']:
            print(f"   - {recipient['full_name']} ({recipient['email']}): {'✅ Signed' if recipient['is_signed'] else '⏳ Pending'}")
    else:
        print(f"⚠️  Could not check final status: {status_response.status_code}")
    
    # Step 6: List all e-signature requests
    print(f"\n📋 Step 6: List all e-signature requests")
    
    list_response = requests.get(f"{BASE_URL}/esignature/list", headers=headers)
    
    if list_response.status_code == 200:
        requests_data = list_response.json()
        print(f"✅ Total e-signature requests: {len(requests_data)}")
        for req in requests_data:
            print(f"   - {req['title']} ({req['id']}): {req['status']}")
    else:
        print(f"⚠️  Could not list requests: {list_response.status_code}")
    
    print(f"\n🎉 E-signature signing test completed successfully!")
    return True

if __name__ == "__main__":
    print("🧪 Starting E-signature Signing Test...")
    success = test_esignature_signing()
    
    if success:
        print("\n✅ All tests passed! System admin can now sign documents.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        sys.exit(1) 