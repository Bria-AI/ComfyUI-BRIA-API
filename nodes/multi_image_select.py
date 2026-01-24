import os
import json
from typing import List

import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image, ImageOps

try:
    from folder_paths import get_input_directory
except Exception:
    get_input_directory = None


IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")


def input_root() -> str:
    return os.path.abspath(get_input_directory() if get_input_directory else "input")


def parse_paths(value: str) -> List[str]:
    if not value:
        return []
    try:
        data = json.loads(value)
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        pass
    return []



class BriaMultiImageSelect:
    """
    Select multiple images and return them as a list of PIL Images.
    Images keep their original size.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "selected_paths": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Filled automatically by Select Images button",
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "filenames")
    FUNCTION = "load"
    CATEGORY = "API Nodes"

    def load(self, selected_paths: str):
        paths = parse_paths(selected_paths)
        if not paths:
            raise RuntimeError("BriaMultiImageSelect: No images selected")

        root = input_root()
        pil_images: List[Image.Image] = []
        names: List[str] = []

        for rel in paths:
            abs_path = os.path.join(root, rel)
            if not abs_path.lower().endswith(IMG_EXTS):
                continue
            if not os.path.isfile(abs_path):
                continue

            pil_images.append(Image.open(abs_path))
            names.append(os.path.splitext(os.path.basename(rel))[0])

        if not pil_images:
            raise RuntimeError("BriaMultiImageSelect: No valid images found")

        filenames = ", ".join(names)
        return (pil_images, filenames)
