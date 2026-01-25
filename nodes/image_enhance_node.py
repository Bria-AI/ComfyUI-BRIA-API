import io
import requests
import numpy as np
from PIL import Image
import torch

from .common import (
    deserialize_and_get_comfy_key,
    image_to_base64,
    normalize_images_input,
    poll_status_until_completed
)

class ImageEnhanceNode():
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
            },
            "optional": {
                "steps_num": ("INT", {"default": 20, "min": 10, "max": 50}),
                "resolution": (["1MP", "2MP", "4MP"], {"default": "1MP"}),
                "visual_input_content_moderation": ("BOOLEAN", {"default": False}),
                "visual_output_content_moderation": ("BOOLEAN", {"default": False}),
                "seed": ("INT", {"default": 681794}),
                "preserve_alpha": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("output_images", "seeds",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/enhance"

    def execute(
        self,
        images,
        api_key,
        visual_input_content_moderation,
        visual_output_content_moderation,
        seed,
        steps_num,
        resolution,
        preserve_alpha
    ):
        # Validate API key
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)

        # Normalize input to list of PIL images
        images = normalize_images_input(images)

        batch_results = []
        batch_seeds = []

        for idx, pil_image in enumerate(images):
            try:
                image_base64 = image_to_base64(pil_image)

                payload = {
                    "image": image_base64,
                    "visual_input_content_moderation": visual_input_content_moderation,
                    "visual_output_content_moderation": visual_output_content_moderation,
                    "seed": seed,
                    "steps_num": steps_num,
                    "resolution": resolution,
                    "preserve_alpha": preserve_alpha
                }

                headers = {
                    "Content-Type": "application/json",
                    "api_token": f"{api_key}"
                }

                # Send request
                response = requests.post(self.api_url, json=payload, headers=headers)
                if response.status_code not in (200, 202):
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")

                # Poll until completion
                response_dict = response.json()
                status_url = response_dict.get("status_url")
                if not status_url:
                    raise Exception("No status_url returned from API")

                print(f"ImageEnhanceNode - Initial request successful for image {idx}, polling for completion...")
                final_response = poll_status_until_completed(status_url, api_key)
                result_image_url = final_response["result"]["image_url"]
                used_seed = final_response["result"].get("seed", seed)

                # Download and process image
                image_response = requests.get(result_image_url)
                result_image = Image.open(io.BytesIO(image_response.content)).convert("RGB")
                result_array = np.array(result_image).astype(np.float32) / 255.0
                result_tensor = torch.from_numpy(result_array)  # shape: (H,W,C)

                batch_results.append(result_tensor)
                batch_seeds.append(used_seed)

            except Exception as e:
                print(f"[ImageEnhanceNode] Skipping image {idx} due to error: {e}")
                # Append fallback tensor with same size as input
                fallback_array = np.array(pil_image).astype(np.float32) / 255.0
                batch_results.append(torch.from_numpy(fallback_array))
                batch_seeds.append(seed)

        # Return list of tensors (not concatenated) + comma-separated seeds
        combined_seeds = ",".join(map(str, batch_seeds))
        return (batch_results, combined_seeds)
