import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import BinaryIO
import uuid
import json
import re
import logging
from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

logger = logging.getLogger(__name__)

# Import mock service
from .aws_service_mock import mock_aws_service

class AWSService:
    def __init__(self):
        try:
            # Check if AWS credentials are available
            if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
                raise NoCredentialsError()
                
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
            # Test credentials by listing buckets
            self.s3_client.list_buckets()
            self.use_mock = False
            logger.info("Using real AWS S3 service")
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"AWS credentials not available or invalid: {e}. Using mock service.")
            self.use_mock = True
            self.mock_service = mock_aws_service
    
    def _validate_bucket_name(self, bucket_name: str) -> bool:
        """Validate S3 bucket name according to AWS rules"""
        # S3 bucket naming rules:
        # - 3-63 characters long
        # - Only lowercase letters, numbers, dots (.), and hyphens (-)
        # - Must begin and end with a letter or number
        # - Cannot contain two adjacent periods
        # - Cannot be formatted as an IP address
        
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            return False
        
        # Check for valid characters only (lowercase letters, numbers, dots, hyphens)
        if not re.match(r'^[a-z0-9.-]+$', bucket_name):
            return False
        
        # Must begin and end with letter or number
        if not re.match(r'^[a-z0-9].*[a-z0-9]$', bucket_name):
            return False
        
        # Cannot contain two adjacent periods
        if '..' in bucket_name:
            return False
        
        # Cannot be formatted as an IP address (simplified check)
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', bucket_name):
            return False
        
        # Additional AWS restrictions
        if bucket_name.startswith('xn--') or bucket_name.endswith('-s3alias'):
            return False
        
        return True
    
    async def create_company_bucket(self, company_id: str) -> str:
        """Create S3 bucket for company"""
        if self.use_mock:
            return await self.mock_service.create_company_bucket(company_id)
            
        # Clean company_id to make it S3-compliant
        # Remove any non-alphanumeric characters and convert to lowercase
        clean_company_id = re.sub(r'[^a-z0-9]', '', company_id.lower())
        
        # Generate a random suffix for uniqueness
        random_suffix = uuid.uuid4().hex[:8]
        
        # Create bucket name with format: company-{clean_id}-{suffix}
        bucket_name = f"company-{clean_company_id}-{random_suffix}"
        
        # Ensure bucket name doesn't exceed 63 characters
        if len(bucket_name) > 63:
            # Calculate maximum length for company_id part
            max_company_id_length = 63 - len("company--") - len(random_suffix)
            clean_company_id = clean_company_id[:max_company_id_length]
            bucket_name = f"company-{clean_company_id}-{random_suffix}"
        
        # Validate the final bucket name
        if not self._validate_bucket_name(bucket_name):
            raise ValueError(f"Generated bucket name is invalid: {bucket_name}")
        
        try:
            # Create bucket with proper region handling
            if AWS_REGION == 'us-east-1':
                # us-east-1 is the default region and doesn't need LocationConstraint
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                # All other regions require LocationConstraint
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                )
            
            # Enable versioning for better data protection
            try:
                self.s3_client.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
            except ClientError as versioning_error:
                # Versioning failure shouldn't prevent bucket creation
                print(f"Warning: Could not enable versioning for bucket {bucket_name}: {versioning_error}")
            
            # Set up bucket encryption for security
            try:
                self.s3_client.put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        'Rules': [
                            {
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': 'AES256'
                                }
                            }
                        ]
                    }
                )
            except ClientError as encryption_error:
                # Encryption failure shouldn't prevent bucket creation
                print(f"Warning: Could not enable encryption for bucket {bucket_name}: {encryption_error}")
            
            # Block public access for security
            try:
                self.s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
            except ClientError as public_access_error:
                # Public access block failure shouldn't prevent bucket creation
                print(f"Warning: Could not set public access block for bucket {bucket_name}: {public_access_error}")
            
            return bucket_name
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'BucketAlreadyExists':
                # Try again with a different random suffix
                return await self.create_company_bucket(company_id)
            elif error_code == 'InvalidBucketName':
                raise Exception(f"Invalid bucket name '{bucket_name}': {error_message}")
            else:
                raise Exception(f"Failed to create S3 bucket '{bucket_name}': {error_message}")
        except Exception as e:
            raise Exception(f"Failed to create S3 bucket: {str(e)}")

    async def create_system_admin_bucket(self, bucket_name: str, folder_name: str) -> str:
        """Create S3 bucket for system admin"""
        if self.use_mock:
            return await self.mock_service.create_system_admin_bucket(bucket_name, folder_name)
            
        # Clean bucket name to make it S3-compliant (remove underscores and other invalid chars)
        clean_bucket_name = re.sub(r'[^a-z0-9.-]', '-', bucket_name.lower())
        
        # Ensure it doesn't start or end with hyphens
        clean_bucket_name = clean_bucket_name.strip('-')
        
        # Validate the cleaned bucket name
        if not self._validate_bucket_name(clean_bucket_name):
            raise ValueError(f"Invalid bucket name: {clean_bucket_name}")
        
        try:
            # Create bucket with proper region handling
            if AWS_REGION == 'us-east-1':
                # us-east-1 is the default region and doesn't need LocationConstraint
                self.s3_client.create_bucket(Bucket=clean_bucket_name)
            else:
                # All other regions require LocationConstraint
                self.s3_client.create_bucket(
                    Bucket=clean_bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                )
            
            # Enable versioning for better data protection
            try:
                self.s3_client.put_bucket_versioning(
                    Bucket=clean_bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
            except ClientError as versioning_error:
                print(f"Warning: Could not enable versioning for bucket {clean_bucket_name}: {versioning_error}")
            
            # Set up bucket encryption for security
            try:
                self.s3_client.put_bucket_encryption(
                    Bucket=clean_bucket_name,
                    ServerSideEncryptionConfiguration={
                        'Rules': [
                            {
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': 'AES256'
                                }
                            }
                        ]
                    }
                )
            except ClientError as encryption_error:
                print(f"Warning: Could not enable encryption for bucket {clean_bucket_name}: {encryption_error}")
            
            # Block public access for security
            try:
                self.s3_client.put_public_access_block(
                    Bucket=clean_bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
            except ClientError as public_access_error:
                print(f"Warning: Could not set public access block for bucket {clean_bucket_name}: {public_access_error}")
            
            # Create system admin folder
            folder_key = f"{folder_name}/"
            try:
                self.s3_client.put_object(
                    Bucket=clean_bucket_name,
                    Key=folder_key,
                    Body=b'',
                    Tagging="Type=SystemAdmin"
                )
            except ClientError as folder_error:
                print(f"Warning: Could not create system admin folder: {folder_error}")
            
            return clean_bucket_name
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'BucketAlreadyExists':
                # Bucket already exists, which is fine for system admin
                return clean_bucket_name
            elif error_code == 'InvalidBucketName':
                raise Exception(f"Invalid bucket name '{clean_bucket_name}': {error_message}")
            else:
                raise Exception(f"Failed to create system admin S3 bucket '{clean_bucket_name}': {error_message}")
        except Exception as e:
            raise Exception(f"Failed to create system admin S3 bucket: {str(e)}")
    
    async def create_user_folder(self, bucket_name: str, user_id: str) -> str:
        """Create user folder in company bucket"""
        if self.use_mock:
            return await self.mock_service.create_user_folder(bucket_name, user_id)
            
        folder_key = f"users/{user_id}/"
        try:
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=folder_key,
                Body=b'',
                Tagging=f"UserId={user_id}"
            )
            return folder_key
        except ClientError as e:
            raise Exception(f"Failed to create user folder: {str(e)}")
    
    async def create_custom_folder(self, bucket_name: str, user_id: str, folder_name: str) -> str:
        """Create a custom folder within user's directory"""
        if self.use_mock:
            return await self.mock_service.create_custom_folder(bucket_name, user_id, folder_name)
            
        # Sanitize folder name to be S3-safe
        safe_folder_name = re.sub(r'[^a-zA-Z0-9_-]', '_', folder_name)
        folder_key = f"users/{user_id}/{safe_folder_name}/"
        
        try:
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=folder_key,
                Body=b'',
                Tagging=f"UserId={user_id}&FolderName={safe_folder_name}"
            )
            return folder_key
        except ClientError as e:
            raise Exception(f"Failed to create custom folder: {str(e)}")
    
    async def upload_file(
        self, 
        bucket_name: str, 
        file_key: str, 
        file_data: BinaryIO,
        user_id: str,
        company_id: str
    ) -> str:
        """Upload file to S3"""
        if self.use_mock:
            return await self.mock_service.upload_file(bucket_name, file_key, file_data, user_id, company_id)
            
        try:
            self.s3_client.upload_fileobj(
                file_data,
                bucket_name,
                file_key,
                ExtraArgs={
                    'Tagging': f'UserId={user_id}&CompanyId={company_id}'
                }
            )
            return f"s3://{bucket_name}/{file_key}"
        except ClientError as e:
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def download_file(self, bucket_name: str, file_key: str) -> bytes:
        """Download file from S3"""
        if self.use_mock:
            return await self.mock_service.download_file(bucket_name, file_key)
            
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
            return response['Body'].read()
        except ClientError as e:
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def delete_file(self, bucket_name: str, file_key: str):
        """Delete file from S3"""
        if self.use_mock:
            return await self.mock_service.delete_file(bucket_name, file_key)
            
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=file_key)
        except ClientError as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
    async def delete_company_bucket(self, bucket_name: str) -> bool:
        """Delete entire S3 bucket and all its contents"""
        if self.use_mock:
            return await self.mock_service.delete_company_bucket(bucket_name)
            
        try:
            # First, delete all objects in the bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            
            for page in pages:
                if 'Contents' in page:
                    objects = [{'Key': obj['Key']} for obj in page['Contents']]
                    if objects:
                        self.s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': objects}
                        )
            
            # Then delete the bucket itself
            self.s3_client.delete_bucket(Bucket=bucket_name)
            return True
            
        except ClientError as e:
            print(f"Failed to delete bucket {bucket_name}: {str(e)}")
            return False
        except Exception as e:
            print(f"Failed to delete bucket {bucket_name}: {str(e)}")
            return False

# Create service instance that automatically falls back to mock if needed
aws_service = AWSService() 