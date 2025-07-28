#!/usr/bin/env python3
"""
Simple credentials test - checks what's missing
"""
import os
from dotenv import load_dotenv

load_dotenv()

def check_credentials():
    """Check which credentials are missing"""
    print("🔍 Checking Credentials Configuration")
    print("=" * 50)
    
    # Management Database
    mgmt_db_url = os.getenv("MANAGEMENT_DATABASE_URL")
    if mgmt_db_url:
        print("✅ MANAGEMENT_DATABASE_URL: SET")
    else:
        print("❌ MANAGEMENT_DATABASE_URL: MISSING")
    
    # Neon API
    neon_key = os.getenv("NEON_API_KEY") 
    if neon_key:
        print(f"✅ NEON_API_KEY: SET ({neon_key[:10]}...)")
    else:
        print("❌ NEON_API_KEY: MISSING")
    
    neon_project = os.getenv("NEON_PROJECT_ID")
    if neon_project:
        print(f"✅ NEON_PROJECT_ID: SET ({neon_project})")
    else:
        print("❌ NEON_PROJECT_ID: MISSING")
    
    # AWS
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    if aws_key:
        print(f"✅ AWS_ACCESS_KEY_ID: SET ({aws_key[:10]}...)")
    else:
        print("❌ AWS_ACCESS_KEY_ID: MISSING")
    
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    if aws_secret:
        print(f"✅ AWS_SECRET_ACCESS_KEY: SET ({aws_secret[:10]}...)")
    else:
        print("❌ AWS_SECRET_ACCESS_KEY: MISSING")
    
    # Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        print(f"✅ ANTHROPIC_API_KEY: SET ({anthropic_key[:10]}...)")
    else:
        print("❌ ANTHROPIC_API_KEY: MISSING")
    
    print("\n" + "=" * 50)
    
    # Test database connection
    print("🔍 Testing Database Connection")
    print("-" * 30)
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        if mgmt_db_url:
            result = urlparse(mgmt_db_url)
            
            conn = psycopg2.connect(
                host=result.hostname,
                port=result.port or 5432,
                database=result.path[1:],
                user=result.username,
                password=result.password
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            
            print("✅ MANAGEMENT_DB: CONNECTION OK")
        else:
            print("❌ MANAGEMENT_DB: NO URL TO TEST")
            
    except Exception as e:
        print(f"❌ MANAGEMENT_DB: CONNECTION FAILED - {e}")
    
    # Test Neon API
    print("\n🔍 Testing Neon API")
    print("-" * 30)
    
    try:
        import requests
        
        if neon_key:
            headers = {
                "Authorization": f"Bearer {neon_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://console.neon.tech/api/v2/projects",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                print(f"✅ NEON_API: CONNECTION OK ({len(projects.get('projects', []))} projects)")
            else:
                print(f"❌ NEON_API: HTTP {response.status_code} - {response.text[:100]}")
        else:
            print("❌ NEON_API: NO KEY TO TEST")
            
    except Exception as e:
        print(f"❌ NEON_API: CONNECTION FAILED - {e}")

def check_missing_vars():
    """List environment variables that need to be set"""
    required_vars = [
        "MANAGEMENT_DATABASE_URL",
        "NEON_API_KEY", 
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "ANTHROPIC_API_KEY"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"\n❌ Missing Environment Variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nTo set these variables, create a .env file or export them:")
        for var in missing:
            print(f"   export {var}=your_value_here")
    else:
        print("\n✅ All required environment variables are set")

if __name__ == "__main__":
    check_credentials()
    check_missing_vars() 