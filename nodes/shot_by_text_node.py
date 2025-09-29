from .utils.shot_utils import get_text_input_types, create_text_payload, make_api_request, shot_by_text_api_url, PlacementType


class ShotByTextOriginalNode:
    @classmethod
    def INPUT_TYPES(self):
        input_types = get_text_input_types()
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
        api_key,
        sku="",
        sync=True,
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
            PlacementType.ORIGINAL.value,
            original_quality=True,
            sku=sku,
            sync=sync,
            optimize_description=optimize_description,
            exclude_elements=exclude_elements,
            force_rmbg=force_rmbg,
            content_moderation=content_moderation,
        )
        return make_api_request(self.api_url, payload, api_key)
