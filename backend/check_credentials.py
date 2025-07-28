#!/usr/bin/env python3
"""
Credential and Configuration Check Script
"""

import os
from app.config import (
    MANAGEMENT_DATABASE_URL,
    NEON_API_KEY, 
    NEON_PROJECT_ID,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    ANTHROPIC_API_KEY,
    SECRET_KEY
)

def check_credentials():
    """Check all required credentials and configurations"""
    print("🔍 Checking Multi-Tenant Document Management System Credentials\n")
    
    issues = []
    
    # Database Configuration
    print("📊 Database Configuration:")
    print(f"  ✅ Management Database URL: {'SET' if MANAGEMENT_DATABASE_URL else 'NOT SET'}")
    print(f"  ✅ Neon API Key: {'SET' if NEON_API_KEY else 'NOT SET'}")
    print(f"  ✅ Neon Project ID: {'SET' if NEON_PROJECT_ID else 'NOT SET'}")
    
    if not MANAGEMENT_DATABASE_URL:
        issues.append("MANAGEMENT_DATABASE_URL is required")
    if not NEON_API_KEY:
        issues.append("NEON_API_KEY is required for creating company databases")
    
    # AWS Configuration
    print("\n☁️ AWS Configuration:")
    print(f"  {'✅' if AWS_ACCESS_KEY_ID else '⚠️'} AWS Access Key ID: {'SET' if AWS_ACCESS_KEY_ID else 'NOT SET'}")
    print(f"  {'✅' if AWS_SECRET_ACCESS_KEY else '⚠️'} AWS Secret Access Key: {'SET' if AWS_SECRET_ACCESS_KEY else 'NOT SET'}")
    
    if not AWS_ACCESS_KEY_ID:
        issues.append("AWS_ACCESS_KEY_ID is required for S3 document storage")
    if not AWS_SECRET_ACCESS_KEY:
        issues.append("AWS_SECRET_ACCESS_KEY is required for S3 document storage")
    
    # AI Configuration
    print("\n🤖 AI Configuration:")
    print(f"  {'✅' if ANTHROPIC_API_KEY else '⚠️'} Anthropic API Key: {'SET' if ANTHROPIC_API_KEY else 'NOT SET'}")
    
    if not ANTHROPIC_API_KEY:
        issues.append("ANTHROPIC_API_KEY is required for AI document processing")
    
    # Security Configuration
    print("\n🔐 Security Configuration:")
    is_default_secret = SECRET_KEY == "your-super-secret-jwt-key-here-change-this-in-production"
    print(f"  {'⚠️' if is_default_secret else '✅'} JWT Secret Key: {'DEFAULT (CHANGE THIS)' if is_default_secret else 'CUSTOM'}")
    
    if is_default_secret:
        issues.append("SECRET_KEY is using default value - change for production")
    
    # Summary
    print("\n" + "="*60)
    if not issues:
        print("✅ All credentials are properly configured!")
        print("🚀 System is ready to start")
    else:
        print("⚠️ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 Missing credentials will cause runtime errors")
        print("   Create a .env file in the backend directory with these variables")
    
    print("="*60)
    
    return len(issues) == 0

if __name__ == "__main__":
    check_credentials() 