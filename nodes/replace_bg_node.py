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

class ReplaceBgNode():
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
            },
            "optional": {
                "mode": (["base", "fast", "high_control"], {"default": "base"}),
                "prompt": ("STRING", {"default": ""}),
                "ref_images": ("IMAGE",),
                "refine_prompt": ("BOOLEAN", {"default": True}),
                "enhance_ref_images": ("BOOLEAN", {"default": True}),
                "original_quality": ("BOOLEAN", {"default": False}),
                "negative_prompt": ("STRING", {"default": None}),
                "seed": ("STRING", {"default": "681794"}),  # Accept comma-separated seeds
                "visual_output_content_moderation": ("BOOLEAN", {"default": False}),
                "prompt_content_moderation": ("BOOLEAN", {"default": False}),
                "force_background_detection": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_images",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/replace_background"

    def execute(
        self,
        images,
        mode,
        refine_prompt,
        original_quality,
        negative_prompt,
        seed,
        api_key,
        visual_output_content_moderation,
        prompt_content_moderation,
        enhance_ref_images,
        force_background_detection,
        prompt=None,
        ref_images=None
    ):
        if api_key.strip() in ("", "BRIA_API_TOKEN"):
            raise Exception("Please insert a valid API key.")
        images = normalize_images_input(images)

        # Normalize reference images
        ref_images_base64 = []
        if ref_images is not None:
            ref_images_list = normalize_images_input(ref_images)
            ref_images_base64 = [image_to_base64(img) for img in ref_images_list]

        # Prepare per-image seeds
        seed_values = [int(s.strip()) for s in seed.split(",")] if isinstance(seed, str) else [seed]
        if len(seed_values) < len(images):
            seed_values += [seed_values[-1]] * (len(images) - len(seed_values))

        batch_results = []

        for idx, pil_image in enumerate(images):
            try:
                image_base64 = image_to_base64(pil_image)

                payload = {
                    "image": image_base64,
                    "mode": mode,
                    "prompt": prompt,
                    "ref_images": ref_images_base64,
                    "refine_prompt": refine_prompt,
                    "original_quality": original_quality,
                    "negative_prompt": negative_prompt,
                    "seed": seed_values[idx],
                    "prompt_content_moderation": prompt_content_moderation,
                    "visual_output_content_moderation": visual_output_content_moderation,
                    "enhance_ref_images": enhance_ref_images,
                    "force_background_detection": force_background_detection
                }

                headers = bria_json_headers(api_key)
                response = requests.post(self.api_url, json=payload, headers=headers)
                if response.status_code not in (200, 202):
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")

                response_dict = response.json()
                status_url = response_dict.get("status_url")
                if not status_url:
                    raise Exception("No status_url returned from API")

                print(f"ReplaceBgNode - Initial request successful for image {idx}, polling for completion...")
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
                print(f"[ReplaceBgNode] Skipping image {idx} due to error: {e}")
                fallback_array = np.array(pil_image).astype(np.float32) / 255.0
                batch_results.append(torch.from_numpy(fallback_array))

        return (batch_results,)
