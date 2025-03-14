"""
Main Module

This module provides the main functions for URL analysis.
"""

import base64
import time
import os
from dotenv import load_dotenv

from .django_setup import setup_django
from .html_fetcher import fetch_html
from .screenshot import capture_screenshot
from .content_extractor import extract_content
from .gemini_analyzer import configure_gemini, analyze_screenshot_with_gemini, categorize_with_gemini
from .utils import load_api_key

def normalize_url(url):
    """
    URL'yi normalize eder.
    
    Args:
        url (str): Normalize edilecek URL
        
    Returns:
        str: Normalize edilmiş URL
    """
    # Add https:// protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        print(f"URL'ye protokol eklendi: {url}")
    
    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]
    
    return url

def analyze_url(url):
    """
    URL'yi analiz edip kategori belirler.
    
    Args:
        url (str): Analiz edilecek URL
        
    Returns:
        str: Analiz sonucu
    """
    # Normalize URL
    url = normalize_url(url)
    
    print(f"\nURL analiz ediliyor: {url}")
    
    # API anahtarını yükle ve Gemini'yi yapılandır
    api_key = load_api_key()
    if not configure_gemini(api_key):
        return f"URL: {url}\nSonuç: Gemini API yapılandırılamadı."
    
    # HTML içeriğini çek
    html = fetch_html(url)
    content = None
    category_json = None
    
    if html:
        # Ana içeriği ayıkla
        content = extract_content(html)
    
    # HTML içeriği alınamadıysa veya içerik çıkarılamazsa, Selenium ile ekran görüntüsü al
    if not html or not content or len(content.strip()) < 50:
        print("HTML içeriği alınamadı veya içerik yetersiz, Selenium ile ekran görüntüsü alınıyor...")
        screenshot = capture_screenshot(url)
        
        if screenshot:
            # PNG verisini base64'e dönüştür
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            # Ekran görüntüsünü Gemini ile analiz et ve kategorize et
            category_json = analyze_screenshot_with_gemini(screenshot_base64, url)
    
    # Eğer ekran görüntüsü analizi yapılmadıysa veya başarısız olduysa, HTML içeriğini kategorize et
    if not category_json and content:
        # İçeriği kategorize et
        category_json = categorize_with_gemini(content, url)
    
    if not content and not category_json:
        return f"URL: {url}\nSonuç: İçerik alınamadı veya analiz edilemedi."
    
    return f"URL: {url}\nSonuç: {category_json}\n"

def main():
    """
    Ana fonksiyon.
    
    Bu fonksiyon, kullanıcıdan URL'ler alır ve her birini analiz eder.
    """
    # Django ortamını başlat
    setup_django()
    
    print("Web Sayfası Kategori Analizi")
    print("----------------------------")
    print("URL'leri girin (birden fazla URL için her satıra bir URL yazın, bitirmek için boş satır girin):")
    
    urls = []
    while True:
        url = input().strip()
        if not url:
            break
        urls.append(url)
    
    if not urls:
        print("URL girilmedi.")
        return
    
    results = []
    for url in urls:
        result = analyze_url(url)
        results.append(result)
        # API rate limit'e takılmamak için kısa bir bekleme
        time.sleep(1)
    
    print("\nANALİZ SONUÇLARI:")
    print("================")
    for result in results:
        print(result)

if __name__ == "__main__":
    main() 