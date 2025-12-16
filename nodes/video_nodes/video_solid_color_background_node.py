import os
import uuid
import requests
import folder_paths
from ..common import deserialize_and_get_comfy_key, poll_status_until_completed
from .video_utils import upload_video_to_s3

class VideoSolidColorBackgroundNode():
    """
    Apply a solid color background to a video using the Bria API.

    Parameters:
        api_key (str): Your Bria API key.
        video_url (str): Local path or URL of the video to process.
        background_color (str, optional): Color to apply as background. Default is "Transparent".
        output_container_and_codec (str, optional): Desired output format and codec. Default is "mp4_h264".
        preserve_audio (bool, optional): Whether to keep the audio track. Default is True.

    Returns:
        result_video_url (STRING): URL of the video with the solid color background applied.
    """
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "video_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of video to process (provide either frames or video_url)"
                }),
            },
            "optional": {
                "background_color": ([
                    "Transparent",
                    "Black",
                    "White",
                    "Gray",
                    "Red",
                    "Green",
                    "Blue",
                    "Yellow",
                    "Cyan",
                    "Magenta",
                    "Orange"
                ], {"default": "Transparent"}),
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
                ], {"default": "webm_vp9"}),
                "preserve_audio": ("BOOLEAN", {"default": True}),   
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_video_url",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/video/edit/remove_background"

    def execute(self, api_key, video_url, background_color="Transparent", output_container_and_codec="webm_vp9", preserve_audio=True):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)
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
            
            print("Step 3: Calling Bria API for solid color background...")
            payload = {
                "video": input_video_url,
                "background_color": background_color,
                "output_container_and_codec": output_container_and_codec,
                "preserve_audio": preserve_audio
            }

            headers = {
                "Content-Type": "application/json",
                "api_token": f"{api_key}"
            }

            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200 or response.status_code == 202:
                print('Initial Video Solid Color Background request successful, polling for completion...')
                response_dict = response.json()

                status_url = response_dict.get('status_url')
                request_id = response_dict.get('request_id')
                
                if not status_url:
                    raise Exception("No status_url returned from API")
                
                print(f"Request ID: {request_id}, Status URL: {status_url}")
                
                final_response = poll_status_until_completed(status_url, api_key, timeout=3600, check_interval=5)
                
                result_video_url = final_response['result']['video_url']
                
                print(f"Video processing completed. Result URL: {result_video_url}")
                print(f"Solid color background processing complete! Use Preview Video URL node to view the result.")
                
                return (result_video_url,)
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