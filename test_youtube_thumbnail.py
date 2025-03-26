#!/usr/bin/env python
"""
Test script for the YouTube Thumbnail functionality.
"""

import os
import sys
import django
import uuid
from urllib.parse import urlparse, parse_qs

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tagwisebackend.settings')
django.setup()

# Import the YouTube analyzer functions
from tagwiseapp.reader.youtube_analyzer import (
    extract_youtube_video_id, 
    get_youtube_thumbnail,
    get_youtube_thumbnail_webp,
    fetch_youtube_thumbnail
)

def extract_video_id_from_url(url):
    """Extract YouTube video ID from URL."""
    # Handle youtu.be URLs
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    
    # Handle youtube.com URLs
    parsed_url = urlparse(url)
    if "youtube.com" in parsed_url.netloc:
        if "watch" in parsed_url.path:
            return parse_qs(parsed_url.query).get("v", [None])[0]
        elif "embed" in parsed_url.path:
            return parsed_url.path.split("/")[-1]
    
    # Try with our specialized function
    return extract_youtube_video_id(url)

def test_thumbnail_functions(url):
    """Test all thumbnail functions with a given URL."""
    print(f"Testing YouTube thumbnail functions with URL: {url}")
    
    # Extract video ID
    video_id = extract_video_id_from_url(url)
    if not video_id:
        print("Failed to extract video ID from URL.")
        return
    
    print(f"Video ID: {video_id}")
    
    # Test standard JPG thumbnail URLs
    print("\nTesting standard JPG thumbnails...")
    thumbnail_formats = ["maxresdefault.jpg", "sddefault.jpg", "hqdefault.jpg", "mqdefault.jpg", "default.jpg"]
    for format in thumbnail_formats:
        url = f"https://img.youtube.com/vi/{video_id}/{format}"
        print(f"- {format}: {url}")
    
    # Get best thumbnail URL
    print("\nGetting best thumbnail URL...")
    best_thumbnail = get_youtube_thumbnail(video_id)
    print(f"Best thumbnail URL: {best_thumbnail}")
    
    # Get WebP thumbnail URL
    print("\nGetting WebP thumbnail URL...")
    webp_thumbnail = get_youtube_thumbnail_webp(video_id)
    print(f"WebP thumbnail URL: {webp_thumbnail}")
    
    # Download thumbnail
    print("\nDownloading thumbnail...")
    thumbnail_data = fetch_youtube_thumbnail(video_id)
    if thumbnail_data:
        print(f"Successfully downloaded thumbnail: {len(thumbnail_data)} bytes")
        
        # Create thumbnails directory if it doesn't exist
        os.makedirs("thumbnails", exist_ok=True)
        
        # Save thumbnail to file
        filename = f"youtube_{video_id}_{str(uuid.uuid4())[:8]}.jpg"
        filepath = os.path.join("thumbnails", filename)
        
        with open(filepath, "wb") as f:
            f.write(thumbnail_data)
        
        print(f"Saved thumbnail to: {filepath}")
    else:
        print("Failed to download thumbnail.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Default test URL - Rick Astley's "Never Gonna Give You Up"
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    test_thumbnail_functions(url) 