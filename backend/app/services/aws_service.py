import boto3
from botocore.exceptions import ClientError
from typing import BinaryIO
import uuid
from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

class AWSService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    
    async def create_company_bucket(self, company_id: str) -> str:
        """Create S3 bucket for company"""
        bucket_name = f"company-{company_id}-{uuid.uuid4().hex[:8]}"
        try:
            # Handle region-specific bucket creation
            if AWS_REGION == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                )
            
            # Set up bucket policy for multi-tenant isolation
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "CompanyAccess",
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject", "s3:PutObject"],
                        "Resource": f"arn:aws:s3:::{bucket_name}/*",
                        "Condition": {
                            "StringEquals": {
                                "s3:ExistingObjectTag/CompanyId": company_id
                            }
                        }
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=str(bucket_policy)
            )
            
            return bucket_name
        except ClientError as e:
            raise Exception(f"Failed to create S3 bucket: {str(e)}")
    
    async def create_user_folder(self, bucket_name: str, user_id: str) -> str:
        """Create user folder in company bucket"""
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
    
    async def upload_file(
        self, 
        bucket_name: str, 
        file_key: str, 
        file_data: BinaryIO,
        user_id: str,
        company_id: str
    ) -> str:
        """Upload file to S3"""
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
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
            return response['Body'].read()
        except ClientError as e:
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def delete_file(self, bucket_name: str, file_key: str):
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=file_key)
        except ClientError as e:
            raise Exception(f"Failed to delete file: {str(e)}")

aws_service = AWSService() 