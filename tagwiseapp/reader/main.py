"""
Main Module

This module provides the main functions for URL analysis.
"""

import base64
import time
import os
import json
from dotenv import load_dotenv

from .django_setup import setup_django
from .html_fetcher import fetch_html
from .screenshot import capture_screenshot
from .content_extractor import extract_content
from .content_analyzer import analyze_screenshot, categorize_content
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
    
    # API anahtarını yükle
    api_key = load_api_key()
    
    # YouTube URL kontrolü yap
    try:
        from .youtube_analyzer import is_youtube_url, analyze_youtube_video
        
        # Eğer YouTube URL'i ise, YouTube analiz fonksiyonunu kullan
        if is_youtube_url(url):
            print(f"YouTube URL'i tespit edildi, YouTube analizörü kullanılıyor: {url}")
            result = analyze_youtube_video(url)
            
            if result:
                print(f"YouTube analizi tamamlandı: {result}")
                return f"URL: {url}\nSonuç: {json.dumps(result, ensure_ascii=False)}\n"
    except Exception as e:
        print(f"YouTube analizi denemesi sırasında hata: {e}")
        print("Standart analize devam ediliyor...")
    
    # YouTube analizi yapılmadıysa veya başarısız olduysa, standart analizi devam ettir
    
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
            # Ekran görüntüsünü analiz et ve kategorize et
            category_json = analyze_screenshot(screenshot_base64, url)
    
    # Eğer ekran görüntüsü analizi yapılmadıysa veya başarısız olduysa, HTML içeriğini kategorize et
    if not category_json and content:
        # İçeriği kategorize et
        category_json = categorize_content(content, url)
    
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