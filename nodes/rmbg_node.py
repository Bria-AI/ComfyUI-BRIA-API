import io
import requests
import numpy as np
from PIL import Image
import torch

from .common import deserialize_and_get_comfy_key, image_to_base64, normalize_images_input, poll_status_until_completed, to_pil_safe

class RmbgNode():
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),  # Accepts list of PIL Images or single tensor
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}), 
            },
            "optional": {
                "visual_input_content_moderation": ("BOOLEAN", {"default": False}), 
                "visual_output_content_moderation": ("BOOLEAN", {"default": False}), 
                "preserve_alpha": ("BOOLEAN", {"default": True}), 
            }               
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_images",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/remove_background"

    def execute(self, images, visual_input_content_moderation, visual_output_content_moderation, preserve_alpha, api_key):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)

        # Normalize input to list of PIL images
        images = normalize_images_input(images)

        batch_results = []

        for idx, pil_image in enumerate(images):
            try:
                image_base64 = image_to_base64(pil_image)

                payload = {
                    "image": image_base64,
                    "visual_input_content_moderation": visual_input_content_moderation,
                    "visual_output_content_moderation": visual_output_content_moderation,
                    "preserve_alpha": preserve_alpha
                }

                headers = {
                    "Content-Type": "application/json",
                    "api_token": f"{api_key}"
                }

                response = requests.post(self.api_url, json=payload, headers=headers)
                if response.status_code not in (200, 202):
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")

                # Poll until completion
                response_dict = response.json()
                status_url = response_dict.get('status_url')
                if not status_url:
                    raise Exception("No status_url returned from API")

                print(f"RmbgNode - Initial request successful for image {idx}, polling for completion...")
                final_response = poll_status_until_completed(status_url, api_key)
                result_image_url = final_response['result']['image_url']

                # Download result
                image_response = requests.get(result_image_url)
                result_image = Image.open(io.BytesIO(image_response.content))

                # Convert to float32 tensor (H, W, C), 0-1
                result_array = np.array(result_image).astype(np.float32) / 255.0
                result_tensor = torch.from_numpy(result_array)  # shape: (H,W,4)
                batch_results.append(result_tensor)

            except Exception as e:
                print(f"[RmbgNode] Skipping image {idx} due to error: {e}")
                # Append empty tensor of the same size as original
                empty_array = np.zeros((pil_image.height, pil_image.width, 4), dtype=np.float32)
                batch_results.append(torch.from_numpy(empty_array))

        # Return list of tensors (Comfy preview handles this correctly)
        return (batch_results,)
