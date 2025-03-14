import httpx
from bs4 import BeautifulSoup
import os
import time
import base64
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re
from difflib import SequenceMatcher
import django
import sys
from django.db import connection
import io
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse

# Django ortamını başlat (script doğrudan çalıştırıldığında)
def setup_django():
    # Django projesinin ana dizinini bul
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)  # tagwiseapp'in üst dizini
    
    # Django ayarlarını yükle
    if project_dir not in sys.path:
        sys.path.append(project_dir)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tagwisebackend.settings')
    
    # Django'yu başlat
    django.setup()
    print("Django ortamı başlatıldı.")

# Script doğrudan çalıştırıldığında Django'yu başlat
if __name__ == "__main__":
    setup_django()

# .env dosyasından API anahtarını yükle
load_dotenv()

# Gemini API anahtarını al ve ortam değişkenine ayarla
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

print(f"Gemini API anahtarı yüklendi: {'Evet' if GEMINI_API_KEY else 'Hayır'}")
genai.configure(api_key=GEMINI_API_KEY)

def fetch_html(url):
    """
    URL'den HTML içeriğini çeker.
    
    Args:
        url (str): Çekilecek sayfanın URL'si
        
    Returns:
        str or None: Başarılı olursa HTML içeriği, başarısız olursa None
    """
    try:
        print(f"URL'ye bağlanılıyor: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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

def capture_screenshot(url):
    """
    Selenium ile URL'nin ekran görüntüsünü alır.
    
    Args:
        url (str): Ekran görüntüsü alınacak sayfanın URL'si
        
    Returns:
        bytes or None: Başarılı olursa ekran görüntüsü bytes olarak, başarısız olursa None
    """
    print(f"Selenium ile ekran görüntüsü alınıyor: {url}")
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(("tag name", "body"))
        )
        
        screenshot = driver.get_screenshot_as_png()
        return screenshot
        
    except WebDriverException as e:
        print(f"Selenium WebDriver hatası: {e}")
        return None
    except TimeoutException as e:
        print(f"Sayfa yükleme zaman aşımı: {e}")
        return None
    except Exception as e:
        print(f"Ekran görüntüsü alırken beklenmeyen hata: {str(e)}")
        return None
    finally:
        if driver:
            driver.quit()

def analyze_screenshot_with_gemini(screenshot_base64, url, existing_title=None, existing_description=None):
    """Gemini AI ile ekran görüntüsünü analiz eder."""
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
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'promptimage.txt'), 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Mevcut kategorileri ve etiketleri prompt'a ekle
        prompt_with_categories = prompt_template + f"""

Mevcut ana kategoriler: {existing_categories['main_categories']}

Mevcut alt kategoriler: {existing_categories['subcategories']}

Mevcut etiketler: {existing_tags}

URL: {url}
"""
        
        # Eğer başlık ve açıklama zaten varsa, bunları belirt
        if existing_title:
            prompt_with_categories += f"\nSayfanın başlığı: {existing_title}"
        
        if existing_description:
            prompt_with_categories += f"\nSayfanın açıklaması: {existing_description}"
        
        # Gemini'ye istek gönder
        response = model.generate_content([prompt_with_categories, image_data])
        
        # Yanıtı al
        result = response.text
        
        # JSON formatını düzelt
        result = correct_json_format(result)
        
        try:
            # JSON'ı ayrıştır
            json_result = json.loads(result)
            
            # Başlık ve açıklama kontrolü
            if 'title' not in json_result or not json_result['title']:
                if existing_title:
                    json_result['title'] = existing_title
                else:
                    # URL'den başlık oluştur
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc
                    path = parsed_url.path
                    json_result['title'] = f"{domain}{path}"
            
            if 'description' not in json_result or not json_result['description']:
                if existing_description:
                    json_result['description'] = existing_description
                else:
                    json_result['description'] = f"Bu sayfa {url} adresinde bulunmaktadır."
            
            # Kategorileri ve etiketleri eşleştir
            json_result = match_categories_and_tags(json_result, existing_categories, existing_tags)
            
            # Eğer tags alanı yoksa, boş bir liste ekle
            if 'tags' not in json_result:
                json_result['tags'] = []
            
            return json_result
            
        except json.JSONDecodeError as e:
            print(f"JSON ayrıştırma hatası: {e}")
            print(f"Ham yanıt: {result}")
            
            # Fallback JSON
            fallback_json = {
                "title": existing_title if existing_title else url,
                "description": existing_description if existing_description else f"Bu sayfa {url} adresinde bulunmaktadır.",
                "main_category": "",
                "subcategory": "",
                "tags": []
            }
            
            return fallback_json
    
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda fallback JSON
        fallback_json = {
            "title": existing_title if existing_title else url,
            "description": existing_description if existing_description else f"Bu sayfa {url} adresinde bulunmaktadır.",
            "main_category": "",
            "subcategory": "",
            "tags": []
        }
        
        return fallback_json

