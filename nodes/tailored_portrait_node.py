import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import image_to_base64, preprocess_image

class TailoredPortraitNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "tailored_model_id": ("INT",),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}), # API Key input with a default value
            },
            "optional": {
                "seed": ("INT", {"default": 123456}),
                "tailored_model_influence": ("FLOAT", {"default": 0.9}),
                "id_strength": ("FLOAT", {"default": 0.7}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/tailored-gen/restyle_portrait"  # Eraser API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, tailored_model_id, api_key, seed, tailored_model_influence, id_strength):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")

        # Convert the image and mask directly to  if isinstance(image, torch.Tensor):
        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)
            
        image_base64 = image_to_base64(image)

        # Prepare the API request payload
        payload = {
            "id_image_file": f"{image_base64}",
            "tailored_model_id": tailored_model_id,
            "tailored_model_influence": tailored_model_influence,
            "id_strength": id_strength,
            "seed": seed
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
                image_response = requests.get(response_dict['image_res'])
                result_image = Image.open(io.BytesIO(image_response.content))
                result_image = result_image.convert("RGB")
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}")

        except Exception as e:
            raise Exception(f"{e}")
