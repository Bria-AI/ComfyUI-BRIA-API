import os
import requests
from ..common import deserialize_and_get_comfy_key, poll_status_until_completed
from .video_utils import frames_to_video, video_to_frames, upload_video_to_s3

class VideoIncreaseResolutionNode():
    """
    Bria Video Increase Resolution Node
    
    This node increases the resolution of videos using the Bria API.
    It accepts video frames from the Load Video node, uploads to S3,
    processes via API, and returns the processed frames for preview.
    
    Parameters:
    - frames: Batch of image frames from Load Video node
    - api_key: Your Bria API token
    - desired_increase: Integer scale factor for upscaling (2 or 4)
    - output_container_and_codec: Output video format and codec (default: mp4_h264)
    - preserve_audio: Audio preservation (default: False)
    """
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "frames": ("IMAGE", {"tooltip": "Batch of video frames"}),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
            },
            "optional": {
                "desired_increase": (['2', '4'], {"default": '2'}),
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
                "video_format": ("STRING", {
                    "default": "mp4",
                    "tooltip": "Original video format from Load Video node"
                }),
                "fbs": ("FLOAT", {
                    "default": 25,
                    "tooltip": "Original video format from Load Video node"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "FLOAT")
    RETURN_NAMES = ("frames", "frame_count", "fps")
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/video/edit/increase_resolution"

    def execute(self, frames, api_key, video_format, fbs, desired_increase='2', output_container_and_codec="mp4_h264", 
                preserve_audio=False):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)
        
        print(f"Processing {frames.shape[0]} frames for resolution increase...")
        
        # Step 1: Convert frames to video
        print("Step 1: Converting frames to video...")
        video_path = frames_to_video(frames, fbs, video_format=video_format)
        
        try:
            # Step 2: Upload video to S3
            print("Step 2: Uploading video to S3...")
            filename = f"input_video_{os.path.basename(video_path)}"
            video_url = upload_video_to_s3(video_path, filename, api_key)
            
            # Step 3: Call Bria API for resolution increase
            print("Step 3: Calling Bria API for resolution increase...")
            payload = {
                "video": video_url,
                "desired_increase": desired_increase,
                "output_container_and_codec": output_container_and_codec,
                "preserve_audio": preserve_audio
            }

            headers = {
                "Content-Type": "application/json",
                "api_token": f"{api_key}"
            }

            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200 or response.status_code == 202:
                print('Initial Video Increase Resolution request successful, polling for completion...')
                response_dict = response.json()

                status_url = response_dict.get('status_url')
                request_id = response_dict.get('request_id')
                
                if not status_url:
                    raise Exception("No status_url returned from API")
                
                print(f"Request ID: {request_id}, Status URL: {status_url}")
                
                final_response = poll_status_until_completed(status_url, api_key, timeout=3600, check_interval=5)
                
                result_video_url = final_response['result']['video_url']
                
                print(f"Video processing completed. Result URL: {result_video_url}")
                
                # Step 4: Download and convert processed video to frames
                print("Step 4: Downloading and converting processed video to frames...")
                result_frames, result_frame_count, result_fps = video_to_frames(result_video_url)
                
                print(f"Resolution increase complete! Processed {result_frame_count} frames.")
                
                return (result_frames, result_frame_count, result_fps)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code} {response.text}")

        except Exception as e:
            raise Exception(f"{e}")
        finally:
            # Clean up temporary video file
            try:
                if os.path.exists(video_path):
                    os.unlink(video_path)
            except:
                pass