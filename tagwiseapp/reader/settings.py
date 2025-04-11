"""
LLM Settings Module

This module provides centralized configuration settings for LLM providers.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Default LLM provider and model settings
DEFAULT_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")  # gemini, openai, anthropic
FALLBACK_PROVIDERS = os.getenv("FALLBACK_LLM_PROVIDERS", "openai,anthropic").split(",")

# Model configurations by provider
MODEL_CONFIGS = {
    "gemini": {
        "text_model": "gemini-2.0-flash",
        "vision_model": "gemini-2.0-flash",
        "temperature": 0.2,
        "max_tokens": 1500,
    },
    "openai": {
        "text_model": "gpt-4o",
        "vision_model": "gpt-4o-vision",
        "temperature": 0.2,
        "max_tokens": 1500,
    },
    "anthropic": {
        "text_model": "claude-3-sonnet-20240229",
        "vision_model": "claude-3-sonnet-20240229",
        "temperature": 0.2,
        "max_tokens": 1500,
    }
}

# Timeout settings (in seconds)
REQUEST_TIMEOUT = 30
RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds between retries

# Response formats
RESPONSE_FORMAT = "json"

def get_model_config(provider=None, model_type="text"):
    """
    Returns the configuration for the specified provider and model type.
    
    Args:
        provider (str, optional): The provider name (gemini, openai, anthropic)
        model_type (str, optional): Model type (text or vision)
        
    Returns:
        dict: Model configuration
    """
    # Use default provider if none specified
    if not provider:
        provider = DEFAULT_PROVIDER
    
    # Get provider config, fallback to gemini if provider not found
    provider_config = MODEL_CONFIGS.get(provider, MODEL_CONFIGS["gemini"])
    
    # Get model name based on model type
    model_name = provider_config.get(f"{model_type}_model")
    
    # Return configuration
    return {
        "provider": provider,
        "model_name": model_name,
        "temperature": provider_config.get("temperature", 0.2),
        "max_tokens": provider_config.get("max_tokens", 1500),
    } 