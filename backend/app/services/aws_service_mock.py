import uuid
import re
from typing import BinaryIO
import logging

logger = logging.getLogger(__name__)

class MockAWSService:
    """Mock AWS service for testing without real AWS credentials"""
    
    def __init__(self):
        self.created_buckets = set()
        self.uploaded_files = {}
        self.file_contents = {}  # bucket -> {file_key -> file_content}
        logger.info("Using Mock AWS Service - no real S3 operations will be performed")
    
    def _validate_bucket_name(self, bucket_name: str) -> bool:
        """Validate S3 bucket name according to AWS rules"""
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            return False
        
        if not re.match(r'^[a-z0-9.-]+$', bucket_name):
            return False
        
        if not re.match(r'^[a-z0-9].*[a-z0-9]$', bucket_name):
            return False
        
        if '..' in bucket_name:
            return False
        
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', bucket_name):
            return False
        
        if bucket_name.startswith('xn--') or bucket_name.endswith('-s3alias'):
            return False
        
        return True
    
    async def create_company_bucket(self, company_id: str) -> str:
        """Create mock S3 bucket for company"""
        # Clean company_id to make it S3-compliant
        clean_company_id = re.sub(r'[^a-z0-9]', '', company_id.lower())
        
        # Generate a random suffix for uniqueness
        random_suffix = uuid.uuid4().hex[:8]
        
        # Create bucket name with format: company-{clean_id}-{suffix}
        bucket_name = f"company-{clean_company_id}-{random_suffix}"
        
        # Ensure bucket name doesn't exceed 63 characters
        if len(bucket_name) > 63:
            max_company_id_length = 63 - len("company--") - len(random_suffix)
            clean_company_id = clean_company_id[:max_company_id_length]
            bucket_name = f"company-{clean_company_id}-{random_suffix}"
        
        # Validate the final bucket name
        if not self._validate_bucket_name(bucket_name):
            raise ValueError(f"Generated bucket name is invalid: {bucket_name}")
        
        # Simulate bucket creation
        self.created_buckets.add(bucket_name)
        logger.info(f"Mock: Created S3 bucket '{bucket_name}' for company {company_id}")
        
        return bucket_name
    
    async def create_system_admin_bucket(self, bucket_name: str, folder_name: str) -> str:
        """Create mock S3 bucket for system admin"""
        # Clean bucket name to make it S3-compliant (remove underscores and other invalid chars)
        clean_bucket_name = re.sub(r'[^a-z0-9.-]', '-', bucket_name.lower())
        
        # Ensure it doesn't start or end with hyphens
        clean_bucket_name = clean_bucket_name.strip('-')
        
        # Validate the cleaned bucket name
        if not self._validate_bucket_name(clean_bucket_name):
            raise ValueError(f"Generated bucket name is invalid: {clean_bucket_name}")
        
        # Simulate bucket creation
        self.created_buckets.add(clean_bucket_name)
        logger.info(f"Mock: Created system admin S3 bucket '{clean_bucket_name}'")
        
        # Create system admin folder
        folder_key = f"{folder_name}/"
        if clean_bucket_name not in self.uploaded_files:
            self.uploaded_files[clean_bucket_name] = set()
        self.uploaded_files[clean_bucket_name].add(folder_key)
        logger.info(f"Mock: Created system admin folder '{folder_key}' in bucket '{clean_bucket_name}'")
        
        return clean_bucket_name
    
    async def create_user_folder(self, bucket_name: str, user_id: str) -> str:
        """Create mock user folder in company bucket"""
        folder_key = f"users/{user_id}/"
        
        if bucket_name not in self.created_buckets:
            raise Exception(f"Bucket {bucket_name} does not exist")
        
        # Simulate folder creation
        if bucket_name not in self.uploaded_files:
            self.uploaded_files[bucket_name] = set()
        
        self.uploaded_files[bucket_name].add(folder_key)
        logger.info(f"Mock: Created user folder '{folder_key}' in bucket '{bucket_name}'")
        
        return folder_key
    
    async def create_custom_folder(self, bucket_name: str, user_id: str, folder_name: str) -> str:
        """Create mock custom folder within user's directory"""
        # Sanitize folder name to be S3-safe
        safe_folder_name = re.sub(r'[^a-zA-Z0-9_-]', '_', folder_name)
        folder_key = f"users/{user_id}/{safe_folder_name}/"
        
        if bucket_name not in self.created_buckets:
            raise Exception(f"Bucket {bucket_name} does not exist")
        
        # Simulate folder creation
        if bucket_name not in self.uploaded_files:
            self.uploaded_files[bucket_name] = set()
        
        self.uploaded_files[bucket_name].add(folder_key)
        logger.info(f"Mock: Created custom folder '{folder_key}' in bucket '{bucket_name}'")
        
        return folder_key
    
    async def upload_file(
        self, 
        bucket_name: str, 
        file_key: str, 
        file_data: BinaryIO,
        user_id: str,
        company_id: str
    ) -> str:
        """Mock file upload to S3"""
        if bucket_name not in self.created_buckets:
            raise Exception(f"Bucket {bucket_name} does not exist")
        
        # Simulate file upload
        if bucket_name not in self.uploaded_files:
            self.uploaded_files[bucket_name] = set()
        
        if bucket_name not in self.file_contents:
            self.file_contents[bucket_name] = {}
        
        self.uploaded_files[bucket_name].add(file_key)
        
        # Store the actual file content
        file_data.seek(0)
        file_content = file_data.read()
        file_size = len(file_content)
        self.file_contents[bucket_name][file_key] = file_content
        file_data.seek(0)
        
        logger.info(f"Mock: Uploaded file '{file_key}' ({file_size} bytes) to bucket '{bucket_name}'")
        
        return f"s3://{bucket_name}/{file_key}"
    
    async def download_file(self, bucket_name: str, file_key: str) -> bytes:
        """Mock file download from S3"""
        if bucket_name not in self.created_buckets:
            raise Exception(f"Bucket {bucket_name} does not exist")
        
        if bucket_name not in self.uploaded_files or file_key not in self.uploaded_files[bucket_name]:
            raise Exception(f"File {file_key} does not exist in bucket {bucket_name}")
        
        # Return the actual stored file content
        if bucket_name in self.file_contents and file_key in self.file_contents[bucket_name]:
            file_content = self.file_contents[bucket_name][file_key]
            logger.info(f"Mock: Downloaded file '{file_key}' ({len(file_content)} bytes) from bucket '{bucket_name}'")
            return file_content
        else:
            # Fallback to mock content if somehow content wasn't stored
            logger.warning(f"Mock: File content not found for '{file_key}', returning mock content")
            return b"Mock file content"
    
    async def delete_file(self, bucket_name: str, file_key: str):
        """Mock file deletion from S3"""
        if bucket_name not in self.created_buckets:
            raise Exception(f"Bucket {bucket_name} does not exist")
        
        if bucket_name in self.uploaded_files and file_key in self.uploaded_files[bucket_name]:
            self.uploaded_files[bucket_name].remove(file_key)
            # Also remove the stored content
            if bucket_name in self.file_contents and file_key in self.file_contents[bucket_name]:
                del self.file_contents[bucket_name][file_key]
            logger.info(f"Mock: Deleted file '{file_key}' from bucket '{bucket_name}'")
        else:
            logger.warning(f"Mock: File '{file_key}' not found in bucket '{bucket_name}'")
    
    async def delete_company_bucket(self, bucket_name: str) -> bool:
        """Mock deletion of entire S3 bucket and all its contents"""
        if bucket_name not in self.created_buckets:
            logger.warning(f"Mock: Bucket '{bucket_name}' does not exist")
            return False
        
        # Simulate bucket deletion
        self.created_buckets.remove(bucket_name)
        if bucket_name in self.uploaded_files:
            del self.uploaded_files[bucket_name]
        if bucket_name in self.file_contents:
            del self.file_contents[bucket_name]
        
        logger.info(f"Mock: Deleted bucket '{bucket_name}' and all its contents")
        return True
    
    def list_buckets(self) -> list:
        """List all mock buckets (for debugging)"""
        return list(self.created_buckets)
    
    def list_files(self, bucket_name: str) -> list:
        """List all mock files in bucket (for debugging)"""
        if bucket_name not in self.created_buckets:
            return []
        return list(self.uploaded_files.get(bucket_name, set()))

# Create mock instance
mock_aws_service = MockAWSService() 