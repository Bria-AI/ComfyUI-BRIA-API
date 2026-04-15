import requests
from .common import (
    bria_json_headers,
    image_to_base64,
    normalize_images_input,
    poll_status_until_completed,
)


class FIBOEditStructuredInstructionNode:
    """FIBO Edit Structured Instruction Node - Generate structured instructions for image editing"""

    api_url = "https://engine.prod.bria-api.com/v2/structured_instruction/generate"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_token": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "images": ("IMAGE",),
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

    def _build_payload(self, processed_image, instruction):
        payload = {
            "instruction": instruction,
            "images": [image_to_base64(processed_image)],
        }
        return payload

    def execute(self, api_token, images, instruction):
        self._validate_token(api_token)
        # Normalize input to list of PIL images
        images = normalize_images_input(images)

        batch_results = []

        for idx, pil_image in enumerate(images):
            try:
                payload = self._build_payload(pil_image, instruction)
                headers = bria_json_headers(api_token)

                response = requests.post(self.api_url, json=payload, headers=headers)

                if response.status_code not in (200, 202):
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")

                print(f"Initial request successful for image {idx}, polling for completion...")
                response_dict = response.json()
                status_url = response_dict.get("status_url")
                if not status_url:
                    raise Exception("No status_url returned from API")

                final_response = poll_status_until_completed(status_url, api_token)
                result = final_response.get("result", {})
                structured_instruction = result.get("structured_instruction", "")
                batch_results.append(structured_instruction)

            except Exception as e:
                print(f"[FIBOEditStructuredInstructionNode] Skipping image {idx} due to error: {e}")
                batch_results.append("")

        combined_instructions = "\n---\n".join(batch_results)
        return (combined_instructions,)