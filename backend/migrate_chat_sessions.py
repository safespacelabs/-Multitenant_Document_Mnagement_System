"""
Migration script to add ChatSession tables to all existing company databases.
Run this once to update production databases with the new session management tables.

Usage:
    python migrate_chat_sessions.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from app.database import get_management_db
from app import models
from app.models_company import CompanyBase, ChatSession, ChatHistory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_table_exists(engine, table_name):
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def migrate_company_database(company_id, database_url):
    """Add ChatSession table to a company database"""
    try:
        logger.info(f"Migrating company {company_id}...")
        engine = create_engine(database_url)

        # Check if tables already exist
        has_sessions = check_table_exists(engine, 'chat_sessions')

        if has_sessions:
            logger.info(f"  ✅ Company {company_id} already has chat_sessions table")
        else:
            logger.info(f"  📝 Creating chat_sessions table for company {company_id}...")

            # Create only the ChatSession table
            ChatSession.__table__.create(engine, checkfirst=True)
            logger.info(f"  ✅ Created chat_sessions table")

        # Check and update ChatHistory table to add session_id column if missing
        with engine.connect() as conn:
            # Check if session_id column exists in chat_history
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='chat_history' AND column_name='session_id'
            """))

            if not result.fetchone():
                logger.info(f"  📝 Adding session_id column to chat_history...")
                conn.execute(text("""
                    ALTER TABLE chat_history
                    ADD COLUMN session_id VARCHAR;
                """))
                conn.commit()
                logger.info(f"  ✅ Added session_id column to chat_history")
            else:
                logger.info(f"  ✅ chat_history already has session_id column")

        # Update User table to add chat_sessions relationship (no DB change needed, just ORM)
        logger.info(f"  ✅ Company {company_id} migration complete")

        engine.dispose()
        return True

    except Exception as e:
        logger.error(f"  ❌ Failed to migrate company {company_id}: {str(e)}")
        return False


def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("Starting Chat Session Migration")
    logger.info("=" * 60)

    # Get management database
    management_db = next(get_management_db())

    try:
        # Get all companies
        companies = management_db.query(models.Company).all()
        logger.info(f"\nFound {len(companies)} companies to migrate")

        success_count = 0
        fail_count = 0

        for company in companies:
            if company.database_url:
                success = migrate_company_database(company.id, company.database_url)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            else:
                logger.warning(f"⚠️  Company {company.id} ({company.name}) has no database_url, skipping")

        logger.info("\n" + "=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"✅ Successfully migrated: {success_count} companies")
        if fail_count > 0:
            logger.info(f"❌ Failed to migrate: {fail_count} companies")
        logger.info("\n✅ Migration complete!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        management_db.close()


if __name__ == "__main__":
    main()
