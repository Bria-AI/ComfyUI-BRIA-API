from .utils.shot_utils import get_text_input_types, create_text_payload, make_api_request, shot_by_text_api_url, PlacementType


class ShotByTextAutomaticAspectRatioNode:
    @classmethod
    def INPUT_TYPES(self):
        input_types = get_text_input_types()
        input_types["required"]["aspect_ratio"] = (
            ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
            {"default": "1:1"},
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
        aspect_ratio,
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
            PlacementType.AUTOMATIC_ASPECT_RATIO.value,
            aspect_ratio=aspect_ratio,
            sku=sku,
            sync=sync,
            optimize_description=optimize_description,
            exclude_elements=exclude_elements,
            force_rmbg=force_rmbg,
            content_moderation=content_moderation,
        )
        return make_api_request(self.api_url, payload, api_key)
