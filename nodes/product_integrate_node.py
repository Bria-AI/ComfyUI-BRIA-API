import requests
import torch

from .common import (
    bria_json_headers,
    image_to_base64,
    poll_status_until_completed,
    postprocess_image,
    preprocess_image,
)


class ProductIntegrateNode:
    """Product Integrate Node - Integrate a single product into a background scene"""

    api_url = "https://engine.prod.bria-api.com/v2/image/edit/product/integrate"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_token": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "scene": ("IMAGE",),
                "product_image": ("IMAGE",),
                "x_coordinate": ("INT", {"default": 0, "min": 0, "max": 10000}),
                "y_coordinate": ("INT", {"default": 0, "min": 0, "max": 10000}),
                "width": ("INT", {"default": 512, "min": 1, "max": 10000}),
                "height": ("INT", {"default": 512, "min": 1, "max": 10000}),
            },
            "optional": {
                "seed": ("STRING", {"default": "123456"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("IMAGE", "seed")
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def _validate_token(self, api_token: str):
        if api_token.strip() == "" or api_token.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API token.")

    def _build_payload(
        self,
        scene_image,
        product_image,
        x_coordinate,
        y_coordinate,
        width,
        height,
        seed,
    ):
        payload = {
            "scene": image_to_base64(scene_image),
            "products": [
                {
                    "image": image_to_base64(product_image),
                    "coordinates": {
                        "x": x_coordinate,
                        "y": y_coordinate,
                        "width": width,
                        "height": height,
                    }
                }
            ],
            "seed": int(seed),
        }

        return payload

    def execute(
        self,
        api_token,
        scene,
        product_image,
        x_coordinate,
        y_coordinate,
        width,
        height,
        seed,
    ):
        self._validate_token(api_token)
        # Process single scene image
        if isinstance(scene, torch.Tensor):
            processed_scene = preprocess_image(scene)
        if isinstance(product_image, torch.Tensor):
            processed_product = preprocess_image(product_image)

        payload = self._build_payload(
            processed_scene,
            processed_product,
            x_coordinate,
            y_coordinate,
            width,
            height,
            seed,
        )

        headers = bria_json_headers(api_token)

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)

            if response.status_code in (200, 202):
                print(
                    f"Initial product integrate request successful, polling for completion..."
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
                used_seed = result.get("seed", seed)

                image_response = requests.get(result_image_url)
                result_image = postprocess_image(image_response.content)

                return (result_image, used_seed)
            else:
                raise Exception(
                    f"API request failed with status code {response.status_code} {response.text}"
                )

        except Exception as e:
            raise Exception(f"[ProductIntegrateNode] Error: {e}")
