import requests
import torch

from .common import (
    bria_asset_headers,
    bria_json_headers,
    image_to_base64,
    poll_status_until_completed,
    preprocess_image,
    preprocess_mask,
    postprocess_image,
)


class FIBOEditNode:
    """FIBO Edit Node - Edit images with instructions"""

    api_url = "https://engine.prod.bria-api.com/v2/image/edit"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_token": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "images": ("IMAGE",),
            },
            "optional": {
                "instruction": ("STRING",),
                "mask": ("MASK",),
                "structured_instruction": ("STRING",),
                "negative_prompt": ("STRING",),
                "steps_num": (
                    "INT",
                    {
                        "default": 30,
                        "min": 1,
                        "max": 100,
                    },
                ),
                "guidance_scale": (
                    "INT",
                    {
                        "default": 5,
                        "min": 1,
                        "max": 20,
                    },
                ),
                "seed": ("INT", {"default": 123456}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("IMAGE", "structured_instruction", "seed")
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def _validate_token(self, api_token: str):
        if api_token.strip() == "" or api_token.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API token.")

    def _build_payload(
        self,
        instruction,
        images,
        mask=None,
        structured_instruction=None,
        negative_prompt=None,
        steps_num=50,
        guidance_scale=5,
        seed=123456,
    ):
        # Process images
        if isinstance(images, torch.Tensor):
            processed_images = preprocess_image(images)
        else:
            processed_images = images

        payload = {
            "images": [image_to_base64(processed_images)],
            "steps_num": steps_num,
            "guidance_scale": guidance_scale,
            "seed": seed,
        }

        # Add optional mask
        if mask is not None:
            if isinstance(mask, torch.Tensor):
                processed_mask = preprocess_mask(mask)
            else:
                processed_mask = mask
            payload["mask"] = image_to_base64(processed_mask)

        # Add optional structured_instruction
        if structured_instruction:
            payload["structured_instruction"] = structured_instruction
         # Add optional structured_instruction
        if instruction:
            payload["instruction"] = instruction
        # Add optional negative_prompt
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        return payload

    def execute(
        self,
        api_token,
        instruction,
        images,
        mask=None,
        structured_instruction=None,
        negative_prompt=None,
        steps_num=50,
        guidance_scale=5,
        seed=123456,
    ):
        self._validate_token(api_token)
        payload = self._build_payload(
            instruction,
            images,
            mask,
            structured_instruction,
            negative_prompt,
            steps_num,
            guidance_scale,
            seed,
        )
        headers = bria_json_headers(api_token)

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

                image_response = requests.get(
                    result_image_url,
                    headers=bria_asset_headers(),
                )
                result_image = postprocess_image(image_response.content)

                return (result_image, structured_prompt, used_seed)

            raise Exception(
                f"Error: API request failed with status code {response.status_code} {response.text}"
            )

        except Exception as e:
            raise Exception(f"{e}")