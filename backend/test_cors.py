#!/usr/bin/env python3
"""
Test CORS configuration
"""
import requests
import json

def test_cors():
    """Test CORS endpoints"""
    base_url = "https://multitenant-backend-mlap.onrender.com"
    
    print("🧪 Testing CORS Configuration")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        "/",
        "/health", 
        "/test-cors",
        "/debug-cors"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Testing: {endpoint}")
            response = requests.get(f"{base_url}{endpoint}")
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}...")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_cors()