def extract_content(html):
    """HTML içeriğinden header ve footer dışındaki ana içeriği çıkarır."""
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

def find_similar_category(category_name, is_main_category=True, accept_new=True):
    """
    Veritabanında benzer bir kategori adı arar ve bulursa döndürür.
    Bulamazsa ve accept_new=True ise orijinal kategori adını döndürür.
    
    Args:
        category_name (str): Aranacak kategori adı
        is_main_category (bool): Ana kategori mi yoksa alt kategori mi
        accept_new (bool): Eşleşme bulunamazsa yeni kategori kabul edilsin mi
        
    Returns:
        bool: Yeni kategori mi (True) yoksa mevcut kategori mi (False)
        str: Eşleşen kategori adı veya orijinal kategori adı
    """
    if not category_name:
        return False, category_name
    
    # Debug için yazdır
    print(f"Benzer kategori aranıyor: '{category_name}', Ana kategori mi: {is_main_category}")
    
    try:
        # Django'nun ORM'sini kullanarak kategorileri al
        from django.db import connection
        
        # Veritabanındaki kategorileri al
        with connection.cursor() as cursor:
            if is_main_category:
                # Ana kategorileri al (parent_id NULL olanlar)
                cursor.execute("SELECT id, name FROM tagwiseapp_category WHERE parent_id IS NULL")
            else:
                # Alt kategorileri al (parent_id NULL olmayanlar)
                cursor.execute("SELECT id, name FROM tagwiseapp_category WHERE parent_id IS NOT NULL")
            
            existing_categories = [(row[0], row[1]) for row in cursor.fetchall()]
        
        if not existing_categories:
            print("Veritabanında hiç kategori bulunamadı.")
            return True, category_name  # Yeni kategori olarak işaretle
        
        print(f"Veritabanında bulunan kategoriler: {[cat[1] for cat in existing_categories]}")
        
        # Tam eşleşme kontrolü (case insensitive)
        for cat_id, cat_name in existing_categories:
            if cat_name.lower() == category_name.lower():
                print(f"Tam eşleşme bulundu: '{cat_name}'")
                return False, cat_name  # Mevcut kategori
        
        # Kök kontrolü (örneğin "Haber" ve "Haberler")
        normalized_category = category_name.lower()
        for cat_id, cat_name in existing_categories:
            normalized_existing = cat_name.lower()
            
            # Eğer biri diğerinin başlangıcı ise ve en az 4 karakter eşleşiyorsa
            if (normalized_existing.startswith(normalized_category) or 
                normalized_category.startswith(normalized_existing)) and \
               min(len(normalized_existing), len(normalized_category)) >= 4:
                
                # Daha kısa olanı tercih et (örneğin "Haber" > "Haberler")
                if len(cat_name) <= len(category_name):
                    print(f"Kök eşleşmesi bulundu (kısa): '{cat_name}' <- '{category_name}'")
                    return False, cat_name  # Mevcut kategori
                else:
                    print(f"Kök eşleşmesi bulundu (uzun): '{cat_name}' -> '{category_name}'")
                    return True, category_name  # Yeni kategori olarak işaretle
        
        # En yüksek benzerlik oranını bul
        best_match = None
        best_ratio = 0
        
        for cat_id, cat_name in existing_categories:
            # Benzerlik oranını hesapla
            ratio = SequenceMatcher(None, cat_name.lower(), category_name.lower()).ratio()
            
            # Benzerlik oranı yeterince yüksekse kaydet (eşik değerini 0.7'ye yükselttik)
            if ratio > 0.7 and ratio > best_ratio:
                best_match = cat_name
                best_ratio = ratio
        
        if best_match:
            print(f"Benzerlik eşleşmesi bulundu: '{best_match}' (benzerlik: {best_ratio:.2f})")
            return False, best_match  # Mevcut kategori
        
        # Eşleşme bulunamadı, yeni kategori olarak kabul et
        if accept_new:
            print(f"Eşleşme bulunamadı, yeni kategori olarak kabul ediliyor: '{category_name}'")
            return True, category_name  # Yeni kategori olarak işaretle
        else:
            print(f"Eşleşme bulunamadı ve yeni kategori kabul edilmiyor, orijinal kategori kullanılıyor: '{category_name}'")
            return False, category_name  # Mevcut kategori olarak işaretle
    
    except Exception as e:
        print(f"Kategori eşleştirme sırasında hata oluştu: {e}")
        import traceback
        print(traceback.format_exc())
        return accept_new, category_name  # Hata durumunda orijinal kategori adını döndür

