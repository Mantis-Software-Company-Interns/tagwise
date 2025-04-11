#!/usr/bin/env python3
"""
Test script for the refactored content_analyzer module.
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

# Import the refactored content analyzer module
from tagwiseapp.reader.content_analyzer import categorize_content

# Test content
TEST_CONTENT = """
Python, nesne yönelimli, yorumlamalı, birimsel ve etkileşimli yüksek seviyeli bir programlama dilidir.
Girintilere dayalı özel söz dizimi, onu diğer yaygın dillerden ayırır.
Django, Python ile yazılmış yüksek seviyeli bir web çerçevesidir.
Machine learning ve yapay zeka uygulamalarında sıklıkla kullanılır.
"""

TEST_URL = "https://www.example.com/python-programming"

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Check if API keys exist
    from tagwiseapp.reader.settings import GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
    
    logger.info("Available API keys:")
    logger.info(f"Gemini API key: {'✓' if GEMINI_API_KEY else '✗'}")
    logger.info(f"OpenAI API key: {'✓' if OPENAI_API_KEY else '✗'}")
    logger.info(f"Anthropic API key: {'✓' if ANTHROPIC_API_KEY else '✗'}")
    
    # Test the categorize_content function
    logger.info("Testing categorize_content function...")
    try:
        result = categorize_content(
            content=TEST_CONTENT, 
            url=TEST_URL,
            existing_title="Python Programming",
            existing_description="A high-level programming language"
        )
        logger.info(f"Test successful!")
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc()) 