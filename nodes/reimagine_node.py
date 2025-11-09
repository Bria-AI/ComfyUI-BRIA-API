import requests

from .common import deserialize_and_get_comfy_key, postprocess_image, preprocess_image, image_to_base64


class ReimagineNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "api_key": ("STRING", ),
                "prompt": ("STRING",),
            },
            "optional": {
                "seed": ("INT", {"default": -1}),
                "steps_num": ("INT", {"default": 12}), # if used with tailored, possibly get this from the tailored model info node
                "structure_ref_influence": ("FLOAT", {"default": 0.75}),
                "fast": ("INT", {"default": 0}), # if used with tailored, possibly get this from the tailored model info node
                "structure_image": ("IMAGE", ),
                "tailored_model_id": ("STRING", ),
                "tailored_model_influence": ("FLOAT", {"default": 0.5}),
                "tailored_generation_prefix": ("STRING",), # if used with tailored, possibly get this from the tailored model info node
                "content_moderation": ("INT", {"default": 0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/reimagine" #"http://0.0.0.0:5000/v1/reimagine"

    def execute(
            self, api_key, prompt, seed, 
            steps_num, fast, structure_ref_influence, structure_image=None,
            tailored_model_id=None, tailored_model_influence=None, tailored_generation_prefix=None,
            content_moderation=0,
        ):    
        api_key = deserialize_and_get_comfy_key(api_key)    
        payload = {
            "prompt": tailored_generation_prefix + prompt,
            "num_results": 1,
            "sync": True,
            "seed": seed,
            "steps_num": steps_num,
            "include_generation_prefix": False,
            "content_moderation": content_moderation,
        }
        if structure_image is not None:
            structure_image = preprocess_image(structure_image)
            structure_image = image_to_base64(structure_image)
            payload["structure_image_file"] = structure_image
            payload["structure_ref_influence"] = structure_ref_influence
        if tailored_model_id is not None and tailored_model_id != "":
            payload["tailored_model_id"] = tailored_model_id
            payload["tailored_model_influence"] = tailored_model_influence
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
