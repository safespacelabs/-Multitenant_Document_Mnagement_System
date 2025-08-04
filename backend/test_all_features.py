#!/usr/bin/env python3
"""
Comprehensive test script to verify all features work for all companies and roles
"""

import requests
import json

def test_all_features():
    """Test all features for all companies and roles"""
    
    print("🚀 Comprehensive Feature Test for All Companies and Roles")
    print("=" * 60)
    
    # Test known working credentials
    test_cases = [
        {
            "company": "Amazon",
            "username": "Hradmin1_amazon",
            "password": "hr_amazon123",
            "role": "hr_admin"
        },
        {
            "company": "SafespaceLabs", 
            "username": "hr_admin_safespacelabs",
            "password": "hr_safespacelabs123",
            "role": "hr_admin"
        },
        {
            "company": "Microsoft",
            "username": "hr_admin_microsoft", 
            "password": "hr_microsoft123",
            "role": "hr_admin"
        },
        {
            "company": "FIFA",
            "username": "hr_admin_fifa",
            "password": "hr_fifa123", 
            "role": "hr_admin"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🏢 Testing Company: {test_case['company']}")
        print("-" * 40)
        
        # Test login
        token = test_user_login(test_case)
        if token:
            # Test all features
            test_document_management(token, test_case)
            test_esignature_functionality(token, test_case)
            test_user_management(token, test_case)
            test_chatbot_functionality(token, test_case)

def test_user_login(test_case):
    """Test user login functionality"""
    try:
        login_data = {
            "username": test_case["username"],
            "password": test_case["password"]
        }
        
        response = requests.post("http://localhost:8000/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"  ✅ Login successful for {test_case['username']}")
            return token
        else:
            print(f"  ❌ Login failed for {test_case['username']}: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"  ❌ Login test error: {str(e)}")
        return None

def test_document_management(token, test_case):
    """Test document management functionality"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test document list
        response = requests.get("http://localhost:8000/api/documents/", headers=headers)
        if response.status_code == 200:
            print(f"    ✅ Document list working")
        else:
            print(f"    ❌ Document list failed: {response.status_code}")
        
        # Test folders
        response = requests.get("http://localhost:8000/api/documents/folders", headers=headers)
        if response.status_code == 200:
            print(f"    ✅ Folders working")
        else:
            print(f"    ❌ Folders failed: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ Document management test error: {str(e)}")

def test_esignature_functionality(token, test_case):
    """Test e-signature functionality"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test e-signature list
        response = requests.get("http://localhost:8000/api/esignature/list", headers=headers)
        if response.status_code == 200:
            print(f"    ✅ E-signature list working")
        else:
            print(f"    ❌ E-signature list failed: {response.status_code}")
        
        # Test e-signature permissions
        response = requests.get("http://localhost:8000/api/esignature/permissions/my-role", headers=headers)
        if response.status_code == 200:
            permissions = response.json()
            print(f"    ✅ E-signature permissions working - {len(permissions)} permissions")
        else:
            print(f"    ❌ E-signature permissions failed: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ E-signature test error: {str(e)}")

def test_user_management(token, test_case):
    """Test user management functionality"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test user list
        response = requests.get("http://localhost:8000/api/users/", headers=headers)
        if response.status_code == 200:
            users = response.json()
            print(f"    ✅ User management working - {len(users)} users")
        else:
            print(f"    ❌ User management failed: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ User management test error: {str(e)}")

def test_chatbot_functionality(token, test_case):
    """Test chatbot functionality"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test chatbot
        chat_data = {"question": "Hello, how are you?"}
        response = requests.post("http://localhost:8000/api/chat", json=chat_data, headers=headers)
        if response.status_code == 200:
            print(f"    ✅ Chatbot working")
        else:
            print(f"    ❌ Chatbot failed: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ Chatbot test error: {str(e)}")

def test_system_admin_features():
    """Test system admin specific features"""
    print(f"\n👑 Testing System Admin Features")
    print("-" * 40)
    
    try:
        # Test system admin login
        login_data = {
            "username": "system_admin_admin2",
            "password": "admin123"
        }
        
        response = requests.post("http://localhost:8000/api/auth/system-admin/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"  ✅ System admin login successful")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test system documents
            response = requests.get("http://localhost:8000/api/documents/system/", headers=headers)
            if response.status_code == 200:
                print(f"  ✅ System documents working")
            else:
                print(f"  ❌ System documents failed: {response.status_code}")
            
            # Test system chatbot
            chat_data = {"question": "System admin test"}
            response = requests.post("http://localhost:8000/api/chat/system", json=chat_data, headers=headers)
            if response.status_code == 200:
                print(f"  ✅ System chatbot working")
            else:
                print(f"  ❌ System chatbot failed: {response.status_code}")
                
        else:
            print(f"  ❌ System admin login failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ System admin test error: {str(e)}")

if __name__ == "__main__":
    print("🔍 Starting comprehensive feature test...")
    
    # Test all company features
    test_all_features()
    
    # Test system admin features
    test_system_admin_features()
    
    print("\n" + "=" * 60)
    print("✅ Comprehensive Feature Test Complete!")
    print("=" * 60) 