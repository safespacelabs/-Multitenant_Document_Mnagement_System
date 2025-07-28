import asyncio
import aiohttp
import json
from typing import Dict, Optional
from app.config import NEON_API_KEY, NEON_PROJECT_ID
import logging

logger = logging.getLogger(__name__)

class NeonDatabaseService:
    def __init__(self):
        self.api_key = NEON_API_KEY
        self.project_id = NEON_PROJECT_ID
        self.base_url = "https://console.neon.tech/api/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def create_company_database(self, company_id: str, company_name: str) -> Dict[str, str]:
        """
        Create a new database for a company
        Returns database connection details
        """
        database_name = f"company_{company_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                # Create database
                create_db_payload = {
                    "database": {
                        "name": database_name,
                        "owner_name": "neondb_owner"
                    }
                }
                
                async with session.post(
                    f"{self.base_url}/projects/{self.project_id}/databases",
                    headers=self.headers,
                    json=create_db_payload
                ) as response:
                    if response.status == 201:
                        db_data = await response.json()
                        logger.info(f"Created database {database_name} for company {company_id}")
                        
                        # Get connection details
                        connection_details = await self._get_connection_string(database_name)
                        
                        return {
                            "database_name": database_name,
                            "database_url": connection_details["database_url"],
                            "host": connection_details["host"],
                            "port": connection_details["port"],
                            "user": connection_details["user"],
                            "password": connection_details["password"]
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create database for company {company_id}: {error_text}")
                        raise Exception(f"Failed to create database: {error_text}")
                        
        except Exception as e:
            logger.error(f"Error creating database for company {company_id}: {str(e)}")
            raise

    async def _get_connection_string(self, database_name: str) -> Dict[str, str]:
        """
        Get connection string for the database
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Get project connection details
                async with session.get(
                    f"{self.base_url}/projects/{self.project_id}/connection_uri",
                    headers=self.headers,
                    params={"database_name": database_name, "pooled": "true"}
                ) as response:
                    if response.status == 200:
                        connection_data = await response.json()
                        connection_uri = connection_data.get("uri", "")
                        
                        # Parse connection details
                        return self._parse_connection_uri(connection_uri, database_name)
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get connection string: {error_text}")
                        raise Exception(f"Failed to get connection string: {error_text}")
                        
        except Exception as e:
            logger.error(f"Error getting connection string: {str(e)}")
            raise

    def _parse_connection_uri(self, uri: str, database_name: str) -> Dict[str, str]:
        """
        Parse Neon connection URI and return components
        """
        try:
            # Format: postgresql://user:password@host:port/database
            if not uri.startswith("postgresql://"):
                # Fallback: construct from management database URL
                from app.config import MANAGEMENT_DATABASE_URL
                base_uri = MANAGEMENT_DATABASE_URL
                # Replace database name
                if "/" in base_uri:
                    base_part = base_uri.rsplit("/", 1)[0]
                    uri = f"{base_part}/{database_name}"
                else:
                    uri = f"{base_uri}/{database_name}"
            
            # Parse the URI
            parts = uri.replace("postgresql://", "").split("@")
            if len(parts) != 2:
                raise ValueError("Invalid URI format")
                
            user_pass = parts[0]
            host_db = parts[1]
            
            if ":" in user_pass:
                user, password = user_pass.split(":", 1)
            else:
                user = user_pass
                password = ""
                
            if "/" in host_db:
                host_port, _ = host_db.split("/", 1)
            else:
                host_port = host_db
                
            if ":" in host_port:
                host, port = host_port.split(":", 1)
                port = port.split("?")[0]  # Remove query parameters
            else:
                host = host_port
                port = "5432"
            
            # Ensure SSL parameters
            ssl_params = "?sslmode=require&channel_binding=require"
            if "?" not in uri:
                database_url = f"{uri}{ssl_params}"
            else:
                database_url = uri
                
            return {
                "database_url": database_url,
                "host": host,
                "port": port,
                "user": user,
                "password": password
            }
            
        except Exception as e:
            logger.error(f"Error parsing connection URI: {str(e)}")
            raise

    async def delete_company_database(self, database_name: str) -> bool:
        """
        Delete a company's database
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.base_url}/projects/{self.project_id}/databases/{database_name}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully deleted database {database_name}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to delete database {database_name}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error deleting database {database_name}: {str(e)}")
            return False

    async def test_connection(self, database_url: str) -> bool:
        """
        Test database connection
        """
        try:
            from sqlalchemy import create_engine
            engine = create_engine(database_url)
            
            # Test connection
            with engine.connect() as connection:
                from sqlalchemy import text
                connection.execute(text("SELECT 1"))
                return True
                
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False

# Global instance
neon_service = NeonDatabaseService() 