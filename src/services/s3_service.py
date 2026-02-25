import boto3
from botocore.exceptions import ClientError
from src.core.config import settings
from src.core.logging import logger
from typing import Optional

# Initialize S3 client with optional credentials
_s3_kwargs = {"region_name": settings.AWS_REGION}
if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
    _s3_kwargs.update({
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "aws_session_token": settings.AWS_SESSION_TOKEN
    })

s3_client = boto3.client('s3', **_s3_kwargs)

async def generate_presigned_url(
    bucket: str,
    object_key: str,
    file_size: int,
    content_type: str,
    expiration: int = 3600
) -> str:
    """Rule 3.2: Logic to generate a presigned URL or initiate multipart upload."""
    try:
        # 100MB threshold (Rule 3.2)
        if file_size < 100 * 1024 * 1024:
            # Single PUT upload
            params = {
                'Bucket': bucket,
                'Key': object_key,
                'ContentType': content_type,
            }
            # Rule: Only add KMS if configured (for dev simplicity)
            if settings.KMS_KEY_ID:
                params['ServerSideEncryption'] = 'aws:kms'
                params['SSEKMSKeyId'] = settings.KMS_KEY_ID
                
            url = s3_client.generate_presigned_url(
                'put_object',
                Params=params,
                ExpiresIn=expiration,
                HttpMethod='PUT'
            )
            logger.info(f"Generated single-put presigned URL for {object_key}")
            return url
        else:
            # Multipart upload - returns the UploadId
            logger.info(f"Large file detected ({file_size} bytes). Initiating multipart upload for {object_key}")
            return await initiate_multipart_upload(bucket, object_key, content_type)
            
    except Exception as e:
        logger.error(f"Error generating presigned URL for {object_key}: {e}", exc_info=True)
        raise

async def initiate_multipart_upload(bucket: str, object_key: str, content_type: str) -> str:
    """Initiates a multipart upload and returns the UploadId."""
    try:
        params = {
            'Bucket': bucket,
            'Key': object_key,
            'ContentType': content_type,
        }
        # Rule: Only add KMS if configured
        if settings.KMS_KEY_ID:
            params['ServerSideEncryption'] = 'aws:kms'
            params['SSEKMSKeyId'] = settings.KMS_KEY_ID
            
        response = s3_client.create_multipart_upload(**params)
        upload_id = response['UploadId']
        logger.info(f"Initiated multipart upload: {upload_id}")
        return upload_id
    except Exception as e:
        logger.error(f"Error initiating multipart upload: {e}", exc_info=True)
        raise

async def abort_multipart_upload(bucket: str, object_key: str, upload_id: str) -> None:
    """Abort an incomplete multipart upload to save costs."""
    try:
        s3_client.abort_multipart_upload(
            Bucket=bucket,
            Key=object_key,
            UploadId=upload_id
        )
        logger.info(f"Aborted multipart upload: {upload_id} for {object_key}")
    except ClientError as e:
        logger.error(f"Failed to abort multipart upload {upload_id}: {e}", exc_info=True)
