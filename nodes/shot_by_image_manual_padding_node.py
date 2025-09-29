from .utils.shot_utils import get_image_input_types, create_image_payload, make_api_request, shot_by_image_api_url


class ShotByImageManualPaddingNode:
    @classmethod
    def INPUT_TYPES(self):
        input_types = get_image_input_types()
        input_types["required"]["padding_values"] = ("STRING", {"default": "0,0,0,0"})

        return input_types

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "API Nodes"
    FUNCTION = "execute"

    def __init__(self):
        self.api_url = shot_by_image_api_url

    def execute(
        self,
        image,
        ref_image,
        padding_values,
        api_key,
        sku="",
        sync=False,
        enhance_ref_image=True,
        ref_image_influence=1.0,
        force_rmbg=False,
        content_moderation=False,
    ):
        payload = create_image_payload(
            image,
            ref_image,
            api_key,
            "manual_padding",
            padding_values=padding_values,
            sku=sku,
            sync=sync,
            enhance_ref_image=enhance_ref_image,
            ref_image_influence=ref_image_influence,
            force_rmbg=force_rmbg,
            content_moderation=content_moderation,
        )
        return make_api_request(self.api_url, payload, api_key)
