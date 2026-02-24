import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_bulk_upload():
    payload = {
        "uploads": [
            {
                "filename": "test_video1.mp4",
                "file_size": 1024 * 1024,  # 1 MB
                "content_type": "video/mp4"
            },
            {
                "filename": "large_video2.mkv",
                "file_size": 1024 * 1024 * 500, # 500 MB (Multipart)
                "content_type": "video/x-matroska"
            }
        ]
    }
    
    print(f"Sending bulk upload request to {BASE_URL}/bulk-upload...")
    response = requests.post(f"{BASE_URL}/bulk-upload", json=payload)
    
    if response.status_code == 201:
        print("✅ Bulk upload initiation successful!")
        results = response.json().get("results", [])
        for i, res in enumerate(results):
            print(f"\nFile {i+1}:")
            print(f"  Upload ID: {res['upload_id']}")
            print(f"  Object Key: {res['object_key']}")
            print(f"  Presigned URL/ID: {res['presigned_url'][:50]}...")
    else:
        print(f"❌ Failed! Status Code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_bulk_upload()
