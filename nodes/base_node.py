import numpy as np
import requests
from PIL import Image
import io
import base64
from torchvision.transforms import ToPILImage, ToTensor
import torch

# Base class for shared functionality between both nodes
class BriaAPINode:
    def __init__(self, api_url):
        self.api_url = api_url
    
    def preprocess_image(self, image):
        if isinstance(image, torch.Tensor):
            # Print image shape for debugging
            if image.dim() == 4:  # (batch_size, height, width, channels)
                image = image.squeeze(0)  # Remove the batch dimension (1)
                # Convert to PIL after permuting to (height, width, channels)
                image = ToPILImage()(image.permute(2, 0, 1))  # (height, width, channels)
            else:
                print("Unexpected image dimensions. Expected 4D tensor.")
        return image

    def preprocess_mask(self, mask):
        if isinstance(mask, torch.Tensor):
            # Print mask shape for debugging
            if mask.dim() == 3:  # (batch_size, height, width)
                mask = mask.squeeze(0)  # Remove the batch dimension (1)
                # Convert to PIL (grayscale mask)
                mask = ToPILImage()(mask)  # No permute needed for grayscale
            else:
                print("Unexpected mask dimensions. Expected 3D tensor.")
        return mask
    
    def postprocess_image(self, image):
        result_image = Image.open(io.BytesIO(image))
        result_image = result_image.convert("RGB")
        result_image = np.array(result_image).astype(np.float32) / 255.0
        result_image = torch.from_numpy(result_image)[None,]
        return result_image


    def image_to_base64(self, pil_image):
        # Convert a PIL image to a base64-encoded string
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")  # Save the image to the buffer in PNG format
        buffered.seek(0)  # Rewind the buffer to the beginning
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def process_request(self, image, mask, api_key):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")

        # Check if image and mask are tensors, if so, convert to NumPy arrays
        if isinstance(image, torch.Tensor):
            image = self.preprocess_image(image)
        if isinstance(mask, torch.Tensor):
            mask = self.preprocess_mask(mask)

        # Convert the image and mask directly to Base64 strings
        image_base64 = self.image_to_base64(image)
        mask_base64 = self.image_to_base64(mask)

        # Prepare the API request payload
        payload = {
            "file": f"{image_base64}",
            "mask_file": f"{mask_base64}"
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
                result_image = result_image.convert("RGBA")
                result_image = np.array(result_image).astype(np.float32) / 255.0
                result_image = torch.from_numpy(result_image)[None,]
                # image_tensor = image_tensor = ToTensor()(output_image)
                # image_tensor = image_tensor.permute(1, 2, 0) / 255.0  # Shape now becomes [1, 2200, 1548, 3]
                # print(f"output tensor shape is: {image_tensor.shape}")
                return (result_image,)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code}")

        except Exception as e:
            raise Exception(f"{e}")
