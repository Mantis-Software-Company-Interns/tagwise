"""
TagWise Reader Package

This package contains modules for analyzing web pages and categorizing them.
"""

# Import main functions for easy access
from .main import analyze_url, main 

# Import content analyzer functions for easy access
from .content_analyzer import categorize_content, analyze_screenshot, generate_summary_from_content, generate_summary_from_screenshot

# Import HTML utility functions
from .html_utils import clean_html_content, MAX_CONTENT_LENGTH

# Import category matcher functions
from .category_matcher import find_similar_category, find_similar_tag, get_existing_categories, get_existing_tags, match_categories_and_tags

# Import YouTube analyzer functions for easy access
from .youtube_analyzer import is_youtube_url, analyze_youtube_video, extract_youtube_video_id, \
                              get_youtube_thumbnail, get_youtube_thumbnail_webp, fetch_youtube_thumbnail 