#!/usr/bin/env python3
"""
Demo script showing how the multi-tenant system works
with the same user/admin logic as before
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def demo_system():
    print("🚀 Multi-Tenant Document Management Demo")
    print("=" * 50)
    
    # 1. System Admin Login
    print("\n1️⃣ System Admin Login")
    print("-" * 30)
    
    admin_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if admin_login.status_code == 200:
        admin_token = admin_login.json()["access_token"]
        print("✅ System admin logged in successfully")
        print(f"   Role: {admin_login.json()['user']['role']}")
    else:
        print("❌ System admin login failed")
        print("   Make sure you've run: python create_admin.py")
        return
    
    # 2. Create Company (with isolated database)
    print("\n2️⃣ Create Company with Isolated Database")
    print("-" * 30)
    
    company_data = {
        "name": "Acme Corporation", 
        "email": "admin@acme.com"
    }
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_company = requests.post(
        f"{BASE_URL}/api/companies/", 
        json=company_data,
        headers=headers
    )
    
    if create_company.status_code == 200:
        company = create_company.json()
        company_id = company["id"]
        print("✅ Company created with isolated database")
        print(f"   Company ID: {company_id}")
        print(f"   Database: {company['database_name']}")
        print(f"   S3 Bucket: {company['s3_bucket_name']}")
    else:
        print("❌ Company creation failed")
        print(f"   Error: {create_company.text}")
        return
    
    # 3. Test Company Database
    print("\n3️⃣ Test Company Database Connection")
    print("-" * 30)
    
    test_db = requests.get(
        f"{BASE_URL}/api/companies/{company_id}/database/test",
        headers=headers
    )
    
    if test_db.status_code == 200:
        result = test_db.json()
        print(f"✅ Company database test: {result['connection_test']}")
    else:
        print("❌ Database test failed")
    
    # 4. Register Company User (HR Admin)
    print("\n4️⃣ Register HR Admin (Same Logic as Before)")
    print("-" * 30)
    
    hr_admin_data = {
        "username": "hr_admin",
        "email": "hr@acme.com", 
        "password": "password123",
        "full_name": "HR Administrator",
        "role": "hr_admin"
    }
    
    register_hr = requests.post(
        f"{BASE_URL}/api/auth/register?company_id={company_id}",
        json=hr_admin_data
    )
    
    if register_hr.status_code == 200:
        hr_token = register_hr.json()["access_token"]
        print("✅ HR Admin registered in company database")
        print(f"   Username: {hr_admin_data['username']}")
        print(f"   Role: {hr_admin_data['role']}")
    else:
        print("❌ HR Admin registration failed")
        print(f"   Error: {register_hr.text}")
        return
    
    # 5. HR Admin Invites Employee (Same Process as Before)
    print("\n5️⃣ HR Admin Invites Employee (Same as Before)")
    print("-" * 30)
    
    hr_headers = {"Authorization": f"Bearer {hr_token}"}
    invite_data = {
        "email": "employee@acme.com",
        "full_name": "John Employee", 
        "role": "employee"
    }
    
    invite_employee = requests.post(
        f"{BASE_URL}/api/user-management/invite",
        json=invite_data,
        headers=hr_headers
    )
    
    if invite_employee.status_code == 200:
        invitation = invite_employee.json()
        print("✅ Employee invitation sent")
        print(f"   Email: {invite_data['email']}")
        print(f"   Role: {invite_data['role']} (same hierarchy as before)")
        print(f"   Unique ID: {invitation['unique_id']}")
    else:
        print("❌ Employee invitation failed")
        print(f"   Error: {invite_employee.text}")
    
    # 6. Check System Status
    print("\n6️⃣ System Status")
    print("-" * 30)
    
    status = requests.get(f"{BASE_URL}/api/system/status")
    if status.status_code == 200:
        data = status.json()
        print("✅ System Status:")
        print(f"   Companies: {data['companies_registered']}")
        print(f"   System Users: {data['system_users']}")
        print(f"   Active DB Connections: {data['company_database_connections']}")
    
    print("\n" + "=" * 50)
    print("✅ Demo Complete!")
    print("\nKey Points:")
    print("• Same user roles: hr_admin, hr_manager, employee, customer")
    print("• Same invitation system with unique IDs")
    print("• Same permission hierarchy") 
    print("• Same API endpoints")
    print("• Added: True database isolation per company")
    print("• Added: Company-specific S3 buckets")
    print("• Added: System admin capabilities")

if __name__ == "__main__":
    try:
        demo_system()
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}") 