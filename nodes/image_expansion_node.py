import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import deserialize_and_get_comfy_key, image_to_base64, preprocess_image, poll_status_until_completed


class ImageExpansionNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}), # API Key input with a default value
            },
            
            "optional": {
                "original_image_size": ("STRING",),
                "original_image_location": ("STRING",),
                "canvas_size": ("STRING", {"default": "1000, 1000"}),
                "aspect_ratio": (["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9","None"], {"default": "None"}),
                "prompt": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": 681794}),
                "negative_prompt": ("STRING", {"default": "Ugly, mutated"}),
                "prompt_content_moderation": ("BOOLEAN", {"default": False}),
                "preserve_alpha": ("BOOLEAN", {"default": True}),
                "visual_input_content_moderation": ("BOOLEAN", {"default": False}),
                "visual_output_content_moderation": ("BOOLEAN", {"default": False}),
            } 
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/expand"  # Image Expansion API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, 
                original_image_size,
                original_image_location,
                canvas_size,
                aspect_ratio,
                prompt,
                seed,
                negative_prompt,
                prompt_content_moderation,
                preserve_alpha,
                visual_input_content_moderation,
                visual_output_content_moderation,
                api_key):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)
        original_image_size = [int(x.strip()) for x in original_image_size.split(",")] if original_image_size else ()
        original_image_location = [int(x.strip()) for x in original_image_location.split(",")] if original_image_location else ()
        canvas_size = [int(x.strip()) for x in canvas_size.split(",")] if canvas_size else ()
        
        if negative_prompt == "":
            negative_prompt = " " # hack to avoid error in triton which expects non-empty string

        # Check if image and mask are tensors, if so, convert to NumPy arrays
        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)

        # Convert the image directly to Base64 string
        image_base64 = image_to_base64(image)
        if aspect_ratio and aspect_ratio != "None":
            payload = {
            "image": image_base64,
            "aspect_ratio": aspect_ratio,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "prompt_content_moderation": prompt_content_moderation,
            "preserve_alpha": preserve_alpha,
            "visual_input_content_moderation": visual_input_content_moderation,
            "visual_output_content_moderation": visual_output_content_moderation
        }
        else:
            payload = {
                "image": image_base64,
                "original_image_size": original_image_size,
                "original_image_location": original_image_location,
                "canvas_size": canvas_size,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "seed": seed,
                "prompt_content_moderation": prompt_content_moderation,
                "preserve_alpha": preserve_alpha,
                "visual_input_content_moderation": visual_input_content_moderation,
                "visual_output_content_moderation": visual_output_content_moderation
            }

        headers = {
            "Content-Type": "application/json",
            "api_token": f"{api_key}"
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200 or response.status_code == 202:
                print('Initial image expansion request successful, polling for completion...')
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
                
                # Download and process the result image
                image_response = requests.get(result_image_url)
                result_image = Image.open(io.BytesIO(image_response.content))
                result_image = result_image.convert("RGB")
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            raise Exception(f"{e}")
