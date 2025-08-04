#!/usr/bin/env python3
"""
Test script to verify login functionality
"""

import requests
import json

def test_login():
    """Test login for Amazon HR admin"""
    
    # Test data
    login_data = {
        "username": "Hradmin1_amazon",
        "password": "hr_amazon123"
    }
    
    # API endpoint
    url = "http://localhost:8000/api/auth/login"
    
    try:
        print("🔐 Testing login for Amazon HR admin...")
        print(f"Username: {login_data['username']}")
        print(f"Password: {login_data['password']}")
        print()
        
        # Make login request
        response = requests.post(url, json=login_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"Token: {data.get('access_token', 'No token')[:50]}...")
            print(f"User: {data.get('user', {}).get('username', 'No user')}")
            print(f"Role: {data.get('user', {}).get('role', 'No role')}")
            print(f"Company ID: {data.get('user', {}).get('company_id', 'No company')}")
            
            # Test accessing documents endpoint
            token = data.get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            
            print("\n🔍 Testing document access...")
            doc_response = requests.get("http://localhost:8000/api/documents/", headers=headers)
            print(f"Documents Status: {doc_response.status_code}")
            
            if doc_response.status_code == 200:
                print("✅ Document access successful!")
            else:
                print(f"❌ Document access failed: {doc_response.text}")
                
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_login() 