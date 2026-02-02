"""
Migration Script: Add New Columns to Expiry Notifications Table

This script adds the following columns to the expiry_notifications table:
- ai_generated_reasons (JSON)
- recommended_action (TEXT)
- hr_notified (BOOLEAN)
- hr_notification_sent_at (TIMESTAMP)
- reminder_count (INTEGER)
- last_reminder_at (TIMESTAMP)
- agent_run_id (VARCHAR with index)

Also creates new tables if they don't exist:
- expiry_agent_runs
- expiry_agent_config
- hr_chat_actions
- bulk_user_imports

Run this script after deploying the new expiry agent features.

Usage:
    cd backend
    python -m app.scripts.migrate_expiry_agent_columns
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from sqlalchemy import inspect, text
from app.database import get_management_db, get_company_db
from app.models import Company
from app.models_document_analysis import Base as DocumentAnalysisBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# New columns to add to expiry_notifications table
NEW_COLUMNS = [
    {
        'name': 'ai_generated_reasons',
        'sql': 'ALTER TABLE expiry_notifications ADD COLUMN IF NOT EXISTS ai_generated_reasons JSON'
    },
    {
        'name': 'recommended_action',
        'sql': 'ALTER TABLE expiry_notifications ADD COLUMN IF NOT EXISTS recommended_action TEXT'
    },
    {
        'name': 'hr_notified',
        'sql': 'ALTER TABLE expiry_notifications ADD COLUMN IF NOT EXISTS hr_notified BOOLEAN DEFAULT FALSE'
    },
    {
        'name': 'hr_notification_sent_at',
        'sql': 'ALTER TABLE expiry_notifications ADD COLUMN IF NOT EXISTS hr_notification_sent_at TIMESTAMP'
    },
    {
        'name': 'reminder_count',
        'sql': 'ALTER TABLE expiry_notifications ADD COLUMN IF NOT EXISTS reminder_count INTEGER DEFAULT 0'
    },
    {
        'name': 'last_reminder_at',
        'sql': 'ALTER TABLE expiry_notifications ADD COLUMN IF NOT EXISTS last_reminder_at TIMESTAMP'
    },
    {
        'name': 'agent_run_id',
        'sql': 'ALTER TABLE expiry_notifications ADD COLUMN IF NOT EXISTS agent_run_id VARCHAR(255)'
    }
]

# Index to create on agent_run_id
AGENT_RUN_ID_INDEX = """
CREATE INDEX IF NOT EXISTS ix_expiry_notifications_agent_run_id
ON expiry_notifications (agent_run_id)
"""

# New tables that should exist
NEW_TABLES = [
    'expiry_agent_runs',
    'expiry_agent_config',
    'hr_chat_actions',
    'bulk_user_imports'
]


def get_existing_columns(engine, table_name: str) -> list:
    """Get list of existing column names for a table"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return [col['name'] for col in columns]
    except Exception as e:
        logger.error(f"Error getting columns for {table_name}: {e}")
        return []


def get_missing_tables(engine) -> list:
    """Check which tables are missing from the database"""
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        missing = [table for table in NEW_TABLES if table not in existing_tables]
        return missing
    except Exception as e:
        logger.error(f"Error inspecting tables: {e}")
        return NEW_TABLES


def migrate_company_database(company_id: str, database_url: str) -> dict:
    """
    Migrate a single company database:
    1. Add new columns to expiry_notifications
    2. Create new tables if missing
    """
    result = {
        'company_id': company_id,
        'status': 'pending',
        'columns_added': [],
        'tables_created': [],
        'errors': []
    }

    try:
        # Get company database connection
        company_db_gen = get_company_db(company_id, database_url)
        company_db = next(company_db_gen)

        try:
            engine = company_db.bind

            # Step 1: Check if expiry_notifications table exists
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()

            if 'expiry_notifications' in existing_tables:
                # Get existing columns
                existing_columns = get_existing_columns(engine, 'expiry_notifications')
                logger.info(f"  Existing columns: {existing_columns}")

                # Add missing columns
                for col_def in NEW_COLUMNS:
                    if col_def['name'] not in existing_columns:
                        try:
                            with engine.connect() as conn:
                                conn.execute(text(col_def['sql']))
                                conn.commit()
                            result['columns_added'].append(col_def['name'])
                            logger.info(f"    Added column: {col_def['name']}")
                        except Exception as e:
                            error_msg = f"Failed to add {col_def['name']}: {str(e)}"
                            result['errors'].append(error_msg)
                            logger.error(f"    {error_msg}")
                    else:
                        logger.info(f"    Column already exists: {col_def['name']}")

                # Create index on agent_run_id
                try:
                    with engine.connect() as conn:
                        conn.execute(text(AGENT_RUN_ID_INDEX))
                        conn.commit()
                    logger.info(f"    Created/verified index on agent_run_id")
                except Exception as e:
                    logger.warning(f"    Index creation note: {str(e)}")

            else:
                logger.info(f"  expiry_notifications table doesn't exist, will be created")

            # Step 2: Create missing tables using SQLAlchemy
            missing_tables = get_missing_tables(engine)
            if missing_tables:
                logger.info(f"  Creating missing tables: {missing_tables}")
                DocumentAnalysisBase.metadata.create_all(bind=engine)
                result['tables_created'] = missing_tables

            # Verify
            still_missing = get_missing_tables(engine)
            if still_missing:
                result['errors'].append(f"Tables still missing: {still_missing}")

            # Determine final status
            if result['errors']:
                result['status'] = 'partial' if (result['columns_added'] or result['tables_created']) else 'error'
            elif result['columns_added'] or result['tables_created']:
                result['status'] = 'success'
            else:
                result['status'] = 'skipped'

        finally:
            company_db.close()

    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(str(e))
        logger.error(f"  Company {company_id}: Error - {e}")

    return result


