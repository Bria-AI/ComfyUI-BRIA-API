import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import image_to_base64, preprocess_image


class ImageExpansionNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "original_image_size": ("STRING",),
                "original_image_location": ("STRING",),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}), # API Key input with a default value
            },
            
            "optional": {
                "canvas_size": ("STRING", {"default": "1000, 1000"}),
                "prompt": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": 681794}),
                "negative_prompt": ("STRING", {"default": "Ugly, mutated"}),
            } 
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/image_expansion"  # Image Expansion API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, 
                original_image_size,
                original_image_location,
                canvas_size,
                prompt,
                seed,
                negative_prompt,
                api_key):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        
        original_image_size = [int(x.strip()) for x in original_image_size.split(",")]
        original_image_location = [int(x.strip()) for x in original_image_location.split(",")]
        canvas_size = [int(x.strip()) for x in canvas_size.split(",")]
        
        if prompt == "":
            prompt = None
        if negative_prompt == "":
            negative_prompt = " " # hack to avoid error in triton which expects non-empty string

        # Check if image and mask are tensors, if so, convert to NumPy arrays
        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)

        # Convert the image directly to Base64 string
        image_base64 = image_to_base64(image)

        # Prepare the API request payload
        payload = {
            "file": f"{image_base64}",
            "original_image_size": original_image_size,
            "original_image_location": original_image_location,
            "canvas_size": canvas_size,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": seed
            # "sync": True
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
                image_response = requests.get(response_dict['result_url'])
                result_image = Image.open(io.BytesIO(image_response.content))
                result_image = result_image.convert("RGB")
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}")

        except Exception as e:
            raise Exception(f"{e}")
