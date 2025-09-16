import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import preprocess_image, image_to_base64, poll_status_until_completed


class RemoveForegroundNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}), # API Key input with a default value
            },
            "optional": {
                "visual_input_content_moderation": ("BOOLEAN", {"default": False}), 
                "visual_output_content_moderation": ("BOOLEAN", {"default": False}), 
                "preserve_alpha": ("BOOLEAN", {"default": True}), 
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/erase_foreground"  # remove foreground API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, visual_input_content_moderation, visual_output_content_moderation, preserve_alpha, api_key):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")

        # Check if image is tensor, if so, convert to NumPy array
        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)

        # Prepare the API request payload
        # temporary save the image to /tmp
        # temp_img_path = "/tmp/temp_img.jpeg"
        # image.save(temp_img_path, format="JPEG")
        
#         files=[('file',('temp_img.jpeg', open(temp_img_path, 'rb'),'image/jpeg'))
#   ]
        payload = {
            "image": image_to_base64(image),
            "visual_input_content_moderation": visual_input_content_moderation,
            "visual_output_content_moderation":visual_output_content_moderation,
            "preserve_alpha": preserve_alpha
        }

        headers = {
            "Content-Type": "application/json",
            "api_token": f"{api_key}"
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)

            if response.status_code == 200 or response.status_code == 202:
                print('Initial request successful, polling for completion...')
                response_dict = response.json()
                status_url = response_dict.get('status_url')
                request_id = response_dict.get('request_id')
                
                if not status_url:
                    raise Exception("No status_url returned from API")
                
                print(f"Request ID: {request_id}, Status URL: {status_url}")
                
                # Poll status URL until completion
                final_response = poll_status_until_completed(status_url, api_key)
                
                # Get the result image URL
                result_image_url = final_response['result']['image_url']
                
                image_response = requests.get(result_image_url)
                result_image = Image.open(io.BytesIO(image_response.content))
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}")

        except Exception as e:
            raise Exception(f"{e}")
