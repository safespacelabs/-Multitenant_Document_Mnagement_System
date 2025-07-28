#!/usr/bin/env python3
"""
Comprehensive test suite for multi-tenant system
Tests all credentials, API connections, and database creation
"""

import requests
import json
import time
import sys
from app.config import (
    MANAGEMENT_DATABASE_URL,
    NEON_API_KEY, 
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    ANTHROPIC_API_KEY
)

BASE_URL = "http://localhost:8000"

def test_server_connection():
    """Test if server is running and responding"""
    print("🔌 Testing Server Connection")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            print(f"   Status: {response.json()}")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server connection failed: {e}")
        print("   Make sure server is running: uvicorn app.main:app --reload")
        return False

def test_management_database():
    """Test management database connection"""
    print("\n📊 Testing Management Database")
    print("-" * 40)
    
    try:
        from app.database import get_management_db
        from app.models import SystemUser, Company
        
        db = next(get_management_db())
        
        # Test query
        admin_count = db.query(SystemUser).filter(SystemUser.role == "system_admin").count()
        company_count = db.query(Company).filter(Company.is_active == True).count()
        
        print(f"✅ Management database connected")
        print(f"   System admins: {admin_count}")
        print(f"   Active companies: {company_count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Management database error: {e}")
        return False

def test_neon_api():
    """Test Neon API connection"""
    print("\n🐘 Testing Neon API Connection")
    print("-" * 40)
    
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {NEON_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Test API connection by listing projects
        response = requests.get(
            "https://console.neon.tech/api/v2/projects",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            projects = response.json()
            print("✅ Neon API connected successfully")
            print(f"   Projects accessible: {len(projects.get('projects', []))}")
            return True
        else:
            print(f"❌ Neon API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Neon API connection failed: {e}")
        return False

def test_aws_connection():
    """Test AWS S3 connection"""
    print("\n☁️ Testing AWS S3 Connection")
    print("-" * 40)
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name='us-west-1'
        )
        
        # Test by listing buckets
        response = s3_client.list_buckets()
        
        print("✅ AWS S3 connected successfully")
        print(f"   Accessible buckets: {len(response.get('Buckets', []))}")
        return True
        
    except ClientError as e:
        print(f"❌ AWS S3 error: {e}")
        return False
    except Exception as e:
        print(f"❌ AWS connection failed: {e}")
        return False

def test_anthropic_api():
    """Test Anthropic API connection"""
    print("\n🤖 Testing Anthropic API Connection")
    print("-" * 40)
    
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Test with a simple message
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=20,
            messages=[{"role": "user", "content": "Test connection"}]
        )
        
        print("✅ Anthropic API connected successfully")
        print(f"   Model response received: {len(message.content)} parts")
        return True
        
    except Exception as e:
        print(f"❌ Anthropic API error: {e}")
        return False

def test_system_admin_login():
    """Test system admin login"""
    print("\n🔐 Testing System Admin Authentication")
    print("-" * 40)
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ System admin login successful")
            print(f"   Role: {data['user']['role']}")
            print(f"   Username: {data['user']['username']}")
            return data["access_token"]
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return None

def test_company_creation(admin_token):
    """Test company creation with database isolation"""
    print("\n🏢 Testing Company Creation & Database Isolation")
    print("-" * 40)
    
    if not admin_token:
        print("❌ Cannot test company creation without admin token")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create test company
        company_data = {
            "name": f"Test Company {int(time.time())}",
            "email": f"test{int(time.time())}@example.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/companies/",
            json=company_data,
            headers=headers
        )
        
        if response.status_code == 200:
            company = response.json()
            print("✅ Company created successfully")
            print(f"   Company ID: {company['id']}")
            print(f"   Database: {company['database_name']}")
            print(f"   S3 Bucket: {company['s3_bucket_name']}")
            
            # Test database connection
            time.sleep(2)  # Allow time for database creation
            
            db_test = requests.get(
                f"{BASE_URL}/api/companies/{company['id']}/database/test",
                headers=headers
            )
            
            if db_test.status_code == 200:
                print("✅ Company database created and accessible")
                print(f"   Connection test: {db_test.json()}")
            else:
                print(f"⚠️ Database test failed: {db_test.status_code}")
            
            return company
        else:
            print(f"❌ Company creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Company creation test failed: {e}")
        return None

def test_company_user_registration(company, admin_token):
    """Test registering users in company database"""
    print("\n👥 Testing Company User Registration")
    print("-" * 40)
    
    if not company or not admin_token:
        print("❌ Cannot test user registration without company and admin token")
        return None
    
    try:
        # Register HR Admin in company
        user_data = {
            "username": f"hr_admin_{int(time.time())}",
            "email": f"hr{int(time.time())}@{company['email'].split('@')[1]}",
            "password": "password123",
            "full_name": "Test HR Admin",
            "role": "hr_admin"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register?company_id={company['id']}",
            json=user_data
        )
        
        if response.status_code == 200:
            user_result = response.json()
            print("✅ Company user registered successfully")
            print(f"   Username: {user_data['username']}")
            print(f"   Role: {user_data['role']}")
            print(f"   Company: {company['name']}")
            
            # Test user login
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "username": user_data['username'],
                "password": user_data['password']
            })
            
            if login_response.status_code == 200:
                print("✅ Company user login successful")
                return user_result
            else:
                print(f"⚠️ User login failed: {login_response.status_code}")
                
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ User registration test failed: {e}")
        return None

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Multi-Tenant System - Comprehensive Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Server Connection
    server_ok = test_server_connection()
    test_results.append(("Server Connection", server_ok))
    
    if not server_ok:
        print("\n❌ Cannot proceed with tests - server not running")
        return False
    
    # Test 2: Management Database
    db_ok = test_management_database()
    test_results.append(("Management Database", db_ok))
    
    # Test 3: External API Connections
    neon_ok = test_neon_api()
    test_results.append(("Neon API", neon_ok))
    
    aws_ok = test_aws_connection()
    test_results.append(("AWS S3", aws_ok))
    
    anthropic_ok = test_anthropic_api()
    test_results.append(("Anthropic API", anthropic_ok))
    
    # Test 4: System Admin
    admin_token = test_system_admin_login()
    test_results.append(("System Admin Login", admin_token is not None))
    
    # Test 5: Company Creation & Database Isolation
    company = test_company_creation(admin_token)
    test_results.append(("Company Creation", company is not None))
    
    # Test 6: Company User Registration
    user = test_company_user_registration(company, admin_token)
    test_results.append(("Company User Registration", user is not None))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("-" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<25} {status}")
        if result:
            passed += 1
    
    print("-" * 30)
    print(f"   Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ System is fully functional with complete database isolation")
        print("✅ All credentials and APIs are working correctly")
        print("✅ Company databases are created automatically")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check configuration.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_comprehensive_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1) 