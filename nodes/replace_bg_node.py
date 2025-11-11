import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import deserialize_and_get_comfy_key, image_to_base64, preprocess_image, preprocess_mask, poll_status_until_completed


class ReplaceBgNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}), # API Key input with a default value
            },
            "optional": {
                "mode": (["base", "fast", "high_control"], {"default": "base"}),
                "prompt": ("STRING",),
                "ref_images": ("IMAGE",),
                "refine_prompt": ("BOOLEAN", {"default": True}), 
                "enhance_ref_images": ("BOOLEAN", {"default": True}), 
                "original_quality": ("BOOLEAN", {"default": False}), 
                "negative_prompt": ("STRING", {"default": None}), 
                "seed": ("INT", {"default": 681794}),
                "visual_output_content_moderation": ("BOOLEAN", {"default": False}), 
                "prompt_content_moderation": ("BOOLEAN", {"default": False}),
                "force_background_detection": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/replace_background"  # Replace BG API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, mode,
                refine_prompt,
                original_quality,
                negative_prompt,
                seed,
                api_key,
                visual_output_content_moderation,
                prompt_content_moderation,
                enhance_ref_images,
                force_background_detection,
                prompt=None,
                ref_images=None,):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)

        # Check if image and mask are tensors, if so, convert to NumPy arrays
        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)

        # Convert the image to Base64 string
        image_base64 = image_to_base64(image)
        
        if ref_images is not None:
            ref_images = preprocess_image(ref_images)
            ref_images = [image_to_base64(ref_images)]
        else:
            ref_images=[]

        # Prepare the API request payload for v2 API
        payload = {
            "image": image_base64,
            "mode": mode,
            "prompt": prompt,
            "ref_images":ref_images,
            "refine_prompt": refine_prompt,
            "original_quality": original_quality,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "prompt_content_moderation": prompt_content_moderation,
            "visual_output_content_moderation":visual_output_content_moderation,
            "enhance_ref_images":enhance_ref_images,
            "force_background_detection": force_background_detection        
        }   

        headers = {
            "Content-Type": "application/json",
            "api_token": f"{api_key}"
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200 or response.status_code == 202:
                print('Initial replace background request successful, polling for completion...')
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
                raise Exception(f"Error: API request failed with status code {response.status_code}{response.text}")

        except Exception as e:
            raise Exception(f"{e}")
