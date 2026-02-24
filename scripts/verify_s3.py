import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
    region_name=os.getenv('AWS_REGION')
)

bucket_name = os.getenv('S3_BUCKET')

try:
    print(f"Testing PutObject on bucket: {bucket_name}")
    s3.put_object(
        Bucket=bucket_name,
        Key="connection_test.txt",
        Body="Connection test successful."
    )
    print(f"SUCCESS: Successfully wrote to '{bucket_name}'.")
    
    # Cleanup
    s3.delete_object(Bucket=bucket_name, Key="connection_test.txt")
except Exception as e:
    print(f"ERROR: S3 access test failed. {e}")
