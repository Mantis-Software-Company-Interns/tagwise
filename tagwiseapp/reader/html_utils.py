"""
HTML Utilities Module

This module provides functions for HTML content processing.
"""

import re
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Maximum content length to process (characters)
MAX_CONTENT_LENGTH = 15000

def clean_html_content(html_content):
    """
    HTML içeriğindeki HTML etiketlerini temizler ve düz metin çıkarır.
    
    Args:
        html_content (str): HTML içeriği
        
    Returns:
        str: Temizlenmiş düz metin
    """
    try:
        # Check if content is empty
        if not html_content or len(html_content) < 10:
            logger.warning("HTML content is empty or too short")
            return ""
            
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "iframe", "head", "meta", "link"]):
            script.extract()
        
        # Get text and normalize whitespace
        text = soup.get_text(separator=' ')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove non-printable characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        
        logger.info(f"Cleaned HTML content, original size: {len(html_content)}, new size: {len(text)}")
        return text
        
    except Exception as e:
        logger.error(f"Error cleaning HTML content: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return html_content 