import os
import torch
import numpy as np
import folder_paths
import av

class LoadVideoFramesNode:
    """
    Bria Load Video Frames Node
    
    This node loads a video file and extracts all frames as images.
    The user can upload a video and it will be converted into a batch of image tensors
    that can be used with other nodes in the pipeline.
    
    Parameters:
    - video: Video file to load from input directory
    
    Returns:
    - frames: Batch of images (IMAGE tensor format)
    - frame_count: Total number of frames extracted
    - fps: Frames per second of the video
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["video"])
        
        return {
            "required": {
                "video": (sorted(files), {"video_upload": True}),
            },
            "optional": {
                "max_frames": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 10000,
                    "step": 1,
                    "tooltip": "Maximum number of frames to extract (0 = all frames)"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "INT", "FLOAT", "STRING")
    RETURN_NAMES = ("frames", "frame_count", "fps", "video_format")
    FUNCTION = "load_video"
    CATEGORY = "API Nodes"
    DESCRIPTION = "Loads a video file and extracts frames as a batch of images."

    def load_video(self, video, max_frames=0):
        video_path = folder_paths.get_annotated_filepath(video)
        video_format = os.path.splitext(video)[1].lower().lstrip('.')
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        frames = []
        frame_index = 0
        extracted_count = 0
        
        try:
            # Open video using PyAV
            container = av.open(video_path)
            
            # Get video stream
            video_stream = None
            for stream in container.streams:
                if stream.type == 'video':
                    video_stream = stream
                    break
            
            if video_stream is None:
                raise ValueError(f"No video stream found in {video}")
            
            # Get FPS
            if video_stream.average_rate is not None:
                fps = float(video_stream.average_rate)
            
            print(f"Loading video: {video}")
            print(f"Video FPS: {fps}")
            print(f"Video resolution: {video_stream.width}x{video_stream.height}")
            
            # Decode frames
            for frame in container.decode(video_stream):
                # Convert frame to RGB PIL Image
                img = frame.to_image()
                
                # Convert PIL Image to numpy array
                img_array = np.array(img.convert('RGB')).astype(np.float32) / 255.0
                
                # Convert to torch tensor with shape [H, W, C]
                img_tensor = torch.from_numpy(img_array)
                
                frames.append(img_tensor)
                extracted_count += 1
                frame_index += 1
                
                # Check if we've reached max_frames
                if max_frames > 0 and extracted_count >= max_frames:
                    break
            
            container.close()
            
            if len(frames) == 0:
                raise ValueError(f"No frames could be extracted from {video}")
            
            # Stack frames into a single tensor with shape [B, H, W, C]
            frames_tensor = torch.stack(frames, dim=0)
            
            print(f"Extracted {extracted_count} frames from video")
            print(f"Output tensor shape: {frames_tensor.shape}")
            print(f"Video format: {video_format}")
            
            return (frames_tensor, extracted_count, fps, video_format)
            
        except Exception as e:
            raise Exception(f"Error loading video {video}: {str(e)}")
    
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