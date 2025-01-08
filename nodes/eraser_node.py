from .common import process_request

class EraserNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "mask": ("MASK",),  # Binary mask input
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"})  # API Key input with a default value
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v1/eraser"  # Eraser API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, mask, api_key):
        return process_request(self.api_url, image, mask, api_key)
    