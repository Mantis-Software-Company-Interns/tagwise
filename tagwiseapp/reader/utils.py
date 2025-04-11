"""
Utils Module

This module provides utility functions for the reader package.
"""

import base64
import json
import os
from urllib.parse import urlparse
from PIL import Image
import io
from dotenv import load_dotenv
import re
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_api_key():
    """
    .env dosyasından Gemini API anahtarını yükler.
    
    Returns:
        str: Gemini API anahtarı
    """
    load_dotenv()
    
    # Gemini API anahtarını al ve ortam değişkenine ayarla
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    
    print(f"Gemini API anahtarı yüklendi: {'Evet' if GEMINI_API_KEY else 'Hayır'}")
    return GEMINI_API_KEY

def correct_json_format(text):
    """
    Gemini AI tarafından döndürülen metni düzgün JSON formatına dönüştürür.
    
    Markdown code blocks, başlangıç ve bitiş karakterlerini temizler.
    
    Args:
        text (str): Düzeltilecek metin
        
    Returns:
        str: Düzeltilmiş JSON metni
    """
    logger.info(f"Correcting JSON format for text length: {len(text)}")
    
    if not text:
        return "{}"
    
    # Log the first and last 100 characters of input for debugging
    logger.debug(f"Input text starts with: {text[:100]}")
    logger.debug(f"Input text ends with: {text[-100:] if len(text) > 100 else text}")
    
    # Replace markdown code block delimiters if they exist
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Find the first { and last } to extract the JSON part
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx >= 0 and end_idx >= 0 and start_idx < end_idx:
        text = text[start_idx:end_idx+1]
    else:
        logger.warning(f"Could not find valid JSON structure in text: {text[:50]}...")
        return "{}"
    
    # Try to validate the extracted JSON
    try:
        json_obj = json.loads(text)
        valid_json = json.dumps(json_obj)
        logger.info("Successfully parsed and validated JSON")
        return valid_json
    except json.JSONDecodeError as e:
        logger.warning(f"JSON validation error: {str(e)}")
        
        # Additional recovery attempts for malformed JSON
        try:
            # Try to fix common JSON errors:
            
            # 1. Fix trailing commas in objects and arrays
            text = re.sub(r',\s*}', '}', text)
            text = re.sub(r',\s*\]', ']', text)
            
            # 2. Fix missing quotes around keys
            text = re.sub(r'(\{|\,)\s*([a-zA-Z0-9_]+)\s*:', r'\1 "\2":', text)
            
            # 3. Escape unescaped quotes in string values
            # This is a complex problem that would require more sophisticated parsing
            
            # 4. Fix boolean and null values (true/false/null without quotes)
            text = re.sub(r':\s*True\s*([,}])', r': true\1', text)
            text = re.sub(r':\s*False\s*([,}])', r': false\1', text)
            text = re.sub(r':\s*None\s*([,}])', r': null\1', text)
            
            # Try parsing again
            json_obj = json.loads(text)
            valid_json = json.dumps(json_obj)
            logger.info("Successfully parsed JSON after corrections")
            return valid_json
        except json.JSONDecodeError as e2:
            logger.error(f"Failed to correct JSON: {str(e2)}")
            logger.error(f"Problematic JSON: {text}")
            return "{}"