def get_existing_categories():
    """
    Veritabanındaki tüm kategorileri alır.
    
    Returns:
        dict: Ana kategoriler ve alt kategoriler sözlüğü
    """
    try:
        # Django ortamını başlat
        if 'django' not in sys.modules or not django.apps.apps.is_installed('tagwiseapp'):
            setup_django()
        
        from django.db import connection
        
        # Ana kategorileri al
        main_categories = []
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name FROM tagwiseapp_category WHERE parent_id IS NULL")
            main_categories = [(row[0], row[1]) for row in cursor.fetchall()]
        
        # Alt kategorileri al
        subcategories = []
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, parent_id FROM tagwiseapp_category WHERE parent_id IS NOT NULL")
            subcategories = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
        
        # Ana kategorileri ve alt kategorileri eşleştir
        category_map = {
            "main_categories": [cat[1] for cat in main_categories],
            "subcategories": [cat[1] for cat in subcategories],
            "parent_map": {}
        }
        
        # Her alt kategorinin hangi ana kategoriye ait olduğunu belirle
        for sub_id, sub_name, parent_id in subcategories:
            for main_id, main_name in main_categories:
                if parent_id == main_id:
                    if main_name not in category_map["parent_map"]:
                        category_map["parent_map"][main_name] = []
                    category_map["parent_map"][main_name].append(sub_name)
        
        print(f"Veritabanından {len(main_categories)} ana kategori ve {len(subcategories)} alt kategori alındı.")
        return category_map
    
    except Exception as e:
        print(f"Kategorileri alırken hata oluştu: {e}")
        import traceback
        print(traceback.format_exc())
        return {"main_categories": [], "subcategories": [], "parent_map": {}}

def get_existing_tags():
    """
    Veritabanındaki tüm etiketleri alır.
    
    Returns:
        list: Etiketlerin listesi
    """
    try:
        # Django ortamını başlat
        if 'django' not in sys.modules or not django.apps.apps.is_installed('tagwiseapp'):
            setup_django()
        
        from django.db import connection
        
        # Etiketleri al
        tags = []
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name FROM tagwiseapp_tag")
            tags = [row[1] for row in cursor.fetchall()]
        
        print(f"Veritabanından {len(tags)} etiket alındı.")
        return tags
    
    except Exception as e:
        print(f"Etiketleri alırken hata oluştu: {e}")
        import traceback
        print(traceback.format_exc())
        return []

