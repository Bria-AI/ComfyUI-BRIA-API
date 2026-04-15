import io
import requests
import numpy as np
from PIL import Image
import torch

from .common import (
    bria_json_headers,
    image_to_base64,
    normalize_images_input,
    to_pil_safe,
)

class TailoredPortraitNode():
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "tailored_model_id": ("STRING",),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
            },
            "optional": {
                "seed": ("INT", {"default": 123456}),
                "tailored_model_influence": ("FLOAT", {"default": 0.9}),
                "id_strength": ("FLOAT", {"default": 0.7}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_images",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/tailored-gen/restyle_portrait"

    def execute(
        self,
        images,
        tailored_model_id,
        api_key,
        seed,
        tailored_model_influence,
        id_strength
    ):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        # Normalize images to list of PIL images
        images = normalize_images_input(images)

        batch_results = []

        for idx, pil_image in enumerate(images):
            try:
                image_base64 = image_to_base64(pil_image)

                payload = {
                    "id_image_file": image_base64,
                    "tailored_model_id": int(tailored_model_id),
                    "tailored_model_influence": tailored_model_influence,
                    "id_strength": id_strength,
                    "seed": seed
                }

                headers = bria_json_headers(api_key)

                response = requests.post(self.api_url, json=payload, headers=headers)
                if response.status_code != 200:
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")

                response_dict = response.json()
                image_response = requests.get(response_dict["image_res"])
                result_image = Image.open(io.BytesIO(image_response.content)).convert("RGB")

                # Convert to float32 tensor (H,W,C), 0-1
                result_array = np.array(result_image).astype(np.float32) / 255.0
                result_tensor = torch.from_numpy(result_array)

                batch_results.append(result_tensor)

            except Exception as e:
                print(f"[TailoredPortraitNode] Skipping image {idx} due to error: {e}")
                fallback_array = np.array(pil_image).astype(np.float32) / 255.0
                batch_results.append(torch.from_numpy(fallback_array))

        # Return list of tensors (avoids size/dtype mismatch)
        return (batch_results,)
