#!/usr/bin/env python3
"""
Script to initialize default document categories and folders for companies.
This creates the organizational structure similar to PFile interface.
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from app.database import get_management_db
from app import models

def initialize_document_categories():
    """Initialize default document categories and folders for all companies"""
    
    # Load environment variables
    load_dotenv()
    
    # Get management database connection
    management_db = next(get_management_db())
    
    try:
        # Get all active companies
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        print(f"Found {len(companies)} active companies")
        
        # Default categories based on PFile interface
        default_categories = [
            {
                "name": "career_development",
                "display_name": "Career Development",
                "description": "Documents related to career growth, training, and development",
                "icon": "briefcase",
                "color": "#3B82F6",
                "sort_order": 1
            },
            {
                "name": "compensation",
                "display_name": "Compensation",
                "description": "Salary, benefits, and compensation related documents",
                "icon": "dollar-sign",
                "color": "#10B981",
                "sort_order": 2
            },
            {
                "name": "employee_central",
                "display_name": "Employee Central",
                "description": "Core employee information and records",
                "icon": "user",
                "color": "#8B5CF6",
                "sort_order": 3
            },
            {
                "name": "onboarding_offboarding",
                "display_name": "On/Offboarding",
                "description": "Employee onboarding and offboarding documents",
                "icon": "file-text",
                "color": "#F59E0B",
                "sort_order": 4
            },
            {
                "name": "performance_goals",
                "display_name": "Performance and Goals",
                "description": "Performance reviews, goals, and assessments",
                "icon": "trending-up",
                "color": "#EF4444",
                "sort_order": 5
            },
            {
                "name": "platform",
                "display_name": "Platform",
                "description": "System and platform related documents",
                "icon": "monitor",
                "color": "#6B7280",
                "sort_order": 6
            },
            {
                "name": "others",
                "display_name": "Others",
                "description": "Miscellaneous documents and files",
                "icon": "more-horizontal",
                "color": "#9CA3AF",
                "sort_order": 7
            }
        ]
        
        for company in companies:
            print(f"\n🔧 Processing company: {company.name} ({company.id})")
            
            try:
                # Create engine for company database
                company_engine = create_engine(company.database_url)
                
                # Create document_categories table if it doesn't exist
                with company_engine.connect() as conn:
                    # Check if table exists
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'document_categories'
                        );
                    """))
                    table_exists = result.scalar()
                    
                    if not table_exists:
                        print(f"  📋 Creating document_categories table...")
                        conn.execute(text("""
                            CREATE TABLE document_categories (
                                id VARCHAR PRIMARY KEY,
                                name VARCHAR NOT NULL,
                                display_name VARCHAR NOT NULL,
                                description TEXT,
                                icon VARCHAR,
                                color VARCHAR,
                                parent_category_id VARCHAR,
                                company_id VARCHAR,
                                is_active BOOLEAN DEFAULT TRUE,
                                sort_order INTEGER DEFAULT 0,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                        """))
                        conn.commit()
                        print(f"  ✅ Created document_categories table")
                    
                    # Create document_folders table if it doesn't exist
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'document_folders'
                        );
                    """))
                    folders_table_exists = result.scalar()
                    
                    if not folders_table_exists:
                        print(f"  📋 Creating document_folders table...")
                        conn.execute(text("""
                            CREATE TABLE document_folders (
                                id VARCHAR PRIMARY KEY,
                                name VARCHAR NOT NULL,
                                display_name VARCHAR NOT NULL,
                                description TEXT,
                                category_id VARCHAR,
                                parent_folder_id VARCHAR,
                                company_id VARCHAR,
                                created_by_user_id VARCHAR NOT NULL,
                                is_active BOOLEAN DEFAULT TRUE,
                                sort_order INTEGER DEFAULT 0,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                        """))
                        conn.commit()
                        print(f"  ✅ Created document_folders table")
                    
                    # Create document_access table if it doesn't exist
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'document_access'
                        );
                    """))
                    access_table_exists = result.scalar()
                    
                    if not access_table_exists:
                        print(f"  📋 Creating document_access table...")
                        conn.execute(text("""
                            CREATE TABLE document_access (
                                id VARCHAR PRIMARY KEY,
                                document_id VARCHAR NOT NULL,
                                user_id VARCHAR,
                                role_id VARCHAR,
                                access_type VARCHAR NOT NULL,
                                granted_by_user_id VARCHAR NOT NULL,
                                company_id VARCHAR,
                                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                expires_at TIMESTAMP,
                                is_active BOOLEAN DEFAULT TRUE
                            );
                        """))
                        conn.commit()
                        print(f"  ✅ Created document_access table")
                    
                    # Create document_audit_logs table if it doesn't exist
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'document_audit_logs'
                        );
                    """))
                    audit_table_exists = result.scalar()
                    
                    if not audit_table_exists:
                        print(f"  📋 Creating document_audit_logs table...")
                        conn.execute(text("""
                            CREATE TABLE document_audit_logs (
                                id VARCHAR PRIMARY KEY,
                                document_id VARCHAR NOT NULL,
                                user_id VARCHAR NOT NULL,
                                action VARCHAR NOT NULL,
                                details JSON,
                                ip_address VARCHAR,
                                user_agent VARCHAR,
                                company_id VARCHAR,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                        """))
                        conn.commit()
                        print(f"  ✅ Created document_audit_logs table")
                    
                    # Insert default categories
                    print(f"  📁 Inserting default document categories...")
                    for category in default_categories:
                        category_id = f"cat_{company.id}_{category['name']}"
                        
                        # Check if category already exists
                        result = conn.execute(text("""
                            SELECT id FROM document_categories 
                            WHERE name = :name AND company_id = :company_id
                        """), {"name": category['name'], "company_id": company.id})
                        
                        if not result.fetchone():
                            conn.execute(text("""
                                INSERT INTO document_categories (
                                    id, name, display_name, description, icon, color, 
                                    company_id, sort_order, created_at
                                ) VALUES (
                                    :id, :name, :display_name, :description, :icon, :color,
                                    :company_id, :sort_order, CURRENT_TIMESTAMP
                                )
                            """), {
                                "id": category_id,
                                "name": category['name'],
                                "display_name": category['display_name'],
                                "description": category['description'],
                                "icon": category['icon'],
                                "color": category['color'],
                                "company_id": company.id,
                                "sort_order": category['sort_order']
                            })
                            print(f"    ✅ Added category: {category['display_name']}")
                        else:
                            print(f"    ✅ Category already exists: {category['display_name']}")
                    
                    # Create default folders for each category
                    print(f"  📂 Creating default folders...")
                    for category in default_categories:
                        category_id = f"cat_{company.id}_{category['name']}"
                        
                        # Create a default folder for each category
                        folder_id = f"folder_{company.id}_{category['name']}_default"
                        folder_name = f"{category['display_name']} Documents"
                        
                        # Check if folder already exists
                        result = conn.execute(text("""
                            SELECT id FROM document_folders 
                            WHERE name = :name AND company_id = :company_id
                        """), {"name": f"{category['name']}_default", "company_id": company.id})
                        
                        if not result.fetchone():
                            conn.execute(text("""
                                INSERT INTO document_folders (
                                    id, name, display_name, description, category_id,
                                    company_id, created_by_user_id, sort_order, created_at
                                ) VALUES (
                                    :id, :name, :display_name, :description, :category_id,
                                    :company_id, :created_by_user_id, :sort_order, CURRENT_TIMESTAMP
                                )
                            """), {
                                "id": folder_id,
                                "name": f"{category['name']}_default",
                                "display_name": folder_name,
                                "description": f"Default folder for {category['display_name']} documents",
                                "category_id": category_id,
                                "company_id": company.id,
                                "created_by_user_id": "system",  # Placeholder
                                "sort_order": category['sort_order']
                            })
                            print(f"    ✅ Created folder: {folder_name}")
                        else:
                            print(f"    ✅ Folder already exists: {folder_name}")
                    
                    conn.commit()
                    print(f"  ✅ Completed setup for {company.name}")
                
                company_engine.dispose()
                
            except Exception as e:
                print(f"  ❌ Error processing {company.name}: {str(e)}")
                continue
        
        print(f"\n🎉 Document categories and folders initialization completed for {len(companies)} companies")
        
    except Exception as e:
        print(f"❌ Error in initialization: {str(e)}")
        raise
    finally:
        management_db.close()

if __name__ == "__main__":
    print("🚀 Starting document categories and folders initialization...")
    initialize_document_categories()
    print("✅ Initialization completed successfully!")
