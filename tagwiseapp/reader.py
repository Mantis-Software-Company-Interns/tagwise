import httpx
from bs4 import BeautifulSoup
import os
import time
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
import re
from difflib import SequenceMatcher
import django
import sys
from django.db import connection

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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print(f"Gemini API anahtarı yüklendi: {'Evet' if GEMINI_API_KEY else 'Hayır'}")

# API anahtarı yoksa varsayılan değeri kullan

def fetch_html(url):
    """URL'den HTML içeriğini çeker."""
    try:
        print(f"URL'ye bağlanılıyor: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Timeout değerini artıralım
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
    except Exception as e:
        print(f"HTML çekerken beklenmeyen hata: {e}")
        import traceback
        print(traceback.format_exc())
        return None

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

def find_similar_category(category_name, is_main_category=True):
    """
    Veritabanında benzer bir kategori adı arar ve bulursa döndürür.
    
    Args:
        category_name (str): Aranacak kategori adı
        is_main_category (bool): Ana kategori mi yoksa alt kategori mi aranıyor
        
    Returns:
        str: Eşleşen kategori adı veya orijinal kategori adı
    """
    if not category_name:
        return category_name
    
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
            return category_name
        
        print(f"Veritabanında bulunan kategoriler: {[cat[1] for cat in existing_categories]}")
        
        # Tam eşleşme kontrolü (case insensitive)
        for cat_id, cat_name in existing_categories:
            if cat_name.lower() == category_name.lower():
                print(f"Tam eşleşme bulundu: '{cat_name}'")
                return cat_name
        
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
                    return cat_name
                else:
                    print(f"Kök eşleşmesi bulundu (uzun): '{cat_name}' -> '{category_name}'")
                    return category_name
        
        # En yüksek benzerlik oranını bul
        best_match = None
        best_ratio = 0
        
        for cat_id, cat_name in existing_categories:
            # Benzerlik oranını hesapla
            ratio = SequenceMatcher(None, cat_name.lower(), category_name.lower()).ratio()
            
            # Benzerlik oranı yeterince yüksekse kaydet
            if ratio > 0.75 and ratio > best_ratio:  # Eşik değerini 0.75'e düşürdük
                best_match = cat_name
                best_ratio = ratio
        
        if best_match:
            print(f"Benzerlik eşleşmesi bulundu: '{best_match}' (benzerlik: {best_ratio:.2f})")
            return best_match
        
        print(f"Eşleşme bulunamadı, orijinal kategori kullanılıyor: '{category_name}'")
        return category_name
    
    except Exception as e:
        print(f"Kategori eşleştirme sırasında hata oluştu: {e}")
        import traceback
        print(traceback.format_exc())
        return category_name  # Hata durumunda orijinal kategori adını döndür

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

def categorize_with_gemini(content, url):
    """Gemini AI ile içeriği analiz edip kategori belirler."""
    if not content or len(content.strip()) < 50:
        return "{\"hata\": \"Web sitesine erişilemedi veya içeriği anlaşılamadı.\"}"
    
    # İçeriği kısalt (Gemini'nin token limitine uygun olması için)
    max_length = 15000
    if len(content) > max_length:
        content = content[:max_length] + "..."
    
    # Veritabanındaki mevcut kategorileri al
    existing_categories = get_existing_categories()
    
    client = genai.Client(
        api_key=GEMINI_API_KEY,
    )

    model = "gemini-2.0-flash"
    
    # URL, içerik ve mevcut kategorileri birleştir
    input_text = f"""URL: {url}

İçerik:
{content}

Mevcut Kategoriler:
Ana Kategoriler: {', '.join(existing_categories['main_categories'])}
Alt Kategoriler: {', '.join(existing_categories['subcategories'])}

Ana Kategori-Alt Kategori İlişkileri:
"""

    # Ana kategori-alt kategori ilişkilerini ekle
    for main_cat, sub_cats in existing_categories['parent_map'].items():
        input_text += f"- {main_cat}: {', '.join(sub_cats)}\n"
    
    print(f"Gemini'ye gönderilen mevcut kategoriler: {existing_categories['main_categories']}")
    
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=input_text
                ),
            ],
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE",  # Block none
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE",  # Block none
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE",  # Block none
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE",  # Block none
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_CIVIC_INTEGRITY",
                threshold="BLOCK_NONE",  # Block none
            ),
        ],
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            properties = {
                "categories": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        properties = {
                            "main_category": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "subcategory": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "tags": genai.types.Schema(
                                type = genai.types.Type.ARRAY,
                                items = genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                ),
                            ),
                        },
                    ),
                ),
            },
        ),
        system_instruction=[
            types.Part.from_text(text="""
**Sen, web sitelerini analiz ederek otomatik kategori ve etiket ataması yapma konusunda uzmanlaşmış bir yapay zekâ asistanısın.**  
Görevin, verilen URL'deki web sitesinin içeriğini derinlemesine inceleyerek, en uygun üst kategori, alt kategori ve etiketleri belirlemek.  

**ÖNEMLİ KURALLAR:**
1. **Öncelikle mevcut kategori listesinden seçim yapmaya çalış.** Eğer içerik için uygun bir kategori mevcut kategoriler arasında varsa, o kategoriyi kullan.
2. **Eğer içerik için mevcut kategoriler arasında uygun bir kategori bulamazsan, yeni bir kategori önerebilirsin.**
3. **Mevcut bir ana kategoriye ait alt kategori önerirken, o ana kategoriye ait mevcut alt kategorilerden birini seçmeye çalış.**
4. **Eğer uygun alt kategori yoksa**, yeni bir alt kategori öner.
5. İçerikle en alakalı **3-5 adet etiket** belirle.  

3. **Çıktıyı Yalnızca Aşağıdaki JSON Formatında Ver:**  

**Örnek Çıktı:**  

```json
{
    \"categories\": [
        {
            \"main_category\": \"Yazılım\",
            \"subcategory\": \"Yazılım Geliştirme\",
            \"tags\": [\"Yapay Zeka\", \"Kodlama\", \"Programlama\"]
        },
        {
            \"main_category\": \"Danışmanlık\",
            \"subcategory\": \"Yazılım Danışmanlığı\",
            \"tags\": [\"Teknik Destek\", \"IT Çözümleri\", \"Dijital Dönüşüm\"]
        }
    ]
}
```"""),
        ],
    )

    try:
        response = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response += chunk.text
        
        print(f"Gemini yanıtı alındı: {response[:200]}...")  # İlk 200 karakteri yazdır
        
        # Yanıtı doğru JSON formatına dönüştürmeye çalış
        try:
            # Yanıt zaten JSON formatında mı kontrol et
            parsed_response = json.loads(response)
            
            # Eğer categories anahtarı yoksa, uygun formata dönüştür
            if 'categories' not in parsed_response:
                # Birden fazla JSON objesi olabilir
                json_matches = re.findall(r'\{[\s\S]*?"categories"[\s\S]*?\}', response)
                
                if json_matches:
                    # İlk eşleşmeyi kullan
                    response = json_matches[0]
                    parsed_response = json.loads(response)
            
            # Kategorileri doğrula ve mevcut kategorilerle eşleştir
            if 'categories' in parsed_response:
                print("Gemini'nin önerdiği kategoriler doğrulanıyor...")
                for i, category in enumerate(parsed_response['categories']):
                    print(f"Kategori {i+1} doğrulanıyor...")
                    
                    # Ana kategori kontrolü
                    if 'main_category' in category:
                        main_cat = category['main_category']
                        # Eğer ana kategori mevcut değilse, benzer bir kategori bulmaya çalış
                        if main_cat not in existing_categories['main_categories']:
                            print(f"Bilgi: '{main_cat}' ana kategorisi veritabanında bulunamadı.")
                            # En benzer ana kategoriyi bul
                            best_match = None
                            best_ratio = 0
                            for existing in existing_categories['main_categories']:
                                ratio = SequenceMatcher(None, existing.lower(), main_cat.lower()).ratio()
                                if ratio > 0.8 and ratio > best_ratio:  # Yüksek benzerlik eşiği
                                    best_match = existing
                                    best_ratio = ratio
                            
                            if best_match:
                                print(f"'{main_cat}' yerine benzer kategori '{best_match}' kullanılıyor (benzerlik: {best_ratio:.2f})")
                                category['main_category'] = best_match
                                # Yeni kategori önerisini işaretle
                                category['is_new_main_category'] = False
                            else:
                                print(f"'{main_cat}' yeni bir ana kategori olarak öneriliyor.")
                                # Yeni kategori önerisini işaretle
                                category['is_new_main_category'] = True
                        else:
                            # Mevcut kategori
                            category['is_new_main_category'] = False
                    
                    # Alt kategori kontrolü
                    if 'subcategory' in category and 'main_category' in category:
                        sub_cat = category['subcategory']
                        main_cat = category['main_category']
                        
                        # Ana kategori yeni değilse, alt kategori kontrolü yap
                        if not category.get('is_new_main_category', False):
                            # Bu ana kategoriye ait alt kategorileri kontrol et
                            valid_subcats = existing_categories['parent_map'].get(main_cat, [])
                            
                            if sub_cat not in valid_subcats:
                                print(f"Bilgi: '{sub_cat}' alt kategorisi '{main_cat}' ana kategorisine ait değil.")
                                # Bu ana kategoriye ait en benzer alt kategoriyi bul
                                best_match = None
                                best_ratio = 0
                                for existing in valid_subcats:
                                    ratio = SequenceMatcher(None, existing.lower(), sub_cat.lower()).ratio()
                                    if ratio > 0.8 and ratio > best_ratio:  # Yüksek benzerlik eşiği
                                        best_match = existing
                                        best_ratio = ratio
                                
                                if best_match:
                                    print(f"'{sub_cat}' yerine benzer alt kategori '{best_match}' kullanılıyor (benzerlik: {best_ratio:.2f})")
                                    category['subcategory'] = best_match
                                    # Yeni alt kategori önerisini işaretle
                                    category['is_new_subcategory'] = False
                                else:
                                    print(f"'{sub_cat}' yeni bir alt kategori olarak öneriliyor.")
                                    # Yeni alt kategori önerisini işaretle
                                    category['is_new_subcategory'] = True
                            else:
                                # Mevcut alt kategori
                                category['is_new_subcategory'] = False
                        else:
                            # Ana kategori yeni olduğu için alt kategori de yeni
                            print(f"'{sub_cat}' yeni bir alt kategori olarak öneriliyor (yeni ana kategori altında).")
                            category['is_new_subcategory'] = True
                
                print("Kategori doğrulama tamamlandı.")
                # Güncellenmiş yanıtı JSON formatına dönüştür
                return json.dumps(parsed_response, ensure_ascii=False)
            
            # Yanıt zaten doğru formatta
            return response
        except json.JSONDecodeError as e:
            print(f"JSON ayrıştırma hatası: {e}")
            # JSON formatında değilse, uygun formata dönüştürmeye çalış
            json_matches = re.findall(r'\{[\s\S]*?"categories"[\s\S]*?\}', response)
            
            if json_matches:
                # İlk eşleşmeyi kullan
                return json_matches[0]
            
            # Hiçbir JSON formatı bulunamadıysa, ham yanıtı döndür
            return response
    except Exception as e:
        print(f"Gemini AI ile kategori belirlerken hata: {e}")
        import traceback
        print(traceback.format_exc())  # Detaylı hata mesajını yazdır
        return "{\"hata\": \"Kategori belirlenemedi\"}"

def analyze_url(url):
    """URL'yi analiz edip kategori belirler."""
    print(f"\nURL analiz ediliyor: {url}")
    
    # HTML içeriğini çek
    html = fetch_html(url)
    if not html:
        return f"URL: {url}\nSonuç: HTML içeriği çekilemedi."
    
    # Ana içeriği ayıkla
    content = extract_content(html)
    if not content:
        return f"URL: {url}\nSonuç: İçerik ayıklanamadı."
    
    # İçeriği kategorize et
    category_json = categorize_with_gemini(content, url)
    
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