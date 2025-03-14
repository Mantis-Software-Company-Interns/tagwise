"""
Content Extractor Module

This module provides functions for extracting content from HTML.
"""

from bs4 import BeautifulSoup
from urllib.parse import urlparse

def extract_content(html):
    """
    HTML içeriğinden header ve footer dışındaki ana içeriği çıkarır.
    
    Args:
        html (str): HTML içeriği
        
    Returns:
        str: Çıkarılan metin içeriği
    """
    if not html:
        return ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Header ve footer elementlerini kaldır
    for header in soup.find_all(['header', 'nav']):
        header.decompose()
    
    for footer in soup.find_all(['footer']):
        footer.decompose()
    
    # Diğer gereksiz elementleri kaldır
    for element in soup.find_all(['script', 'style', 'iframe', 'svg']):
        element.decompose()
    
    # Ana içerik bölümlerini bul
    main_content = soup.find('main') or soup.find('article') or soup.find('div', {'id': 'content'}) or soup.find('div', {'class': 'content'})
    
    # Ana içerik bulunamadıysa, body içeriğini kullan
    if not main_content:
        main_content = soup.body
    
    # Eğer hala içerik bulunamadıysa, tüm metni al
    if not main_content:
        return soup.get_text(strip=True)
    
    # Metni temizle ve döndür
    text = main_content.get_text(separator=' ', strip=True)
    return text

def extract_description(content):
    """
    İçerikten açıklama çıkarır.
    
    Args:
        content (str): Metin içeriği
        
    Returns:
        str: Çıkarılan açıklama
    """
    if not content:
        return ""
    
    # İçeriği satırlara böl
    lines = content.split('\n')
    
    # Boş olmayan ilk 3 satırı al
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    
    if non_empty_lines:
        # İlk 3 satırı birleştir (veya daha az varsa hepsini)
        description = ' '.join(non_empty_lines[:3])
        
        # Maksimum 200 karakter
        if len(description) > 200:
            description = description[:197] + "..."
        
        return description
    
    return ""

if __name__ == "__main__":
    # Test için
    test_html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <header>Header content</header>
            <main>
                <h1>Main Content</h1>
                <p>This is the main content of the page.</p>
                <p>This is another paragraph.</p>
            </main>
            <footer>Footer content</footer>
        </body>
    </html>
    """
    
    content = extract_content(test_html)
    print(f"Extracted content: {content}")
    
    description = extract_description(content)
    print(f"Extracted description: {description}") 