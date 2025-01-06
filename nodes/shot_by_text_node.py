import numpy as np
import requests
from PIL import Image
import io
import base64
from torchvision.transforms import ToPILImage, ToTensor
import torch

from .base_node import BriaAPINode

# shot by text Node
class ShotByTextNode(BriaAPINode):
    @staticmethod
    def INPUT_TYPES():
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "scene_description": ("STRING",),
                "optimize_description": ("INT", {"default": 1}),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"})  # API Key input with a default value
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        super().__init__("https://engine.prod.bria-api.com/v1/product/lifestyle_shot_by_text")  # Eraser API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, api_key, scene_description, optimize_description, ):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")

        # Check if image and mask are tensors, if so, convert to NumPy arrays
        if isinstance(image, torch.Tensor):
            image = self.preprocess_image(image)

        optimize_description = bool(optimize_description)
        image_base64 = self.image_to_base64(image)
        payload = {
            "file": image_base64,
            "scene_description": scene_description,
            "optimize_description": optimize_description,
            "placement_type": "original",
            "original_quality": True,
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
                image_response = requests.get(response_dict['result'][0][0])
                result_image = self.postprocess_image(image_response.content)
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}")

        except Exception as e:
            raise Exception(f"{e}")                

