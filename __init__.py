from .bria_api_node import EraserNode, GenerativeFillNode

# Map the node class to a name used internally by ComfyUI
NODE_CLASS_MAPPINGS = {
    "BriaEraser": EraserNode,  # Return the class, not an instance
    "BriaGenerativeFill": GenerativeFillNode,
}

# Map the node display name to the one shown in the ComfyUI node interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "BriaEraser": "Bria Eraser",
    "BriaGenerativeFill": "Bria Generative Fill",
}
