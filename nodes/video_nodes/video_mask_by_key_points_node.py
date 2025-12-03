import requests
from ..common import deserialize_and_get_comfy_key, poll_status_until_completed
import json

class VideoMaskByKeyPointsNode():
    """
    Bria Video Mask by Key Points Node
    
    This node generates a mask for specific elements in videos based on key point coordinates
    using the Bria API. It accepts a publicly accessible video URL and an array of coordinate
    objects defining the mask hints.
    
    Parameters:
    - video_url: Publicly accessible URL of the input video
    - api_key: Your Bria API token
    - key_points: Array of coordinate objects defining the mask hints (JSON format)
    - output_container_and_codec: Output video format and codec (default: mp4_h264)
    - preserve_audio: Audio preservation (default: True)
    """
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "video_url": ("STRING", {"default": ""}),
                "key_points": ("STRING", {"default": "[]", "multiline": True}),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
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
    RETURN_NAMES = ("mask_url_response",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/video/segment/mask_by_key_points"

    def execute(self, video_url, key_points, api_key, output_container_and_codec="mp4_h264", preserve_audio=True):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)
        
        try:
            key_points_array = json.loads(key_points)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON format for key_points: {e}")
        
        # Prepare the API request payload
        payload = {
            "video": video_url,
            "key_points": key_points_array,
            "output_container_and_codec": output_container_and_codec,
            "preserve_audio": preserve_audio
        }

        headers = {
            "Content-Type": "application/json",
            "api_token": f"{api_key}"
        }

        try:
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
                
                return (result_mask_url,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code} {response.text}")

        except Exception as e:
            raise Exception(f"{e}")