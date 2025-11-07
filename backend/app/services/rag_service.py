"""
RAG Service Client for Document Extraction & QA Integration

This service integrates the advanced RAG (Retrieval Augmented Generation) capabilities
from the deployed document extraction service with the multi-tenant document management system.

Key Features:
- Vector similarity search with embeddings
- Hybrid search (BM25 + vector)
- Cross-encoder re-ranking
- I9 document validation
- Multi-tenant support via company_id:user_id mapping
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# URL of the deployed document extraction service
RAG_SERVICE_URL = os.getenv(
    "RAG_SERVICE_URL",
    "https://document-uploadation-with-qa-backend.onrender.com"
)

# Timeout for RAG service requests (in seconds)
RAG_REQUEST_TIMEOUT = 30.0


class RAGService:
    """Client for the Document Extraction & QA RAG service"""

    def __init__(self, service_url: str = RAG_SERVICE_URL):
        self.service_url = service_url.rstrip('/')
        self.timeout = httpx.Timeout(RAG_REQUEST_TIMEOUT, connect=10.0)

    def _get_tenant_id(self, company_id: str, user_id: Optional[str] = None) -> str:
        """
        Generate a unique tenant identifier for multi-tenant separation.

        Format: company_{company_id}

        NOTE: We use company-level isolation (not user-level) so that all users
        within a company can access all company documents. This allows:
        - Users to find documents uploaded by other users in their company
        - Better collaboration within teams
        - Persistent document access after page refresh

        The user_id parameter is kept for backwards compatibility but not used
        in the tenant ID generation.
        """
        return f"company_{company_id}"

    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        company_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a document to the RAG service for processing.

        Args:
            file_content: Binary content of the document
            filename: Original filename
            company_id: Company identifier for tenant isolation
            user_id: Optional user identifier (stored in metadata only, not used for isolation)
            metadata: Optional metadata to associate with the document

        Returns:
            Dictionary with document_id and ingestion status

        Note: Uses company-level tenant ID so all users in the company can access the document.
        """
        tenant_id = self._get_tenant_id(company_id, user_id)

        logger.info(f"📤 Uploading to RAG with tenant_id: {tenant_id} (company: {company_id}, user: {user_id})")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {'file': (filename, file_content)}
                data = {'user_id': tenant_id}

                if metadata:
                    data['metadata'] = str(metadata)

                response = await client.post(
                    f"{self.service_url}/documents/upload",
                    files=files,
                    data=data
                )
                response.raise_for_status()

                result = response.json()
                logger.info(f"Document uploaded to RAG service: {result.get('document_id')} for tenant {tenant_id}")

                return result

        except httpx.HTTPError as e:
            logger.error(f"Failed to upload document to RAG service: {str(e)}")
            raise Exception(f"RAG service upload failed: {str(e)}")

    async def query_documents(
        self,
        question: str,
        company_id: str,
        user_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        document_names: Optional[List[str]] = None,
        limit: int = 12
    ) -> Dict[str, Any]:
        """
        Query documents using advanced RAG with vector similarity search.

        Args:
            question: User's question
            company_id: Company identifier for tenant isolation
            user_id: Optional user identifier (not used for isolation, kept for compatibility)
            document_ids: Optional list of specific document IDs to query
            document_names: Optional list of specific document filenames to query
            limit: Maximum number of chunks to retrieve (default: 12)

        Returns:
            Dictionary with answer, contexts, and debug information

        Note: Uses company-level tenant ID to search ALL company documents, not just user's documents.
        This allows finding documents uploaded by any user in the company.
        """
        tenant_id = self._get_tenant_id(company_id, user_id)

        logger.info(f"🔍 Querying RAG with tenant_id: {tenant_id} (company: {company_id}, user: {user_id})")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "user_id": tenant_id,
                    "question": question,
                    "limit": limit
                }

                # Add document filters if specified
                if document_ids:
                    if len(document_ids) == 1:
                        payload["document_id"] = document_ids[0]
                    else:
                        payload["document_ids"] = document_ids

                if document_names:
                    if len(document_names) == 1:
                        payload["document_name"] = document_names[0]
                    else:
                        payload["document_names"] = document_names

                response = await client.post(
                    f"{self.service_url}/query",
                    json=payload
                )
                response.raise_for_status()

                result = response.json()
                logger.info(f"RAG query successful for tenant {tenant_id}: {result.get('debug', {}).get('total_chunks', 0)} chunks retrieved")

                return result

        except httpx.HTTPError as e:
            logger.error(f"Failed to query RAG service: {str(e)}")
            raise Exception(f"RAG service query failed: {str(e)}")

    async def get_document_status(
        self,
        document_id: str,
        company_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check the processing status of a document.

        Args:
            document_id: Document ID from RAG service
            company_id: Company identifier
            user_id: Optional user identifier

        Returns:
            Dictionary with document status information
        """
        tenant_id = self._get_tenant_id(company_id, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.service_url}/documents/status",
                    params={
                        "document_id": document_id,
                        "user_id": tenant_id
                    }
                )
                response.raise_for_status()

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to get document status from RAG service: {str(e)}")
            raise Exception(f"RAG service status check failed: {str(e)}")

    async def list_documents(
        self,
        company_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all documents for a tenant in the RAG service.

        Args:
            company_id: Company identifier
            user_id: Optional user identifier

        Returns:
            List of document metadata dictionaries
        """
        tenant_id = self._get_tenant_id(company_id, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.service_url}/documents",
                    params={"user_id": tenant_id}
                )
                response.raise_for_status()

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to list documents from RAG service: {str(e)}")
            raise Exception(f"RAG service list failed: {str(e)}")

    async def delete_document(
        self,
        document_id: str,
        company_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a document from the RAG service.

        Args:
            document_id: Document ID from RAG service
            company_id: Company identifier
            user_id: Optional user identifier

        Returns:
            Confirmation dictionary
        """
        tenant_id = self._get_tenant_id(company_id, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.service_url}/documents/{document_id}",
                    params={"user_id": tenant_id}
                )
                response.raise_for_status()

                logger.info(f"Document deleted from RAG service: {document_id} for tenant {tenant_id}")

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to delete document from RAG service: {str(e)}")
            raise Exception(f"RAG service delete failed: {str(e)}")

    # I9 Document Validation Methods

    async def get_i9_summary(
        self,
        company_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get I9 compliance summary for a tenant.

        Args:
            company_id: Company identifier
            user_id: Optional user identifier

        Returns:
            I9 compliance summary
        """
        tenant_id = self._get_tenant_id(company_id, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.service_url}/i9/summary",
                    params={"user_id": tenant_id}
                )
                response.raise_for_status()

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to get I9 summary from RAG service: {str(e)}")
            raise Exception(f"RAG service I9 summary failed: {str(e)}")

    async def get_expiring_i9_documents(
        self,
        company_id: str,
        days: int = 30,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get I9 documents expiring within specified days.

        Args:
            company_id: Company identifier
            days: Number of days ahead to check (default: 30)
            user_id: Optional user identifier

        Returns:
            List of expiring I9 documents
        """
        tenant_id = self._get_tenant_id(company_id, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.service_url}/i9/expiring",
                    params={
                        "user_id": tenant_id,
                        "days": days
                    }
                )
                response.raise_for_status()

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to get expiring I9 documents from RAG service: {str(e)}")
            raise Exception(f"RAG service I9 expiring query failed: {str(e)}")

    async def get_expired_i9_documents(
        self,
        company_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get expired I9 documents.

        Args:
            company_id: Company identifier
            user_id: Optional user identifier

        Returns:
            List of expired I9 documents
        """
        tenant_id = self._get_tenant_id(company_id, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.service_url}/i9/expired",
                    params={"user_id": tenant_id}
                )
                response.raise_for_status()

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to get expired I9 documents from RAG service: {str(e)}")
            raise Exception(f"RAG service I9 expired query failed: {str(e)}")

    async def get_invalid_i9_documents(
        self,
        company_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get invalid I9 documents.

        Args:
            company_id: Company identifier
            user_id: Optional user identifier

        Returns:
            List of invalid I9 documents
        """
        tenant_id = self._get_tenant_id(company_id, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.service_url}/i9/invalid",
                    params={"user_id": tenant_id}
                )
                response.raise_for_status()

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to get invalid I9 documents from RAG service: {str(e)}")
            raise Exception(f"RAG service I9 invalid query failed: {str(e)}")

    async def query_i9_documents(
        self,
        question: str,
        company_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query I9 documents with natural language questions.

        This is a specialized query that handles I9-specific questions like:
        - "Which passports are expiring soon?"
        - "Show me all invalid visas"
        - "Is my green card still valid?"

        Args:
            question: Natural language question about I9 documents
            company_id: Company identifier
            user_id: Optional user identifier

        Returns:
            Answer with I9 document information
        """
        # Use the regular query endpoint but add I9 context
        return await self.query_documents(
            question=question,
            company_id=company_id,
            user_id=user_id
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the RAG service is available.

        Returns:
            Health status dictionary
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{self.service_url}/health")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"RAG service health check failed: {str(e)}")
            return {"status": "unavailable", "error": str(e)}

    async def models_health_check(self) -> Dict[str, Any]:
        """
        Check the status of ML models in the RAG service.

        Returns:
            Models health status dictionary
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.get(f"{self.service_url}/health/models")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"RAG service models health check failed: {str(e)}")
            return {"status": "unavailable", "error": str(e)}


# Create singleton instance
rag_service = RAGService()