def find_similar_tag(tag_name, existing_tags=None, accept_new=True):
    """
    Veritabanında benzer bir etiket adı arar ve bulursa döndürür.
    Bulamazsa ve accept_new=True ise orijinal etiket adını döndürür.
    
    Args:
        tag_name (str): Aranacak etiket adı
        existing_tags (list): Mevcut etiketlerin listesi (None ise veritabanından alınır)
        accept_new (bool): Eşleşme bulunamazsa yeni etiket kabul edilsin mi
        
    Returns:
        bool: Yeni etiket mi (True) yoksa mevcut etiket mi (False)
        str: Eşleşen etiket adı veya orijinal etiket adı
    """
    if not tag_name:
        return False, tag_name
    
    # Debug için yazdır
    print(f"Benzer etiket aranıyor: '{tag_name}'")
    
    try:
        # Eğer existing_tags parametresi verilmemişse, veritabanından al
        if existing_tags is None:
            # Django'nun ORM'sini kullanarak etiketleri al
            from django.db import connection
            
            # Veritabanındaki etiketleri al
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, name FROM tagwiseapp_tag")
                existing_tags = [row[1] for row in cursor.fetchall()]
        
        if not existing_tags:
            print("Veritabanında hiç etiket bulunamadı.")
            return True, tag_name  # Yeni etiket olarak işaretle
        
        # Tam eşleşme kontrolü (case insensitive)
        for tag_name_db in existing_tags:
            if tag_name_db.lower() == tag_name.lower():
                print(f"Tam eşleşme bulundu: '{tag_name_db}'")
                return False, tag_name_db  # Mevcut etiket
        
        # En yüksek benzerlik oranını bul
        best_match = None
        best_ratio = 0
        
        for tag_name_db in existing_tags:
            # Benzerlik oranını hesapla
            ratio = SequenceMatcher(None, tag_name_db.lower(), tag_name.lower()).ratio()
            
            # Benzerlik oranı yeterince yüksekse kaydet (eşik değerini 0.8'e yükselttik)
            if ratio > 0.8 and ratio > best_ratio:
                best_match = tag_name_db
                best_ratio = ratio
        
        if best_match:
            print(f"Benzerlik eşleşmesi bulundu: '{best_match}' (benzerlik: {best_ratio:.2f})")
            return False, best_match  # Mevcut etiket
        
        # Eşleşme bulunamadı, yeni etiket olarak kabul et
        if accept_new:
            print(f"Eşleşme bulunamadı, yeni etiket olarak kabul ediliyor: '{tag_name}'")
            return True, tag_name  # Yeni etiket olarak işaretle
        else:
            print(f"Eşleşme bulunamadı ve yeni etiket kabul edilmiyor, orijinal etiket kullanılıyor: '{tag_name}'")
            return False, tag_name  # Mevcut etiket olarak işaretle
    
    except Exception as e:
        print(f"Etiket eşleştirme sırasında hata oluştu: {e}")
        import traceback
        print(traceback.format_exc())
        return accept_new, tag_name  # Hata durumunda orijinal etiket adını döndür

