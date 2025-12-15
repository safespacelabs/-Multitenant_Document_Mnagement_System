"""
User Table Migration Script - All Phases
Migrates existing user tables to include extended fields from usertable.csv schema
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import asyncio
from datetime import datetime, date
import uuid

# Import database manager
from app.database import get_db, engine as management_engine, SessionLocal
from app.models import Company


def get_all_companies():
    """Get all companies from management database"""
    db = SessionLocal()
    try:
        companies = db.query(Company).all()
        return companies
    finally:
        db.close()


def migrate_company_database(company_id: str, database_url: str):
    """Migrate a single company database"""
    print(f"\n{'='*80}")
    print(f"Migrating company: {company_id}")
    print(f"Database: {database_url[:50]}...")
    print(f"{'='*80}\n")

    try:
        # Create engine for company database
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Phase 1: Core Identity & Employment Fields
        print("Phase 1: Adding Core Identity & Employment Fields...")
        session.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS first_name VARCHAR,
            ADD COLUMN IF NOT EXISTS last_name VARCHAR,
            ADD COLUMN IF NOT EXISTS middle_initial VARCHAR,
            ADD COLUMN IF NOT EXISTS gender VARCHAR DEFAULT 'Not Specified',
            ADD COLUMN IF NOT EXISTS employee_id VARCHAR,
            ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'active',
            ADD COLUMN IF NOT EXISTS hire_date DATE,
            ADD COLUMN IF NOT EXISTS timezone VARCHAR DEFAULT 'US/Pacific',
            ADD COLUMN IF NOT EXISTS default_locale VARCHAR DEFAULT 'en_US',
            ADD COLUMN IF NOT EXISTS display_name VARCHAR;
        """))
        session.commit()
        print("[OK] Phase 1 columns added successfully")

        # Phase 2: Organizational Hierarchy
        print("\nPhase 2: Adding Organizational Hierarchy Fields...")
        session.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS manager VARCHAR DEFAULT 'NO_MANAGER',
            ADD COLUMN IF NOT EXISTS division VARCHAR DEFAULT 'Unassigned',
            ADD COLUMN IF NOT EXISTS department VARCHAR DEFAULT 'General',
            ADD COLUMN IF NOT EXISTS location VARCHAR DEFAULT 'Remote',
            ADD COLUMN IF NOT EXISTS job_code VARCHAR DEFAULT '00000000',
            ADD COLUMN IF NOT EXISTS title VARCHAR DEFAULT 'Employee',
            ADD COLUMN IF NOT EXISTS hr VARCHAR,
            ADD COLUMN IF NOT EXISTS business_unit VARCHAR,
            ADD COLUMN IF NOT EXISTS matrix_manager VARCHAR,
            ADD COLUMN IF NOT EXISTS second_manager VARCHAR,
            ADD COLUMN IF NOT EXISTS custom_manager VARCHAR;
        """))
        session.commit()
        print("[OK] Phase 2 columns added successfully")

        # Phase 3: Contact & Address Information
        print("\nPhase 3: Adding Contact & Address Fields...")
        session.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS address_line1 VARCHAR DEFAULT 'Address Not Provided',
            ADD COLUMN IF NOT EXISTS address_line2 VARCHAR,
            ADD COLUMN IF NOT EXISTS city VARCHAR DEFAULT 'Unknown',
            ADD COLUMN IF NOT EXISTS state VARCHAR DEFAULT 'CA',
            ADD COLUMN IF NOT EXISTS zip_code VARCHAR DEFAULT '00000',
            ADD COLUMN IF NOT EXISTS country VARCHAR DEFAULT 'United States',
            ADD COLUMN IF NOT EXISTS business_phone VARCHAR,
            ADD COLUMN IF NOT EXISTS business_fax VARCHAR;
        """))
        session.commit()
        print("[OK] Phase 3 columns added successfully")

        # Phase 4: Review & Performance Tracking
        print("\nPhase 4: Adding Review & Performance Fields...")
        session.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS review_frequency VARCHAR,
            ADD COLUMN IF NOT EXISTS last_review_date DATE,
            ADD COLUMN IF NOT EXISTS assignment_uuid UUID;
        """))
        session.commit()
        print("[OK] Phase 4 columns added successfully")

        # Phase 5: Custom Fields
        print("\nPhase 5: Adding Custom Fields...")
        session.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS custom01 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom02 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom03 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom04 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom05 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom06 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom07 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom08 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom09 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom10 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom11 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom12 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom13 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom14 VARCHAR,
            ADD COLUMN IF NOT EXISTS custom15 VARCHAR;
        """))
        session.commit()
        print("[OK] Phase 5 columns added successfully")

        # Phase 6: Authentication & Access Control
        print("\nPhase 6: Adding Authentication & Access Fields...")
        session.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS login_method VARCHAR,
            ADD COLUMN IF NOT EXISTS proxy VARCHAR,
            ADD COLUMN IF NOT EXISTS assignment_id_external VARCHAR;
        """))
        session.commit()
        print("[OK] Phase 6 columns added successfully")

        # Migrate existing user data
        print("\nMigrating existing user data...")
        session.execute(text("""
            UPDATE users
            SET
                -- Phase 1: Split full_name into first_name and last_name
                first_name = COALESCE(first_name, SPLIT_PART(full_name, ' ', 1)),
                last_name = COALESCE(last_name,
                    CASE
                        WHEN full_name LIKE '% %' THEN SUBSTRING(full_name FROM POSITION(' ' IN full_name) + 1)
                        ELSE ''
                    END
                ),
                employee_id = COALESCE(employee_id, COALESCE(unique_id, 'EMP_' || SUBSTRING(id, 1, 8))),
                status = COALESCE(status, CASE WHEN is_active THEN 'active' ELSE 'inactive' END),
                hire_date = COALESCE(hire_date, DATE(created_at)),
                gender = COALESCE(gender, 'Not Specified'),
                timezone = COALESCE(timezone, 'US/Pacific'),
                default_locale = COALESCE(default_locale, 'en_US'),

                -- Phase 2: Set organizational defaults
                manager = COALESCE(manager, 'NO_MANAGER'),
                division = COALESCE(division, 'General Operations'),
                department = COALESCE(department,
                    CASE
                        WHEN role = 'hr_admin' THEN 'Human Resources'
                        WHEN role = 'hr_manager' THEN 'Human Resources'
                        WHEN role = 'employee' THEN 'General'
                        ELSE 'Customer Relations'
                    END
                ),
                location = COALESCE(location, 'Remote Office'),
                job_code = COALESCE(job_code, '50000000'),
                title = COALESCE(title,
                    CASE
                        WHEN role = 'hr_admin' THEN 'HR Administrator'
                        WHEN role = 'hr_manager' THEN 'HR Manager'
                        WHEN role = 'employee' THEN 'Employee'
                        WHEN role = 'customer' THEN 'Customer'
                        WHEN role = 'system_admin' THEN 'System Administrator'
                        ELSE 'User'
                    END
                ),

                -- Phase 3: Set address defaults
                address_line1 = COALESCE(address_line1, 'Address Not Provided'),
                city = COALESCE(city, 'Unknown'),
                state = COALESCE(state, 'CA'),
                zip_code = COALESCE(zip_code, '00000'),
                country = COALESCE(country, 'United States'),

                -- Phase 4: Set UUID if not exists
                assignment_uuid = COALESCE(assignment_uuid, gen_random_uuid()),

                -- Phase 5: Map company_id to custom08
                custom08 = COALESCE(custom08, company_id)
            WHERE first_name IS NULL OR employee_id IS NULL;
        """))
        session.commit()

        # Get count of migrated users
        result = session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        print(f"[OK] Migrated {user_count} existing users with default values")

        # Add unique constraint on employee_id if not exists
        print("\nAdding database constraints...")
        try:
            session.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'users_employee_id_key'
                    ) THEN
                        ALTER TABLE users ADD CONSTRAINT users_employee_id_key UNIQUE (employee_id);
                    END IF;
                END $$;
            """))
            session.commit()
            print("[OK] Unique constraint added on employee_id")
        except Exception as e:
            print(f"[WARN] Warning: Could not add unique constraint (might already exist): {e}")
            session.rollback()

        # Create indexes for better query performance
        print("\nCreating indexes...")
        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id);
                CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);
                CREATE INDEX IF NOT EXISTS idx_users_division ON users(division);
                CREATE INDEX IF NOT EXISTS idx_users_location ON users(location);
                CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
            """))
            session.commit()
            print("[OK] Indexes created successfully")
        except Exception as e:
            print(f"[WARN] Warning: Could not create indexes: {e}")
            session.rollback()

        print(f"\n{'='*80}")
        print(f"[OK] Migration completed successfully for company: {company_id}")
        print(f"{'='*80}\n")

        session.close()
        engine.dispose()
        return True

    except Exception as e:
        print(f"\n[ERROR] Migration failed for company {company_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main migration function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Migrate user table to extended schema')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip confirmation prompt and proceed with migration')
    args = parser.parse_args()

    print("\n" + "="*80)
    print("USER TABLE MIGRATION - EXTENDED SCHEMA")
    print("="*80)
    print("\nThis script will:")
    print("  1. Add 40+ new fields to the users table across all company databases")
    print("  2. Migrate existing user data with sensible defaults")
    print("  3. Create necessary indexes and constraints")
    print("\nNOTE: All new fields are nullable to ensure backward compatibility")
    print("\n" + "="*80 + "\n")

    # Skip confirmation if --yes flag is provided
    if not args.yes:
        response = input("Do you want to proceed with the migration? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled.")
            return
    else:
        print("Auto-confirming migration (--yes flag provided)...")

    # Get all companies
    companies = get_all_companies()

    if not companies:
        print("No companies found in the management database.")
        return

    print(f"\nFound {len(companies)} companies to migrate:\n")
    for company in companies:
        print(f"  - {company.id}: {company.name}")

    print(f"\n{'='*80}\n")

    success_count = 0
    fail_count = 0

    for company in companies:
        try:
            if migrate_company_database(company.id, company.database_url):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"Error migrating {company.id}: {e}")
            fail_count += 1

    # Summary
    print("\n" + "="*80)
    print("MIGRATION SUMMARY")
    print("="*80)
    print(f"Total companies: {len(companies)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print("="*80 + "\n")

    if fail_count == 0:
        print("[OK] All migrations completed successfully!")
    else:
        print(f"[WARN] {fail_count} migration(s) failed. Please check the errors above.")


if __name__ == "__main__":
    main()
