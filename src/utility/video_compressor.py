import subprocess
import os

def compress_video(input_path: str, output_path: str):
    """
    Basic example: reduce resolution and use H.264 encoding.
    """
    # -y to overwrite existing file
    cmd = cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", "scale=640:-1",
        "-vcodec", "libx264",
        "-crf", "32",
        "-preset", "fast",
        "-acodec", "aac",
        "-b:a", "64k",
        "-strict", "experimental",
        output_path
    ]
    subprocess.run(cmd, check=True)

def batch_compress_videos(file_paths):
    compressed_files = []
    for f in file_paths:
        base, ext = os.path.splitext(f)
        output_file = base + "_compressed.mp4"
        compress_video(f, output_file)
        compressed_files.append(output_file)
    return compressed_files
