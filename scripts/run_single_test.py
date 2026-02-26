import requests
import os
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000/api/v1"
FILE_PATH = r"C:\Users\petchiappan.p\Downloads\sample-4.mp4"

def test_upload():
    if not os.path.exists(FILE_PATH):
        print(f"Error: File not found at {FILE_PATH}")
        return

    file_size = os.path.getsize(FILE_PATH)
    filename = os.path.basename(FILE_PATH)
    
    print(f"File: {filename} ({file_size} bytes)")

    # Step 1: Initiate Upload
    print("Initiating upload via API...")
    payload = {
        "filename": filename,
        "file_size": file_size,
        "content_type": "video/mp4"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/upload", json=payload)
        response.raise_for_status()
        data = response.json()
        
        presigned_url = data["presigned_url"]
        upload_id = data["upload_id"]
        print(f"Success! Upload ID: {upload_id}")
        
        # Step 2: Upload to S3
        print("Uploading file to S3 via presigned URL...")
        with open(FILE_PATH, 'rb') as f:
            upload_response = requests.put(
                presigned_url, 
                data=f, 
                headers={'Content-Type': 'video/mp4'}
            )
            upload_response.raise_for_status()
            
        print(" SUCCESS: File uploaded successfully to S3!")
        
    except Exception as e:
        print(f" FAILED: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Detail: {e.response.text}")

if __name__ == "__main__":
    test_upload()
