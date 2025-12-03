import requests
from ..common import deserialize_and_get_comfy_key, poll_status_until_completed

class VideoEraseElementsNode():
    """
    Bria Video Erase Elements Node
    
    This node erases specific elements from videos based on a text prompt using the Bria API.
    It accepts a publicly accessible video URL and a text instruction describing the object
    to be masked and removed.
    
    Parameters:
    - video_url: Publicly accessible URL of the input video
    - api_key: Your Bria API token
    - prompt: Text instruction describing the object to be masked
    - output_container_and_codec: Output video format and codec (default: mp4_h264)
    - preserve_audio: Audio preservation (default: True)
    """
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "video_url": ("STRING", {"default": ""}),
                "mask_url": ("STRING", {"default": ""}),
                "prompt": ("STRING", {"default": ""}),
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
    RETURN_NAMES = ("video_url_response",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/video/edit/erase"

    def execute(self, video_url, mask_url, prompt, api_key, output_container_and_codec="mp4_h264", preserve_audio=True):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)
        
        # Prepare the API request payload
        payload = {
            "video": video_url,
            "mask":mask_url,
            "prompt": prompt,
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
                print('Initial Video Erase Elements request successful, polling for completion...')
                response_dict = response.json()

                status_url = response_dict.get('status_url')
                request_id = response_dict.get('request_id')
                
                if not status_url:
                    raise Exception("No status_url returned from API")
                
                print(f"Request ID: {request_id}, Status URL: {status_url}")
                
                final_response = poll_status_until_completed(status_url, api_key, timeout=3600, check_interval=5)
                
                result_video_url = final_response['result']['video_url']
                
                print(f"Video processing completed. Result URL: {result_video_url}")
                
                return (result_video_url,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code} {response.text}")

        except Exception as e:
            raise Exception(f"{e}")