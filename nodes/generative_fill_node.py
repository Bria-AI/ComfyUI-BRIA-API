import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import image_to_base64, preprocess_image, preprocess_mask


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
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/gen_fill"  # Eraser API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, mask, prompt, api_key):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")

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
            "file": f"{image_base64}",
            "mask_file": f"{mask_base64}",
            "prompt": prompt,
            "negative_prompt": "blurry",
            "sync": True
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
                image_response = requests.get(response_dict['urls'][0])
                result_image = Image.open(io.BytesIO(image_response.content))
                result_image = result_image.convert("RGB")
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}")

        except Exception as e:
            raise Exception(f"{e}")