def categorize_with_gemini(content, url, existing_title=None, existing_description=None):
    """Gemini AI ile içeriği kategorize eder."""
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
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'prompt.txt'), 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Mevcut kategorileri ve etiketleri prompt'a ekle
        prompt_with_categories = prompt_template + f"""

Mevcut ana kategoriler: {existing_categories['main_categories']}

Mevcut alt kategoriler: {existing_categories['subcategories']}

Mevcut etiketler: {existing_tags}

"""
        
        # İçeriği ekle
        prompt_with_categories += input_text
        
        # Gemini'ye istek gönder
        response = model.generate_content(prompt_with_categories)
        
        # Yanıtı al
        result = response.text
        
        # JSON formatını düzelt
        result = correct_json_format(result)
        
        try:
            # JSON'ı ayrıştır
            json_result = json.loads(result)
            
            # Açıklama kontrolü
            if 'description' not in json_result or not json_result['description']:
                # İçerikten açıklama oluştur
                description = extract_description(content)
                if description:
                    json_result['description'] = description
                elif existing_description:
                    json_result['description'] = existing_description
                else:
                    json_result['description'] = f"Bu sayfa {url} adresinde bulunmaktadır."
            
            # Kategorileri ve etiketleri eşleştir
            json_result = match_categories_and_tags(json_result, existing_categories, existing_tags)
            
            # Eğer tags alanı yoksa, boş bir liste ekle
            if 'tags' not in json_result:
                json_result['tags'] = []
            
            return json_result
            
        except json.JSONDecodeError as e:
            print(f"JSON ayrıştırma hatası: {e}")
            print(f"Ham yanıt: {result}")
            
            # Fallback JSON
            fallback_json = {
                "title": existing_title if existing_title else url,
                "description": existing_description if existing_description else f"Bu sayfa {url} adresinde bulunmaktadır.",
                "main_category": "",
                "subcategory": "",
                "tags": []
            }
            
            return fallback_json
    
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda fallback JSON
        fallback_json = {
            "title": existing_title if existing_title else url,
            "description": existing_description if existing_description else f"Bu sayfa {url} adresinde bulunmaktadır.",
            "main_category": "",
            "subcategory": "",
            "tags": []
        }
        
        return fallback_json

def extract_description(content):
    """İçerikten açıklama çıkarır."""
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
        # Part sınıfı yerine doğrudan dict kullanıyoruz
        image_part = {"mime_type": image_type, "data": image_bytes}
        
        return image_part
    
    except Exception as e:
        print(f"Görüntü yüklenirken hata: {e}")
        import traceback
        print(traceback.format_exc())
        return None

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

def match_categories_and_tags(json_result, existing_categories=None, existing_tags=None):
    """
    AI'nin önerdiği kategorileri ve etiketleri veritabanındaki benzer olanlarla eşleştirir.
    
    Args:
        json_result (dict): AI'nin önerdiği kategoriler ve etiketler
        existing_categories (dict): Mevcut kategoriler ve alt kategoriler
        existing_tags (list): Mevcut etiketler
        
    Returns:
        dict: Eşleştirilmiş kategoriler ve etiketler
    """
    # Eğer existing_categories ve existing_tags verilmemişse, veritabanından al
    if existing_categories is None:
        existing_categories = get_existing_categories()
    
    if existing_tags is None:
        existing_tags = get_existing_tags()
    
    # Ana kategoriyi eşleştir
    if 'main_category' in json_result and json_result['main_category']:
        is_new_category, matched_main_category = find_similar_category(json_result['main_category'], True, True)
        
        # Eğer eşleşme varsa ve orijinalden farklıysa, log
        if matched_main_category != json_result['main_category']:
            print(f"Ana kategori eşleştirildi: '{json_result['main_category']}' -> '{matched_main_category}'")
        
        # Eşleştirilmiş ana kategoriyi kaydet
        json_result['main_category'] = matched_main_category
        
        # Yeni kategori ise bonus puan ekle
        if is_new_category:
            json_result['category_bonus'] = 0.1  # Yeni ana kategorilere bonus puan
    
    # Alt kategoriyi eşleştir
    if 'subcategory' in json_result and json_result['subcategory']:
        is_new_subcategory, matched_subcategory = find_similar_category(json_result['subcategory'], False, True)
        
        # Eğer eşleşme varsa ve orijinalden farklıysa, log
        if matched_subcategory != json_result['subcategory']:
            print(f"Alt kategori eşleştirildi: '{json_result['subcategory']}' -> '{matched_subcategory}'")
        
        # Eşleştirilmiş alt kategoriyi kaydet
        json_result['subcategory'] = matched_subcategory
        
        # Yeni alt kategori ise bonus puan ekle
        if is_new_subcategory:
            if 'category_bonus' in json_result:
                json_result['category_bonus'] += 0.05  # Yeni alt kategorilere bonus puan
            else:
                json_result['category_bonus'] = 0.05
    
    # Etiketleri eşleştir
    matched_tags = []
    if 'tags' in json_result and json_result['tags']:
        for tag in json_result['tags']:
            is_new_tag, similar_tag = find_similar_tag(tag, existing_tags, True)
            if similar_tag:
                matched_tags.append(similar_tag)
            else:
                matched_tags.append(tag)  # Eşleşme bulunamazsa orijinal etiketi ekle
    
    # Etiketleri güncelle
    if matched_tags:
        json_result['tags'] = matched_tags
    elif 'tags' not in json_result or not json_result['tags']:
        json_result['tags'] = []
    
    return json_result

