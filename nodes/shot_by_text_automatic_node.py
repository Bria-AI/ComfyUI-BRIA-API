from  .utils.shot_utils import get_text_input_types, create_text_payload, make_api_request, shot_by_text_api_url, PlacementType


class ShotByTextAutomaticNode:
    @classmethod
    def INPUT_TYPES(self):
        input_types = get_text_input_types()
        input_types["required"]["shot_size"] = ("STRING", {"default": "1000, 1000"})
        return input_types

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = (
        "output_image_1",
        "output_image_2",
        "output_image_3",
        "output_image_4",
        "output_image_5",
        "output_image_6",
        "output_image_7",
    )
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
        api_key,
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
            PlacementType.AUTOMATIC.value,
            shot_size=shot_size,
            sync=sync,
            optimize_description=optimize_description,
            exclude_elements=exclude_elements,
            force_rmbg=force_rmbg,
            content_moderation=content_moderation,
        )
        return make_api_request(self.api_url, payload, api_key, Placement_type= PlacementType.AUTOMATIC.value)
