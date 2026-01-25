import requests

from .common import (
    deserialize_and_get_comfy_key,
    normalize_images_input,
    image_to_base64,
    poll_status_until_completed,
)


class GenerateStructuredPromptNodeV2:
    """Structured Prompt Generation Node (multi-image compatible)"""

    api_url = "https://engine.prod.bria-api.com/v2/structured_prompt/generate"

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
                "seed": ("STRING", {"default": "123456"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")  # structured_prompts, seeds as comma-separated string
    RETURN_NAMES = ("structured_prompt", "seed")
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def _validate_token(self, api_token: str):
        if api_token.strip() == "" or api_token.strip() == "BRIA_API_TOKEN":
            raise Exception("Please insert a valid API token.")

    def _build_payload(self, prompt, seed, structured_prompt, processed_image=None):
        payload = {"prompt": prompt, "seed": int(seed)}
        if structured_prompt:
            payload["structured_prompt"] = structured_prompt
        if processed_image is not None:
            payload["images"] = [image_to_base64(processed_image)]
        return payload

    def execute(self, api_token, prompt, seed, structured_prompt, images=None):
        self._validate_token(api_token)
        api_token = deserialize_and_get_comfy_key(api_token)

        images_list = normalize_images_input(images) if images is not None else [None]

        # Seeds per image
        if isinstance(seed, str):
            seed_values = [int(s.strip()) for s in seed.split(",")]
        else:
            seed_values = [seed]
        if len(seed_values) < len(images_list):
            seed_values += [seed_values[-1]] * (len(images_list) - len(seed_values))

        # Structured prompts per image
        if isinstance(structured_prompt, str):
            structured_prompts_list = structured_prompt.split("\n---\n")
        elif isinstance(structured_prompt, list):
            structured_prompts_list = structured_prompt
        else:
            structured_prompts_list = [""] * len(images_list)
        if len(structured_prompts_list) < len(images_list):
            structured_prompts_list += [structured_prompts_list[-1]] * (len(images_list) - len(structured_prompts_list))

        batch_structured_prompts = []
        batch_seeds = []

        for idx, image in enumerate(images_list):
            try:

                payload = self._build_payload(
                    prompt,
                    seed_values[idx],
                    structured_prompts_list[idx],
                    image
                )

                headers = {"Content-Type": "application/json", "api_token": api_token}
                response = requests.post(self.api_url, json=payload, headers=headers)
                if response.status_code not in (200, 202):
                    raise Exception(
                        f"API request failed with status code {response.status_code}: {response.text}"
                    )

                response_dict = response.json()
                print(f"GenerateStructuredPromptNodeV2 - Initial request successful for image {idx}, polling for completion...")

                status_url = response_dict.get("status_url")
                if not status_url:
                    raise Exception("No status_url returned from API")

                final_response = poll_status_until_completed(status_url, api_token)

                result = final_response.get("result", {})
                structured_prompt_result = result.get("structured_prompt", "")
                used_seed = result.get("seed", seed_values[idx])

                batch_structured_prompts.append(structured_prompt_result)
                batch_seeds.append(str(used_seed))  # Keep as string for passing between nodes

            except Exception as e:
                print(f"[GenerateStructuredPromptNodeV2] Skipping iteration {idx} due to error: {e}")
                batch_structured_prompts.append("")
                batch_seeds.append(str(seed_values[idx]))

        # Return combined structured prompts and seeds as strings
        combined_prompts = "\n---\n".join(batch_structured_prompts)
        combined_seeds = ",".join(batch_seeds)
        return combined_prompts, combined_seeds
