#!/usr/bin/env python3
"""
Comprehensive test script to check all authentication and database issues
"""

import requests
import json
from app.database import get_management_db
from app.models import Company
from app.models_company import User
from app.services.database_manager import db_manager
from app.auth import verify_password, get_password_hash

def test_database_connections():
    """Test all database connections"""
    print("🔍 Testing Database Connections")
    print("=" * 50)
    
    try:
        # Test management database
        db = next(get_management_db())
        companies = db.query(Company).all()
        print(f"✅ Management database: {len(companies)} companies found")
        
        for company in companies:
            print(f"\n🏢 Testing {company.name}...")
            
            # Test company database connection
            try:
                company_db_gen = db_manager.get_company_db(company.id, company.database_url)
                company_db = next(company_db_gen)
                
                # Test user query
                users = company_db.query(User).all()
                print(f"  ✅ Company database: {len(users)} users found")
                
                # Test HR admin
                hr_admin = company_db.query(User).filter(User.role == "hr_admin").first()
                if hr_admin:
                    print(f"  ✅ HR Admin: {hr_admin.username} (Active: {hr_admin.is_active})")
                    
                    # Test password verification
                    test_password = f"hr_{company.name.lower()}123"
                    is_valid = verify_password(test_password, hr_admin.hashed_password)
                    print(f"  🔐 Password verification: {is_valid}")
                    
                    if not is_valid:
                        print(f"  🔄 Updating password hash...")
                        new_hash = get_password_hash(test_password)
                        hr_admin.hashed_password = new_hash
                        company_db.commit()
                        print(f"  ✅ Password hash updated")
                else:
                    print(f"  ❌ No HR admin found")
                
                company_db.close()
                
            except Exception as e:
                print(f"  ❌ Company database error: {str(e)}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Management database error: {str(e)}")

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)
    
    # Test login for Amazon HR admin
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
            
            # Test document endpoints
            headers = {"Authorization": f"Bearer {token}"}
            
            print("\n📄 Testing document endpoints...")
            
            # Test folders endpoint
            folders_response = requests.get("http://localhost:8000/api/documents/folders", headers=headers)
            print(f"Folders Status: {folders_response.status_code}")
            if folders_response.status_code == 200:
                print("✅ Folders endpoint working!")
            else:
                print(f"❌ Folders endpoint failed: {folders_response.text}")
            
            # Test documents list endpoint
            docs_response = requests.get("http://localhost:8000/api/documents/", headers=headers)
            print(f"Documents Status: {docs_response.status_code}")
            if docs_response.status_code == 200:
                print("✅ Documents endpoint working!")
            else:
                print(f"❌ Documents endpoint failed: {docs_response.text}")
            
            # Test users endpoint
            users_response = requests.get("http://localhost:8000/api/users/", headers=headers)
            print(f"Users Status: {users_response.status_code}")
            if users_response.status_code == 200:
                print("✅ Users endpoint working!")
            else:
                print(f"❌ Users endpoint failed: {users_response.text}")
                
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ API test error: {str(e)}")

def main():
    """Main function"""
    print("🚀 Comprehensive System Test")
    print("=" * 50)
    
    # Test database connections
    test_database_connections()
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("✅ Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    main() 