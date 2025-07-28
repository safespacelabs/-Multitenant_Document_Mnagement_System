#!/usr/bin/env python3
"""
Comprehensive User Creation Script
Creates users for all companies and all roles with credentials
"""

import asyncio
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Database configuration
MAIN_DATABASE_URL = "postgresql://safespacelabs_user:Y2J6nJSBVF02ILLPNTBSKCNqmCKOXNy8@dpg-ct8b1b56l47c73b7k7g0-a.oregon-postgres.render.com/safespacelabs"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Companies and their database URLs
COMPANIES = {
    "amazon": "postgresql://amazon_user:M32PZEIEhYHOzSLslJWEdAEKdCz7CtJ1@dpg-ct8b1b56l47c73b7k7g0-a.oregon-postgres.render.com/amazon",
    "SafespaceLabs": "postgresql://safespacelabs_user:Y2J6nJSBVF02ILLPNTBSKCNqmCKOXNy8@dpg-ct8b1b56l47c73b7k7g0-a.oregon-postgres.render.com/safespacelabs",
    "Microsoft": "postgresql://microsoft_user:OPWiJJZIr3j6HkBqSqsGPVzGBAMlcjdO@dpg-ct8b1b56l47c73b7k7g0-a.oregon-postgres.render.com/microsoft",
    "FIFA": "postgresql://fifa_user:zZWDOiCkN6t8DYtOZxFzXJTjcyZQNKAW@dpg-ct8b1b56l47c73b7k7g0-a.oregon-postgres.render.com/fifa"
}

# Roles to create
ROLES = ["system_admin", "hr_admin", "hr_manager", "employee", "customer"]

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def create_user_in_database(engine, user_data):
    """Create a user in the database"""
    try:
        with engine.connect() as conn:
            # Check if user already exists
            result = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user_data['email']}
            )
            if result.fetchone():
                print(f"  ⚠️  User {user_data['email']} already exists - skipping")
                return False
            
            # Insert user
            conn.execute(
                text("""
                    INSERT INTO users (email, hashed_password, full_name, role, company_id, is_active, created_at)
                    VALUES (:email, :hashed_password, :full_name, :role, :company_id, :is_active, :created_at)
                """),
                user_data
            )
            conn.commit()
            print(f"  ✅ Created user: {user_data['email']}")
            return True
    except Exception as e:
        print(f"  ❌ Error creating user {user_data['email']}: {str(e)}")
        return False

def main():
    """Main function to create all users"""
    print("🚀 Creating Users for All Companies and Roles")
    print("=" * 60)
    
    credentials = []
    
    # Create users for each company
    for company_name, db_url in COMPANIES.items():
        print(f"\n📊 Processing Company: {company_name}")
        print("-" * 40)
        
        try:
            # Create database connection
            engine = create_engine(db_url)
            
            # Create users for each role in this company
            for role in ROLES:
                email = f"{role}@{company_name.lower()}.com"
                password = f"{role}_{company_name}_2024"
                
                user_data = {
                    'email': email,
                    'hashed_password': hash_password(password),
                    'full_name': f"{role.title()} {company_name}",
                    'role': role,
                    'company_id': company_name,
                    'is_active': True,
                    'created_at': datetime.utcnow()
                }
                
                if create_user_in_database(engine, user_data):
                    credentials.append({
                        'company': company_name,
                        'role': role,
                        'email': email,
                        'password': password
                    })
            
            engine.dispose()
            
        except Exception as e:
            print(f"❌ Error connecting to {company_name} database: {str(e)}")
    
    # Create system-wide users in main database
    print(f"\n🌐 Creating System-Wide Users")
    print("-" * 40)
    
    try:
        main_engine = create_engine(MAIN_DATABASE_URL)
        
        # Create additional system admins
        system_users = [
            {
                'email': 'super.admin@system.com',
                'password': 'SuperAdmin2024!',
                'full_name': 'Super Administrator',
                'role': 'system_admin',
                'company_id': 'system'
            },
            {
                'email': 'global.hr@system.com',
                'password': 'GlobalHR2024!',
                'full_name': 'Global HR Manager',
                'role': 'hr_admin',
                'company_id': 'system'
            }
        ]
        
        for user in system_users:
            user_data = {
                'email': user['email'],
                'hashed_password': hash_password(user['password']),
                'full_name': user['full_name'],
                'role': user['role'],
                'company_id': user['company_id'],
                'is_active': True,
                'created_at': datetime.utcnow()
            }
            
            if create_user_in_database(main_engine, user_data):
                credentials.append({
                    'company': 'SYSTEM',
                    'role': user['role'],
                    'email': user['email'],
                    'password': user['password']
                })
        
        main_engine.dispose()
        
    except Exception as e:
        print(f"❌ Error creating system users: {str(e)}")
    
    # Print all credentials
    print("\n" + "=" * 80)
    print("📋 USER CREDENTIALS SUMMARY")
    print("=" * 80)
    
    print("\n🏢 COMPANY USERS:")
    for company in ["amazon", "SafespaceLabs", "Microsoft", "FIFA"]:
        print(f"\n📊 {company.upper()}")
        print("-" * 50)
        company_creds = [c for c in credentials if c['company'] == company]
        for cred in company_creds:
            print(f"  {cred['role'].upper():<15} | {cred['email']:<35} | {cred['password']}")
    
    print(f"\n🌐 SYSTEM USERS:")
    print("-" * 50)
    system_creds = [c for c in credentials if c['company'] == 'SYSTEM']
    for cred in system_creds:
        print(f"  {cred['role'].upper():<15} | {cred['email']:<35} | {cred['password']}")
    
    # Save credentials to file
    with open('user_credentials.txt', 'w') as f:
        f.write("USER CREDENTIALS - MULTITENANT DOCUMENT MANAGEMENT SYSTEM\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("COMPANY USERS:\n")
        for company in ["amazon", "SafespaceLabs", "Microsoft", "FIFA"]:
            f.write(f"\n{company.upper()}:\n")
            f.write("-" * 50 + "\n")
            company_creds = [c for c in credentials if c['company'] == company]
            for cred in company_creds:
                f.write(f"  {cred['role'].upper():<15} | {cred['email']:<35} | {cred['password']}\n")
        
        f.write(f"\nSYSTEM USERS:\n")
        f.write("-" * 50 + "\n")
        system_creds = [c for c in credentials if c['company'] == 'SYSTEM']
        for cred in system_creds:
            f.write(f"  {cred['role'].upper():<15} | {cred['email']:<35} | {cred['password']}\n")
    
    print(f"\n💾 Credentials saved to: user_credentials.txt")
    print(f"✅ Created {len(credentials)} users total")
    print("\n🎉 User creation completed!")

if __name__ == "__main__":
    main() 