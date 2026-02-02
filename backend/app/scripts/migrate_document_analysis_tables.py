"""
Migration Script: Add Document Analysis Tables to Existing Company Databases

This script adds the following tables to all existing company databases:
- document_analysis
- expiry_notifications
- chat_documents
- chat_messages
- expiry_agent_runs
- expiry_agent_config
- hr_chat_actions
- bulk_user_imports

Run this script once after deploying the new expiry agent and HR chatbot features.

Usage:
    cd backend
    python -m app.scripts.migrate_document_analysis_tables
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from sqlalchemy import inspect
from app.database import get_management_db, get_company_db
from app.models import Company
from app.models_document_analysis import Base as DocumentAnalysisBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Tables that should exist after migration
REQUIRED_TABLES = [
    'document_analysis',
    'expiry_notifications',
    'chat_documents',
    'chat_messages',
    'expiry_agent_runs',
    'expiry_agent_config',
    'hr_chat_actions',
    'bulk_user_imports'
]


def get_missing_tables(engine) -> list:
    """Check which tables are missing from the database"""
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        missing = [table for table in REQUIRED_TABLES if table not in existing_tables]
        return missing
    except Exception as e:
        logger.error(f"Error inspecting tables: {e}")
        return REQUIRED_TABLES  # Assume all missing if inspection fails


def migrate_company_database(company_id: str, database_url: str) -> dict:
    """
    Migrate a single company database to add document analysis tables

    Returns:
        dict with migration results
    """
    result = {
        'company_id': company_id,
        'status': 'pending',
        'tables_created': [],
        'tables_existed': [],
        'error': None
    }

    try:
        # Get company database connection
        company_db_gen = get_company_db(company_id, database_url)
        company_db = next(company_db_gen)

        try:
            engine = company_db.bind

            # Check which tables are missing
            missing_tables = get_missing_tables(engine)

            if not missing_tables:
                result['status'] = 'skipped'
                result['tables_existed'] = REQUIRED_TABLES
                logger.info(f"  Company {company_id}: All tables already exist, skipping")
                return result

            # Create missing tables
            logger.info(f"  Company {company_id}: Creating tables: {missing_tables}")
            DocumentAnalysisBase.metadata.create_all(bind=engine)

            # Verify tables were created
            still_missing = get_missing_tables(engine)

            if still_missing:
                result['status'] = 'partial'
                result['tables_created'] = [t for t in missing_tables if t not in still_missing]
                result['error'] = f"Failed to create: {still_missing}"
                logger.warning(f"  Company {company_id}: Partial migration - missing: {still_missing}")
            else:
                result['status'] = 'success'
                result['tables_created'] = missing_tables
                result['tables_existed'] = [t for t in REQUIRED_TABLES if t not in missing_tables]
                logger.info(f"  Company {company_id}: Successfully created {len(missing_tables)} tables")

        finally:
            company_db.close()

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        logger.error(f"  Company {company_id}: Error - {e}")

    return result


def run_migration():
    """Run migration for all active companies"""
    logger.info("=" * 60)
    logger.info("Document Analysis Tables Migration Script")
    logger.info("=" * 60)

    # Get management database
    management_db_gen = get_management_db()
    management_db = next(management_db_gen)

    try:
        # Get all active companies
        companies = management_db.query(Company).filter(
            Company.is_active == True
        ).all()

        logger.info(f"\nFound {len(companies)} active companies to migrate\n")

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
            logger.info(f"[{i}/{len(companies)}] Migrating company: {company.name} ({company.id})")

            if not company.database_url:
                logger.warning(f"  Skipping - no database URL configured")
                stats['error'] += 1
                results.append({
                    'company_id': str(company.id),
                    'company_name': company.name,
                    'status': 'error',
                    'error': 'No database URL'
                })
                continue

            result = migrate_company_database(str(company.id), str(company.database_url))
            result['company_name'] = company.name
            results.append(result)

            stats[result['status']] += 1

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Total companies: {stats['total']}")
        logger.info(f"  Successful:    {stats['success']}")
        logger.info(f"  Skipped:       {stats['skipped']} (tables already exist)")
        logger.info(f"  Partial:       {stats['partial']}")
        logger.info(f"  Errors:        {stats['error']}")

        # Print detailed results for failures
        failures = [r for r in results if r['status'] in ['error', 'partial']]
        if failures:
            logger.info("\nFailed/Partial Migrations:")
            for r in failures:
                logger.info(f"  - {r.get('company_name', 'Unknown')} ({r['company_id']}): {r.get('error', 'Unknown error')}")

        logger.info("\n" + "=" * 60)
        logger.info("Migration Complete!")
        logger.info("=" * 60)

        return results

    finally:
        management_db.close()


def verify_migration():
    """Verify migration was successful for all companies"""
    logger.info("\n" + "=" * 60)
    logger.info("Verifying Migration")
    logger.info("=" * 60)

    management_db_gen = get_management_db()
    management_db = next(management_db_gen)

    try:
        companies = management_db.query(Company).filter(
            Company.is_active == True
        ).all()

        all_good = True

        for company in companies:
            if not company.database_url:
                continue

            try:
                company_db_gen = get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)

                try:
                    missing = get_missing_tables(company_db.bind)
                    if missing:
                        logger.warning(f"  {company.name}: Missing tables - {missing}")
                        all_good = False
                    else:
                        logger.info(f"  {company.name}: OK")
                finally:
                    company_db.close()

            except Exception as e:
                logger.error(f"  {company.name}: Error - {e}")
                all_good = False

        if all_good:
            logger.info("\nAll companies have required tables!")
        else:
            logger.warning("\nSome companies are missing tables. Run migration again.")

    finally:
        management_db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Migrate document analysis tables')
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
                logger.info(f"Result: {result}")
            else:
                logger.error(f"Company {args.company} not found or has no database URL")
        finally:
            management_db.close()
    else:
        run_migration()
