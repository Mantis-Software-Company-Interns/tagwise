"""
Gemini Analyzer Module

This module provides functions for analyzing content with Gemini AI.
"""

import os
import base64
import google.generativeai as genai
import json
from .utils import correct_json_format, ensure_correct_json_structure
from .category_matcher import match_categories_and_tags, get_existing_categories, get_existing_tags
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Gemini API anahtarını al
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    print(f"Gemini API anahtarı yüklendi: {GEMINI_API_KEY[:5]}...")
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("UYARI: Gemini API anahtarı bulunamadı!")

def configure_gemini(api_key=None):
    """
    Gemini API'yi yapılandırır.
    
    Args:
        api_key (str, optional): Gemini API anahtarı. None ise ortam değişkeninden alınır.
        
    Returns:
        bool: Yapılandırma başarılı mı
    """
    try:
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
            
        if not api_key:
            print("Gemini API anahtarı bulunamadı.")
            return False
            
        genai.configure(api_key=api_key)
        print("Gemini API yapılandırıldı.")
        return True
    
    except Exception as e:
        print(f"Gemini API yapılandırılırken hata oluştu: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def analyze_screenshot_with_gemini(screenshot_base64, url, existing_title=None, existing_description=None):
    """
    Gemini AI ile ekran görüntüsünü analiz eder.
    
    Args:
        screenshot_base64 (str): Base64 kodlanmış ekran görüntüsü
        url (str): Analiz edilen URL
        existing_title (str, optional): Mevcut başlık
        existing_description (str, optional): Mevcut açıklama
        
    Returns:
        dict: Analiz sonuçları
    """
    print("Ekran görüntüsü Gemini AI ile analiz ediliyor...")
    
    # Mevcut kategorileri ve etiketleri al
    existing_categories = get_existing_categories()
    existing_tags = get_existing_tags()
    
    try:
        # Modeli seç - API anahtarı zaten global olarak yapılandırıldı
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Base64 kodlu görüntüyü hazırla
        image_data = {"mime_type": "image/png", "data": base64.b64decode(screenshot_base64)}
        
        # Prompt şablonunu oku
        prompt_template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'promptimage.txt')
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Mevcut kategorileri ve etiketleri prompt'a ekle
        prompt_with_categories = prompt_template + f"""

Mevcut ana kategoriler: {existing_categories['main_categories']}

Mevcut alt kategoriler: {existing_categories['subcategories']}

Mevcut etiketler: {existing_tags}

URL: {url}

Lütfen yanıtını aşağıdaki JSON formatında ver:
{{
  "title": "Sayfanın başlığı",
  "description": "Sayfanın kısa açıklaması",
  "main_category": "Ana kategori (yukarıdaki mevcut ana kategorilerden birini seç)",
  "subcategory": "Alt kategori (yukarıdaki mevcut alt kategorilerden birini seç)",
  "tags": ["etiket1", "etiket2", "etiket3"]
}}
"""
        
        # Eğer başlık ve açıklama zaten varsa, bunları belirt
        if existing_title:
            prompt_with_categories += f"\nSayfanın başlığı: {existing_title}"
        
        if existing_description:
            prompt_with_categories += f"\nSayfanın açıklaması: {existing_description}"
        
        # Yapılandırılmış çıktı şeması
        # Gemini'ye istek gönder
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
        
        response = model.generate_content(
            [prompt_with_categories, image_data],
            generation_config=generation_config
        )
        
        # Yanıtı al
        result = response.text
        
        # JSON formatını düzelt
        result = correct_json_format(result)
        
        try:
            # JSON'ı ayrıştır
            json_result = json.loads(result)
            
            # JSON yapısını düzelt
            json_result = ensure_correct_json_structure(json_result, url, existing_title, existing_description)
            
            # Kategorileri ve etiketleri eşleştir
            json_result = match_categories_and_tags(json_result, existing_categories, existing_tags)
            
            return json_result
            
        except json.JSONDecodeError as e:
            print(f"JSON ayrıştırma hatası: {e}")
            print(f"Ham yanıt: {result}")
            
            # Fallback JSON
            fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
            
            return fallback_json
    
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda fallback JSON
        fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
        
        return fallback_json

