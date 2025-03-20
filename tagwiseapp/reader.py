"""
Reader Module

This module is now a wrapper around the modular reader package.
It imports and re-exports the functionality from the reader package.
"""

# Import functionality from the reader package
from .reader.django_setup import setup_django
from .reader.html_fetcher import fetch_html
from .reader.screenshot import capture_screenshot
from .reader.content_extractor import extract_content, extract_description
from .reader.gemini_analyzer import configure_gemini, analyze_screenshot_with_gemini, categorize_with_gemini
from .reader.category_matcher import (
    get_existing_categories, get_existing_tags, 
    find_similar_category, find_similar_tag, 
    match_categories_and_tags, calculate_category_relevance
)
from .reader.utils import (
    load_api_key, correct_json_format, 
    ensure_correct_json_structure, load_image_from_file
)
from .reader.main import analyze_url, main

# For backwards compatibility
if __name__ == "__main__":
    main()