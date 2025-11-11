import requests
import torch
from ..common import deserialize_and_get_comfy_key, postprocess_image, preprocess_image, image_to_base64

shot_by_text_api_url = (
    "https://engine.prod.bria-api.com/v1/product/lifestyle_shot_by_text"
)
shot_by_image_api_url = (
    "https://engine.prod.bria-api.com/v1/product/lifestyle_shot_by_image"
)

from enum import Enum

class PlacementType(str, Enum):
    ORIGINAL = "original"
    AUTOMATIC = "automatic"
    MANUAL_PLACEMENT = "manual_placement"
    MANUAL_PADDING = "manual_padding"
    CUSTOM_COORDINATES = "custom_coordinates"
    AUTOMATIC_ASPECT_RATIO = "automatic_aspect_ratio"



def validate_api_key(api_key):
    """Validate API key input"""
    if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
        raise Exception("Please insert a valid API key.")


def update_payload_for_placement(placement_type, payload, **kwargs):
    if placement_type == PlacementType.AUTOMATIC.value:
        payload["shot_size"] = [
            int(x.strip()) for x in kwargs.get("shot_size").split(",")
        ]
    elif placement_type == PlacementType.MANUAL_PLACEMENT.value:
        payload["shot_size"] = [
            int(x.strip()) for x in kwargs.get("shot_size").split(",")
        ]
        payload["manual_placement_selection"] = [
            kwargs.get("manual_placement_selection", "upper_left")
        ]
    elif placement_type == PlacementType.CUSTOM_COORDINATES.value:
        payload["shot_size"] = [
            int(x.strip()) for x in kwargs.get("shot_size").split(",")
        ]
        payload["foreground_image_size"] = [
            int(x.strip()) for x in kwargs.get("foreground_image_size").split(",")
        ]
        payload["foreground_image_location"] = [
            int(x.strip()) for x in kwargs.get("foreground_image_location").split(",")
        ]
    elif placement_type == PlacementType.MANUAL_PADDING.value:
        payload["padding_values"] = [
            int(x.strip()) for x in kwargs.get("padding_values").split(",")
        ]

    elif placement_type == PlacementType.AUTOMATIC_ASPECT_RATIO.value:
        payload["aspect_ratio"] = kwargs.get("aspect_ratio", "1:1")
    elif placement_type == PlacementType.ORIGINAL.value:
        payload["original_quality"] = kwargs.get("original_quality", True)

    return payload


def create_text_payload(
    image, api_key, scene_description, mode, placement_type, **kwargs
):

    validate_api_key(api_key)


    # Process image
    if isinstance(image, torch.Tensor):
        image = preprocess_image(image)

    image_base64 = image_to_base64(image)

    payload = {
        "file": image_base64,
        "placement_type": placement_type,
        "sync": True,
        "num_results": 1,
        "force_rmbg": kwargs.get("force_rmbg", False),
        "content_moderation": kwargs.get("content_moderation", False),
        "scene_description": scene_description,
        "mode": mode,
        "optimize_description": kwargs.get("optimize_description", True),
    }

    if kwargs.get("exclude_elements", "").strip():
        payload["exclude_elements"] = kwargs["exclude_elements"]

    payload = update_payload_for_placement(placement_type, payload, **kwargs)

    return payload


def create_image_payload(image, ref_image, api_key, placement_type, **kwargs):
    """Create payload for image-based shot nodes"""
    validate_api_key(api_key)

    if isinstance(image, torch.Tensor):
        image = preprocess_image(image)
        if isinstance(ref_image, torch.Tensor):
            ref_image = preprocess_image(ref_image)

        image_base64 = image_to_base64(image)
        ref_image_base64 = image_to_base64(ref_image)

    # Base payload
    payload = {
        "file": image_base64,
        "ref_image_file": ref_image_base64,
        "enhance_ref_image": kwargs.get("enhance_ref_image", True),
        "ref_image_influence": kwargs.get("ref_image_influence", 1.0),
        "placement_type": placement_type,
        "sync": True,
        "num_results": 1,
        "force_rmbg": kwargs.get("force_rmbg", False),
        "content_moderation": kwargs.get("content_moderation", False),
    }

    payload = update_payload_for_placement(placement_type, payload, **kwargs)

    return payload


def make_api_request(api_url, payload, api_key, Placement_type = None):
    """Make API request and return processed image"""


    try:
        api_key = deserialize_and_get_comfy_key(api_key)
        headers = {"Content-Type": "application/json", "api_token": f"{api_key}"}
        response = requests.post(api_url, json=payload, headers=headers)

        if response.status_code == 200:
            print("response is 200")
            response_dict = response.json()
            if Placement_type == PlacementType.AUTOMATIC.value:
                result_images = []
                for i, result in enumerate(response_dict.get("result", [])[:7]):
                    image_url = result[0]
                    image_response = requests.get(image_url)
                    processed = postprocess_image(image_response.content)
                    result_images.append(processed)

                # If less than 7 images, pad with None to match ComfyUI return structure
                while len(result_images) < 7:
                    result_images.append(None)
                print(result_images)

                return tuple(result_images)

            image_response = requests.get(response_dict["result"][0][0])
            result_image = postprocess_image(image_response.content)
            return (result_image,)
        else:
            raise Exception(
                f"Error: API request failed with status code {response.status_code}{response.text}"
            )

    except Exception as e:
        raise Exception(f"{e}")


def get_common_input_types():
    """Get common input types for all nodes"""
    return {
        "required": {"api_key": ("STRING", {"default": "BRIA_API_TOKEN"})},
        "optional": {
            "force_rmbg": ("BOOLEAN", {"default": False}),
            "content_moderation": ("BOOLEAN", {"default": False}),
        },
    }


def get_text_input_types():
    """Get text-specific input types"""
    common = get_common_input_types()
    common["required"].update(
        {
            "image": ("IMAGE",),
            "scene_description": ("STRING",),
            "mode": (["base", "fast", "high_control"], {"default": "fast"}),
        }
    )
    common["optional"].update(
        {
            "optimize_description": ("BOOLEAN", {"default": True}),
            "exclude_elements": ("STRING", {"default": ""}),
        }
    )
    return common


def get_image_input_types():
    """Get image-specific input types"""
    common = get_common_input_types()
    common["required"].update({"image": ("IMAGE",), "ref_image": ("IMAGE",)})
    common["optional"].update(
        {
            "enhance_ref_image": ("BOOLEAN", {"default": True}),
            "ref_image_influence": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
        }
    )
    return common
