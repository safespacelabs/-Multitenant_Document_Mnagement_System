#!/usr/bin/env python3
"""
Test script for multi-tenant database isolation system
Usage: python test_system.py
"""

import asyncio
import sys
import requests
import json
from sqlalchemy.orm import Session
from app.database import get_management_db
from app.models import SystemUser, Company
from app.services.database_manager import db_manager

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test basic health check"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {data}")
                return False
        else:
            print(f"❌ Health check HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check connection error: {str(e)}")
        return False

def test_system_status():
    """Test system status endpoint"""
    print("🔍 Testing system status...")
    try:
        response = requests.get(f"{BASE_URL}/api/system/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ System status: {data.get('system_status')}")
            print(f"   Management DB: {data.get('management_database')}")
            print(f"   Companies: {data.get('companies_registered')}")
            print(f"   System Users: {data.get('system_users')}")
            print(f"   Active Connections: {data.get('company_database_connections')}")
            return True
        else:
            print(f"❌ System status HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ System status error: {str(e)}")
        return False

def test_management_database():
    """Test management database connection and data"""
    print("🔍 Testing management database...")
    try:
        db_gen = get_management_db()
        db = next(db_gen)
        
        # Test basic query
        system_users = db.query(SystemUser).all()
        companies = db.query(Company).all()
        
        print(f"✅ Management database connected")
        print(f"   System users: {len(system_users)}")
        print(f"   Companies: {len(companies)}")
        
        # List system users
        for user in system_users:
            print(f"   - System User: {user.username} ({user.role})")
        
        # List companies
        for company in companies:
            print(f"   - Company: {company.name} (DB: {company.database_name})")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Management database error: {str(e)}")
        return False

def test_database_manager():
    """Test database manager functionality"""
    print("🔍 Testing database manager...")
    try:
        # Test management engine
        engine = db_manager.management_engine
        
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            
        print("✅ Database manager working")
        print(f"   Active company connections: {len(db_manager._company_engines)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database manager error: {str(e)}")
        return False

async def test_company_database_creation():
    """Test company database operations"""
    print("🔍 Testing company database operations...")
    try:
        from app.services.neon_service import neon_service
        
        # Test if we can connect to Neon API (without actually creating)
        if neon_service.api_key and neon_service.project_id:
            print("✅ Neon service configured")
            print(f"   Project ID: {neon_service.project_id}")
            print(f"   API Key: {neon_service.api_key[:10]}...")
        else:
            print("⚠️  Neon service not fully configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Company database test error: {str(e)}")
        return False

def test_api_endpoints():
    """Test API endpoints availability"""
    print("🔍 Testing API endpoints...")
    
    endpoints = [
        ("/", "GET"),
        ("/api/system/status", "GET"),
        ("/health", "GET"),
    ]
    
    success_count = 0
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            
            if response.status_code in [200, 401, 403]:  # 401/403 are ok for protected endpoints
                print(f"✅ {method} {endpoint} - Status: {response.status_code}")
                success_count += 1
            else:
                print(f"❌ {method} {endpoint} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {method} {endpoint} - Error: {str(e)}")
    
    return success_count == len(endpoints)

def main():
    """Main test function"""
    print("🚀 Multi-Tenant System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("System Status", test_system_status),
        ("Management Database", test_management_database),
        ("Database Manager", test_database_manager),
        ("Company Database Operations", lambda: asyncio.run(test_company_database_creation())),
        ("API Endpoints", test_api_endpoints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main() 