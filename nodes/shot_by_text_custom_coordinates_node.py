from .utils.shot_utils import get_text_input_types, create_text_payload, make_api_request, shot_by_text_api_url, PlacementType


class ShotByTextCustomCoordinatesNode:
    @classmethod
    def INPUT_TYPES(self):
        input_types = get_text_input_types()
        input_types["required"]["shot_size"] = ("STRING", {"default": "1000, 1000"})
        input_types["required"]["foreground_image_size"] = (
            "STRING",
            {"default": "500,500"},
        )
        input_types["required"]["foreground_image_location"] = (
            "STRING",
            {"default": "0, 0"},
        )
        return input_types

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = shot_by_text_api_url

    def execute(
        self,
        image,
        scene_description,
        mode,
        shot_size,
        foreground_image_size,
        foreground_image_location,
        api_key,
        sku="",
        sync=False,
        optimize_description=True,
        exclude_elements="",
        force_rmbg=False,
        content_moderation=False,
    ):
        payload = create_text_payload(
            image,
            api_key,
            scene_description,
            mode,
            PlacementType.CUSTOM_COORDINATES.value,
            shot_size=shot_size,
            foreground_image_size=foreground_image_size,
            foreground_image_location=foreground_image_location,
            sku=sku,
            sync=sync,
            optimize_description=optimize_description,
            exclude_elements=exclude_elements,
            force_rmbg=force_rmbg,
            content_moderation=content_moderation,
        )
        return make_api_request(self.api_url, payload, api_key)
