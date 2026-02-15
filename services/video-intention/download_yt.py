#!/usr/bin/env python3
"""
YouTube Shorts Downloader
A simple script to download YouTube Shorts videos using yt-dlp
"""

import sys
import os

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp is not installed.")
    print("Install it using: pip install yt-dlp")
    sys.exit(1)


def download_youtube_short(url, output_path="./downloads", filename=None):
    """
    Download a YouTube Short video

    Args:
        url (str): The URL of the YouTube Short
        output_path (str): Directory where the video will be saved
        filename (str): Optional base filename (without extension) for the downloaded video
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Use custom filename if provided, otherwise use video title
    outtmpl = os.path.join(output_path, f'{filename}.%(ext)s') if filename else os.path.join(output_path, '%(title)s.%(ext)s')

    # Configure yt-dlp options
    ydl_opts = {
        'format': 'best',  # Download best quality available
        'outtmpl': outtmpl,  # Output filename template
        'quiet': False,  # Show progress
        'no_warnings': False,
    }
    
    try:
        print(f"\nDownloading from: {url}")
        print(f"Saving to: {output_path}\n")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info and download
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        print(f"\n✓ Download complete!")
        print(f"File saved as: {filename}")
        return filename
        
    except Exception as e:
        print(f"\n✗ Error downloading video: {str(e)}")
        return None


def main():
    """Main function to handle command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python download_youtube_shorts.py <YouTube_Shorts_URL> [output_directory]")
        print("\nExample:")
        print("  python download_youtube_shorts.py https://youtube.com/shorts/abc123")
        print("  python download_youtube_shorts.py https://youtube.com/shorts/abc123 ./my_videos")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "./downloads"
    
    download_youtube_short(url, output_path)


if __name__ == "__main__":
    main()