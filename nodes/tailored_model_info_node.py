import requests


class TailoredModelInfoNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "model_id": ("STRING",),
                "api_key": ("STRING", )
            }
        }

    RETURN_TYPES = ("STRING", "STRING","INT", "INT", )
    RETURN_NAMES = ("generation_prefix", "model_id", "default_fast",  "default_steps_num", )
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/tailored-gen/models/"

    # Define the execute method as expected by ComfyUI
    def execute(self, model_id, api_key):
        response = requests.get(
            self.api_url + model_id,
            headers={"api_token": api_key}
        )
        if response.status_code == 200:
            generation_prefix = response.json()["generation_prefix"]
            training_version = response.json()["training_version"]
            default_fast = 1 if training_version == "light" else 0
            default_steps_num = 8 if training_version == "light" else 30
            return (generation_prefix, model_id, default_fast, default_steps_num,)
        else:
            raise Exception(f"Error: API request failed with status code {response.status_code} and text {response.text}")
