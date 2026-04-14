import requests
import torch

from .common import (
    bria_json_headers,
    image_to_base64,
    normalize_images_input,
    poll_status_until_completed,
    postprocess_image,
)


class GenerateImageNodeV2:
    """Standard Image Generation Node (multi-image compatible)"""

    api_url = "https://engine.prod.bria-api.com/v2/image/generate"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_token": ("STRING", {"default": "BRIA_API_TOKEN"}),
                "prompt": ("STRING",),
            },
            "optional": {
                "model_version": (["FIBO"], {"default": "FIBO"}),
                "structured_prompt": ("STRING", {"default": ""}),
                "negative_prompt": ("STRING",),
                "images": ("IMAGE",),
                "aspect_ratio": (
                    ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
                    {"default": "1:1"},
                ),
                "steps_num": ("INT", {"default": 50, "min": 35, "max": 50}),
                "guidance_scale": ("INT", {"default": 5, "min": 3, "max": 5}),
                "seed": ("STRING", {"default": "123456"}),  # Accept string to match previous node
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")  # images, structured_prompts, seeds
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
        structured_prompt,
        aspect_ratio,
        steps_num,
        guidance_scale,
        seed,
        negative_prompt=None,
        processed_image=None,
    ):
        payload = {
            "prompt": prompt,
            "model_version": model_version,
            "aspect_ratio": aspect_ratio,
            "steps_num": steps_num,
            "guidance_scale": guidance_scale,
            "seed": int(seed),
        }
        if structured_prompt:
            payload["structured_prompt"] = structured_prompt
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if processed_image is not None:
            payload["images"] = [image_to_base64(processed_image)]
        return payload

    def execute(
        self,
        api_token,
        prompt,
        model_version,
        structured_prompt,
        aspect_ratio,
        steps_num,
        guidance_scale,
        seed,
        negative_prompt=None,
        images=None,
    ):
        self._validate_token(api_token)
        images_list = normalize_images_input(images) if images is not None else [None]

        # Structured prompts per image
        if isinstance(structured_prompt, str):
            structured_prompts_list = structured_prompt.split("\n---\n")
        elif isinstance(structured_prompt, list):
            structured_prompts_list = structured_prompt
        else:
            structured_prompts_list = [""] * len(images_list)
        if len(structured_prompts_list) < len(images_list):
            structured_prompts_list += [structured_prompts_list[-1]] * (len(images_list) - len(structured_prompts_list))

        # Seeds per image
        if isinstance(seed, str):
            seed_values = [int(s.strip()) for s in seed.split(",")]
        else:
            seed_values = [int(seed)]
        if len(seed_values) < len(images_list):
            seed_values += [seed_values[-1]] * (len(images_list) - len(seed_values))

        batch_results = []
        batch_structured_prompts = []
        batch_seeds = []

        for idx, ref_image in enumerate(images_list):
            try:
                payload = self._build_payload(
                    prompt,
                    model_version,
                    structured_prompts_list[idx],
                    aspect_ratio,
                    steps_num,
                    guidance_scale,
                    seed_values[idx],
                    negative_prompt,
                    ref_image,
                )

                headers = bria_json_headers(api_token)
                response = requests.post(self.api_url, json=payload, headers=headers)

                if response.status_code not in (200, 202):
                    raise Exception(
                        f"API request failed with status code {response.status_code}: {response.text}"
                    )
                print(f"GenerateImageNodeV2 - Initial request successful for image {idx}, polling for completion...")
                response_dict = response.json()
                status_url = response_dict.get("status_url")
                if not status_url:
                    raise Exception("No status_url returned from API")

                final_response = poll_status_until_completed(status_url, api_token)
                result = final_response.get("result", {})
                result_image_url = result.get("image_url")
                structured_prompt_result = result.get("structured_prompt", "")
                used_seed = result.get("seed", seed_values[idx])

                image_response = requests.get(result_image_url)
                result_image = postprocess_image(image_response.content)

                batch_results.append(result_image)
                batch_structured_prompts.append(structured_prompt_result)
                batch_seeds.append(str(used_seed))

            except Exception as e:
                print(f"[GenerateImageNodeV2] Skipping iteration {idx} due to error: {e}")
                batch_results.append(torch.zeros((1, 512, 512, 3), dtype=torch.float32))
                batch_structured_prompts.append("")
                batch_seeds.append(str(seed_values[idx]))

        # Return all as strings for proper chaining
        output_batch = torch.cat(batch_results, dim=0)
        combined_structured_prompts = "\n---\n".join(batch_structured_prompts)
        combined_seeds = ",".join(batch_seeds)

        return output_batch, combined_structured_prompts, combined_seeds
