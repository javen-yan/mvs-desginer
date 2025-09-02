"""
S3 storage service for file management.
"""
import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from io import BytesIO
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from werkzeug.datastructures import FileStorage

from app.config import Config


logger = logging.getLogger(__name__)


class S3Service:
    """Service for managing S3 object storage operations."""
    
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, 
                 region: str, bucket_name: str, use_ssl: bool = True):
        """
        Initialize S3 service.
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region: AWS region
            bucket_name: S3 bucket name
            use_ssl: Whether to use SSL for connections
        """
        self.bucket_name = bucket_name
        self.region = region
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region,
                use_ssl=use_ssl
            )
            
            # Test connection
            self._test_connection()
            logger.info(f"S3 service initialized successfully for bucket: {bucket_name}")
            
        except (NoCredentialsError, ClientError) as e:
            logger.error(f"Failed to initialize S3 service: {e}")
            raise
    
    def _test_connection(self) -> None:
        """Test S3 connection and bucket access."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise ValueError(f"Bucket '{self.bucket_name}' does not exist")
            elif error_code == '403':
                raise ValueError(f"Access denied to bucket '{self.bucket_name}'")
            else:
                raise ValueError(f"Error accessing bucket '{self.bucket_name}': {e}")
    
    def upload_file(self, file_obj: FileStorage, key: str, 
                   content_type: Optional[str] = None, 
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload a file to S3.
        
        Args:
            file_obj: File object to upload
            key: S3 object key
            content_type: MIME type of the file
            metadata: Additional metadata for the object
            
        Returns:
            Dictionary containing upload result information
        """
        try:
            # Prepare upload parameters
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': key,
                'Body': file_obj.stream
            }
            
            if content_type:
                upload_params['ContentType'] = content_type
            
            if metadata:
                upload_params['Metadata'] = metadata
            
            # Upload file
            self.s3_client.upload_fileobj(**upload_params)
            
            # Get object info
            object_info = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            
            return {
                'success': True,
                'key': key,
                'size': object_info['ContentLength'],
                'etag': object_info['ETag'].strip('"'),
                'last_modified': object_info['LastModified'].isoformat(),
                'url': self.get_object_url(key)
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_local_file(self, local_path: str, key: str, 
                         content_type: Optional[str] = None,
                         metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload a local file to S3.
        
        Args:
            local_path: Path to local file
            key: S3 object key
            content_type: MIME type of the file
            metadata: Additional metadata for the object
            
        Returns:
            Dictionary containing upload result information
        """
        try:
            if not os.path.exists(local_path):
                return {
                    'success': False,
                    'error': f'Local file not found: {local_path}'
                }
            
            # Prepare upload parameters
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': key,
                'Filename': local_path
            }
            
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = metadata
            
            if extra_args:
                upload_params['ExtraArgs'] = extra_args
            
            # Upload file
            self.s3_client.upload_file(**upload_params)
            
            # Get object info
            object_info = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            
            return {
                'success': True,
                'key': key,
                'size': object_info['ContentLength'],
                'etag': object_info['ETag'].strip('"'),
                'last_modified': object_info['LastModified'].isoformat(),
                'url': self.get_object_url(key)
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload local file to S3: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, key: str, local_path: str) -> Dict[str, Any]:
        """
        Download a file from S3 to local path.
        
        Args:
            key: S3 object key
            local_path: Local path to save the file
            
        Returns:
            Dictionary containing download result information
        """
        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.s3_client.download_file(self.bucket_name, key, local_path)
            
            return {
                'success': True,
                'key': key,
                'local_path': local_path,
                'size': os.path.getsize(local_path)
            }
            
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_object(self, key: str) -> Dict[str, Any]:
        """
        Delete an object from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            Dictionary containing deletion result information
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            
            return {
                'success': True,
                'key': key,
                'message': 'Object deleted successfully'
            }
            
        except ClientError as e:
            logger.error(f"Failed to delete object from S3: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_objects(self, keys: List[str]) -> Dict[str, Any]:
        """
        Delete multiple objects from S3.
        
        Args:
            keys: List of S3 object keys
            
        Returns:
            Dictionary containing deletion result information
        """
        try:
            delete_dict = {
                'Objects': [{'Key': key} for key in keys]
            }
            
            response = self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete=delete_dict
            )
            
            deleted = response.get('Deleted', [])
            errors = response.get('Errors', [])
            
            return {
                'success': len(errors) == 0,
                'deleted_count': len(deleted),
                'error_count': len(errors),
                'errors': errors
            }
            
        except ClientError as e:
            logger.error(f"Failed to delete objects from S3: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_objects(self, prefix: str = '', max_keys: int = 1000) -> Dict[str, Any]:
        """
        List objects in S3 bucket.
        
        Args:
            prefix: Object key prefix to filter by
            max_keys: Maximum number of objects to return
            
        Returns:
            Dictionary containing list of objects
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"')
                })
            
            return {
                'success': True,
                'objects': objects,
                'count': len(objects),
                'truncated': response.get('IsTruncated', False)
            }
            
        except ClientError as e:
            logger.error(f"Failed to list objects from S3: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_object_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for an S3 object.
        
        Args:
            key: S3 object key
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return ''
    
    def get_upload_url(self, key: str, content_type: str = None, 
                      expires_in: int = 3600) -> Dict[str, Any]:
        """
        Generate a presigned URL for uploading to S3.
        
        Args:
            key: S3 object key
            content_type: MIME type of the file
            expires_in: URL expiration time in seconds
            
        Returns:
            Dictionary containing presigned URL and fields
        """
        try:
            conditions = []
            if content_type:
                conditions.append({"Content-Type": content_type})
            
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=key,
                Conditions=conditions,
                ExpiresIn=expires_in
            )
            
            return {
                'success': True,
                'url': response['url'],
                'fields': response['fields']
            }
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def object_exists(self, key: str) -> bool:
        """
        Check if an object exists in S3.
        
        Args:
            key: S3 object key
            
        Returns:
            True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking object existence: {e}")
                return False
    
    def get_object_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an S3 object.
        
        Args:
            key: S3 object key
            
        Returns:
            Dictionary containing object information or None if not found
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            
            return {
                'key': key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            else:
                logger.error(f"Error getting object info: {e}")
                return None


def create_s3_service(config: Config) -> Optional[S3Service]:
    """
    Create S3 service instance from configuration.
    
    Args:
        config: Application configuration
        
    Returns:
        S3Service instance or None if S3 is not configured
    """
    if not all([
        config.AWS_ACCESS_KEY_ID,
        config.AWS_SECRET_ACCESS_KEY,
        config.S3_BUCKET_NAME
    ]):
        logger.warning("S3 configuration incomplete, S3 features will be disabled")
        return None
    
    try:
        return S3Service(
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region=config.AWS_REGION,
            bucket_name=config.S3_BUCKET_NAME,
            use_ssl=config.S3_USE_SSL
        )
    except Exception as e:
        logger.error(f"Failed to create S3 service: {e}")
        return None