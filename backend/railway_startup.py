#!/usr/bin/env python3
"""
Railway startup script for database initialization and application startup
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def setup_database():
    """Initialize database tables on Railway deployment"""
    try:
        from app.database import get_management_db
        from app.services.database_manager import db_manager
        from app import models
        
        print("🔧 Setting up database tables...")
        
        # Create management database tables
        models.Base.metadata.create_all(bind=db_manager.management_engine)
        print("✅ Management database tables created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting Railway deployment setup...")
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed. Exiting...")
        sys.exit(1)
    
    print("✅ Railway setup completed successfully!")

if __name__ == "__main__":
    main()