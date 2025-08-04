#!/usr/bin/env python3
"""
Test script to simulate frontend authentication flow
"""

import requests
import json

def test_frontend_auth_flow():
    """Test the complete frontend authentication flow"""
    
    # Test login
    login_data = {
        "username": "Hradmin1_amazon",
        "password": "hr_amazon123"
    }
    
    try:
        print("🔐 Step 1: Testing login...")
        response = requests.post("http://localhost:8000/api/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            user_data = data.get('user', {})
            company_data = data.get('company', {})
            
            print(f"✅ Login successful!")
            print(f"Token: {token[:50]}...")
            print(f"User: {user_data.get('username')}")
            print(f"Role: {user_data.get('role')}")
            print(f"Company ID: {user_data.get('company_id')}")
            print(f"Company Name: {company_data.get('name')}")
            
            # Test endpoints that the frontend would call
            headers = {"Authorization": f"Bearer {token}"}
            
            print("\n🔍 Step 2: Testing frontend endpoints...")
            
            # Test documents endpoint (what frontend calls)
            print("Testing /api/documents/...")
            docs_response = requests.get("http://localhost:8000/api/documents/", headers=headers)
            print(f"Documents Status: {docs_response.status_code}")
            if docs_response.status_code != 200:
                print(f"Documents Error: {docs_response.text}")
            
            # Test users endpoint (what frontend calls)
            print("Testing /api/users/...")
            users_response = requests.get("http://localhost:8000/api/users/", headers=headers)
            print(f"Users Status: {users_response.status_code}")
            if users_response.status_code != 200:
                print(f"Users Error: {users_response.text}")
            
            # Test folders endpoint
            print("Testing /api/documents/folders...")
            folders_response = requests.get("http://localhost:8000/api/documents/folders", headers=headers)
            print(f"Folders Status: {folders_response.status_code}")
            if folders_response.status_code != 200:
                print(f"Folders Error: {folders_response.text}")
                
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_frontend_auth_flow() 