def run_migration():
    """Run migration for all active companies"""
    logger.info("=" * 70)
    logger.info("Expiry Agent Columns & Tables Migration Script")
    logger.info("=" * 70)
    logger.info("\nThis migration will:")
    logger.info("  1. Add new columns to expiry_notifications table")
    logger.info("  2. Create new tables: expiry_agent_runs, expiry_agent_config,")
    logger.info("     hr_chat_actions, bulk_user_imports")
    logger.info("")

    # Get management database
    management_db_gen = get_management_db()
    management_db = next(management_db_gen)

    try:
        # Get all active companies
        companies = management_db.query(Company).filter(
            Company.is_active == True
        ).all()

        logger.info(f"Found {len(companies)} active companies to migrate\n")

        if not companies:
            logger.info("No companies found. Nothing to migrate.")
            return

        # Migration statistics
        stats = {
            'total': len(companies),
            'success': 0,
            'skipped': 0,
            'partial': 0,
            'error': 0
        }

        results = []

        # Migrate each company
        for i, company in enumerate(companies, 1):
            logger.info(f"[{i}/{len(companies)}] Migrating: {company.name} (ID: {company.id})")

            if not company.database_url:
                logger.warning(f"  Skipping - no database URL configured")
                stats['error'] += 1
                results.append({
                    'company_id': str(company.id),
                    'company_name': company.name,
                    'status': 'error',
                    'errors': ['No database URL']
                })
                continue

            result = migrate_company_database(str(company.id), str(company.database_url))
            result['company_name'] = company.name
            results.append(result)

            stats[result['status']] += 1

            # Log result summary
            if result['columns_added']:
                logger.info(f"    Columns added: {result['columns_added']}")
            if result['tables_created']:
                logger.info(f"    Tables created: {result['tables_created']}")

        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("Migration Summary")
        logger.info("=" * 70)
        logger.info(f"Total companies:     {stats['total']}")
        logger.info(f"  Successful:        {stats['success']}")
        logger.info(f"  Skipped:           {stats['skipped']} (already up to date)")
        logger.info(f"  Partial:           {stats['partial']}")
        logger.info(f"  Errors:            {stats['error']}")

        # Print detailed results for failures
        failures = [r for r in results if r['status'] in ['error', 'partial']]
        if failures:
            logger.info("\nCompanies with Issues:")
            for r in failures:
                logger.info(f"  - {r.get('company_name', 'Unknown')} ({r['company_id']}):")
                for err in r.get('errors', []):
                    logger.info(f"      {err}")

        logger.info("\n" + "=" * 70)
        logger.info("Migration Complete!")
        logger.info("=" * 70)

        return results

    finally:
        management_db.close()


def verify_migration():
    """Verify migration was successful for all companies"""
    logger.info("\n" + "=" * 70)
    logger.info("Verifying Migration")
    logger.info("=" * 70)

    management_db_gen = get_management_db()
    management_db = next(management_db_gen)

    try:
        companies = management_db.query(Company).filter(
            Company.is_active == True
        ).all()

        all_good = True
        expected_columns = [col['name'] for col in NEW_COLUMNS]

        for company in companies:
            if not company.database_url:
                continue

            try:
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)

                try:
                    engine = company_db.bind

                    # Check tables
                    missing_tables = get_missing_tables(engine)

                    # Check columns
                    existing_columns = get_existing_columns(engine, 'expiry_notifications')
                    missing_columns = [c for c in expected_columns if c not in existing_columns]

                    if missing_tables or missing_columns:
                        logger.warning(f"  {company.name}:")
                        if missing_tables:
                            logger.warning(f"    Missing tables: {missing_tables}")
                        if missing_columns:
                            logger.warning(f"    Missing columns: {missing_columns}")
                        all_good = False
                    else:
                        logger.info(f"  {company.name}: OK")

                finally:
                    company_db.close()

            except Exception as e:
                logger.error(f"  {company.name}: Error - {e}")
                all_good = False

        if all_good:
            logger.info("\nAll companies have required tables and columns!")
        else:
            logger.warning("\nSome companies need migration. Run without --verify flag.")

    finally:
        management_db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Migrate expiry agent columns and tables')
    parser.add_argument('--verify', action='store_true', help='Only verify, do not migrate')
    parser.add_argument('--company', type=str, help='Migrate specific company ID only')

    args = parser.parse_args()

    if args.verify:
        verify_migration()
    elif args.company:
        # Migrate single company
        management_db_gen = get_management_db()
        management_db = next(management_db_gen)
        try:
            company = management_db.query(Company).filter(
                Company.id == args.company
            ).first()
            if company and company.database_url:
                result = migrate_company_database(str(company.id), str(company.database_url))
                logger.info(f"\nResult: {result}")
            else:
                logger.error(f"Company {args.company} not found or has no database URL")
        finally:
            management_db.close()
    else:
        run_migration()
