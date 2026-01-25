import numpy as np
from PIL import Image
import io
import torch
import base64
from torchvision.transforms import ToPILImage
import requests
import time
import json


COMFY_KEY_ERROR = (
    "Invalid Token Type\n\n"
    "The API token you’ve entered is not a ComfyUI token.\n"
    "Please use the valid token from your BRIA Account API Keys page:\n"
    "https://platform.bria.ai/console/account/api-keys"
)

def postprocess_image(image):
    result_image = Image.open(io.BytesIO(image))
    result_image = result_image.convert("RGB")
    result_image = np.array(result_image).astype(np.float32) / 255.0
    result_image = torch.from_numpy(result_image)[None,]
    return result_image

def image_to_base64(pil_image):
    # Convert a PIL image to a base64-encoded string
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")  # Save the image to the buffer in PNG format
    buffered.seek(0)  # Rewind the buffer to the beginning
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def preprocess_image(image):
    if isinstance(image, torch.Tensor):
        # Print image shape for debugging
        if image.dim() == 4:  # (batch_size, height, width, channels)
            image = image.squeeze(0)  # Remove the batch dimension (1)
            # Convert to PIL after permuting to (height, width, channels)
            image = ToPILImage()(image.permute(2, 0, 1))  # (height, width, channels)
        else:
            print("Unexpected image dimensions. Expected 4D tensor.")
    return image

def to_pil_safe(image):
    """
    Converts a single image tensor or numpy array (H,W,C) to PIL Image.
    Handles float32 in 0-1 and uint8.
    """
    if isinstance(image, torch.Tensor):
        image = image.detach().cpu().numpy()

    # If image is empty, replace with 1x1 black
    if image.size == 0:
        image = np.zeros((1,1,3), dtype=np.uint8)

    # Ensure float images are scaled 0-255
    if image.dtype in [np.float32, np.float64]:
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)

    # Handle grayscale images
    if image.ndim == 2:
        return Image.fromarray(image, mode="L")
    elif image.shape[2] == 3:
        return Image.fromarray(image, mode="RGB")
    elif image.shape[2] == 4:
        return Image.fromarray(image, mode="RGBA")
    else:
        raise ValueError(f"Cannot convert image with shape {image.shape} to PIL")


def preprocess_mask(mask):
    if isinstance(mask, torch.Tensor):
        # Print mask shape for debugging
        if mask.dim() == 3:  # (batch_size, height, width)
            mask = mask.squeeze(0)  # Remove the batch dimension (1)
            # Convert to PIL (grayscale mask)
            mask = ToPILImage()(mask)  # No permute needed for grayscale
        else:
            print("Unexpected mask dimensions. Expected 3D tensor.")
    return mask


def process_request(api_url, image, mask, api_key, visual_input_content_moderation, visual_output_content_moderation):
    if api_key.strip() == "" or api_key.strip() == "BRIA_API_TOKEN":
        raise Exception("Please insert a valid API key.")
    api_key = deserialize_and_get_comfy_key(api_key)

    # Check if image and mask are tensors, if so, convert to NumPy arrays
    if isinstance(image, torch.Tensor):
        image = preprocess_image(image)
    if isinstance(mask, torch.Tensor):
        mask = preprocess_mask(mask)

    # Convert the image and mask directly to Base64 strings
    image_base64 = image_to_base64(image)
    mask_base64 = image_to_base64(mask)

    # Prepare the API request payload for v2 API
    payload = {
        "image": image_base64,
        "mask": mask_base64,
        "visual_input_content_moderation":visual_input_content_moderation,
        "visual_output_content_moderation":visual_output_content_moderation
    }

    headers = {
        "Content-Type": "application/json",
        "api_token": f"{api_key}"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers) 
        if response.status_code == 200 or response.status_code == 202:
            print('Initial request successful, polling for completion...')
            response_dict = response.json()
            status_url = response_dict.get('status_url')
            request_id = response_dict.get('request_id')
            
            if not status_url:
                raise Exception("No status_url returned from API")
            
            print(f"Request ID: {request_id}, Status URL: {status_url}")
            
            final_response = poll_status_until_completed(status_url, api_key)
            result_image_url = final_response['result']['image_url']
            
            # Download and process the result image
            image_response = requests.get(result_image_url)
            result_image = Image.open(io.BytesIO(image_response.content))
            result_image = result_image.convert("RGBA")
            result_image = np.array(result_image).astype(np.float32) / 255.0
            result_image = torch.from_numpy(result_image)[None,]
            # image_tensor = image_tensor = ToTensor()(output_image)
            # image_tensor = image_tensor.permute(1, 2, 0) / 255.0  # Shape now becomes [1, 2200, 1548, 3]
            # print(f"output tensor shape is: {image_tensor.shape}")
            return (result_image,)  
        else:
            raise Exception(f"Error: API request failed with status code {response.status_code} {response.text}")

    except Exception as e:
        raise Exception(f"{e}")


def poll_status_until_completed(status_url, api_key, timeout=360, check_interval=2):
    """
    Poll a status URL until the status is COMPLETED or timeout is reached.
    
    Args:
        status_url (str): The status URL to poll
        api_key (str): API token for authentication
        timeout (int): Maximum time to wait in seconds (default: 360)
        check_interval (int): Time between checks in seconds (default: 2)
    
    Returns:
        dict: The final response containing the result
    
    Raises:
        Exception: If timeout is reached or API request fails
    """
    start_time = time.time()
    headers = {"api_token": api_key}
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(status_url, headers=headers)            
            if response.status_code == 200 or response.status_code == 202:
                response_dict = response.json()
                status = response_dict.get("status", "").upper()
                
                if status == "COMPLETED":
                    return response_dict
                elif status == "ERROR":
                    raise Exception(f"Request failed: {response_dict}")
                else:
                    print(f"Status: {status}, waiting...")
                    time.sleep(check_interval)
            else:
                raise Exception(f"Status check failed with status code {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error checking status: {e}")
    
    raise Exception(f"Timeout reached after {timeout} seconds")

def deserialize_and_get_comfy_key(encoded: str) -> str:
    """
    Decodes a base64-encoded JSON token and returns the ComfyUI API key.
    """
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
        payload = json.loads(decoded)

        if payload.get("type") != "comfy":
            raise Exception(COMFY_KEY_ERROR)

        return payload.get("apiKey")

    except Exception as e:
        raise Exception(COMFY_KEY_ERROR)

def normalize_images_input(images):
    """
    Converts various image inputs into a list of PIL images:
    - PIL.Image → [PIL.Image]
    - list of PIL.Image → unchanged
    - torch.Tensor (H,W,C) → [PIL.Image]
    - torch.Tensor (B,H,W,C) → list of PIL.Images
    """


    if isinstance(images, Image.Image):
        return [images]
    elif isinstance(images, list):
        return [to_pil_safe(img) if isinstance(img, torch.Tensor) else img for img in images]
    elif isinstance(images, torch.Tensor):
        if images.ndim == 3:  # (H,W,C)
            return [to_pil_safe(images)]
        elif images.ndim == 4:  # (B,H,W,C)
            return [to_pil_safe(img) for img in images]
        else:
            raise ValueError(f"Unsupported tensor shape: {images.shape}")
    else:
        raise ValueError(f"Unsupported input type: {type(images)}")

   
