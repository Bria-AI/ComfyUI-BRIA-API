import requests

from .common import postprocess_image, preprocess_image, image_to_base64


class TailoredGenNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "model_id": ("STRING",),
                "api_key": ("STRING", ),
            },
            "optional": {
                "prompt": ("STRING",),
                "generation_prefix": ("STRING",), # possibly get this from the tailored model info node
                "aspect_ratio": (["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"], {"default": "4:3"}),
                "seed": ("INT", {"default": -1}),
                "model_influence": ("FLOAT", {"default": 1.0}),
                "negative_prompt": ("STRING", {"default": ""}),
                "fast": ("INT", {"default": 1}), # possibly get this from the tailored model info node
                "steps_num": ("INT", {"default": 8}), # possibly get this from the tailored model info node
                "guidance_method_1": (["controlnet_canny", "controlnet_depth", "controlnet_recoloring", "controlnet_color_grid"], {"default": "controlnet_canny"}),
                "guidance_method_1_scale": ("FLOAT", {"default": 1.0}),
                "guidance_method_1_image": ("IMAGE", ),
                "guidance_method_2": (["controlnet_canny", "controlnet_depth", "controlnet_recoloring", "controlnet_color_grid"], {"default": "controlnet_canny"}),
                "guidance_method_2_scale": ("FLOAT", {"default": 1.0}),
                "guidance_method_2_image": ("IMAGE", ),
                "content_moderation": ("INT", {"default": 0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/text-to-image/tailored/" #"http://0.0.0.0:5000/v1/text-to-image/tailored/"

    def execute(
            self, model_id, api_key, prompt, generation_prefix, aspect_ratio, 
            seed, model_influence, negative_prompt, fast, steps_num,
            guidance_method_1=None, guidance_method_1_scale=None, guidance_method_1_image=None,
            guidance_method_2=None, guidance_method_2_scale=None, guidance_method_2_image=None,
            content_moderation=0,
        ):
        payload = {
            "prompt": generation_prefix + prompt,
            "num_results": 1,
            "aspect_ratio": aspect_ratio,
            "sync": True,
            "seed": seed,
            "model_influence": model_influence,
            "negative_prompt": negative_prompt,
            "fast": fast,
            "steps_num": steps_num,
            "include_generation_prefix": False,
            "content_moderation": content_moderation,
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
        response = requests.post(
            self.api_url + model_id,
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
