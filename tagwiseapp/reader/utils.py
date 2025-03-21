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
    
    # Description alanını özel olarak işle
    try:
        # Önce description alanını bul ve ayır
        desc_start = text.find('"description"')
        if desc_start != -1:
            # Description değerinin başlangıcını bul
            value_start = text.find(':', desc_start) + 1
            # İlk tırnak işaretini bul
            quote_start = text.find('"', value_start)
            if quote_start != -1:
                # Kapanış tırnağını bul (escape edilmiş tırnakları atla)
                pos = quote_start + 1
                while pos < len(text):
                    if text[pos] == '"' and text[pos-1] != '\\':
                        # Doğru kapanış tırnağını bulduk
                        quote_end = pos
                        # Description değerini al
                        desc_value = text[quote_start+1:quote_end]
                        # Türkçe karakter sorunlarını düzelt
                        desc_value = desc_value.replace('",', '')
                        desc_value = desc_value.replace(',"', '')
                        desc_value = desc_value.replace('"u,n', '"un')
                        desc_value = desc_value.replace('"ı,n', '"ın')
                        desc_value = desc_value.replace('"i,n', '"in')
                        # İç tırnakları escape et
                        desc_value = desc_value.replace('"', '\\"')
                        # Düzeltilmiş description'ı metne yerleştir
                        text = text[:quote_start+1] + desc_value + text[quote_end:]
                        break
                    pos += 1
    except Exception as e:
        print(f"Description düzeltme hatası: {e}")
    
    # Tek tırnak yerine çift tırnak kullan
    text = text.replace("'", '"')
    
    # Tag dizisindeki tırnak işareti sorunlarını düzelt
    try:
        tags_start = text.find('"tags"')
        if tags_start != -1:
            # Tags array başlangıcını bul
            array_start = text.find('[', tags_start)
            if array_start != -1:
                # Array sonunu bul
                bracket_count = 1
                pos = array_start + 1
                while pos < len(text) and bracket_count > 0:
                    if text[pos] == '[':
                        bracket_count += 1
                    elif text[pos] == ']':
                        bracket_count -= 1
                    pos += 1
                
                if bracket_count == 0:
                    array_end = pos - 1
                    # Tags içeriğini al
                    tags_content = text[array_start+1:array_end]
                    # Tırnak işaretlerini düzelt
                    tags_items = re.findall(r'"[^"]*"|\S+', tags_content)
                    fixed_tags = []
                    for item in tags_items:
                        item = item.strip().strip(',').strip('"').strip("'")
                        if item:
                            fixed_tags.append(f'"{item}"')
                    # Düzeltilmiş tags array'ini yerleştir
                    text = text[:array_start+1] + ', '.join(fixed_tags) + text[array_end:]
    except Exception as e:
        print(f"Tags düzeltme hatası: {e}")
    
    # Gereksiz boşlukları ve satır sonlarını temizle
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    print(f"Düzeltilmiş JSON: {text[:100]}...")
    
    return text

