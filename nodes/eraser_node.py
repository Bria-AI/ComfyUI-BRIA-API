import numpy as np
import requests
from PIL import Image
import io
import base64
from torchvision.transforms import ToPILImage, ToTensor
import torch

from .base_node import BriaAPINode

# Eraser Node
class EraserNode(BriaAPINode):
    @staticmethod
    def INPUT_TYPES():
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
        super().__init__("https://engine.prod.bria-api.com/v1/eraser")  # Eraser API URL

    # Define the execute method as expected by ComfyUI
    def execute(self, image, mask, api_key):
        return self.process_request(image, mask, api_key)
    