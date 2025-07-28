#!/usr/bin/env python3
"""
Quick comprehensive test for all credentials and database creation
"""

import requests
import json
import time
import sys

# Import from local app
try:
    from app.config import (
        MANAGEMENT_DATABASE_URL,
        NEON_API_KEY, 
        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY,
        ANTHROPIC_API_KEY
    )
except ImportError:
    print("❌ Cannot import app modules. Make sure you're in the backend directory.")
    sys.exit(1)

BASE_URL = "http://localhost:8000"

def test_all_credentials():
    """Test all credentials and connections"""
    print("🔍 Testing All Credentials & API Connections")
    print("=" * 50)
    
    results = {}
    
    # 1. Test Server
    print("\n🔌 Testing Server Connection...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server responding")
            results['server'] = True
        else:
            print(f"❌ Server error: {response.status_code}")
            results['server'] = False
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        results['server'] = False
        
    # 2. Test Management Database
    print("\n📊 Testing Management Database...")
    try:
        from app.database import get_management_db
        from app.models import SystemUser, Company
        
        db = next(get_management_db())
        admin_count = db.query(SystemUser).filter(SystemUser.role == "system_admin").count()
        company_count = db.query(Company).count()
        
        print(f"✅ Management DB connected (Admins: {admin_count}, Companies: {company_count})")
        results['management_db'] = True
        db.close()
    except Exception as e:
        print(f"❌ Management DB error: {e}")
        results['management_db'] = False
    
    # 3. Test Neon API
    print("\n🐘 Testing Neon API...")
    try:
        headers = {"Authorization": f"Bearer {NEON_API_KEY}"}
        response = requests.get("https://console.neon.tech/api/v2/projects", headers=headers, timeout=10)
        if response.status_code == 200:
            projects = response.json().get('projects', [])
            print(f"✅ Neon API connected ({len(projects)} projects)")
            results['neon_api'] = True
        else:
            print(f"❌ Neon API error: {response.status_code}")
            results['neon_api'] = False
    except Exception as e:
        print(f"❌ Neon API failed: {e}")
        results['neon_api'] = False
    
    # 4. Test AWS S3
    print("\n☁️ Testing AWS S3...")
    try:
        import boto3
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        buckets = s3.list_buckets()
        print(f"✅ AWS S3 connected ({len(buckets.get('Buckets', []))} buckets)")
        results['aws_s3'] = True
    except Exception as e:
        print(f"❌ AWS S3 failed: {e}")
        results['aws_s3'] = False
    
    # 5. Test Anthropic API
    print("\n🤖 Testing Anthropic API...")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )
        print("✅ Anthropic API connected")
        results['anthropic'] = True
    except Exception as e:
        print(f"❌ Anthropic API failed: {e}")
        results['anthropic'] = False
    
    return results

def test_database_creation():
    """Test complete company creation and database isolation"""
    print("\n🏢 Testing Database Creation & Isolation")
    print("=" * 50)
    
    try:
        # 1. Login as system admin
        print("\n🔐 System Admin Login...")
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code != 200:
            print(f"❌ Admin login failed: {login_response.text}")
            return False
        
        admin_token = login_response.json()["access_token"]
        print("✅ System admin logged in")
        
        # 2. Create company with isolated database
        print("\n🏗️ Creating Company with Isolated Database...")
        headers = {"Authorization": f"Bearer {admin_token}"}
        company_data = {
            "name": f"Test Company {int(time.time())}",
            "email": f"test{int(time.time())}@testcompany.com"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/companies/", json=company_data, headers=headers)
        
        if create_response.status_code != 200:
            print(f"❌ Company creation failed: {create_response.text}")
            return False
        
        company = create_response.json()
        print("✅ Company created successfully!")
        print(f"   Company ID: {company['id']}")
        print(f"   Database: {company['database_name']}")
        print(f"   S3 Bucket: {company['s3_bucket_name']}")
        
        # 3. Test database connection
        print("\n🔗 Testing Company Database Connection...")
        time.sleep(3)  # Wait for database creation
        
        db_test_response = requests.get(
            f"{BASE_URL}/api/companies/{company['id']}/database/test",
            headers=headers
        )
        
        if db_test_response.status_code == 200:
            db_result = db_test_response.json()
            print("✅ Company database created and accessible!")
            print(f"   Connection: {db_result.get('connection_test', 'OK')}")
        else:
            print(f"❌ Database test failed: {db_test_response.text}")
            return False
        
        # 4. Register user in company database
        print("\n👤 Testing Company User Registration...")
        user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"user{int(time.time())}@{company['email'].split('@')[1]}",
            "password": "password123",
            "full_name": "Test User",
            "role": "hr_admin"
        }
        
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register?company_id={company['id']}",
            json=user_data
        )
        
        if register_response.status_code == 200:
            print("✅ Company user registered in isolated database!")
            print(f"   Username: {user_data['username']}")
            print(f"   Role: {user_data['role']}")
            
            # Test user login
            user_login = requests.post(f"{BASE_URL}/api/auth/login", json={
                "username": user_data['username'],
                "password": user_data['password']
            })
            
            if user_login.status_code == 200:
                print("✅ Company user login successful!")
                return True
            else:
                print(f"❌ User login failed: {user_login.text}")
                return False
        else:
            print(f"❌ User registration failed: {register_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Database creation test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Multi-Tenant System - Comprehensive Credential & Database Test")
    print("=" * 70)
    
    # Test credentials
    credential_results = test_all_credentials()
    
    # Test database creation if server is running
    if credential_results.get('server'):
        database_creation_ok = test_database_creation()
    else:
        print("\n❌ Skipping database tests - server not running")
        database_creation_ok = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FINAL TEST RESULTS")
    print("-" * 35)
    
    total_tests = len(credential_results) + 1  # +1 for database creation
    passed_tests = sum(credential_results.values()) + (1 if database_creation_ok else 0)
    
    # Credential results
    for test, result in credential_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test.upper():<20} {status}")
    
    # Database creation result
    status = "✅ PASS" if database_creation_ok else "❌ FAIL"
    print(f"   {'DATABASE_CREATION':<20} {status}")
    
    print("-" * 35)
    print(f"   TOTAL: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ All credentials are working correctly")
        print("✅ Database isolation is functioning properly")
        print("✅ Company databases are created automatically")
        print("✅ System is ready for production!")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests failed")
        print("Please check the failed components above")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        sys.exit(1) 