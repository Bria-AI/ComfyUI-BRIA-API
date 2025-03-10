from nodes.tailored_portrait_node import TailoredPortraitNode
from .nodes import (EraserNode, GenFillNode, ImageExpansionNode, ReplaceBgNode, RmbgNode, RemoveForegroundNode, ShotByTextNode, ShotByImageNode, TailoredGenNode,
                     TailoredModelInfoNode, Text2ImageBaseNode, Text2ImageFastNode, Text2ImageHDNode,
                     ReimagineNode)
# Map the node class to a name used internally by ComfyUI
NODE_CLASS_MAPPINGS = {
    "BriaEraser": EraserNode,  # Return the class, not an instance
    "BriaGenFill": GenFillNode,
    "ImageExpansionNode": ImageExpansionNode,
    "ReplaceBgNode": ReplaceBgNode,
    "RmbgNode": RmbgNode,
    "RemoveForegroundNode": RemoveForegroundNode,
    "ShotByTextNode": ShotByTextNode,
    "ShotByImageNode": ShotByImageNode,
    "BriaTailoredGen": TailoredGenNode,
    "TailoredModelInfoNode": TailoredModelInfoNode,
    "TailoredPortraitNode": TailoredPortraitNode,
    "Text2ImageBaseNode": Text2ImageBaseNode,
    "Text2ImageFastNode": Text2ImageFastNode,
    "Text2ImageHDNode": Text2ImageHDNode,
    "ReimagineNode": ReimagineNode,
}
# Map the node display name to the one shown in the ComfyUI node interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "BriaEraser": "Bria Eraser",
    "BriaGenFill": "Bria GenFill",
    "ImageExpansionNode": "Bria Image Expansion",
    "ReplaceBgNode": "Bria Replace Background",
    "RmbgNode": "Bria RMBG",
    "RemoveForegroundNode": "Bria Remove Foreground",
    "ShotByTextNode": "Bria Shot By Text",
    "ShotByImageNode": "Bria Shot By Image",
    "BriaTailoredGen": "Bria Tailored Gen",
    "TailoredModelInfoNode": "Bria Tailored Model Info",
    "Text2ImageBaseNode": "Bria Text2Image Base",
    "Text2ImageFastNode": "Bria Text2Image Fast",
    "Text2ImageHDNode": "Bria Text2Image HD",
    "ReimagineNode": "Bria Reimagine",
}
