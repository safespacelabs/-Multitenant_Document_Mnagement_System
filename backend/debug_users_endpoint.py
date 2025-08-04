#!/usr/bin/env python3
"""
Debug script to test the users endpoint specifically
"""

import requests
import json

def debug_users_endpoint():
    """Debug the users endpoint"""
    
    # Test login first
    login_data = {
        "username": "Hradmin1_amazon",
        "password": "hr_amazon123"
    }
    
    try:
        print("🔐 Testing login...")
        response = requests.post("http://localhost:8000/api/auth/login", json=login_data)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ Login successful! Token: {token[:50]}...")
            
            # Test users endpoint with detailed error handling
            headers = {"Authorization": f"Bearer {token}"}
            
            print("\n🔍 Testing users endpoint...")
            users_response = requests.get("http://localhost:8000/api/users/", headers=headers)
            print(f"Users Status: {users_response.status_code}")
            print(f"Users Response Headers: {dict(users_response.headers)}")
            
            if users_response.status_code == 200:
                print("✅ Users endpoint working!")
                users_data = users_response.json()
                print(f"Found {len(users_data)} users")
            else:
                print(f"❌ Users endpoint failed!")
                print(f"Response text: {users_response.text}")
                
                # Try to parse error details
                try:
                    error_data = users_response.json()
                    print(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print("Could not parse error response as JSON")
                    
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    debug_users_endpoint() 