from .bria_api_node import EraserNode

# Map the node class to a name used internally by ComfyUI
NODE_CLASS_MAPPINGS = {
    "BriaEraser": EraserNode,  # Return the class, not an instance
}

# Map the node display name to the one shown in the ComfyUI node interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "BriaEraser": "Bria Eraser",
}
