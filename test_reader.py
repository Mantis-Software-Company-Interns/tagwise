#!/usr/bin/env python3
"""
Test script for the reader package.
Tests all the fixed functions to ensure they work correctly.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Django setup to initialize Django environment
from tagwiseapp.reader.django_setup import setup_django
setup_django()

# Import the fixed functions
from tagwiseapp.reader.html_utils import clean_html_content, MAX_CONTENT_LENGTH
from tagwiseapp.reader.category_matcher import (
    find_similar_category, 
    find_similar_tag, 
    get_existing_categories, 
    get_existing_tags, 
    match_categories_and_tags
)
from tagwiseapp.reader.category_prompt_factory import CategoryPromptFactory
from tagwiseapp.reader.settings import get_model_config

# Test HTML content
TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Test Content</h1>
    <p>This is a test paragraph for HTML cleaning.</p>
    <script>console.log("This should be removed");</script>
</body>
</html>
"""

def test_html_utils():
    """Test HTML utility functions"""
    logger.info("Testing HTML utility functions...")
    
    # Test clean_html_content
    cleaned_text = clean_html_content(TEST_HTML)
    logger.info(f"Cleaned HTML: {cleaned_text}")
    
    # Test MAX_CONTENT_LENGTH
    logger.info(f"MAX_CONTENT_LENGTH: {MAX_CONTENT_LENGTH}")
    
    return "HTML utils test passed" if cleaned_text else "HTML utils test failed"

def test_category_matcher():
    """Test category matcher functions"""
    logger.info("Testing category matcher functions...")
    
    # Test get_existing_categories
    categories = get_existing_categories()
    logger.info(f"Found {len(categories)} categories")
    
    # Test get_existing_tags
    tags = get_existing_tags()
    logger.info(f"Found {len(tags)} tags")
    
    # Test find_similar_category
    test_category = "Technology"
    matched_category = find_similar_category(test_category, categories, is_main_category=True, accept_new=True)
    logger.info(f"Matched category for '{test_category}': {matched_category}")
    
    # Test find_similar_tag (if tags exist)
    if tags:
        test_tag = tags[0]['name']
        matched_tag = find_similar_tag(test_tag, tags, accept_new=True)
        logger.info(f"Matched tag for '{test_tag}': {matched_tag}")
    
    return "Category matcher test passed"

def test_category_prompt_factory():
    """Test category prompt factory"""
    logger.info("Testing category prompt factory...")
    
    # Test create_category_prompt
    prompt = CategoryPromptFactory.create_category_prompt(
        content="This is a test content",
        url="https://example.com",
        existing_title="Test Title",
        existing_description="Test Description",
        existing_categories=get_existing_categories(),
        existing_tags=get_existing_tags()
    )
    logger.info(f"Generated prompt length: {len(prompt)}")
    
    # Test create_screenshot_category_prompt
    screenshot_prompt = CategoryPromptFactory.create_screenshot_category_prompt(
        url="https://example.com",
        existing_title="Test Title",
        existing_description="Test Description",
        existing_categories=get_existing_categories(),
        existing_tags=get_existing_tags()
    )
    logger.info(f"Generated screenshot prompt length: {len(screenshot_prompt)}")
    
    return "Category prompt factory test passed" if prompt and screenshot_prompt else "Category prompt factory test failed"

def test_settings():
    """Test settings functions"""
    logger.info("Testing settings functions...")
    
    # Test get_model_config
    config = get_model_config()
    logger.info(f"Model config: {config}")
    
    return "Settings test passed" if config else "Settings test failed"

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run tests
    results = []
    results.append(test_html_utils())
    results.append(test_category_matcher())
    results.append(test_category_prompt_factory())
    results.append(test_settings())
    
    # Print results
    logger.info("Test results:")
    for result in results:
        logger.info(f"- {result}")
    
    # Check if all tests passed
    if all(result.endswith("passed") for result in results):
        logger.info("All tests passed!")
        sys.exit(0)
    else:
        logger.error("Some tests failed!")
        sys.exit(1) 