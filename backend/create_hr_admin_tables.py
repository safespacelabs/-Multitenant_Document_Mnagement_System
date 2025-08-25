#!/usr/bin/env python3
"""
Database migration script to create HR admin tables for company databases.
This script adds new tables for document analytics, compliance, workflows, and notifications.
"""

import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_management_db
from app.models import Company
from app.models_company import (
    CompanyBase, DocumentAnalytics, ComplianceRule, ComplianceViolation,
    DocumentWorkflow, WorkflowStep, DocumentNotification, DocumentTag,
    DocumentTagMapping, DocumentVersion
)

def create_hr_admin_tables_for_company(company_db_url):
    """Create HR admin tables for a specific company database"""
    try:
        # Create engine for company database
        engine = create_engine(company_db_url)
        
        # Create all tables
        CompanyBase.metadata.create_all(engine)
        
        print(f"✅ Successfully created HR admin tables for company database")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create HR admin tables: {str(e)}")
        return False

def create_hr_admin_tables():
    """Create HR admin tables for all company databases"""
    print("🚀 Starting HR Admin tables creation...")
    
    try:
        # Get management database session
        management_db = next(get_management_db())
        
        # Get all active companies
        companies = management_db.query(Company).filter(Company.is_active == True).all()
        
        print(f"📊 Found {len(companies)} active companies")
        
        success_count = 0
        failed_count = 0
        
        for company in companies:
            print(f"\n🏢 Processing company: {company.name}")
            print(f"   Database: {company.database_name}")
            print(f"   URL: {company.database_url}")
            
            try:
                if create_hr_admin_tables_for_company(company.database_url):
                    success_count += 1
                    print(f"   ✅ Success")
                else:
                    failed_count += 1
                    print(f"   ❌ Failed")
                    
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Error: {str(e)}")
        
        print(f"\n🎯 Migration Summary:")
        print(f"   Total companies: {len(companies)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {failed_count}")
        
        if failed_count == 0:
            print("🎉 All HR admin tables created successfully!")
        else:
            print("⚠️  Some companies failed. Check the logs above.")
            
    except Exception as e:
        print(f"❌ Failed to get companies from management database: {str(e)}")
        return False
    finally:
        if 'management_db' in locals():
            management_db.close()
    
    return True

def create_sample_data_for_company(company_db_url):
    """Create sample data for HR admin features"""
    try:
        engine = create_engine(company_db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create sample document categories
        from app.models_company import DocumentCategory
        
        categories = [
            {"name": "HR", "display_name": "Human Resources", "description": "HR related documents", "icon": "users", "color": "#3B82F6"},
            {"name": "Legal", "display_name": "Legal Documents", "description": "Legal and compliance documents", "icon": "scale", "color": "#EF4444"},
            {"name": "Finance", "display_name": "Financial Reports", "description": "Financial and accounting documents", "icon": "dollar-sign", "color": "#10B981"},
            {"name": "Operations", "display_name": "Operations", "description": "Operational documents", "icon": "settings", "color": "#8B5CF6"},
            {"name": "Marketing", "display_name": "Marketing", "description": "Marketing and sales documents", "icon": "trending-up", "color": "#F59E0B"}
        ]
        
        for cat_data in categories:
            existing = session.query(DocumentCategory).filter(DocumentCategory.name == cat_data["name"]).first()
            if not existing:
                category = DocumentCategory(
                    name=cat_data["name"],
                    display_name=cat_data["display_name"],
                    description=cat_data["description"],
                    icon=cat_data["icon"],
                    color=cat_data["color"],
                    is_active=True,
                    sort_order=len(categories)
                )
                session.add(category)
        
        # Create sample compliance rules
        from app.models_company import ComplianceRule
        
        rules = [
            {
                "name": "Document Retention Policy",
                "description": "Documents must be retained for specified periods",
                "rule_type": "retention",
                "retention_period_days": 2555,  # 7 years
                "requires_approval": True,
                "requires_signature": False
            },
            {
                "name": "Access Control Policy",
                "description": "Documents must have proper access controls",
                "rule_type": "access_control",
                "retention_period_days": None,
                "requires_approval": True,
                "requires_signature": False
            }
        ]
        
        for rule_data in rules:
            existing = session.query(ComplianceRule).filter(ComplianceRule.name == rule_data["name"]).first()
            if not existing:
                rule = ComplianceRule(
                    name=rule_data["name"],
                    description=rule_data["description"],
                    rule_type=rule_data["rule_type"],
                    retention_period_days=rule_data["retention_period_days"],
                    requires_approval=rule_data["requires_approval"],
                    requires_signature=rule_data["requires_signature"],
                    is_active=True
                )
                session.add(rule)
        
        session.commit()
        print(f"✅ Sample data created successfully")
        session.close()
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()

def create_sample_data():
    """Create sample data for all company databases"""
    print("\n🎨 Creating sample data for HR admin features...")
    
    try:
        # Get management database session
        management_db = next(get_management_db())
        
        # Get all active companies
        companies = management_db.query(Company).filter(Company.is_active == True).all()
        
        for company in companies:
            print(f"\n🏢 Adding sample data for company: {company.name}")
            create_sample_data_for_company(company.database_url)
            
    except Exception as e:
        print(f"❌ Failed to create sample data: {str(e)}")
    finally:
        if 'management_db' in locals():
            management_db.close()

if __name__ == "__main__":
    print("🚀 HR Admin Tables Migration Script")
    print("=" * 50)
    
    # Create tables
    if create_hr_admin_tables():
        print("\n" + "=" * 50)
        
        # Ask if user wants to create sample data
        response = input("\n🤔 Would you like to create sample data for HR admin features? (y/n): ")
        if response.lower() in ['y', 'yes']:
            create_sample_data()
    
    print("\n✨ Migration script completed!")
