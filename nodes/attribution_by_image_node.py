import requests

from .common import (
    bria_json_headers,
    image_to_base64,
    normalize_images_input,
    poll_status_until_completed,
    to_pil_safe,
)

class AttributionByImageNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "images": ("IMAGE",),
                "model_version": (["2.3", "3.0", "3.2"], {"default": "2.3"}),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("api_response",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/attribution/by_image"

    def execute(self, images, model_version, api_key):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        images = normalize_images_input(images)

        batch_results = []

        for idx, pil_image in enumerate(images):
            try:
                image_base64 = image_to_base64(pil_image)

                payload = {
                    "image": image_base64,
                    "model_version": model_version,
                }

                headers = bria_json_headers(api_key)

                response = requests.post(self.api_url, json=payload, headers=headers)
                
                if response.status_code not in (200, 202):
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")

                # Poll until completion
                response_dict = response.json()
                status_url = response_dict.get('status_url')
                if not status_url:
                    raise Exception("No status_url returned from API")

                final_response = poll_status_until_completed(status_url, api_key)
                content = str(final_response.get("result", {}).get("content", ""))
                batch_results.append(content)

            except Exception as e:
                print(f"[AttributionByImageNode] Skipping image {idx} due to error: {e}")
                batch_results.append("")

        # Join all responses with a delimiter
        combined_response = "\n---\n".join(batch_results)
        return (combined_response,)
