import boto3
from src.core.config import settings

def fix_cors():
    client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_session_token=settings.AWS_SESSION_TOKEN,
        region_name=settings.AWS_REGION
    )

    cors_configuration = {
        'CORSRules': [
            {
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['PUT', 'POST', 'GET', 'DELETE'],
                'AllowedOrigins': ['*'],
                'ExposeHeaders': ['ETag', 'x-amz-server-side-encryption', 'x-amz-request-id', 'x-amz-id-2'],
                'MaxAgeSeconds': 3000
            }
        ]
    }

    print(f"Applying CORS to bucket: {settings.S3_BUCKET}")
    try:
        client.put_bucket_cors(
            Bucket=settings.S3_BUCKET,
            CORSConfiguration=cors_configuration
        )
        print(" SUCCESS! CORS updated to expose ETag.")
    except Exception as e:
        print(f" Error updating CORS: {e}")

if __name__ == "__main__":
    fix_cors()
