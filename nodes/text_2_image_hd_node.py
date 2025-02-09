import requests

from .common import postprocess_image


class Text2ImageHDNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "api_key": ("STRING", ),
            },
            "optional": {
                "prompt": ("STRING",),
                "aspect_ratio": (["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"], {"default": "4:3"}),
                "seed": ("INT", {"default": -1}),
                "negative_prompt": ("STRING", {"default": ""}),
                "steps_num": ("INT", {"default": 30}), 
                "prompt_enhancement": ("INT", {"default": 0}),
                "text_guidance_scale": ("INT", {"default": 5}),
                "medium": (["photography", "art", "none"], {"default": "none"}),
                "content_moderation": ("INT", {"default": 0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/text-to-image/hd/2.3" #"http://0.0.0.0:5000/v1/text-to-image/hd/2.3"

    def execute(
            self, api_key, prompt, aspect_ratio, seed, negative_prompt, 
            steps_num, prompt_enhancement, text_guidance_scale, medium, content_moderation=0,
        ):
        payload = {
            "prompt": prompt,
            "num_results": 1,
            "aspect_ratio": aspect_ratio,
            "sync": True,
            "seed": seed,
            "negative_prompt": negative_prompt,
            "steps_num": steps_num,
            "text_guidance_scale": text_guidance_scale,
            "prompt_enhancement": prompt_enhancement,
            "content_moderation": content_moderation,
        }
        if medium != "none":
            payload["medium"] = medium
        response = requests.post(
            self.api_url,
            json=payload,
            headers={"api_token": api_key}
        )
        if response.status_code == 200:
                response_dict = response.json()
                image_response = requests.get(response_dict['result'][0]["urls"][0])
                result_image = postprocess_image(image_response.content)
                return (result_image,)
        else:
            raise Exception(f"Error: API request failed with status code {response.status_code} and text {response.text}")
