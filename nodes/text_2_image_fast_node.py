import requests

from .common import postprocess_image, preprocess_image, image_to_base64


class Text2ImageFastNode():
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
                "steps_num": ("INT", {"default": 8}), 
                "prompt_enhancement": ("INT", {"default": 0}),
                "guidance_method_1": (["controlnet_canny", "controlnet_depth", "controlnet_recoloring", "controlnet_color_grid"], {"default": "controlnet_canny"}),
                "guidance_method_1_scale": ("FLOAT", {"default": 1.0}),
                "guidance_method_1_image": ("IMAGE", ),
                "guidance_method_2": (["controlnet_canny", "controlnet_depth", "controlnet_recoloring", "controlnet_color_grid"], {"default": "controlnet_canny"}),
                "guidance_method_2_scale": ("FLOAT", {"default": 1.0}),
                "guidance_method_2_image": ("IMAGE", ),
                "image_prompt_mode": (["regular", "style_only"], {"default": "regular"}),
                "image_prompt_image": ("IMAGE", ),
                "image_prompt_scale": ("FLOAT", {"default": 1.0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/text-to-image/fast/2.3" #"http://0.0.0.0:5000/v1/text-to-image/fast/2.3"

    def execute(
            self, api_key, prompt, aspect_ratio, seed, 
            steps_num, prompt_enhancement,
            guidance_method_1=None, guidance_method_1_scale=None, guidance_method_1_image=None,
            guidance_method_2=None, guidance_method_2_scale=None, guidance_method_2_image=None,
            image_prompt_mode=None, image_prompt_image=None, image_prompt_scale=None,
        ):
        prompt_enhancement = bool(prompt_enhancement)
        payload = {
            "prompt": prompt,
            "num_results": 1,
            "aspect_ratio": aspect_ratio,
            "sync": True,
            "seed": seed,
            "steps_num": steps_num,
            "prompt_enhancement": prompt_enhancement,
        }
        if guidance_method_1_image is not None:
            guidance_method_1_image = preprocess_image(guidance_method_1_image)
            guidance_method_1_image = image_to_base64(guidance_method_1_image)
            payload["guidance_method_1"] = guidance_method_1
            payload["guidance_method_1_scale"] = guidance_method_1_scale
            payload["guidance_method_1_image_file"] = guidance_method_1_image
        if guidance_method_2_image is not None:
            guidance_method_2_image = preprocess_image(guidance_method_2_image)
            guidance_method_2_image = image_to_base64(guidance_method_2_image)
            payload["guidance_method_2"] = guidance_method_2
            payload["guidance_method_2_scale"] = guidance_method_2_scale
            payload["guidance_method_2_image_file"] = guidance_method_2_image
        if image_prompt_image is not None:
            image_prompt_image = preprocess_image(image_prompt_image)
            image_prompt_image = image_to_base64(image_prompt_image)
            payload["image_prompt_mode"] = image_prompt_mode
            payload["image_prompt_file"] = image_prompt_image
            payload["image_prompt_scale"] = image_prompt_scale
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
