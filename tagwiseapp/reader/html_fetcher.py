"""
HTML Fetcher Module

This module provides functions for fetching HTML content from URLs.
"""

import httpx

def fetch_html(url):
    """
    URL'den HTML içeriğini çeker.
    
    Args:
        url (str): Çekilecek sayfanın URL'si
        
    Returns:
        str or None: Başarılı olursa HTML içeriği, başarısız olursa None
    """
    try:
        # Add https:// protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            print(f"URL'ye protokol eklendi: {url}")
            
        print(f"URL'ye bağlanılıyor: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }
        response = httpx.get(url, headers=headers, timeout=60.0, follow_redirects=True)
        response.raise_for_status()
        print(f"Bağlantı başarılı, durum kodu: {response.status_code}")
        return response.text
    except httpx.RequestError as e:
        print(f"URL'ye bağlanırken hata oluştu: {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"HTTP hata kodu: {e.response.status_code}")
        return None
    except httpx.TimeoutException as e:
        print(f"Bağlantı zaman aşımına uğradı: {e}")
        return None
    except Exception as e:
        print(f"HTML çekerken beklenmeyen hata: {str(e)}")
        return None

if __name__ == "__main__":
    # Test için
    test_url = "www.example.com"  # Protocol missing
    html = fetch_html(test_url)
    if html:
        print(f"HTML içeriği başarıyla alındı. İlk 100 karakter: {html[:100]}")
    else:
        print("HTML içeriği alınamadı.") 