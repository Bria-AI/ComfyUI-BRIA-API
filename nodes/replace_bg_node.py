import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import image_to_base64, preprocess_image, preprocess_mask


class ReplaceBgNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}), # API Key input with a default value
            },
            "optional": {
                "fast": ("BOOLEAN", {"default": True}), 
                "bg_prompt": ("STRING",),
                "ref_image": ("IMAGE",), # Input ref image from another node
                "refine_prompt": ("BOOLEAN", {"default": True}), 
                "enhance_ref_image": ("BOOLEAN", {"default": True}), 
                "original_quality": ("BOOLEAN", {"default": False}), 
                "force_rmbg": ("BOOLEAN", {"default": False}), 
                "negative_prompt": ("STRING", {"default": None}), 
                "seed": ("INT", {"default": 681794}),
                "content_moderation": ("BOOLEAN", {"default": False}), 
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/background/replace"  # Replace BG API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, fast,
                refine_prompt,
                enhance_ref_image,
                original_quality,
                force_rmbg,
                negative_prompt,
                seed,
                api_key,
                content_moderation,
                bg_prompt=None,
                ref_image=None,):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")

        # Check if image and mask are tensors, if so, convert to NumPy arrays
        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)

        # Convert the image and mask directly to Base64 strings
        image_base64 = image_to_base64(image)
        ref_image_file = None # initialization, will be updated if it is supplied
        if ref_image is not None:
            ref_image = preprocess_image(ref_image)
            ref_image_file = image_to_base64(ref_image)

        # Prepare the API request payload
        payload = {
            "file": f"{image_base64}",
            "fast": fast,
            "bg_prompt": bg_prompt,
            "ref_image_file": ref_image_file,
            "refine_prompt": refine_prompt,
            "enhance_ref_image": enhance_ref_image,
            "original_quality": original_quality,
            "force_rmbg": force_rmbg,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "sync": True,
            "num_results": 1,
            "content_moderation": content_moderation            
        }   

        headers = {
            "Content-Type": "application/json",
            "api_token": f"{api_key}"
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            # Check for successful response
            if response.status_code == 200:
                print('response is 200')
                # Process the output image from API response
                response_dict = response.json()
                image_response = requests.get(response_dict['result'][0][0]) # first indexing for batched, second for url
                result_image = Image.open(io.BytesIO(image_response.content))
                result_image = result_image.convert("RGB")
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}")

        except Exception as e:
            raise Exception(f"{e}")
