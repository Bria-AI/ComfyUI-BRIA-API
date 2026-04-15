import io
import requests
import numpy as np
from PIL import Image
import torch

from .common import (
    bria_json_headers,
    image_to_base64,
    normalize_images_input,
    poll_status_until_completed,
)

class RemoveForegroundNode():
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
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
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/erase_foreground"

    def execute(
        self,
        images,
        visual_input_content_moderation,
        visual_output_content_moderation,
        preserve_alpha,
        api_key
    ):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
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

                headers = bria_json_headers(api_key)

                response = requests.post(self.api_url, json=payload, headers=headers)
                if response.status_code not in (200, 202):
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")

                response_dict = response.json()
                status_url = response_dict.get("status_url")
                if not status_url:
                    raise Exception("No status_url returned from API")

                print(f"RemoveForegroundNode - Initial request successful for image {idx}, polling for completion...")
                final_response = poll_status_until_completed(status_url, api_key)
                result_image_url = final_response["result"]["image_url"]

                # Download result
                image_response = requests.get(result_image_url)
                result_image = Image.open(io.BytesIO(image_response.content)).convert("RGB")

                # Convert to float32 tensor (H, W, C)
                result_array = np.array(result_image).astype(np.float32) / 255.0
                result_tensor = torch.from_numpy(result_array)

                batch_results.append(result_tensor)

            except Exception as e:
                print(f"[RemoveForegroundNode] Skipping image {idx} due to error: {e}")
                # fallback: use original image as tensor
                fallback_array = np.array(pil_image).astype(np.float32) / 255.0
                batch_results.append(torch.from_numpy(fallback_array))

        # Return list of tensors
        return (batch_results,)
