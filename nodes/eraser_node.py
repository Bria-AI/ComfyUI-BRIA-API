from .common import process_request

class EraserNode():
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),  # Input image from another node
                "mask": ("MASK",),  # Binary mask input
                "api_key": ("STRING", {"default": "BRIA_API_TOKEN"})  # API Key input with a default value
            },
            "optional": {
                "visual_input_content_moderation": ("BOOLEAN", {"default": False}), 
                "visual_output_content_moderation": ("BOOLEAN", {"default": False}), 
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"  # This is the method that will be executed

    def __init__(self):
        self.api_url = "https://engine.prod.bria-api.com/v2/image/edit/erase"  # Eraser API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, mask, api_key, visual_input_content_moderation, visual_output_content_moderation):
        return process_request(self.api_url, image, mask, api_key, visual_input_content_moderation, visual_output_content_moderation)
    