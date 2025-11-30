import requests
from .common import deserialize_and_get_comfy_key, poll_status_until_completed, postprocess_image


class _BaseRefineImageNodeV2:
    """Base class for refine image nodes (standard & pro)."""

    api_url = None  # Must be overridden by subclasses
    generate_api_url = None
    supports_negative_prompt = True  # Can be overridden by subclasses

    @classmethod
    def INPUT_TYPES(cls):
        optional_inputs = {
            "model_version": (["FIBO"], {"default": "FIBO"}),
            "aspect_ratio": (
                ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
                {"default": "1:1"},
            ),
            "steps_num": ("INT", {"default": 50, "min": 20, "max": 50}),
            "guidance_scale": ("INT", {"default": 5, "min": 3, "max": 5}),
            "seed": ("INT", {"default": 123456}),
        }
        
        # Add negative_prompt only if supported
        if cls.supports_negative_prompt:
            optional_inputs["negative_prompt"] = ("STRING", {"default": ""})
        
        return {
            "required": {
                "api_token": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "prompt": ("STRING",),
                "structured_prompt": ("STRING",),
            },
            "optional": optional_inputs,
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
        structured_prompt,
        model_version,
        aspect_ratio,
        steps_num,
        guidance_scale,
        seed,
        negative_prompt=None,
    ):
        payload = {
            "prompt": prompt,
            "model_version": model_version,
            "aspect_ratio": aspect_ratio,
            "steps_num": steps_num,
            "guidance_scale": guidance_scale,
            "seed": seed,
            "structured_prompt": structured_prompt,
        }
        
        if self.supports_negative_prompt and negative_prompt is not None:
            payload["negative_prompt"] = negative_prompt
        
        return payload

    def execute(
        self,
        api_token,
        prompt,
        structured_prompt,
        model_version,
        aspect_ratio,
        steps_num,
        guidance_scale,
        seed,
        negative_prompt=None,
    ):
        self._validate_token(api_token)
        payload = self._build_payload(
            prompt,
            structured_prompt,
            model_version,
            aspect_ratio,
            steps_num,
            guidance_scale,
            seed,
            negative_prompt,
        )
        api_token = deserialize_and_get_comfy_key(api_token)
        headers = {"Content-Type": "application/json", "api_token": api_token}

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)

            if response.status_code in (200, 202):
                print(f"Initial refine request successful to {self.api_url}, polling for completion...")
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

                # Step 2 to call genearte image
                payloadForImageGenetrate = {
                    "prompt": prompt,
                    "structured_prompt":structured_prompt,
                    "model_version": model_version,
                    "aspect_ratio": aspect_ratio,
                    "steps_num": steps_num,
                    "guidance_scale": guidance_scale,
                    "seed": used_seed,
                }
                
                # Add negative_prompt only if supported and provided
                if self.supports_negative_prompt and negative_prompt is not None:
                    payloadForImageGenetrate["negative_prompt"] = negative_prompt
                
                headers = {"Content-Type": "application/json", "api_token": api_token}

                response = requests.post(self.generate_api_url, json=payloadForImageGenetrate, headers=headers)

                if response.status_code in (200, 202):
                    print(
                        f"Initial request successful to {self.generate_api_url}, polling for completion..."
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


class RefineImageNodeV2(_BaseRefineImageNodeV2):
    """Standard Refine Image Node"""
    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/structured_prompt/generate"
        self.generate_api_url = "https://engine.prod.bria-api.com/v2/image/generate"


class RefineImageLiteNodeV2(_BaseRefineImageNodeV2):
    """Lite Refine Image Node"""
    supports_negative_prompt = False
    
    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/structured_prompt/generate/lite"
        self.generate_api_url = "https://engine.prod.bria-api.com/v2/image/generate/lite"