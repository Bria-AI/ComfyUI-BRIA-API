import os
import folder_paths

class LoadVideoFramesNode:
    """
    Load a video file from the input folder or upload.

    Parameters:
        video (str): Selected or uploaded video filename.

    Returns:
        video_path (STRING): Absolute path to the video file.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["video"])
        
        return {
            "required": {
                "video": (sorted(files), {"video_upload": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "load_video"
    CATEGORY = "API Nodes"

    def load_video(self, video):
        video_path = folder_paths.get_annotated_filepath(video)        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
    
        return (video_path,)
    
    @classmethod
    def IS_CHANGED(cls, video, **kwargs):
        """Force re-execution when video file changes"""
        video_path = folder_paths.get_annotated_filepath(video)
        if os.path.exists(video_path):
            return os.path.getmtime(video_path)
        return float("nan")
    
    @classmethod
    def VALIDATE_INPUTS(cls, video, **kwargs):
        """Validate that the video file exists"""
        if not folder_paths.exists_annotated_filepath(video):
            return f"Invalid video file: {video}"
        return True