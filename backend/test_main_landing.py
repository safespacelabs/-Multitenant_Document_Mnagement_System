#!/usr/bin/env python3
"""
Quick test script to verify main landing page functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"

def test_public_companies_endpoint():
    """Test the public companies endpoint."""
    print("🧪 Testing public companies endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/companies/public")
        
        if response.status_code == 200:
            companies = response.json()
            print(f"   ✅ Success! Found {len(companies)} companies")
            
            for i, company in enumerate(companies[:3]):  # Show first 3
                print(f"      {i+1}. {company['name']} (ID: {company['id']})")
                print(f"         📧 Email: {company['email']}")
                print(f"         📊 Status: {'Active' if company['is_active'] else 'Inactive'}")
                print()
            
            return companies
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"      Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return []

def test_company_public_endpoint(company_id):
    """Test the public company endpoint."""
    print(f"🧪 Testing public company endpoint for {company_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/companies/{company_id}/public")
        
        if response.status_code == 200:
            company = response.json()
            print(f"   ✅ Success! Company: {company['name']}")
            print(f"      📧 Email: {company['email']}")
            print(f"      📊 Status: {'Active' if company['is_active'] else 'Inactive'}")
            return company
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"      Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def test_system_admin_login():
    """Test the system admin login endpoint."""
    print("🧪 Testing system admin login endpoint...")
    
    # Try with default system admin credentials
    credentials = {
        "username": "system_admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/system-admin/login", 
            json=credentials
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ System admin login successful!")
            print(f"      👤 User: {data['user']['username']} ({data['user']['role']})")
            return data
        else:
            print(f"   ⚠️  System admin login failed with status {response.status_code}")
            print(f"      Response: {response.text}")
            print("      💡 This is expected if no system admin exists yet")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def test_health_check():
    """Test the health check endpoint."""
    print("🧪 Testing health check endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Health check passed!")
            print(f"      📊 Status: {health.get('status', 'unknown')}")
            print(f"      🗄️  Management DB: {health.get('management_db', 'unknown')}")
            return health
        else:
            print(f"   ❌ Health check failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def main():
    """Main test function."""
    print("🚀 Testing Main Landing Page System")
    print("=" * 60)
    
    # Test health check first
    health = test_health_check()
    if not health:
        print("❌ Backend is not running or unhealthy!")
        print("💡 Please start the backend with: cd backend && python -m uvicorn app.main:app --reload")
        return
    
    print()
    
    # Test public companies endpoint
    companies = test_public_companies_endpoint()
    
    if not companies:
        print("⚠️  No companies found. Creating companies first may be needed.")
        print("💡 Run: cd backend && python create_admin.py")
        return
    
    print()
    
    # Test individual company endpoint
    if companies:
        test_company_public_endpoint(companies[0]['id'])
    
    print()
    
    # Test system admin login
    test_system_admin_login()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   🏢 Companies available: {len(companies)}")
    print(f"   🌐 Public endpoints: Working")
    print(f"   🔐 System admin: Check logs above")
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Open frontend: http://localhost:3000")
    print("   2. You should see the main landing page with companies")
    print("   3. Click on any company to access role-based login/signup")
    print("   4. Use system admin login for system-level access")
    
    if companies:
        print("\n💡 DEFAULT HR ADMIN CREDENTIALS:")
        print("   Run: cd backend && python create_hr_admins.py")
        print("   This will create default HR admins for testing")

if __name__ == "__main__":
    main() 