def ensure_correct_json_structure(json_data, url, existing_title=None, existing_description=None):
    """
    Gemini AI'dan dönen JSON yapısının doğru formatta olmasını sağlar.
    
    Args:
        json_data (dict): Kontrol edilecek JSON verisi
        url (str): URL bilgisi
        existing_title (str, optional): Mevcut başlık
        existing_description (str, optional): Mevcut açıklama
        
    Returns:
        dict: Düzeltilmiş JSON verisi
    """
    # Boş JSON kontrolü
    if not json_data or not isinstance(json_data, dict):
        json_data = {}
    
    # Temel alanların varlığını kontrol et
    corrected_json = {
        "url": url,
        "title": json_data.get("title", existing_title or ""),
        "description": json_data.get("description", existing_description or ""),
        "categories": [],
        "tags": []
    }
    
    # Kategorileri kontrol et
    categories = json_data.get("categories", [])
    if isinstance(categories, list):
        corrected_json["categories"] = categories
    elif isinstance(categories, dict):
        # Dict formatındaki kategorileri array formatına dönüştür
        category_array = []
        for main_cat, sub_cats in categories.items():
            if isinstance(sub_cats, list):
                for sub_cat in sub_cats:
                    category_array.append({"main": main_cat, "sub": sub_cat})
            else:
                category_array.append({"main": main_cat, "sub": str(sub_cats)})
        corrected_json["categories"] = category_array
    
    # Etiketleri kontrol et
    tags = json_data.get("tags", [])
    if isinstance(tags, list):
        corrected_json["tags"] = tags
    elif isinstance(tags, str):
        # Virgülle ayrılmış string formatındaki etiketleri array'e dönüştür
        corrected_json["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    # Boş kategori ve etiket kontrolü
    if not corrected_json["categories"]:
        corrected_json["categories"] = [{"main": "Genel", "sub": "Diğer"}]
    
    if not corrected_json["tags"]:
        corrected_json["tags"] = ["genel"]
    
    return corrected_json

def load_image_from_file(image_path):
    """
    Dosyadan görüntü yükler ve Gemini API için uygun formata dönüştürür.
    
    Args:
        image_path (str): Görüntü dosyasının yolu
        
    Returns:
        dict: Gemini API için görüntü nesnesi
    """
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Görüntü türünü belirle
        image_type = "image/jpeg"  # Varsayılan
        if image_path.lower().endswith(".png"):
            image_type = "image/png"
        elif image_path.lower().endswith(".gif"):
            image_type = "image/gif"
        elif image_path.lower().endswith(".webp"):
            image_type = "image/webp"
        
        # Gemini API için görüntü nesnesi oluştur
        image_part = {"mime_type": image_type, "data": image_bytes}
        
        return image_part
    
    except Exception as e:
        print(f"Görüntü yüklenirken hata: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def extract_thumbnail_from_html(html, url):
    """
    HTML içeriğinden thumbnail meta etiketlerini çeker ve resmi indirir.
    Öncelikli olarak og:image ve twitter:image meta etiketlerini kullanır.
    
    Args:
        html (str): HTML içeriği
        url (str): Sayfanın URL'si
        
    Returns:
        bytes: İndirilen resim verisi veya None
    """
    try:
        from bs4 import BeautifulSoup
        import requests
        from urllib.parse import urljoin, urlparse
        from PIL import Image
        import io
        
        # HTML içeriğini parse et
        soup = BeautifulSoup(html, 'html.parser')
        image_url = None
        
        # 1. og:image meta etiketlerini kontrol et (en yaygın ve güvenilir yöntem)
        og_tags = soup.find_all('meta', attrs={'property': lambda x: x and 'og:image' in x})
        if og_tags:
            for tag in og_tags:
                content = tag.get('content')
                if content and ('http://' in content or 'https://' in content):
                    image_url = content
                    print(f"og:image bulundu: {image_url[:100]}...")
                    break
        
        # 2. twitter:image meta etiketlerini kontrol et
        if not image_url:
            twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and 'twitter:image' in x})
            if twitter_tags:
                for tag in twitter_tags:
                    content = tag.get('content')
                    if content and ('http://' in content or 'https://' in content):
                        image_url = content
                        print(f"twitter:image bulundu: {image_url[:100]}...")
                        break
        
        # 3. Schema.org image meta etiketlerini kontrol et
        if not image_url:
            schema_tags = soup.find_all('meta', attrs={'itemprop': 'image'})
            if schema_tags:
                for tag in schema_tags:
                    content = tag.get('content')
                    if content:
                        image_url = content
                        print(f"schema.org image bulundu: {image_url[:100]}...")
                        break
        
        # Göreceli URL'yi mutlak URL'ye çevir
        if image_url and not image_url.startswith(('http://', 'https://')):
            image_url = urljoin(url, image_url)
            print(f"URL mutlak URL'ye çevrildi: {image_url}")
        
        # Resmi indir ve doğrula
        if image_url:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Referer": url
            }
            
            try:
                response = requests.get(image_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    
                    # Resim formatını doğrula
                    if 'image' in content_type:
                        try:
                            # Resmi PIL ile aç ve boyutlarını kontrol et
                            img = Image.open(io.BytesIO(response.content))
                            width, height = img.size
                            
                            # Minimum boyut kontrolü
                            if width >= 200 and height >= 200:
                                print(f"Geçerli resim indirildi: {width}x{height}")
                                return response.content
                            else:
                                print(f"Resim çok küçük: {width}x{height}")
                        except Exception as img_error:
                            print(f"Resim doğrulama hatası: {img_error}")
                    else:
                        print(f"Geçersiz içerik türü: {content_type}")
            except Exception as req_error:
                print(f"Resim indirme hatası: {req_error}")
        
        return None
        
    except Exception as e:
        print(f"Thumbnail çekilirken hata: {e}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    # Test için
    api_key = load_api_key()
    print(f"API Key: {api_key[:5]}..." if api_key else "API Key not found")
    
    # JSON düzeltme testi
    test_json = "```json\n{'title': 'Test Title', 'description': 'Test Description'}\n```"
    corrected = correct_json_format(test_json)
    print(f"Corrected JSON: {corrected}")
    
    # JSON yapısı düzeltme testi
    test_result = {"title": "Test Title"}
    corrected_structure = ensure_correct_json_structure(test_result, "https://example.com")
    print(f"Corrected structure: {corrected_structure}") 