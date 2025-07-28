#!/usr/bin/env python3
"""
Initialize Dynamic E-signature System for All Companies
This script ensures all companies have E-signature tables and sets up the dynamic permission system
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_management_db
from app.services.database_manager import db_manager
from app.utils.permissions import ESignaturePermissions, PermissionAction
from app import models
import traceback

def initialize_dynamic_esignature_system():
    """Initialize the dynamic E-signature system for all companies"""
    try:
        print("🚀 Initializing Dynamic E-signature System...")
        
        # Step 1: Get all companies
        management_db = next(get_management_db())
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        if not companies:
            print("❌ No active companies found!")
            return False
        
        print(f"📋 Found {len(companies)} active companies")
        
        # Step 2: Ensure E-signature tables exist for all companies
        success_count = 0
        for company in companies:
            print(f"\n🏢 Processing company: {company.name} (ID: {company.id})")
            
            try:
                # Ensure E-signature tables exist
                success = db_manager.ensure_esignature_tables_exist(
                    str(company.id), 
                    str(company.database_url)
                )
                
                if success:
                    print(f"✅ E-signature tables verified for {company.name}")
                    success_count += 1
                else:
                    print(f"❌ Failed to verify E-signature tables for {company.name}")
                    
            except Exception as e:
                print(f"❌ Error processing company {company.name}: {str(e)}")
                continue
        
        management_db.close()
        
        # Step 3: Initialize role permission system
        print(f"\n🔐 Initializing Role Permission System...")
        
        # Display base roles
        base_roles = list(ESignaturePermissions.BASE_PERMISSIONS.keys())
        print(f"📊 Base roles available: {', '.join(base_roles)}")
        
        # Display available permissions
        permissions = [action.value for action in PermissionAction]
        print(f"🔑 Available permissions: {', '.join(permissions)}")
        
        # Test permission system
        print(f"\n🧪 Testing Permission System...")
        
        test_roles = ["system_admin", "hr_admin", "hr_manager", "employee", "customer"]
        
        for role in test_roles:
            summary = ESignaturePermissions.get_role_summary(role)
            can_create = ESignaturePermissions.can_create_request(role)
            can_send = ESignaturePermissions.can_send_request(role)
            can_manage = ESignaturePermissions.has_permission(role, PermissionAction.MANAGE)
            
            print(f"  • {role}: Create={can_create}, Send={can_send}, Manage={can_manage}")
        
        # Step 4: Test dynamic role creation
        print(f"\n🎯 Testing Dynamic Role Creation...")
        
        # Create a test custom role
        custom_role_name = "test_custom_role"
        custom_permissions = {
            PermissionAction.CREATE: True,
            PermissionAction.SEND: True,
            PermissionAction.VIEW: True,
            PermissionAction.CANCEL: False,
            PermissionAction.SIGN: True,
            PermissionAction.DOWNLOAD: True,
            PermissionAction.MANAGE: False,
            PermissionAction.APPROVE: False,
            PermissionAction.WORKFLOW_CREATE: False,
            PermissionAction.WORKFLOW_MANAGE: False,
            PermissionAction.BULK_SEND: False,
            PermissionAction.AUDIT_VIEW: False,
        }
        
        try:
            ESignaturePermissions.add_custom_role(custom_role_name, custom_permissions)
            print(f"✅ Custom role '{custom_role_name}' created successfully")
            
            # Test the custom role
            test_summary = ESignaturePermissions.get_role_summary(custom_role_name)
            print(f"  • Custom role can create: {test_summary['can_create']}")
            print(f"  • Custom role can send: {test_summary['can_send']}")
            print(f"  • Custom role can manage: {test_summary['can_manage']}")
            
            # Clean up test role
            ESignaturePermissions.remove_custom_role(custom_role_name)
            print(f"🧹 Test custom role '{custom_role_name}' cleaned up")
            
        except Exception as e:
            print(f"❌ Error testing custom role: {str(e)}")
        
        # Step 5: Test unknown role handling
        print(f"\n🔍 Testing Unknown Role Handling...")
        
        test_unknown_roles = [
            "project_manager",
            "team_lead", 
            "senior_developer",
            "guest_user",
            "external_consultant"
        ]
        
        for unknown_role in test_unknown_roles:
            permissions = ESignaturePermissions.get_role_permissions(unknown_role)
            can_create = ESignaturePermissions.can_create_request(unknown_role)
            print(f"  • {unknown_role}: Auto-detected permissions (can_create={can_create})")
        
        # Step 6: Final verification
        print(f"\n📊 Final System Status:")
        print(f"  • Companies processed: {success_count}/{len(companies)}")
        print(f"  • Base roles: {len(base_roles)}")
        print(f"  • Custom roles: {len(ESignaturePermissions.CUSTOM_PERMISSIONS)}")
        print(f"  • Permission actions: {len(permissions)}")
        
        if success_count == len(companies):
            print(f"\n🎉 Dynamic E-signature System initialized successfully!")
            print(f"✨ All companies now have E-signature tables and dynamic permissions!")
            return True
        else:
            print(f"\n⚠️ System partially initialized. {len(companies) - success_count} companies had issues.")
            return False
        
    except Exception as e:
        print(f"❌ Error initializing dynamic E-signature system: {str(e)}")
        traceback.print_exc()
        return False

def verify_company_esignature_setup(company_id: str, database_url: str):
    """Verify E-signature setup for a specific company"""
    try:
        print(f"🔍 Verifying E-signature setup for company {company_id}...")
        
        # Get company database
        company_db_gen = db_manager.get_company_db(company_id, database_url)
        company_db = next(company_db_gen)
        
        # Check tables exist
        from sqlalchemy import inspect
        inspector = inspect(company_db.bind)
        
        if inspector is not None:
            existing_tables = inspector.get_table_names()
        else:
            existing_tables = []
        
        esignature_tables = [
            'esignature_documents',
            'esignature_recipients', 
            'esignature_audit_logs',
            'workflow_approvals'
        ]
        
        missing_tables = [table for table in esignature_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        # Check if we can create a test record
        from app.models_company import ESignatureDocument
        from datetime import datetime, timedelta
        
        test_doc = ESignatureDocument(
            id="test_doc_verification",
            document_id="test_doc_123",
            title="Test Document",
            message="Test message",
            status="pending",
            created_by_user_id="test_user",
            require_all_signatures=True,
            expires_at=datetime.utcnow() + timedelta(days=14),
            created_at=datetime.utcnow()
        )
        
        company_db.add(test_doc)
        company_db.flush()
        
        # Query it back
        retrieved_doc = company_db.query(ESignatureDocument).filter(
            ESignatureDocument.id == "test_doc_verification"
        ).first()
        
        if retrieved_doc:
            print(f"✅ E-signature tables working correctly")
            
            # Clean up test record
            company_db.delete(retrieved_doc)
            company_db.commit()
            
            company_db.close()
            return True
        else:
            print(f"❌ Failed to create/retrieve test record")
            company_db.close()
            return False
            
    except Exception as e:
        print(f"❌ Error verifying company setup: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("     DYNAMIC E-SIGNATURE SYSTEM INITIALIZATION")
    print("=" * 60)
    
    success = initialize_dynamic_esignature_system()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ INITIALIZATION COMPLETED SUCCESSFULLY!")
        print("🚀 The system is now ready for dynamic E-signature operations!")
        print("📋 All companies can now use E-signature features with role-based permissions!")
        print("🔄 New companies will automatically get E-signature tables!")
        print("🎯 Custom roles can be created and managed dynamically!")
    else:
        print("❌ INITIALIZATION FAILED!")
        print("🔧 Please check the errors above and try again.")
    
    print("=" * 60)
    
    sys.exit(0 if success else 1) 