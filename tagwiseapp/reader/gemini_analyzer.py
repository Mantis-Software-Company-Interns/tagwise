"""
Gemini Analyzer Module (Legacy)

This module provides backward compatibility with the original Gemini analyzer.
All functions are redirected to the new content_analyzer module which uses LangChain.
"""

import os
import base64
import warnings
import logging
from dotenv import load_dotenv

# Import functions from the new module
from .content_analyzer import (
    generate_summary_from_screenshot,
    generate_summary_from_content,
    categorize_content,
    analyze_screenshot
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Gemini API key for backwards compatibility
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    logger.info(f"Gemini API anahtarı yüklendi: {GEMINI_API_KEY[:5]}...")
else:
    logger.warning("UYARI: Gemini API anahtarı bulunamadı!")

def configure_gemini(api_key=None):
    """
    Gemini API'yi yapılandırır. (Legacy)
    
    Args:
        api_key (str, optional): Gemini API anahtarı. None ise ortam değişkeninden alınır.
        
    Returns:
        bool: Yapılandırma başarılı mı
    """
    warnings.warn(
        "configure_gemini() is deprecated. The system now uses LangChain for provider-agnostic operations.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        # No need to configure Gemini specifically anymore
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
            logger.info("Gemini API anahtarı ayarlandı.")
        
        return True
    
    except Exception as e:
        logger.error(f"Gemini API yapılandırılırken hata oluştu: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Redirect all functions to their equivalents in content_analyzer module for backward compatibility

def categorize_summary(summary, url, existing_title=None, existing_description=None):
    """
    Özeti kategorize eder. (Legacy)
    
    Args:
        summary (str): İçerik özeti
        url (str): Analiz edilen URL
        existing_title (str, optional): Mevcut başlık
        existing_description (str, optional): Mevcut açıklama
        
    Returns:
        dict: Kategorize sonuçları
    """
    warnings.warn(
        "categorize_summary() is deprecated. Use categorize_content() from content_analyzer instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return categorize_content(summary, url, existing_title, existing_description)

def analyze_screenshot_with_gemini(screenshot_base64, url, existing_title=None, existing_description=None):
    """
    Gemini AI ile ekran görüntüsünü analiz eder. (Legacy)
    
    Args:
        screenshot_base64 (str): Base64 kodlanmış ekran görüntüsü
        url (str): Analiz edilen URL
        existing_title (str, optional): Mevcut başlık
        existing_description (str, optional): Mevcut açıklama
        
    Returns:
        dict: Analiz sonuçları
    """
    warnings.warn(
        "analyze_screenshot_with_gemini() is deprecated. Use analyze_screenshot() from content_analyzer instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return analyze_screenshot(screenshot_base64, url, existing_title, existing_description)

def categorize_with_gemini(content, url, existing_title=None, existing_description=None):
    """
    Gemini AI ile içeriği kategorize eder. (Legacy)
    
    Args:
        content (str): Metin içeriği
        url (str): Analiz edilen URL
        existing_title (str, optional): Mevcut başlık
        existing_description (str, optional): Mevcut açıklama
        
    Returns:
        dict: Analiz sonuçları
    """
    warnings.warn(
        "categorize_with_gemini() is deprecated. Use categorize_content() from content_analyzer instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return categorize_content(content, url, existing_title, existing_description)

def fix_turkish_json(json_str):
    """
    Türkçe metinlerdeki JSON sorunlarını düzeltir. (Legacy)
    
    Bu fonksiyon, geriye dönük uyumluluk için korunmuştur ancak artık content_analyzer modülünün
    kendi JSON düzeltme mekanizmasını kullanmanız önerilir.
    """
    warnings.warn(
        "fix_turkish_json() is deprecated. The content_analyzer module handles JSON fixes internally.",
        DeprecationWarning,
        stacklevel=2
    )
    
    from .utils import correct_json_format
    return correct_json_format(json_str)

# To ensure this legacy module works when imported directly
if __name__ == "__main__":
    logger.info("Bu modül artık LangChain tabanlı content_analyzer modülünü kullanıyor.")
    logger.info("Doğrudan content_analyzer modülünü kullanmanız önerilir.")
    
    # Test için
    from .utils import load_api_key
    
    api_key = load_api_key()
    if configure_gemini(api_key):
        logger.info("API yapılandırıldı, test için hazır.")
        
        # Test metni
        test_content = """
        Python, nesne yönelimli, yorumlamalı, birimsel ve etkileşimli yüksek seviyeli bir programlama dilidir.
        Girintilere dayalı özel söz dizimi, onu diğer yaygın dillerden ayırır.
        Django, Python ile yazılmış yüksek seviyeli bir web çerçevesidir.
        """
        
        # Test URL'si
        test_url = "https://www.example.com/python-programming"
        
        # İçeriği kategorize et
        result = categorize_content(test_content, test_url)
        logger.info(f"Kategorize sonucu: {result}")
    else:
        logger.error("API yapılandırılamadı, test yapılamıyor.") 