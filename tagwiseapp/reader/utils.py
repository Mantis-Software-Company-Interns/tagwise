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
    Gemini'den gelen metni düzgün JSON formatına dönüştürür.
    
    Args:
        text (str): Gemini'den gelen metin
        
    Returns:
        str: Düzeltilmiş JSON metni
    """
    # Markdown kod bloklarını temizle
    text = text.replace('```json', '').replace('```', '').strip()
    
    # Başlangıç ve bitiş süslü parantezlerini bul
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        # Sadece JSON kısmını al
        text = text[start_idx:end_idx+1]
    
    # Tek tırnak yerine çift tırnak kullan
    text = text.replace("'", '"')
    
    # Boşlukları düzelt
    text = text.strip()
    
    print(f"Düzeltilmiş JSON: {text[:100]}...")
    
    return text

def ensure_correct_json_structure(json_result, url, existing_title=None, existing_description=None):
    """
    Gemini API'den gelen JSON'ın doğru yapıda olduğundan emin olur.
    Eksik alanları doldurur ve gereksiz alanları kaldırır.
    
    Args:
        json_result (dict): Gemini API'den gelen JSON
        url (str): İşlenen URL
        existing_title (str, optional): Mevcut başlık
        existing_description (str, optional): Mevcut açıklama
        
    Returns:
        dict: Düzeltilmiş JSON
    """
    # Yeni bir sözlük oluştur
    corrected_json = {}
    
    # Başlık kontrolü
    if 'title' in json_result and json_result['title']:
        corrected_json['title'] = json_result['title']
    elif existing_title:
        corrected_json['title'] = existing_title
    else:
        # URL'den başlık oluştur
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path
        corrected_json['title'] = f"{domain}{path}"
    
    # Açıklama kontrolü
    if 'description' in json_result and json_result['description']:
        corrected_json['description'] = json_result['description']
    elif existing_description:
        corrected_json['description'] = existing_description
    else:
        corrected_json['description'] = f"Bu sayfa {url} adresinde bulunmaktadır."
    
    # Ana kategori kontrolü
    if 'main_category' in json_result and json_result['main_category']:
        corrected_json['main_category'] = json_result['main_category']
    else:
        corrected_json['main_category'] = ""
    
    # Alt kategori kontrolü
    if 'subcategory' in json_result and json_result['subcategory']:
        corrected_json['subcategory'] = json_result['subcategory']
    else:
        corrected_json['subcategory'] = ""
    
    # Etiketler kontrolü
    if 'tags' in json_result and isinstance(json_result['tags'], list):
        corrected_json['tags'] = json_result['tags']
    else:
        corrected_json['tags'] = []
    
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