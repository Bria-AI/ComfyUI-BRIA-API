import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import preprocess_image
from io import BytesIO

class RmbgNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}), # API Key input with a default value
            },
            "optional": {
                "content_moderation": ("BOOLEAN", {"default": False}), 
            }               
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/background/remove"  # RMBG API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, content_moderation, api_key):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")

        # Check if image is tensor, if so, convert to NumPy array
        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)

        # Prepare the API request payload
        image_buffer = BytesIO()
        image.save(image_buffer, format="JPEG")

        # Get binary data from buffer
        image_buffer.seek(0)  # Move cursor to the start of the buffer
        binary_data = image_buffer.read()

        files=[('file',('temp_img.jpeg',  BytesIO(binary_data),'image/jpeg'))]
        payload = {"content_moderation": content_moderation}   

        try:
            response = requests.post(self.api_url, data=payload, headers={"api_token": api_key}, files=files)
            # Check for successful response
            if response.status_code == 200:
                print('response is 200')
                # Process the output image from API response
                response_dict = response.json()
                image_response = requests.get(response_dict['result_url'])
                result_image = Image.open(io.BytesIO(image_response.content))
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}")

        except Exception as e:
            raise Exception(f"{e}")
