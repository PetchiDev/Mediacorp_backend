import os
import httpx
import asyncio
import sys

async def test_bulk_upload_real_file():
    file_path = r"C:\Users\petchiappan.p\Downloads\adventure.mp4"
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    content_type = "video/mp4"

    print(f"Preparing to upload: {filename} ({file_size} bytes)")

    # Step 1: Call Bulk Upload API
    base_url = "http://127.0.0.1:8000/api/v1"
    api_url = f"{base_url}/bulk-upload"
    payload = {
        "uploads": [{"filename": filename, "file_size": file_size, "content_type": content_type}]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Requesting upload initiation from API...")
        response = await client.post(api_url, json=payload)
        if response.status_code != 201:
            print(f"API Error: {response.status_code} - {response.text}")
            return
        
        data = response.json()
        upload_info = data["results"][0]
        upload_id = upload_info["upload_id"]
        is_multipart = upload_info["is_multipart"]
        
        if not is_multipart:
            print(f"Received Single-PUT URL for {filename}")
            presigned_url = upload_info["presigned_url"]
            with open(file_path, "rb") as f:
                s3_response = await client.put(presigned_url, content=f, headers={"Content-Type": content_type})
            
            if s3_response.status_code == 200:
                print(f"SUCCESS: File uploaded to S3: {upload_info['object_key']}")
            else:
                print(f"S3 Upload Failed: {s3_response.status_code} - {s3_response.text}")
        else:
            print(f"Multipart Upload Detected (ID: {upload_info['s3_upload_id']})")
            part_size = 10 * 1024 * 1024  # 10MB parts
            parts = []
            
            with open(file_path, "rb") as f:
                part_number = 1
                while True:
                    chunk = f.read(part_size)
                    if not chunk:
                        break
                    
                    print(f"  Requesting URL for Part {part_number}...")
                    part_url_res = await client.get(f"{base_url}/{upload_id}/part/{part_number}")
                    part_url = part_url_res.json()["presigned_url"]
                    
                    print(f"  Uploading Part {part_number}...")
                    s3_res = await client.put(part_url, content=chunk)
                    etag = s3_res.headers.get("ETag")
                    parts.append({"PartNumber": part_number, "ETag": etag})
                    
                    part_number += 1
            
            print(f"Completing Multipart Upload...")
            complete_res = await client.post(f"{base_url}/{upload_id}/complete", json={"parts": parts})
            if complete_res.status_code == 200:
                print(f"SUCCESS: Multipart upload completed: {complete_res.json().get('location')}")
            else:
                print(f"Completion Failed: {complete_res.text}")

if __name__ == "__main__":
    asyncio.run(test_bulk_upload_real_file())
