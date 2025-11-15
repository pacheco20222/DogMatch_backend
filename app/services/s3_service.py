# app/services/s3_service.py
import boto3
import os
import uuid
from datetime import datetime
from flask import current_app
from botocore.exceptions import ClientError, NoCredentialsError
import mimetypes

class S3Service:
    """
    Service for handling S3 operations for DogMatch photo storage
    """
    
    def __init__(self):
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-2')
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        except NoCredentialsError:
            current_app.logger.error("AWS credentials not found")
            self.s3_client = None
    
    def upload_photo(self, file_data, file_type, user_id, dog_id=None, event_id=None):
        """
        Upload a photo to S3
        
        Args:
            file_data: File data (bytes or file-like object)
            file_type: Type of photo ('user_profile', 'dog_photo', 'event_photo')
            user_id: ID of the user uploading
            dog_id: ID of the dog (for dog photos)
            event_id: ID of the event (for event photos)
        
        Returns:
            dict: {'success': bool, 'url': str, 'key': str, 'error': str}
        """
        if not self.s3_client:
            return {'success': False, 'error': 'S3 client not initialized'}
        
        try:
            # Generate unique filename
            file_extension = self._get_file_extension(file_data)
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Determine S3 key based on photo type
            if file_type == 'user_profile':
                s3_key = f"user-photos/{user_id}/profile_{unique_filename}"
            elif file_type == 'dog_photo':
                s3_key = f"dog-photos/{dog_id}/photo_{unique_filename}"
            elif file_type == 'event_photo':
                s3_key = f"event-photos/{event_id}/banner_{unique_filename}"
            else:
                return {'success': False, 'error': 'Invalid file type'}
            
            # Determine content type
            content_type = mimetypes.guess_type(unique_filename)[0] or 'image/jpeg'
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type
                # Note: ACL removed as modern S3 buckets often have ACLs disabled
                # Photos will be accessed via signed URLs generated on-demand
            )
            
            # Return S3 key - signed URLs will be generated when needed
            # This prevents storing expired URLs in the database
            return {
                'success': True,
                'url': s3_key,  # Store key, not URL
                'key': s3_key,
                'filename': unique_filename,
                'content_type': content_type
            }
            
        except ClientError as e:
            current_app.logger.error(f"S3 upload error: {e}")
            return {'success': False, 'error': f'S3 upload failed: {str(e)}'}
        except Exception as e:
            current_app.logger.error(f"Unexpected error during S3 upload: {e}")
            return {'success': False, 'error': f'Upload failed: {str(e)}'}
    
    def delete_photo(self, s3_key):
        """
        Delete a photo from S3
        
        Args:
            s3_key: S3 object key to delete
        
        Returns:
            dict: {'success': bool, 'error': str}
        """
        if not self.s3_client:
            return {'success': False, 'error': 'S3 client not initialized'}
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return {'success': True}
            
        except ClientError as e:
            current_app.logger.error(f"S3 delete error: {e}")
            return {'success': False, 'error': f'S3 delete failed: {str(e)}'}
        except Exception as e:
            current_app.logger.error(f"Unexpected error during S3 delete: {e}")
            return {'success': False, 'error': f'Delete failed: {str(e)}'}
    
    def _get_file_extension(self, file_data):
        """
        Determine file extension from file data
        """
        # Try to detect from file data (first few bytes)
        if hasattr(file_data, 'read'):
            # File-like object
            position = file_data.tell()
            file_data.seek(0)
            header = file_data.read(10)
            file_data.seek(position)
        else:
            # Bytes data
            header = file_data[:10]
        
        # Check for common image formats
        if header.startswith(b'\xff\xd8\xff'):
            return '.jpg'
        elif header.startswith(b'\x89PNG\r\n\x1a\n'):
            return '.png'
        elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return '.gif'
        elif header.startswith(b'RIFF') and b'WEBP' in header:
            return '.webp'
        else:
            # Default to jpg
            return '.jpg'
    
    def get_photo_url(self, s3_key, signed=True, expiration=3600):
        """
        Generate URL for an S3 object
        
        Args:
            s3_key: S3 object key
            signed: Whether to generate a signed URL (default: True for security)
            expiration: Expiration time in seconds for signed URLs (default: 1 hour)
        
        Returns:
            str: URL (signed or public)
        """
        if not self.s3_client:
            return None
            
        if signed:
            try:
                # Generate signed URL
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration
                )
                return url
            except ClientError as e:
                current_app.logger.error(f"Error generating signed URL: {e}")
                return None
        else:
            # Public URL (requires bucket to be public)
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
    
    def test_connection(self):
        """
        Test S3 connection and bucket access
        
        Returns:
            dict: {'success': bool, 'error': str}
        """
        if not self.s3_client:
            return {'success': False, 'error': 'S3 client not initialized'}
        
        try:
            # Try to list objects in bucket (with limit to avoid large responses)
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=1
            )
            return {'success': True}
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return {'success': False, 'error': f'Bucket {self.bucket_name} does not exist'}
            elif error_code == 'AccessDenied':
                return {'success': False, 'error': 'Access denied to S3 bucket'}
            else:
                return {'success': False, 'error': f'S3 error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Connection test failed: {str(e)}'}


# Global S3 service instance
s3_service = S3Service()
