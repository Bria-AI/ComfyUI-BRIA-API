import requests
import torch

from .common import deserialize_and_get_comfy_key, preprocess_image, image_to_base64, poll_status_until_completed

class AttributionByImageNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),
                "model_version": (["2.3", "3.0","3.2"], {"default": "2.3"}),
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"}),
            },              
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("api_response",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/attribution/by_image"

    # Define the execute method as expected by ComfyUI
    def execute(self, image, model_version, api_key):
        if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API key.")
        api_key = deserialize_and_get_comfy_key(api_key)

        # Check if image is tensor, if so, convert to NumPy array
        if isinstance(image, torch.Tensor):
            image = preprocess_image(image)

        # Convert image to base64 for the new API format
        image_base64 = image_to_base64(image)
        payload = {
            "image": image_base64,
            "model_version": model_version,
        }

        headers = {
            "Content-Type": "application/json",
            "api_token": f"{api_key}"
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200 or response.status_code == 202:
                print('Initial Attribution via Images API request successful, polling for completion...')
                response_dict = response.json()

                status_url = response_dict.get('status_url')
                request_id = response_dict.get('request_id')
                
                if not status_url:
                    raise Exception("No status_url returned from API")
                
                print(f"Request ID: {request_id}, Status URL: {status_url}")
                
                final_response = poll_status_until_completed(status_url, api_key)
                return (str(final_response.get("result",{}).get("content")),)
            else:
                raise Exception(f"Error: API request failed with status code {response.status_code} {response.text}")
        except Exception as e:
            raise Exception(f"{e}")
