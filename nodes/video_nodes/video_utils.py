import os
import requests

from ..common import BRIA_COMFYUI_USER_AGENT


def upload_video_to_s3(video_path, filename, api_token):
    api_url = "https://platform.prod.bria-api.com/upload-video/anonymous/presigned-url"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": BRIA_COMFYUI_USER_AGENT,
    }
    extension = os.path.splitext(filename)[1].lower()
    content_type_map = {
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.avi': 'video/x-msvideo',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
    }
    content_type = content_type_map.get(extension, 'video/mp4')
    if api_token:
        headers["api_token"] = api_token
    
    payload = {
        "file_name": filename,
        "content_type":content_type
    }
    
    print(f"Requesting presigned URL for: {filename}")
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get presigned URL: {response.status_code} {response.text}")
        
        response_data = response.json()
        video_url = response_data.get("video_url")
        upload_url = response_data.get("upload_url")
        
        if not video_url or not upload_url:
            raise Exception(f"Invalid response from presigned URL API: {response_data}")
        
        print(f"Received presigned URL")
        print(f"Video URL: {video_url}")
        
        # Step 2: Upload video to presigned URL
        print(f"Uploading video to S3...")
        
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Determine content type based on file extension
        upload_headers = {
            "Content-Type": content_type
        }

        upload_response = requests.put(upload_url, data=video_data, headers=upload_headers)
        
        if upload_response.status_code not in [200, 204]:
            raise Exception(f"Failed to upload video to S3: {upload_response.status_code}")
        
        print(f"Video uploaded successfully to S3")
        
        return video_url
        
    except Exception as e:
        raise Exception(f"Error uploading video to S3: {str(e)}")

