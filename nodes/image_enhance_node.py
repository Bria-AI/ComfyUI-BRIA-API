import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import deserialize_and_get_comfy_key, image_to_base64, preprocess_image, poll_status_until_completed


class ImageEnhanceNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
            },
            
            "optional": {
                "steps_num": ("INT", {"default": 20, "min": 10, "max": 50}),
                "resolution": (["1MP", "2MP", "4MP"], {"default": "1MP"}),
                "visual_input_content_moderation": ("BOOLEAN", {"default": False}),
                "visual_output_content_moderation": ("BOOLEAN", {"default": False}),
                "seed": ("INT", {"default": 681794}),
                "preserve_alpha": ("BOOLEAN", {"default": True}),
            } 
        }

    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("output_image", "seed")
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/enhance"

    def execute(self, image, 
                api_key,
                visual_input_content_moderation,
                visual_output_content_moderation,
                seed,
                steps_num,
                resolution,
                preserve_alpha):
        
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)


        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)

        image_base64 = image_to_base64(image)
        
        payload = {
            "image": image_base64,
            "visual_input_content_moderation": visual_input_content_moderation,
            "visual_output_content_moderation": visual_output_content_moderation,
            "seed": seed,
            "steps_num": steps_num,
            "resolution": resolution,
            "preserve_alpha": preserve_alpha
        }

        headers = {
            "Content-Type": "application/json",
            "api_token": f"{api_key}"
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200 or response.status_code == 202:
                response_dict = response.json()

                print('Initial image enhancement request successful, polling for completion...')
                status_url = response_dict.get('status_url')
                request_id = response_dict.get('request_id')
                
                if not status_url:
                    raise Exception("No status_url returned from API")
                
                print(f"Request ID: {request_id}, Status URL: {status_url}")
                
                # Poll status URL until completion
                final_response = poll_status_until_completed(status_url, api_key)
                
                # Get the result image URL
                result_image_url = final_response['result']['image_url']
                seed = final_response['result']['seed']
                
                # Download and process the result image
                image_response = requests.get(result_image_url)
                result_image = Image.open(io.BytesIO(image_response.content))
                result_image = result_image.convert("RGB")
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                
                return (result_image,seed,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            raise Exception(f"{e}")