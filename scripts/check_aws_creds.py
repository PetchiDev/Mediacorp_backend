import boto3
from src.core.config import settings

def test_credentials():
    print(f"Testing AWS Credentials for Region: {settings.AWS_REGION}")
    print(f"S3 Bucket: {settings.S3_BUCKET}")
    
    if not settings.AWS_SESSION_TOKEN:
        print(" Error: AWS_SESSION_TOKEN is missing in settings!")
        return

    print(f"Session Token Length: {len(settings.AWS_SESSION_TOKEN)}")
    
    kwargs = {
        "region_name": settings.AWS_REGION,
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "aws_session_token": settings.AWS_SESSION_TOKEN
    }
    
    try:
        s3 = boto3.client('s3', **kwargs)
        print("Attempting to head bucket...")
        s3.head_bucket(Bucket=settings.S3_BUCKET)
        print(" Head bucket success!")
        
        print(f"Attempting CreateMultipartUpload for bucket: {settings.S3_BUCKET}...")
        test_key = "test-multipart-init"
        response = s3.create_multipart_upload(Bucket=settings.S3_BUCKET, Key=test_key)
        upload_id = response['UploadId']
        print(f" Multipart Init Success! UploadId: {upload_id}")
        
        print("Aborting test multipart upload...")
        s3.abort_multipart_upload(Bucket=settings.S3_BUCKET, Key=test_key, UploadId=upload_id)
        print(" Abort Success!")
        
    except Exception as e:
        print(f" Failed: {e}")

if __name__ == "__main__":
    test_credentials()
