#!/usr/bin/env python3
"""
Simple test script to verify backend functionality
"""
import requests
import json

# Backend URL
BACKEND_URL = "https://multitenant-backend-mlap.onrender.com"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_cors():
    """Test the CORS endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/test-cors")
        print(f"✅ CORS test: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def test_categories_no_auth():
    """Test categories endpoint without authentication"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/documents/categories")
        print(f"✅ Categories (no auth): {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 401  # Should return 401 for no auth
    except Exception as e:
        print(f"❌ Categories test failed: {e}")
        return False

def test_enhanced_no_auth():
    """Test enhanced endpoint without authentication"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/documents/enhanced")
        print(f"✅ Enhanced (no auth): {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 401  # Should return 401 for no auth
    except Exception as e:
        print(f"❌ Enhanced test failed: {e}")
        return False

def test_options_categories():
    """Test OPTIONS request for categories"""
    try:
        response = requests.options(f"{BACKEND_URL}/api/documents/categories")
        print(f"✅ Categories OPTIONS: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Categories OPTIONS failed: {e}")
        return False

def test_options_enhanced():
    """Test OPTIONS request for enhanced"""
    try:
        response = requests.options(f"{BACKEND_URL}/api/documents/enhanced")
        print(f"✅ Enhanced OPTIONS: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Enhanced OPTIONS failed: {e}")
        return False

def test_test_categories():
    """Test the test categories endpoint (no auth required)"""
    try:
        response = requests.get(f"{BACKEND_URL}/test-documents/categories")
        print(f"✅ Test Categories: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Test Categories failed: {e}")
        return False

def test_test_enhanced():
    """Test the test enhanced endpoint (no auth required)"""
    try:
        response = requests.get(f"{BACKEND_URL}/test-documents/enhanced")
        print(f"✅ Test Enhanced: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Test Enhanced failed: {e}")
        return False

def test_test_login():
    """Test the test login endpoint to get a token"""
    try:
        response = requests.post(f"{BACKEND_URL}/test-login")
        print(f"✅ Test Login: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        return None
    except Exception as e:
        print(f"❌ Test Login failed: {e}")
        return None

def test_categories_with_token(token):
    """Test categories endpoint with authentication token"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/api/documents/categories", headers=headers)
        print(f"✅ Categories with token: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Categories with token failed: {e}")
        return False

def test_enhanced_with_token(token):
    """Test enhanced endpoint with authentication token"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/api/documents/enhanced", headers=headers)
        print(f"✅ Enhanced with token: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Enhanced with token failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Backend Endpoints")
    print("=" * 50)
    
    # Test basic functionality
    health_ok = test_health()
    cors_ok = test_cors()
    
    # Test CORS preflight
    categories_options_ok = test_options_categories()
    enhanced_options_ok = test_options_enhanced()
    
    # Test endpoints without auth (should return 401)
    categories_no_auth_ok = test_categories_no_auth()
    enhanced_no_auth_ok = test_enhanced_no_auth()
    
    # Test new test endpoints (no auth required)
    test_categories_ok = test_test_categories()
    test_enhanced_ok = test_test_enhanced()
    
    # Test authentication flow
    print("\n🔐 Testing Authentication Flow:")
    token = test_test_login()
    if token:
        categories_with_token_ok = test_categories_with_token(token)
        enhanced_with_token_ok = test_enhanced_with_token(token)
    else:
        categories_with_token_ok = False
        enhanced_with_token_ok = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Health Check: {'✅' if health_ok else '❌'}")
    print(f"CORS Test: {'✅' if cors_ok else '❌'}")
    print(f"Categories OPTIONS: {'✅' if categories_options_ok else '❌'}")
    print(f"Enhanced OPTIONS: {'✅' if enhanced_options_ok else '❌'}")
    print(f"Categories No Auth: {'✅' if categories_no_auth_ok else '❌'}")
    print(f"Enhanced No Auth: {'✅' if enhanced_no_auth_ok else '❌'}")
    print(f"Test Categories: {'✅' if test_categories_ok else '❌'}")
    print(f"Test Enhanced: {'✅' if test_enhanced_ok else '❌'}")
    print(f"Categories with Token: {'✅' if categories_with_token_ok else '❌'}")
    print(f"Enhanced with Token: {'✅' if enhanced_with_token_ok else '❌'}")
    
    if all([health_ok, cors_ok, categories_options_ok, enhanced_options_ok, categories_no_auth_ok, enhanced_no_auth_ok, test_categories_ok, test_enhanced_ok, categories_with_token_ok, enhanced_with_token_ok]):
        print("\n🎉 All tests passed! Backend is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the backend configuration.")
