import requests
from .common import (
    deserialize_and_get_comfy_key,
    image_to_base64,
    poll_status_until_completed,
    preprocess_image,
)
import torch


class _BaseGenerateStructuredPromptNodeV2:
    """Base class for structured prompt generation nodes (standard & lite)."""

    api_url = None  # Each subclass must define its API endpoint

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_token": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "prompt": ("STRING",),
            },
            "optional": {
                "structured_prompt": ("STRING",),
                "images": ("IMAGE",),
                "seed": ("INT", {"default": 123456}),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("structured_prompt", "seed")
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def _validate_token(self, api_token: str):
        if api_token.strip() == "" or api_token.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API token.")

    def _build_payload(
        self,
        prompt,
        seed,
        structured_prompt,
        images=None
    ):
        payload = {
            "prompt": prompt,
            "seed": seed,
            "structured_prompt":structured_prompt
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
        seed,
        structured_prompt,
        images=None,
    ):
        self._validate_token(api_token)
        payload = self._build_payload(
            prompt,
            seed,
            structured_prompt,
            images
        )
        api_token = deserialize_and_get_comfy_key(api_token)

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
                structured_prompt = result.get("structured_prompt", "")
                used_seed = result.get("seed", seed)

                return (structured_prompt, used_seed)

            raise Exception(
                f"Error: API request failed with status code {response.status_code} {response.text}"
            )

        except Exception as e:
            raise Exception(f"{e}")


class GenerateStructuredPromptNodeV2(_BaseGenerateStructuredPromptNodeV2):
    """Standard Structured Prompt Generation Node"""
    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/structured_prompt/generate"


class GenerateStructuredPromptLiteNodeV2(_BaseGenerateStructuredPromptNodeV2):
    """Lite Structured Prompt Generation Node"""
    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/structured_prompt/generate/lite"

