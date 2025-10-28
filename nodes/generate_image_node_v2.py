import requests
import torch

from .common import (
    postprocess_image,
    preprocess_image,
    image_to_base64,
    poll_status_until_completed,
)


class _BaseGenerateImageNodeV2:
    """Base class for image generation nodes (standard & pro)."""

    api_url = None  # Each subclass must define its API endpoint

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_token": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "prompt": ("STRING",),
            },
            "optional": {
                "model_version": (["FIBO"], {"default": "FIBO"}),
                "negative_prompt": ("STRING", {"default": ""}),
                "images": ("IMAGE",),
                "aspect_ratio": (
                    ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
                    {"default": "1:1"},
                ),
                "steps_num": ("INT", {"default": 50, "min": 20, "max": 50}),
                "guidance_scale": ("INT", {"default": 5, "min": 3, "max": 5}),
                "seed": ("INT", {"default": 123456}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "structured_prompt", "seed")
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def _validate_token(self, api_token: str):
        if api_token.strip() == "" or api_token.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API token.")

    def _build_payload(
        self,
        prompt,
        model_version,
        negative_prompt,
        aspect_ratio,
        steps_num,
        guidance_scale,
        seed,
        images=None,
    ):
        payload = {
            "prompt": prompt,
            "model_version": model_version,
            "negative_prompt": negative_prompt,
            "aspect_ratio": aspect_ratio,
            "steps_num": steps_num,
            "guidance_scale": guidance_scale,
            "seed": seed,
        }

        if images is not None:
            if isinstance(images, torch.Tensor):
                preprocess_images = preprocess_image(images)
            payload["images"] = [image_to_base64(preprocess_images)]


        return payload

    def execute(
        self,
        api_token,
        prompt,
        model_version,
        negative_prompt,
        aspect_ratio,
        steps_num,
        guidance_scale,
        seed,
        images=None,
    ):
        self._validate_token(api_token)
        payload = self._build_payload(
            prompt,
            model_version,
            negative_prompt,
            aspect_ratio,
            steps_num,
            guidance_scale,
            seed,
            images,
        )

        headers = {"Content-Type": "application/json", "api_token": api_token}

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)

            if response.status_code in (200, 202):
                print(
                    f"Initial request successful to {self.api_url}, polling for completion..."
                )
                response_dict = response.json()
                status_url = response_dict.get("status_url")
                request_id = response_dict.get("request_id")

                if not status_url:
                    raise Exception("No status_url returned from API")

                print(f"Request ID: {request_id}, Status URL: {status_url}")

                final_response = poll_status_until_completed(status_url, api_token)

                result = final_response.get("result", {})
                result_image_url = result.get("image_url")
                structured_prompt = result.get("structured_prompt", "")
                used_seed = result.get("seed")

                image_response = requests.get(result_image_url)
                result_image = postprocess_image(image_response.content)

                return (result_image, structured_prompt, used_seed)

            raise Exception(
                f"Error: API request failed with status code {response.status_code} {response.text}"
            )

        except Exception as e:
            raise Exception(f"{e}")


class GenerateImageNodeV2(_BaseGenerateImageNodeV2):
    """Standard Image Generation Node"""
    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/generate"


class GenerateImageProNodeV2(_BaseGenerateImageNodeV2):
    """Pro Image Generation Node"""
    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/generate/pro"
