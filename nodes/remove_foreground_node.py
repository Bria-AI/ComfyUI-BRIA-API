import numpy as np
import requests
from PIL import Image
import io
import torch

from .common import preprocess_image, image_to_base64


class RemoveForegroundNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}), # API Key input with a default value
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.internal.prod.bria-api.com/v1/erase_foreground"  # remove foreground API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, api_key):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")

        # Check if image is tensor, if so, convert to NumPy array
        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)

        # Prepare the API request payload
        # temporary save the image to /tmp
        # temp_img_path = "/tmp/temp_img.jpeg"
        # image.save(temp_img_path, format="JPEG")
        
#         files=[('file',('temp_img.jpeg', open(temp_img_path, 'rb'),'image/jpeg'))
#   ]
        payload = {"file": image_to_base64(image)}

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
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}")

        except Exception as e:
            raise Exception(f"{e}")
