import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from src.core.config import settings
from src.core.logging import logger
from typing import Optional

def get_s3_client():
    """Dynamically get S3 client using current settings."""
    config = Config(
        signature_version='s3v4',
        region_name=settings.AWS_REGION
    )
    kwargs = {"region_name": settings.AWS_REGION, "config": config}
    
    # DEBUG: Help identify if stale creds are being used
    ak_hint = settings.AWS_ACCESS_KEY_ID[:5] if settings.AWS_ACCESS_KEY_ID else "NONE"
    st_len = len(settings.AWS_SESSION_TOKEN) if settings.AWS_SESSION_TOKEN else 0
    logger.debug(f"S3 Client Init - AK: {ak_hint}..., Token Len: {st_len}")

    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs.update({
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "aws_session_token": settings.AWS_SESSION_TOKEN
        })
    return boto3.client('s3', **kwargs)

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
                
            client = get_s3_client()
            url = client.generate_presigned_url(
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
            
        client = get_s3_client()
        response = client.create_multipart_upload(**params)
        upload_id = response['UploadId']
        logger.info(f"Initiated multipart upload: {upload_id}")
        return upload_id
    except Exception as e:
        logger.error(f"Error initiating multipart upload: {e}", exc_info=True)
        raise

async def abort_multipart_upload(bucket: str, object_key: str, upload_id: str) -> None:
    """Abort an incomplete multipart upload to save costs."""
    try:
        client = get_s3_client()
        client.abort_multipart_upload(
            Bucket=bucket,
            Key=object_key,
            UploadId=upload_id
        )
        logger.info(f"Aborted multipart upload: {upload_id} for {object_key}")
    except ClientError as e:
        logger.error(f"Failed to abort multipart upload {upload_id}: {e}", exc_info=True)

async def generate_part_presigned_url(
    bucket: str,
    object_key: str,
    upload_id: str,
    part_number: int,
    expiration: int = 3600
) -> str:
    """Generates a presigned URL for a specific part of a multipart upload."""
    try:
        client = get_s3_client()
        url = client.generate_presigned_url(
            'upload_part',
            Params={
                'Bucket': bucket,
                'Key': object_key,
                'UploadId': upload_id,
                'PartNumber': part_number
            },
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        logger.error(f"Error generating part URL for {object_key} part {part_number}: {e}", exc_info=True)
        raise

async def complete_multipart_upload(
    bucket: str,
    object_key: str,
    upload_id: str,
    parts: list[dict]
) -> dict:
    """Completes a multipart upload by merging all parts."""
    try:
        client = get_s3_client()
        response = client.complete_multipart_upload(
            Bucket=bucket,
            Key=object_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        logger.info(f"Successfully completed multipart upload for {object_key}")
        return response
    except Exception as e:
        logger.error(f"Error completing multipart upload for {object_key}: {e}", exc_info=True)
        raise
