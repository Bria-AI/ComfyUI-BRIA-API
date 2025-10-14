import requests
import torch

from .common import (
    postprocess_image,
    preprocess_image,
    image_to_base64,
    poll_status_until_completed,
)


class Text2ImageGaiaGenerateNode:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "api_token": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "prompt": ("STRING",),
            },
            "optional": {
                "mode": (["GAIA"], {"default": "GAIA"}),
                "negative_prompt": ("STRING", {"default": ""}),
                "image": ("IMAGE",),
                "aspect_ratio": (
                    ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
                    {"default": "1:1"},
                ),
                "steps_num": ("INT", {"default": 30, "min": 20, "max": 50}),
                "guidance_scale": ("INT", {"default": 5, "min": 3, "max": 5}),
                "seed": ("INT", {"default": 123456}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "structured_prompt", "seed")
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/generate"

    def execute(
        self,
        api_token,
        prompt,
        mode,
        negative_prompt,
        aspect_ratio,
        steps_num,
        guidance_scale,
        seed,
        image=None,
    ):

        if api_token.strip() == "" or api_token.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API token.")

        payload = {
            "prompt": prompt,
            "mode": mode,
            "negative_prompt": negative_prompt,
            "aspect_ratio": aspect_ratio,
            "steps_num": steps_num,
            "guidance_scale": guidance_scale,
            "seed": seed,
        }

        # Add image if provided
        if image is not None:
            if isinstance(image, torch.Tensor):
                image = preprocess_image(image)
            image_base64 = image_to_base64(image)
            payload["image"] = image_base64

        headers = {"Content-Type": "application/json", "api_token": api_token}

        try:
            # Send initial request to get status URL
            response = requests.post(self.api_url, json=payload, headers=headers)

            if response.status_code == 200 or response.status_code == 202:
                print(
                    "Initial GAIA generate request successful, polling for completion..."
                )
                response_dict = response.json()
                status_url = response_dict.get("status_url")
                request_id = response_dict.get("request_id")

                if not status_url:
                    raise Exception("No status_url returned from API")

                print(f"Request ID: {request_id}, Status URL: {status_url}")

                # Poll for completion
                final_response = poll_status_until_completed(status_url, api_token)

                # Extract results
                result = final_response.get("result", {})
                print(result)
                result_image_url = result.get("image_url")
                structured_prompt = result.get("structured_prompt", "")
                used_seed = result.get("seed")

                # Download and process the result image
                image_response = requests.get(result_image_url)
                result_image = postprocess_image(image_response.content)

                return (result_image, structured_prompt, used_seed)
            else:
                raise Exception(
                    f"Error: API request failed with status code {response.status_code} {response.text}"
                )

        except Exception as e:
            raise Exception(f"{e}")
