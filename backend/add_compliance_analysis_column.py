"""
Migration script to add compliance_analysis JSON column to document_analysis table
This column stores AI-generated compliance analysis with detailed reasons
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import get_management_db
from app.models import Company
from app.config import DATABASE_URL

def add_compliance_analysis_column():
    """Add compliance_analysis JSON column to all company databases"""

    print("[MIGRATION] Starting: Adding compliance_analysis column to document_analysis table")

    # Connect to management database
    management_engine = create_engine(DATABASE_URL)
    ManagementSessionLocal = sessionmaker(bind=management_engine)
    management_db = ManagementSessionLocal()

    try:
        # Get all companies
        companies = management_db.query(Company).filter(Company.is_active == True).all()
        print(f"\n[INFO] Found {len(companies)} active companies")

        success_count = 0
        error_count = 0
        already_exists_count = 0

        for company in companies:
            try:
                print(f"\n[COMPANY] Processing: {company.name} (ID: {company.id})")

                # Connect to company database
                company_engine = create_engine(company.database_url)

                # Check if document_analysis table exists
                check_table_query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'document_analysis'
                    );
                """)

                with company_engine.connect() as conn:
                    result = conn.execute(check_table_query)
                    table_exists = result.scalar()

                    if not table_exists:
                        print(f"   [WARNING] Table document_analysis does not exist, skipping...")
                        continue

                    # Check if column already exists
                    check_column_query = text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_name = 'document_analysis'
                            AND column_name = 'compliance_analysis'
                        );
                    """)

                    result = conn.execute(check_column_query)
                    column_exists = result.scalar()

                    if column_exists:
                        print(f"   [SUCCESS] Column compliance_analysis already exists")
                        already_exists_count += 1
                        continue

                    # Add the column
                    print(f"   [ACTION] Adding compliance_analysis column...")

                    # PostgreSQL JSON column
                    alter_query = text("""
                        ALTER TABLE document_analysis
                        ADD COLUMN compliance_analysis JSON;
                    """)

                    conn.execute(alter_query)
                    conn.commit()

                    print(f"   [SUCCESS] Successfully added compliance_analysis column")
                    success_count += 1

            except Exception as e:
                print(f"   [ERROR] Error processing {company.name}: {str(e)}")
                error_count += 1
                continue

        print(f"\n" + "="*60)
        print(f"[SUMMARY] Migration Summary:")
        print(f"   [SUCCESS] Successfully migrated: {success_count} companies")
        print(f"   [INFO] Already had column: {already_exists_count} companies")
        print(f"   [ERROR] Errors: {error_count} companies")
        print(f"   [TOTAL] Total processed: {len(companies)} companies")
        print("="*60)

    except Exception as e:
        print(f"\n[FATAL] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        management_db.close()

    print("\n[COMPLETE] Migration completed!")

if __name__ == "__main__":
    add_compliance_analysis_column()
