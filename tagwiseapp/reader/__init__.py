"""
TagWise Reader Package

This package contains modules for analyzing web pages and categorizing them.
"""

# Import main functions for easy access
from .main import analyze_url, main 

# Import YouTube analyzer functions for easy access
from .youtube_analyzer import is_youtube_url, analyze_youtube_video, extract_youtube_video_id, \
                              get_youtube_thumbnail, get_youtube_thumbnail_webp, fetch_youtube_thumbnail 