import mimetypes
import os
import torch
import numpy as np
import av
import requests
import tempfile
from fractions import Fraction

def get_video_config(ext):
    ext = ext.lower().replace(".", "")

    configs = {
        "mp4": ("mp4", "libx264", "yuv420p"),
        "mov": ("mov", "libx264", "yuv420p"),
        "mkv": ("matroska", "libx264", "yuv420p"),
        "webm": ("webm", "libvpx-vp9", "yuv420p"),
        "gif": ("gif", "gif", "pal8"),
    }

    if ext in configs:
        return configs[ext]

    print(f"[WARNING] Unknown video format '{ext}', falling back to mp4/h264.")
    return ("mp4", "libx264", "yuv420p")



def frames_to_video(frames, fps, video_format="mp4"):
    """
    Convert a batch of image frames to a video file.
    Automatically selects correct container/codec/pixel-format based on extension.
    """
    # Pick container, codec and pix_fmt
    container_format, codec, pix_fmt = get_video_config(video_format)

    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(suffix=f".{video_format}", delete=False)
    filepath = temp_file.name
    temp_file.close()

    print(f"Converting {frames.shape[0]} frames → {video_format}")
    print(f"Container={container_format}, Codec={codec}, PixFmt={pix_fmt}")

    # Open container with correct format
    container = av.open(filepath, mode="w", format=container_format)

    # Create video stream
    stream = container.add_stream(codec, rate=Fraction(round(fps * 1000), 1000))
    stream.width = frames.shape[2]
    stream.height = frames.shape[1]
    stream.pix_fmt = pix_fmt

    # Encode frames
    for i, frame in enumerate(frames):
        frame_array = torch.clamp(frame * 255, 0, 255)
        frame_np = frame_array.to(dtype=torch.uint8, device="cpu").numpy()


        video_frame = av.VideoFrame.from_ndarray(frame_np, format="rgb24")

        for packet in stream.encode(video_frame):
            container.mux(packet)

        if (i + 1) % 100 == 0:
            print(f"Encoded {i + 1}/{frames.shape[0]} frames...")

    # Flush remaining packets
    for packet in stream.encode():
        container.mux(packet)

    container.close()
    return filepath


def video_to_frames(video_path):
    """
    Convert a video file to a batch of image frames
    
    Args:
        video_path: Path to video file (local or URL)
    
    Returns:
        tuple: (frames_tensor, frame_count, fps)
    """
    # Download if it's a URL
    if video_path.startswith("http://") or video_path.startswith("https://"):
        print(f"Downloading video from: {video_path}")
        response = requests.get(video_path, stream=True)
        if response.status_code != 200:
            raise Exception(f"Failed to download video: {response.status_code}")
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        temp_file.close()
        video_path = temp_file.name
        print(f"Video downloaded to: {video_path}")
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    frames = []
    fps = 24.0  # Default FPS
    
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
            raise ValueError(f"No video stream found in video")
        
        # Get FPS
        if video_stream.average_rate is not None:
            fps = float(video_stream.average_rate)
        
        print(f"Loading video: {video_path}")
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
        
        container.close()
        
        if len(frames) == 0:
            raise ValueError(f"No frames could be extracted from video")
        
        # Stack frames into a single tensor with shape [B, H, W, C]
        frames_tensor = torch.stack(frames, dim=0)
        
        print(f"Extracted {len(frames)} frames from video")
        print(f"Output tensor shape: {frames_tensor.shape}")
        
        # Clean up temporary file if downloaded
        if video_path.startswith(tempfile.gettempdir()):
            try:
                os.unlink(video_path)
            except:
                pass
        
        return (frames_tensor, len(frames), fps)
        
    except Exception as e:
        raise Exception(f"Error loading video: {str(e)}")


def upload_video_to_s3(video_path, filename, api_token):
    api_url = "https://platform.prod.bria-api.com/upload-video/anonymous/presigned-url"
    headers = {
        "Content-Type": "application/json"
    }
    extension = os.path.splitext(filename)[1].lower()
    content_type_map = {
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.avi': 'video/x-msvideo',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
    }
    content_type = content_type_map.get(extension, 'video/mp4')
    if api_token:
        headers["api_token"] = api_token
    
    payload = {
        "file_name": filename,
        "content_type":content_type
    }
    
    print(f"Requesting presigned URL for: {filename}")
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get presigned URL: {response.status_code} {response.text}")
        
        response_data = response.json()
        video_url = response_data.get("video_url")
        upload_url = response_data.get("upload_url")
        
        if not video_url or not upload_url:
            raise Exception(f"Invalid response from presigned URL API: {response_data}")
        
        print(f"Received presigned URL")
        print(f"Video URL: {video_url}")
        
        # Step 2: Upload video to presigned URL
        print(f"Uploading video to S3...")
        
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Determine content type based on file extension
        upload_headers = {
            "Content-Type": content_type
        }

        upload_response = requests.put(upload_url, data=video_data, headers=upload_headers)
        
        if upload_response.status_code not in [200, 204]:
            raise Exception(f"Failed to upload video to S3: {upload_response.status_code}")
        
        print(f"Video uploaded successfully to S3")
        
        return video_url
        
    except Exception as e:
        raise Exception(f"Error uploading video to S3: {str(e)}")

