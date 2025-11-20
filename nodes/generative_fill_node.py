import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import deserialize_and_get_comfy_key, preprocess_image, preprocess_mask, image_to_base64, poll_status_until_completed


class GenFillNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "mask": ("MASK",),  # Binary mask input
                "prompt": ("STRING",),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}), # API Key input with a default value
            },
            "optional": {
                "seed": ("INT", {"default": 123456}),
                "prompt_content_moderation": ("BOOLEAN", {"default": True}), 
                "visual_input_content_moderation": ("BOOLEAN", {"default": False}), 
                "visual_output_content_moderation": ("BOOLEAN", {"default": False}), 


            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/gen_fill"

    # Define the execute method as expected by ComfyUI
    def execute(self, image, mask, prompt, api_key, seed, prompt_content_moderation, visual_input_content_moderation, visual_output_content_moderation):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)

        # Check if image and mask are tensors, if so, convert to NumPy arrays
        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)
        if isinstance(mask, torch.Tensor):
            mask = preprocess_mask(mask)

        # Convert the image and mask directly to Base64 strings
        image_base64 = image_to_base64(image)
        mask_base64 = image_to_base64(mask)

        # Prepare the API request payload
        payload = {
            "image": image_base64,
            "mask": mask_base64,
            "prompt": prompt,
            "negative_prompt": "blurry",
            "seed": seed,
            "prompt_content_moderation":prompt_content_moderation,
            "visual_input_content_moderation":visual_input_content_moderation,
            "visual_output_content_moderation":visual_output_content_moderation,
            "version": 2
        }

        headers = {
            "Content-Type": "application/json",
            "api_token": f"{api_key}"
        }

        try:
            # Send initial request to get status URL
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200 or response.status_code == 202:
                print('Initial genfill request successful, polling for completion...')
                response_dict = response.json()
                status_url = response_dict.get('status_url')
                request_id = response_dict.get('request_id')
                
                if not status_url:
                    raise Exception("No status_url returned from API")
                
                print(f"Request ID: {request_id}, Status URL: {status_url}")
                
                final_response = poll_status_until_completed(status_url, api_key)                
                result_image_url = final_response['result']['image_url']
                image_response = requests.get(result_image_url)
                result_image = Image.open(io.BytesIO(image_response.content))
                result_image = result_image.convert("RGB")
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code} {response.text}")

        except Exception as e:
            raise Exception(f"{e}")
