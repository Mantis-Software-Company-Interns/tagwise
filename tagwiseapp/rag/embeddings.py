from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from django.conf import settings
import logging
from dotenv import load_dotenv

# Ensure environment variables are loaded with priority
load_dotenv(override=True)

logger = logging.getLogger(__name__)

def get_embeddings():
    """
    Returns an instance of GoogleGenerativeAIEmbeddings using the Gemini API key.
    Returns None if there's an error.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set")
        return None
        
    try:
        logger.debug("Creating GoogleGenerativeAIEmbeddings instance")
        logger.debug(f"Using API key starting with: {api_key[:5]}...")
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key,
        )
    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        return None 