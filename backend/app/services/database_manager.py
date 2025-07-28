from typing import Dict, Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from app.config import MANAGEMENT_DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        # Management database connection (for companies, users, etc.)
        self.management_engine = create_engine(
            MANAGEMENT_DATABASE_URL,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_MAX_OVERFLOW,
            pool_pre_ping=True
        )
        self.management_session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.management_engine
        )
        
        # Company database connections cache
        self._company_engines: Dict[str, Engine] = {}
        self._company_sessions: Dict[str, sessionmaker] = {}

    def get_management_db(self) -> Generator[Session, None, None]:
        """Get management database session"""
        db = self.management_session_local()
        try:
            yield db
        finally:
            db.close()

    def get_company_engine(self, company_id: str, database_url: str) -> Engine:
        """Get or create engine for company database"""
        if company_id not in self._company_engines:
            logger.info(f"Creating new engine for company {company_id}")
            engine = create_engine(
                database_url,
                pool_size=5,  # Smaller pool size for company databases
                max_overflow=10,
                pool_pre_ping=True
            )
            self._company_engines[company_id] = engine
            self._company_sessions[company_id] = sessionmaker(
                autocommit=False, autoflush=False, bind=engine
            )
        return self._company_engines[company_id]

    def get_company_db(self, company_id: str, database_url: str) -> Generator[Session, None, None]:
        """Get company database session"""
        if company_id not in self._company_sessions:
            self.get_company_engine(company_id, database_url)
        
        session_local = self._company_sessions[company_id]
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    def remove_company_connection(self, company_id: str):
        """Remove company database connection from cache"""
        if company_id in self._company_engines:
            logger.info(f"Removing engine for company {company_id}")
            engine = self._company_engines.pop(company_id)
            engine.dispose()
        
        if company_id in self._company_sessions:
            self._company_sessions.pop(company_id)

    def create_company_tables(self, company_id: str, database_url: str):
        """Create all company tables including E-signature tables dynamically"""
        try:
            engine = self.get_company_engine(company_id, database_url)
            
            # Import company-specific models (includes E-signature models)
            from app.models_company import CompanyBase
            
            # Create all company tables (including E-signature tables)
            CompanyBase.metadata.create_all(bind=engine)
            
            logger.info(f"✅ Created ALL company tables for company {company_id} including E-signature tables")
            
            # Verify E-signature tables were created
            self._verify_esignature_tables(company_id, database_url)
            
        except Exception as e:
            logger.error(f"❌ Error creating tables for company {company_id}: {str(e)}")
            raise

    def _verify_esignature_tables(self, company_id: str, database_url: str):
        """Verify E-signature tables exist for the company"""
        try:
            from sqlalchemy import inspect
            engine = self.get_company_engine(company_id, database_url)
            inspector = inspect(engine)
            
            esignature_tables = [
                'esignature_documents',
                'esignature_recipients', 
                'esignature_audit_logs',
                'workflow_approvals'
            ]
            
            if inspector is not None:
                existing_tables = inspector.get_table_names()
                missing_tables = [table for table in esignature_tables if table not in existing_tables]
            else:
                missing_tables = esignature_tables
            
            if missing_tables:
                logger.warning(f"⚠️ Missing E-signature tables for company {company_id}: {missing_tables}")
                # Force create missing tables
                from app.models_company import CompanyBase
                CompanyBase.metadata.create_all(bind=engine)
                logger.info(f"✅ Force-created missing E-signature tables for company {company_id}")
            else:
                logger.info(f"✅ All E-signature tables exist for company {company_id}")
                
        except Exception as e:
            logger.error(f"❌ Error verifying E-signature tables for company {company_id}: {str(e)}")

    def cleanup_company_database(self, company_id: str):
        """Clean up company database and remove all data (including E-signature data)"""
        try:
            # Remove from cache first
            self.remove_company_connection(company_id)
            
            # Note: In production, you might want to backup data before deletion
            # or implement soft deletion instead of hard deletion
            
            logger.info(f"🧹 Cleaned up database resources for company {company_id}")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up company database {company_id}: {str(e)}")
            raise

    def ensure_esignature_tables_exist(self, company_id: str, database_url: str):
        """Ensure E-signature tables exist for an existing company (migration support)"""
        try:
            logger.info(f"🔍 Checking E-signature tables for company {company_id}")
            
            # Get company database session
            company_db_gen = self.get_company_db(company_id, database_url)
            company_db = next(company_db_gen)
            
            # Check if E-signature tables exist
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
                logger.info(f"📋 Creating missing E-signature tables for company {company_id}: {missing_tables}")
                
                # Import the models to register them
                from app.models_company import CompanyBase
                
                # Create the missing tables
                CompanyBase.metadata.create_all(bind=company_db.bind)
                
                logger.info(f"✅ E-signature tables created for company {company_id}")
            else:
                logger.info(f"✅ All E-signature tables already exist for company {company_id}")
                
            company_db.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error ensuring E-signature tables for company {company_id}: {str(e)}")
            return False

    def test_company_connection(self, company_id: str, database_url: str) -> bool:
        """Test company database connection"""
        try:
            engine = self.get_company_engine(company_id, database_url)
            with engine.connect() as connection:
                from sqlalchemy import text
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Connection test failed for company {company_id}: {str(e)}")
            return False

# Global database manager instance
db_manager = DatabaseManager() 