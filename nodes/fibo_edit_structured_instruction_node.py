import requests
import torch

from .common import (
    deserialize_and_get_comfy_key,
    image_to_base64,
    poll_status_until_completed,
    preprocess_image,
)


class FIBOEditStructuredInstructionNode:
    """FIBO Edit Structured Instruction Node - Generate structured instructions for image editing"""

    api_url = "https://engine.prod.bria-api.com/v2/structured_instruction/generate"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_token": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "image": ("IMAGE",),
                "instruction": ("STRING",),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("structured_instruction",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def _validate_token(self, api_token: str):
        if api_token.strip() == "" or api_token.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API token.")

    def _build_payload(self, image, instruction):
        # Process image
        if isinstance(image, torch.Tensor):
            processed_image = preprocess_image(image)
        else:
            processed_image = image

        payload = {
            "instruction": instruction,
            "images": [image_to_base64(processed_image)],
        }

        return payload

    def execute(self, api_token, image, instruction):
        self._validate_token(api_token)
        payload = self._build_payload(image, instruction)
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
                structured_instruction = result.get("structured_instruction", "")

                return (structured_instruction,)

            raise Exception(
                f"Error: API request failed with status code {response.status_code} {response.text}"
            )

        except Exception as e:
            raise Exception(f"{e}")