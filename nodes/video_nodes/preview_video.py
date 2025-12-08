import os
import json
import random
import torch
import numpy as np
from PIL import Image
import folder_paths
from comfy.cli_args import args
import av
from fractions import Fraction

class PreviewVideoFramesNode:
    """
    Bria Preview Video Frames Node
    
    This node takes a batch of image frames and creates an actual video file
    that can be played as animation in the ComfyUI interface.
    
    Parameters:
    - frames: Batch of image tensors to preview
    - fps: Frames per second for animation display
    - format: Video format (webp or mp4)
    """
    
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_video_preview_" + ''.join(random.choice("abcdefghijklmnopqrstupvxyz") for _ in range(5))
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "frames": ("IMAGE", {"tooltip": "Batch of image frames to preview"}),
            },
            "optional": {
                "fps": ("FLOAT", {
                    "default": 30.0,
                    "min": 1.0,
                    "max": 120.0,
                    "step": 0.1,
                    "tooltip": "Frames per second for animation playback"
                }),
                "format": ([
                    "mp4_h264",
                    "mp4_h265",
                    "webm_vp9",
                    "mov_h265",
                    "mov_proresks",
                    "mkv_h264",
                    "mkv_h265",
                    "mkv_vp9",
                    "gif",
                    "webp"
                ], {
                    "default": "mp4_h264",
                    "tooltip": "Output video format - matches Bria API formats"
                }),
                "quality": (["high", "medium", "low"], {
                    "default": "medium",
                    "tooltip": "Video quality (affects file size)"
                }),
                "max_preview_frames": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 1000,
                    "step": 1,
                    "tooltip": "Maximum frames to preview (0 = all frames)"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }
    
    RETURN_TYPES = ()
    FUNCTION = "preview_frames"
    OUTPUT_NODE = True
    CATEGORY = "API Nodes"
    DESCRIPTION = "Previews video frames as an animated video in the ComfyUI interface."

    def preview_frames(self, frames, fps=30.0, format="mp4_h264", quality="medium", max_preview_frames=0, prompt=None, extra_pnginfo=None):
        """
        Preview video frames as animated video
        
        Args:
            frames: Batch of image tensors [B, H, W, C]
            fps: Frames per second for display
            format: Output format (supports all Bria API formats)
            quality: Video quality (high, medium, low)
            max_preview_frames: Maximum number of frames to preview (0 = all)
            prompt: Hidden parameter for ComfyUI workflow
            extra_pnginfo: Hidden parameter for ComfyUI metadata
            
        Returns:
            dict: UI output with video file for animation
        """
        filename_prefix = "VideoPreview"
        filename_prefix += self.prefix_append
        
        # Limit frames if specified
        total_frames = frames.shape[0]
        if max_preview_frames > 0 and total_frames > max_preview_frames:
            # Sample frames evenly across the video
            indices = torch.linspace(0, total_frames - 1, max_preview_frames).long()
            frames = frames[indices]
            print(f"Preview limited to {max_preview_frames} frames (sampled from {total_frames} total frames)")
        else:
            print(f"Previewing {total_frames} frames as animated video (format: {format})")
        
        # Get save path
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, 
            self.output_dir, 
            frames[0].shape[1],  # width
            frames[0].shape[0]   # height
        )
        
        # Choose format and create video
        if format == "webp":
            result_file = self._save_as_webp(frames, full_output_folder, filename, counter, fps, quality, prompt, extra_pnginfo)
        elif format == "gif":
            result_file = self._save_as_gif(frames, full_output_folder, filename, counter, fps, quality, prompt, extra_pnginfo)
        else:
            # All video formats (mp4, webm, mov, mkv)
            result_file = self._save_as_video(frames, full_output_folder, filename, counter, fps, format, quality, prompt, extra_pnginfo)
        
        print(f"Saved animated video: {result_file}")
        
        # Return UI output with animation
        return {
            "ui": {
                "images": [{
                    "filename": result_file,
                    "subfolder": subfolder,
                    "type": self.type
                }],
                "animated": (True,)
            }
        }
    
    def _get_format_config(self, format_name):
        """
        Get container, codec, and file extension for a given format
        
        Returns: (container, codec, extension, pixel_format)
        """
        format_map = {
            "mp4_h264": ("mp4", "libx264", "mp4", "yuv420p"),
            "mp4_h265": ("mp4", "libx265", "mp4", "yuv420p"),
            "webm_vp9": ("webm", "libvpx-vp9", "webm", "yuv420p"),
            "mov_h265": ("mov", "libx265", "mov", "yuv420p"),
            "mov_proresks": ("mov", "prores_ks", "mov", "yuv422p10le"),
            "mkv_h264": ("matroska", "libx264", "mkv", "yuv420p"),
            "mkv_h265": ("matroska", "libx265", "mkv", "yuv420p"),
            "mkv_vp9": ("matroska", "libvpx-vp9", "mkv", "yuv420p"),
        }
        return format_map.get(format_name, ("mp4", "libx264", "mp4", "yuv420p"))
    
    
    def _save_as_webp(self, frames, output_folder, filename, counter, fps, quality, prompt, extra_pnginfo):
        """Save frames as animated WEBP"""
        file = f"{filename}_{counter:05}_.webp"
        
        # Convert frames to PIL images
        pil_images = []
        for frame in frames:
            frame_array = 255.0 * frame.cpu().numpy()
            img = Image.fromarray(np.clip(frame_array, 0, 255).astype(np.uint8))
            pil_images.append(img)
        
        # Add metadata to first frame
        metadata = pil_images[0].getexif()
        if not args.disable_metadata:
            if prompt is not None:
                metadata[0x0110] = "prompt:{}".format(json.dumps(prompt))
            if extra_pnginfo is not None:
                inital_exif = 0x010f
                for x in extra_pnginfo:
                    metadata[inital_exif] = "{}:{}".format(x, json.dumps(extra_pnginfo[x]))
                    inital_exif -= 1
        
        # Quality mapping
        quality_values = {"high": 95, "medium": 85, "low": 70}
        webp_quality = quality_values.get(quality, 85)
        
        # Save as animated WEBP
        duration = int(1000.0 / fps)  # duration in milliseconds
        pil_images[0].save(
            os.path.join(output_folder, file),
            save_all=True,
            duration=duration,
            append_images=pil_images[1:],
            exif=metadata,
            lossless=False,
            quality=webp_quality,
            method=4
        )
        
        return file
    
    def _save_as_gif(self, frames, output_folder, filename, counter, fps, quality, prompt, extra_pnginfo):
        """Save frames as animated GIF"""
        file = f"{filename}_{counter:05}_.gif"
        
        # Convert frames to PIL images
        pil_images = []
        for frame in frames:
            frame_array = 255.0 * frame.cpu().numpy()
            img = Image.fromarray(np.clip(frame_array, 0, 255).astype(np.uint8))
            pil_images.append(img)
        
        # Save as animated GIF
        duration = int(1000.0 / fps)  # duration in milliseconds
        optimize = quality == "low"  # Optimize for low quality to reduce size
        pil_images[0].save(
            os.path.join(output_folder, file),
            save_all=True,
            duration=duration,
            append_images=pil_images[1:],
            loop=0,
            optimize=optimize
        )
        
        return file
    
    def _save_as_video(self, frames, output_folder, filename, counter, fps, format_name, quality, prompt, extra_pnginfo):
        """
        Save frames as video using PyAV with support for all Bria API formats
        
        Supports: mp4_h264, mp4_h265, webm_vp9, mov_h265, mov_proresks, mkv_h264, mkv_h265, mkv_vp9
        """
        # Get format configuration
        container_format, codec, extension, pix_fmt = self._get_format_config(format_name)
        
        file = f"{filename}_{counter:05}_.{extension}"
        filepath = os.path.join(output_folder, file)
        
        print(f"Encoding video: container={container_format}, codec={codec}, quality={quality}")
        
        # Open video container
        container = av.open(filepath, mode="w", format=container_format)
        
        # Add metadata if enabled
        if not args.disable_metadata:
            if prompt is not None:
                container.metadata["prompt"] = json.dumps(prompt)
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    container.metadata[x] = json.dumps(extra_pnginfo[x])
        
        # Create video stream
        stream = container.add_stream(codec, rate=Fraction(round(fps * 1000), 1000))
        stream.width = frames.shape[2]   # width
        stream.height = frames.shape[1]  # height
        stream.pix_fmt = pix_fmt
                
        # Encode frames
        for i, frame in enumerate(frames):
            # Convert tensor to numpy array and scale to 0-255
            frame_array = torch.clamp(frame * 255, min=0, max=255)
            frame_np = frame_array.to(device=torch.device("cpu"), dtype=torch.uint8).numpy()
            
            # Create video frame
            video_frame = av.VideoFrame.from_ndarray(frame_np, format="rgb24")
            
            # Encode frame
            for packet in stream.encode(video_frame):
                container.mux(packet)
            
            # Progress update for long videos
            if (i + 1) % 100 == 0:
                print(f"Encoded {i + 1}/{frames.shape[0]} frames...")
        
        # Flush remaining packets
        for packet in stream.encode():
            container.mux(packet)
        
        container.close()
        
        print(f"Video encoding complete: {file}")
        
        return file