def ensure_correct_json_structure(json_result, url, existing_title=None, existing_description=None):
    """
    Gemini AI'dan dönen JSON yapısını doğru formatta olmasını sağlar.
    
    Args:
        json_result (dict): Gemini AI'dan gelen sonuç
        url (str): İşlenen URL
        existing_title (str, optional): Mevcut başlık
        existing_description (str, optional): Mevcut açıklama
        
    Returns:
        dict: Düzeltilmiş JSON yapısı
    """
    print("JSON yapısı düzeltiliyor...")
    
    # Doğru yapıdaki JSON
    corrected_json = {
        'url': url,
        'title': existing_title or json_result.get('title', ''),
        'description': existing_description or json_result.get('description', ''),
        'main_category': '',
        'subcategory': '',
        'categories': [],
        'tags': []
    }
    
    # Eğer kullanıcı bir başlık ve açıklama vermişse, bunları kullan
    if existing_title:
        corrected_json['title'] = existing_title
    else:
        corrected_json['title'] = json_result.get('title', '')
    
    if existing_description:
        corrected_json['description'] = existing_description
    else:
        corrected_json['description'] = json_result.get('description', '')
    
    # Kategori bilgisi, çoklu kategoriler formatında mı?
    if 'categories' in json_result and isinstance(json_result['categories'], list):
        # Kategori dizisini kopyala
        corrected_json['categories'] = []
        
        for category in json_result['categories']:
            # Her bir kategori öğesi için ana ve alt kategori bilgisini kontrol et
            if isinstance(category, dict) and 'main_category' in category:
                category_item = {
                    'main_category': category['main_category']
                }
                
                if 'subcategory' in category:
                    category_item['subcategory'] = category['subcategory']
                else:
                    category_item['subcategory'] = ""
                
                # Düzeltilmiş kategorilere ekle
                corrected_json['categories'].append(category_item)
        
        # Eğer en az bir kategori varsa, ilk kategoriyi ana ve alt kategori olarak kullan
        if corrected_json['categories']:
            corrected_json['main_category'] = corrected_json['categories'][0]['main_category']
            corrected_json['subcategory'] = corrected_json['categories'][0].get('subcategory', "")
    
    else:
        # Eski tarz JSON yanıtlarından categories dizisi oluştur
        corrected_json['categories'] = []
        
        # Tek bir kategori verisi varsa ekle
        if 'main_category' in json_result and json_result['main_category']:
            category_item = {
                'main_category': json_result['main_category']
            }
            
            if 'subcategory' in json_result and json_result['subcategory']:
                category_item['subcategory'] = json_result['subcategory']
            
            corrected_json['categories'].append(category_item)
            
            # Geri uyumluluk için ayrıca tekil alanlara da ekle
            corrected_json['main_category'] = json_result['main_category']
            corrected_json['subcategory'] = json_result.get('subcategory', "")
        else:
            corrected_json['main_category'] = ""
            corrected_json['subcategory'] = ""
    
    # Etiketler kontrolü - daha sıkı kontrol ve temizleme
    if 'tags' in json_result and isinstance(json_result['tags'], list):
        # Boş olmayan ve string olan etiketleri al
        valid_tags = []
        for tag in json_result['tags']:
            if tag and isinstance(tag, str):
                # Tırnak işaretlerini temizle ve boşlukları kırp
                clean_tag = tag.strip().strip('"').strip("'").strip()
                if clean_tag:
                    valid_tags.append(clean_tag)
        
        # Varsayılan genel etiketleri temizle
        default_tags = ['içerik', 'web', 'analiz', 'sayfa']
        valid_tags = [tag for tag in valid_tags if tag.lower() not in default_tags]
        
        corrected_json['tags'] = valid_tags
        
        # Eğer etiketler boş çıktıysa başlık ve açıklamadan etiket çıkar
        if not valid_tags:
            print("Etiketler listesi boş veya sadece varsayılan etiketler içeriyor. İçerikten etiketler oluşturuluyor...")
            
            # İçerikten etiket çıkar
            from collections import Counter
            import re
            
            # Başlık ve açıklamayı birleştir
            title = corrected_json.get('title', '')
            description = corrected_json.get('description', '')
            combined_text = (title + " " + description).lower()
            
            # Noktalama işaretlerini kaldır
            combined_text = re.sub(r'[^\w\s]', ' ', combined_text)
            
            # Stopwords - genel, yaygın, anlamsız kelimeler
            stopwords = ["ve", "veya", "ile", "için", "bu", "bir", "o", "de", "da", "ki", "ne", "ya", "çok", 
                        "nasıl", "en", "içinde", "üzerinde", "arasında", "olarak", "dolayı", "kadar", "önce", 
                        "sonra", "göre", "her", "the", "and", "or", "for", "in", "on", "at", "with", "from", 
                        "to", "a", "an", "by", "is", "are", "was", "were", "içerik", "web", "analiz", "sayfa"]
            
            # Kelimelere böl
            words = combined_text.split()
            
            # Yaygın kelimeleri kaldır
            filtered_words = [word for word in words if word not in stopwords and len(word) > 3]
            
            # En sık geçen anlamlı kelimeleri bul
            word_counter = Counter(filtered_words)
            common_words = word_counter.most_common(10)
            
            # Anlamlı kelimeleri etiket olarak kullan
            content_tags = []
            for word, count in common_words:
                if len(content_tags) >= 5:  # En fazla 5 etiket
                    break
                # İlk harfi büyüt
                tag = word.capitalize()
                if tag and tag not in content_tags:
                    content_tags.append(tag)
            
            # Ana kategoriyi de etiket olarak ekle
            if corrected_json['main_category'] and corrected_json['main_category'] not in content_tags:
                content_tags.append(corrected_json['main_category'])
            
            # Alt kategoriyi de etiket olarak ekle
            if corrected_json['subcategory'] and corrected_json['subcategory'] not in content_tags:
                content_tags.append(corrected_json['subcategory'])
            
            # İçerikten çıkarılan etiketleri kullan
            if content_tags:
                corrected_json['tags'] = content_tags
                print(f"İçerikten oluşturulan etiketler: {content_tags}")
            else:
                # Gerçekten hiç ipucu bulunamadıysa, domain adını kullan
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                domain_parts = domain.split('.')
                
                # Alan adının anlamlı kısmını etiket olarak kullan (genellikle ikinci seviye domain)
                domain_tags = []
                for part in domain_parts:
                    if part not in ['www', 'com', 'net', 'org', 'io', 'co', 'gov', 'edu'] and len(part) > 2:
                        domain_tags.append(part.capitalize())
                
                if domain_tags:
                    corrected_json['tags'] = domain_tags
                    print(f"Alan adından oluşturulan etiketler: {domain_tags}")
                else:
                    # Son çare olarak URL'den ipucu çıkar
                    path_parts = urlparse(url).path.split('/')
                    path_tags = []
                    for part in path_parts:
                        if part and len(part) > 3:
                            # Tire ve alt çizgi ile ayrılmış kelimeleri ayır
                            words = re.split(r'[-_]', part)
                            for word in words:
                                if word and len(word) > 3:
                                    path_tags.append(word.capitalize())
                    
                    if path_tags:
                        corrected_json['tags'] = path_tags[:5]  # En fazla 5 etiket
                        print(f"URL yolundan oluşturulan etiketler: {path_tags[:5]}")
                    else:
                        # En son çare olarak URL temel etiketleri
                        corrected_json['tags'] = ["Site", "Web", "Sayfa", "Bilgi", "İnternet"]
                        print("Hiç ipucu bulunamadı, URL temel etiketleri kullanılıyor")
    else:
        print("Tags anahtarı bulunamadı veya liste değil, içerikten etiketler oluşturuluyor...")
        
        # İçerikten etiket çıkar
        from collections import Counter
        import re
        
        # Başlık ve açıklamayı birleştir
        title = corrected_json.get('title', '')
        description = corrected_json.get('description', '')
        combined_text = (title + " " + description).lower()
        
        # Eğer içerik çok kısaysa, kategorileri kullan
        if len(combined_text) < 20:
            content_tags = []
            
            # Ana kategoriyi etiket olarak ekle
            if corrected_json['main_category']:
                content_tags.append(corrected_json['main_category'])
            
            # Alt kategoriyi etiket olarak ekle
            if corrected_json['subcategory'] and corrected_json['subcategory'] != corrected_json['main_category']:
                content_tags.append(corrected_json['subcategory'])
                
            # URL'den ipucu çıkar
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            domain_parts = domain.split('.')
            
            # Alan adının anlamlı kısmını etiket olarak kullan
            for part in domain_parts:
                if part not in ['www', 'com', 'net', 'org', 'io', 'co', 'gov', 'edu'] and len(part) > 2:
                    content_tags.append(part.capitalize())
            
            if len(content_tags) >= 3:
                corrected_json['tags'] = content_tags[:5]  # En fazla 5 etiket
                print(f"Kategoriler ve alan adından oluşturulan etiketler: {content_tags[:5]}")
            else:
                # URL yolundan ipucu çıkar
                path_parts = urlparse(url).path.split('/')
                path_tags = []
                for part in path_parts:
                    if part and len(part) > 3:
                        # Tire ve alt çizgi ile ayrılmış kelimeleri ayır
                        words = re.split(r'[-_]', part)
                        for word in words:
                            if word and len(word) > 3:
                                path_tags.append(word.capitalize())
                
                if path_tags:
                    corrected_json['tags'] = (content_tags + path_tags)[:5]  # En fazla 5 etiket
                    print(f"Kategoriler ve URL yolundan oluşturulan etiketler: {(content_tags + path_tags)[:5]}")
                else:
                    # En son çare olarak site bazlı etiketler
                    corrected_json['tags'] = ["Site", "Web", "Sayfa", "Bilgi", "İnternet"]
                    print("Hiç ipucu bulunamadı, site bazlı etiketler kullanılıyor")
        else:
            # Noktalama işaretlerini kaldır
            combined_text = re.sub(r'[^\w\s]', ' ', combined_text)
            
            # Stopwords - genel, yaygın, anlamsız kelimeler
            stopwords = ["ve", "veya", "ile", "için", "bu", "bir", "o", "de", "da", "ki", "ne", "ya", "çok", 
                        "nasıl", "en", "içinde", "üzerinde", "arasında", "olarak", "dolayı", "kadar", "önce", 
                        "sonra", "göre", "her", "the", "and", "or", "for", "in", "on", "at", "with", "from", 
                        "to", "a", "an", "by", "is", "are", "was", "were", "içerik", "web", "analiz", "sayfa"]
            
            # Kelimelere böl
            words = combined_text.split()
            
            # Yaygın kelimeleri kaldır
            filtered_words = [word for word in words if word not in stopwords and len(word) > 3]
            
            # En sık geçen anlamlı kelimeleri bul
            word_counter = Counter(filtered_words)
            common_words = word_counter.most_common(10)
            
            # Anlamlı kelimeleri etiket olarak kullan
            content_tags = []
            for word, count in common_words:
                if len(content_tags) >= 5:  # En fazla 5 etiket
                    break
                # İlk harfi büyüt
                tag = word.capitalize()
                if tag and tag not in content_tags:
                    content_tags.append(tag)
            
            # Eğer yeterli sayıda etiket bulunamadıysa, ana ve alt kategoriyi ekle
            if len(content_tags) < 5:
                # Ana kategoriyi etiket olarak ekle
                if corrected_json['main_category'] and corrected_json['main_category'] not in content_tags:
                    content_tags.append(corrected_json['main_category'])
                
                # Alt kategoriyi etiket olarak ekle
                if corrected_json['subcategory'] and corrected_json['subcategory'] not in content_tags and corrected_json['subcategory'] != corrected_json['main_category']:
                    content_tags.append(corrected_json['subcategory'])
            
            if content_tags:
                corrected_json['tags'] = content_tags
                print(f"İçerikten oluşturulan etiketler: {content_tags}")
            else:
                # Alan adından ipucu çıkar
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                domain_parts = domain.split('.')
                
                # Alan adının anlamlı kısmını etiket olarak kullan
                domain_tags = []
                for part in domain_parts:
                    if part not in ['www', 'com', 'net', 'org', 'io', 'co', 'gov', 'edu'] and len(part) > 2:
                        domain_tags.append(part.capitalize())
                
                if domain_tags:
                    corrected_json['tags'] = domain_tags
                    print(f"Alan adından oluşturulan etiketler: {domain_tags}")
                else:
                    # Son çare olarak URL temel etiketleri
                    corrected_json['tags'] = ["Site", "Web", "Sayfa", "Bilgi", "İnternet"]
                    print("Hiç ipucu bulunamadı, URL temel etiketleri kullanılıyor")
    
    # Debug için etiketleri yazdır
    print(f"Düzeltilmiş JSON'daki etiketler: {corrected_json.get('tags', [])}")
    
    # Etiketlerden en az birini ana kategori ve alt kategori olarak kaydır
    # eğer her ikisi de boşsa ve etiketler varsa
    if (not corrected_json['main_category'] or corrected_json['main_category'] == "") and (not corrected_json['subcategory'] or corrected_json['subcategory'] == "") and corrected_json['tags'] and not corrected_json['categories']:
        # İlk etiketi ana kategori olarak kullan
        corrected_json['main_category'] = corrected_json['tags'][0]
        # Eğer birden fazla etiket varsa, ikincisini alt kategori olarak kullan
        if len(corrected_json['tags']) > 1:
            corrected_json['subcategory'] = corrected_json['tags'][1]
        
        # categories dizisini de güncelle
        corrected_json['categories'] = [{
            'main_category': corrected_json['main_category'],
            'subcategory': corrected_json.get('subcategory', "")
        }]
    
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