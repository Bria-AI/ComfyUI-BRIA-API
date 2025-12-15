import os
import uuid
import folder_paths
import requests

class PreviewVideoURLNode:
    """
    Bria Preview Video URL Node
    
    This node takes a video URL as a string and downloads it to preview
    directly in the ComfyUI interface.
    
    Parameters:
    - video_url: URL of the video to preview (http/https)
    """
   
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "URL of the video to preview (http/https)"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }
    
    RETURN_TYPES = ()
    FUNCTION = "preview_video_url"
    OUTPUT_NODE = True
    CATEGORY = "API Nodes"
    DESCRIPTION = "Previews a video from URL directly in the ComfyUI interface."

    def preview_video_url(self, video_url, prompt=None, extra_pnginfo=None):
        """
        Preview video from URL
        
        Args:
            video_url: URL of the video (http/https)
            prompt: Hidden parameter for ComfyUI workflow
            extra_pnginfo: Hidden parameter for ComfyUI metadata
            
        Returns:
            dict: UI output with video file for preview
        """
        if not video_url or video_url.strip() == "":
            raise ValueError("video_url cannot be empty")
        
        if not video_url.startswith("http://") and not video_url.startswith("https://"):
            raise ValueError("video_url must be a valid HTTP or HTTPS URL")
        
        print(f"Downloading video from URL: {video_url}")
        
        # Download video from URL
        try:
            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Determine file extension from URL or Content-Type
            content_type = response.headers.get('Content-Type', '')
            extension = self._get_extension_from_content_type(content_type, video_url)
            
            filename_prefix = str(uuid.uuid4()) + "_video_url_preview"
            
            # Get save path
            full_output_folder = self.output_dir            
            filename = f"{filename_prefix}.{extension}"
            filepath = os.path.join(full_output_folder, filename)
  
            
            # Save video to temp directory
            print(f"Saving video to: {filepath}")
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(filepath)
            print(f"Video downloaded successfully: {filename} ({file_size / (1024*1024):.2f} MB)")
            
            return {
                "ui": {
                    "images": [{
                        "filename": filename,
                        "subfolder": "",
                        "type": self.type,
                        "format": extension
                    }],
                    "animated": (True,),
                    "has_audio": (True,)
                }
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download video from URL: {str(e)}")
        except Exception as e:
            raise Exception(f"Error previewing video: {str(e)}")
    
    def _get_extension_from_content_type(self, content_type, url):
        """
        Determine file extension from Content-Type header or URL
        """
        # Map common video MIME types to extensions
        content_type_map = {
            'video/mp4': 'mp4',
            'video/webm': 'webm',
            'video/quicktime': 'mov',
            'video/x-matroska': 'mkv',
            'video/x-msvideo': 'avi',
            'image/gif': 'gif',
        }
        
        # Try to get extension from Content-Type
        for mime_type, ext in content_type_map.items():
            if mime_type in content_type.lower():
                return ext
        
        # Try to get extension from URL
        url_path = url.split('?')[0]  # Remove query parameters
        if '.' in url_path:
            url_ext = url_path.rsplit('.', 1)[-1].lower()
            if url_ext in ['mp4', 'webm', 'mov', 'mkv', 'avi', 'gif', 'webp']:
                return url_ext
        
        # Default to mp4
        return 'mp4'