def calculate_category_relevance(category, json_result):
    """
    Bir kategorinin içerikle ne kadar ilgili olduğunu hesaplar.
    
    Args:
        category (dict): Değerlendirilecek kategori
        json_result (dict): Tüm analiz sonucu
        
    Returns:
        float: 0 ile 1 arasında bir ilgililik skoru
    """
    try:
        # Başlangıç skoru - daha yüksek bir başlangıç değeri kullanıyoruz
        score = 0.45  # Başlangıç değerini 0.4'ten 0.45'e yükselttik
        
        # Başlık ve açıklamadan anahtar kelimeleri çıkar
        title = json_result.get('title', '').lower()
        description = json_result.get('description', '').lower()
        
        # Ana kategori ve alt kategori
        main_category = category.get('main_category', '').lower()
        subcategory = category.get('subcategory', '').lower()
        
        # Tam kelime eşleşmesi kontrolü için regex kullanımı
        import re
        
        # Kategori adları başlık veya açıklamada tam kelime olarak geçiyorsa skoru artır
        if re.search(r'\b' + re.escape(main_category) + r'\b', title) or re.search(r'\b' + re.escape(main_category) + r'\b', description):
            score += 0.3  # Artış miktarını 0.25'ten 0.3'e yükselttik
            print(f"Kategori '{main_category}' başlık veya açıklamada tam kelime olarak bulundu, skor artırıldı.")
        elif main_category in title or main_category in description:
            # Tam kelime değil ama içerikte geçiyorsa daha az artır
            score += 0.2  # Artış miktarını 0.15'ten 0.2'ye yükselttik
            print(f"Kategori '{main_category}' başlık veya açıklamada kısmen bulundu, skor artırıldı.")
        else:
            # Hiçbir eşleşme yoksa bile minimum bir artış sağla
            score += 0.05
            print(f"Kategori '{main_category}' için minimum skor artışı uygulandı.")
        
        if subcategory and (re.search(r'\b' + re.escape(subcategory) + r'\b', title) or re.search(r'\b' + re.escape(subcategory) + r'\b', description)):
            score += 0.3  # Artış miktarını 0.25'ten 0.3'e yükselttik
            print(f"Alt kategori '{subcategory}' başlık veya açıklamada tam kelime olarak bulundu, skor artırıldı.")
        elif subcategory and (subcategory in title or subcategory in description):
            # Tam kelime değil ama içerikte geçiyorsa daha az artır
            score += 0.2  # Artış miktarını 0.15'ten 0.2'ye yükselttik
            print(f"Alt kategori '{subcategory}' başlık veya açıklamada kısmen bulundu, skor artırıldı.")
        elif subcategory:
            # Alt kategori varsa minimum bir artış sağla
            score += 0.05
            print(f"Alt kategori '{subcategory}' için minimum skor artışı uygulandı.")
        
        # Kategori adının uzunluğunu kontrol et - çok kısa kategoriler (3 harften az) için ceza
        if len(main_category) < 3:
            score -= 0.05  # Cezayı 0.1'den 0.05'e düşürdük
            print(f"Kategori adı '{main_category}' çok kısa, skor azaltıldı.")
        
        if subcategory and len(subcategory) < 3:
            score -= 0.05  # Cezayı 0.1'den 0.05'e düşürdük
            print(f"Alt kategori adı '{subcategory}' çok kısa, skor azaltıldı.")
        
        # Belirli kategori kombinasyonları için uyumluluk kontrolü
        # Örneğin, "Yazılım" ana kategorisi ile "Sanat" alt kategorisi uyumsuz olabilir
        incompatible_pairs = [
            ('yazılım', 'sanat'),
            ('yazılım', 'eğlence'),
            ('teknoloji', 'yemek'),
            ('teknoloji', 'sanat'),
            ('iş', 'oyun'),
            ('finans', 'eğlence'),
            ('sağlık', 'teknoloji'),
            ('eğitim', 'alışveriş')
        ]
        
        for incompatible_main, incompatible_sub in incompatible_pairs:
            if main_category.find(incompatible_main) >= 0 and subcategory.find(incompatible_sub) >= 0:
                score -= 0.25  # Ceza miktarını 0.35'ten 0.25'e düşürdük
                print(f"Uyumsuz kategori çifti tespit edildi: '{main_category}' ve '{subcategory}', skor azaltıldı.")
                break
        
        # Etiketlerle kategori uyumluluğunu kontrol et
        if 'tags' in json_result and json_result['tags']:
            relevant_tags = 0
            total_tags = len(json_result['tags'])
            
            for tag in json_result['tags']:
                tag = tag.lower()
                # Tam kelime eşleşmesi kontrolü
                if (re.search(r'\b' + re.escape(tag) + r'\b', main_category) or 
                    re.search(r'\b' + re.escape(main_category) + r'\b', tag) or 
                    (subcategory and (re.search(r'\b' + re.escape(tag) + r'\b', subcategory) or 
                                      re.search(r'\b' + re.escape(subcategory) + r'\b', tag)))):
                    relevant_tags += 1
                # Kısmi eşleşme kontrolü (tam kelime eşleşmesi yoksa)
                elif (tag in main_category or main_category in tag or 
                     (subcategory and (tag in subcategory or subcategory in tag))):
                    relevant_tags += 0.7  # Kısmi eşleşmelere daha yüksek puan ver (0.5'ten 0.7'ye)
            
            # Etiketlerin ilgililik oranına göre skor artışı
            relevance_ratio = relevant_tags / total_tags
            if relevance_ratio >= 0.4:  # Eşiği %50'den %40'a düşürdük
                score += 0.3  # 0.25'ten 0.3'e yükselttik
                print(f"Kategori ile yüksek oranda ilgili etiketler bulundu (%{relevance_ratio*100:.0f}), skor önemli ölçüde artırıldı.")
            elif relevance_ratio >= 0.2:  # Eşiği %25'ten %20'ye düşürdük
                score += 0.2  # 0.15'ten 0.2'ye yükselttik
                print(f"Kategori ile ilgili etiketler bulundu (%{relevance_ratio*100:.0f}), skor artırıldı.")
            elif relevance_ratio > 0:  # En az bir etiket ilgiliyse
                score += 0.15  # 0.1'den 0.15'e yükselttik
                print(f"Kategori ile az sayıda ilgili etiket bulundu (%{relevance_ratio*100:.0f}), skor artırıldı.")
        
        # Skoru 0-1 aralığında sınırla
        score = max(0.0, min(1.0, score))
        
        return score
    
    except Exception as e:
        print(f"İlgililik skoru hesaplanırken hata: {e}")
        return 0.45  # Hata durumunda yüksek bir skor döndür (0.4 yerine 0.45)

def analyze_url(url):
    """URL'yi analiz edip kategori belirler."""
    print(f"\nURL analiz ediliyor: {url}")
    
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
    """Ana fonksiyon."""
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