def categorize_with_gemini(content, url, existing_title=None, existing_description=None):
    """
    Gemini AI ile içeriği kategorize eder.
    
    Args:
        content (str): Metin içeriği
        url (str): Analiz edilen URL
        existing_title (str, optional): Mevcut başlık
        existing_description (str, optional): Mevcut açıklama
        
    Returns:
        dict: Analiz sonuçları
    """
    print("İçerik Gemini AI ile kategorize ediliyor...")
    
    # Mevcut kategorileri ve etiketleri al
    existing_categories = get_existing_categories()
    existing_tags = get_existing_tags()
    
    try:
        # Modeli seç - API anahtarı zaten global olarak yapılandırıldı
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # URL, içerik, mevcut kategorileri ve etiketleri birleştir
        input_text = f"""URL: {url}

İçerik:
{content}

"""
        # Eğer başlık ve açıklama zaten varsa, bunları belirt
        if existing_title:
            input_text += f"Sayfanın başlığı: {existing_title}\n"
        
        if existing_description:
            input_text += f"Sayfanın açıklaması: {existing_description}\n"
        
        print(f"Gemini'ye gönderilen mevcut kategoriler: {existing_categories['main_categories']}")
        
        # Gemini'ye istek gönder
        prompt_template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'promptimage.txt')
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Mevcut kategorileri ve etiketleri prompt'a ekle
        prompt_with_categories = prompt_template + f"""

Mevcut ana kategoriler: {existing_categories['main_categories']}

Mevcut alt kategoriler: {existing_categories['subcategories']}

Mevcut etiketler: {existing_tags}

"""
        
        # İçeriği ekle
        prompt_with_categories += input_text
        
        # JSON formatı talimatlarını ekle
        prompt_with_categories += """
Lütfen yanıtını aşağıdaki JSON formatında ver:
{
  "title": "Sayfanın başlığı",
  "description": "Sayfanın kısa açıklaması",
  "main_category": "Ana kategori (yukarıdaki mevcut ana kategorilerden birini seç)",
  "subcategory": "Alt kategori (yukarıdaki mevcut alt kategorilerden birini seç)",
  "tags": ["etiket1", "etiket2", "etiket3"]
}
"""
        
        # Gemini'ye istek gönder
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
        
        response = model.generate_content(
            prompt_with_categories,
            generation_config=generation_config
        )
        
        # Yanıtı al
        result = response.text
        
        # JSON formatını düzelt
        result = correct_json_format(result)
        
        try:
            # JSON'ı ayrıştır
            json_result = json.loads(result)
            
            # JSON yapısını düzelt
            json_result = ensure_correct_json_structure(json_result, url, existing_title, existing_description)
            
            # Kategorileri ve etiketleri eşleştir
            json_result = match_categories_and_tags(json_result, existing_categories, existing_tags)
            
            return json_result
            
        except json.JSONDecodeError as e:
            print(f"JSON ayrıştırma hatası: {e}")
            print(f"Ham yanıt: {result}")
            
            # Fallback JSON
            fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
            
            return fallback_json
    
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda fallback JSON
        fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
        
        return fallback_json

if __name__ == "__main__":
    # Test için
    from .utils import load_api_key
    
    api_key = load_api_key()
    if configure_gemini(api_key):
        print("Gemini API yapılandırıldı, test için hazır.")
        
        # Test metni
        test_content = """
        Python, nesne yönelimli, yorumlamalı, birimsel ve etkileşimli yüksek seviyeli bir programlama dilidir.
        Girintilere dayalı özel söz dizimi, onu diğer yaygın dillerden ayırır.
        Django, Python ile yazılmış yüksek seviyeli bir web çerçevesidir.
        """
        
        # Test URL'si
        test_url = "https://www.example.com/python-programming"
        
        # İçeriği kategorize et
        result = categorize_with_gemini(test_content, test_url)
        print(f"Kategorize sonucu: {result}")
    else:
        print("Gemini API yapılandırılamadı, test yapılamıyor.") 