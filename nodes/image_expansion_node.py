import io
import requests
import numpy as np
from PIL import Image
import torch

from .common import (
    bria_asset_headers,
    bria_json_headers,
    image_to_base64,
    normalize_images_input,
    poll_status_until_completed,
)
class ImageExpansionNode():
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
            },
            "optional": {
                "original_image_size": ("STRING",),
                "original_image_location": ("STRING",),
                "canvas_size": ("STRING", {"default": "1000, 1000"}),
                "aspect_ratio": (["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "None"], {"default": "None"}),
                "prompt": ("STRING", {"default": ""}),
                "seed": ("STRING", {"default": "681794"}),  # <-- accepts seeds from Enhance
                "negative_prompt": ("STRING", {"default": "Ugly, mutated"}),
                "prompt_content_moderation": ("BOOLEAN", {"default": False}),
                "preserve_alpha": ("BOOLEAN", {"default": True}),
                "visual_input_content_moderation": ("BOOLEAN", {"default": False}),
                "visual_output_content_moderation": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_images",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/expand"

    def execute(
        self,
        images,
        original_image_size,
        original_image_location,
        canvas_size,
        aspect_ratio,
        prompt,
        seed,
        negative_prompt,
        prompt_content_moderation,
        preserve_alpha,
        visual_input_content_moderation,
        visual_output_content_moderation,
        api_key
    ):
        if api_key.strip() in ("", "BRIA_API_TOKEN"):
            raise Exception("Please insert a valid API key.")
        images = normalize_images_input(images)
        canvas_size = [int(x.strip()) for x in canvas_size.split(",")] if canvas_size else ()
        original_image_size = [int(x.strip()) for x in original_image_size.split(",")] if original_image_size else ()
        original_image_location = [int(x.strip()) for x in original_image_location.split(",")] if original_image_location else ()

        # Prepare per-image seeds
        seed_values = [int(s.strip()) for s in seed.split(",")] if isinstance(seed, str) else [seed]
        if len(seed_values) < len(images):
            seed_values += [seed_values[-1]] * (len(images) - len(seed_values))

        if not negative_prompt:
            negative_prompt = " "

        batch_results = []

        for idx, pil_image in enumerate(images):
            try:
                image_base64 = image_to_base64(pil_image)

                if aspect_ratio and aspect_ratio != "None":
                    payload = {
                        "image": image_base64,
                        "aspect_ratio": aspect_ratio,
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "seed": seed_values[idx],
                        "prompt_content_moderation": prompt_content_moderation,
                        "preserve_alpha": preserve_alpha,
                        "visual_input_content_moderation": visual_input_content_moderation,
                        "visual_output_content_moderation": visual_output_content_moderation
                    }
                else:
                    payload = {
                        "image": image_base64,
                        "original_image_size": original_image_size,
                        "original_image_location": original_image_location,
                        "canvas_size": canvas_size,
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "seed": seed_values[idx],
                        "prompt_content_moderation": prompt_content_moderation,
                        "preserve_alpha": preserve_alpha,
                        "visual_input_content_moderation": visual_input_content_moderation,
                        "visual_output_content_moderation": visual_output_content_moderation
                    }

                headers = bria_json_headers(api_key)
                response = requests.post(self.api_url, json=payload, headers=headers)
                if response.status_code not in (200, 202):
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")

                response_dict = response.json()
                status_url = response_dict.get("status_url")
                if not status_url:
                    raise Exception("No status_url returned from API")

                print(f"ImageExpansionNode - Initial request successful for image {idx}, polling for completion...")
                final_response = poll_status_until_completed(status_url, api_key)
                result_image_url = final_response["result"]["image_url"]

                image_response = requests.get(
                    result_image_url,
                    headers=bria_asset_headers(),
                )
                result_image = Image.open(io.BytesIO(image_response.content)).convert("RGB")
                result_tensor = torch.from_numpy(np.array(result_image).astype(np.float32) / 255.0)

                batch_results.append(result_tensor)

            except Exception as e:
                print(f"[ImageExpansionNode] Skipping image {idx} due to error: {e}")
                fallback_array = np.array(pil_image).astype(np.float32) / 255.0
                batch_results.append(torch.from_numpy(fallback_array))

        return (batch_results,)
