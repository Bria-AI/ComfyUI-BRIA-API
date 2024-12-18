from .bria_api_node import EraserNode, GenFillNode, ShotByTextNode, ShotByImageNode
# Map the node class to a name used internally by ComfyUI
NODE_CLASS_MAPPINGS = {
    "BriaEraser": EraserNode,  # Return the class, not an instance
    "BriaGenFill": GenFillNode,
    "ShotByTextNode": ShotByTextNode,
    "ShotByImageNode": ShotByImageNode,
}
# Map the node display name to the one shown in the ComfyUI node interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "BriaEraser": "Bria Eraser",
    "BriaGenFill": "Bria GenFill",
    "ShotByTextNode": "Bria Shot By Text",
    "ShotByImageNode": "Bria Shot By Image",
}
