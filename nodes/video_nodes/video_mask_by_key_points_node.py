import os
import uuid
import requests
import folder_paths
from ..common import deserialize_and_get_comfy_key, poll_status_until_completed
from .video_utils import upload_video_to_s3
import json

class VideoMaskByKeyPointsNode():
    """
    Generate a video mask using key points with the Bria API.

    Parameters:
        key_points (str): JSON string of key points for masking.
        api_key (str): Your Bria API key.
        video_url (str): Local path or URL of the video to process.
        output_container_and_codec (str, optional): Desired output format and codec. Default is "mp4_h264".
        preserve_audio (bool, optional): Whether to keep the audio track. Default is True.

    Returns:
        mask_url (STRING): URL of the generated video mask.
    """
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "key_points": ("STRING", {"default": "[]", "multiline": True}),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "video_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of video to process (provide either frames or video_url)"
                }),
            },
            "optional": {
                "output_container_and_codec": ([
                    "mp4_h264",
                    "mp4_h265",
                    "webm_vp9",
                    "mov_h265",
                    "mov_proresks",
                    "mkv_h264",
                    "mkv_h265",
                    "mkv_vp9",
                    "gif"
                ], {"default": "mp4_h264"}),
                "preserve_audio": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("mask_url",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/video/segment/mask_by_key_points"

    def execute(self, key_points, api_key, video_url, output_container_and_codec="mp4_h264", preserve_audio=True):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)
        
        try:
            key_points_array = json.loads(key_points)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON format for key_points: {e}")

        video_path = None
        
        if video_url and video_url.strip() != "":
            if os.path.exists(video_url):
                filename = f"{ str(uuid.uuid4())}_{os.path.basename(video_url)}"
                input_video_url = upload_video_to_s3(video_url, filename, api_key)
                
                if not input_video_url or not (input_video_url.startswith('http://') or input_video_url.startswith('https://')):
                    raise Exception(f"Failed to upload video to S3. Got: {input_video_url}")
                
                
                if video_url.startswith(folder_paths.get_temp_directory()):
                    video_path = None
            else:
                input_video_url = video_url
        
        try:
            
            print("Step 3: Calling Bria API for video mask generation by key points...")
            payload = {
                "video": input_video_url,
                "key_points": key_points_array,
                "output_container_and_codec": output_container_and_codec,
                "preserve_audio": preserve_audio
            }

            headers = {
                "Content-Type": "application/json",
                "api_token": f"{api_key}"
            }

            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200 or response.status_code == 202:
                print('Initial Video Mask by Key Points request successful, polling for completion...')
                response_dict = response.json()

                status_url = response_dict.get('status_url')
                request_id = response_dict.get('request_id')
                
                if not status_url:
                    raise Exception("No status_url returned from API")
                
                print(f"Request ID: {request_id}, Status URL: {status_url}")
                
                final_response = poll_status_until_completed(status_url, api_key, timeout=3600, check_interval=5)
                
                result_mask_url = final_response['result']['mask_url']
                
                print(f"Video mask processing completed. Result URL: {result_mask_url}")
                print(f"Video mask generation complete! Use Preview Video URL node to view the result.")
                
                return (result_mask_url,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code} {response.text}")

        except Exception as e:
            raise Exception(f"{e}")
        finally:
            if video_path:
                try:
                    if os.path.exists(video_path):
                        os.unlink(video_path)
                except:
                    pass