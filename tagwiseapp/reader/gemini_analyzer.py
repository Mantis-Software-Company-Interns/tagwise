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
from .text_prompt import TEXT_SYSTEM_INSTRUCTION
from .image_prompt import IMAGE_SYSTEM_INSTRUCTION
from dotenv import load_dotenv
import re

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

def generate_summary_from_screenshot(screenshot_base64, url):
    """
    Ekran görüntüsünden içerik özeti oluşturur.
    
    Args:
        screenshot_base64 (str): Base64 kodlanmış ekran görüntüsü
        url (str): Analiz edilen URL
        
    Returns:
        str: İçerik özeti
    """
    print("Ekran görüntüsünden özet oluşturuluyor...")
    
    try:
        # Modeli seç - sistem talimatlarını destekleyecek bir sürüm
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction="""
            Sen bir web sayfası analisti olarak görev yapıyorsun. 
            Verilen görüntüleri analiz ederek kapsamlı özetler oluşturursun. 
            Özetlerin, sayfanın ana konusunu, amacını, hedef kitlesini ve önemli bilgileri içermelidir.
            Özetlerin en az 200, en fazla 500 kelime olmalıdır.
            """
        )
        
        # Base64 kodlu görüntüyü hazırla
        image_data = {"mime_type": "image/png", "data": base64.b64decode(screenshot_base64)}
        
        # Kullanıcı içeriğini hazırla
        user_content = f"""
        Bu bir web sayfasının ekran görüntüsüdür. Lütfen bu sayfanın içeriğini analiz edip kapsamlı bir özet oluştur.
        
        URL: {url}
        """
        
        # Gemini'ye istek gönder
        response = model.generate_content([user_content, image_data])
        
        # Yanıtı al
        summary = response.text.strip()
        print(f"Ekran görüntüsünden özet oluşturuldu: {summary[:100]}...")
        
        return summary
        
    except Exception as e:
        print(f"Ekran görüntüsünden özet oluşturulurken hata: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda boş özet
        return f"URL: {url} için ekran görüntüsünden özet oluşturulamadı."

def generate_summary_from_content(content, url):
    """
    HTML içeriğinden özet oluşturur.
    
    Args:
        content (str): HTML içeriği
        url (str): Analiz edilen URL
        
    Returns:
        str: İçerik özeti
    """
    print("HTML içeriğinden özet oluşturuluyor...")
    
    try:
        # Modeli seç - sistem talimatlarını destekleyecek bir sürüm
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction="""
            Sen bir web sayfası analisti olarak görev yapıyorsun. 
            Verilen HTML içeriğini analiz ederek kapsamlı özetler oluşturursun. 
            Özetlerin, sayfanın ana konusunu, amacını, hedef kitlesini ve önemli bilgileri içermelidir.
            Özetlerin en az 200, en fazla 500 kelime olmalıdır.
            """
        )
        
        # Kullanıcı içeriğini hazırla
        user_content = f"""
        Bu bir web sayfasının içeriğidir. Lütfen bu içeriği analiz edip kapsamlı bir özet oluştur.
        
        URL: {url}
        
        İçerik:
        {content}
        """
        
        # Gemini'ye istek gönder
        response = model.generate_content(user_content)
        
        # Yanıtı al
        summary = response.text.strip()
        print(f"HTML içeriğinden özet oluşturuldu: {summary[:100]}...")
        
        return summary
        
    except Exception as e:
        print(f"HTML içeriğinden özet oluşturulurken hata: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda boş özet
        return f"URL: {url} için HTML içeriğinden özet oluşturulamadı."

def categorize_summary(summary, url, existing_title=None, existing_description=None):
    """
    Özeti kategorize eder.
    
    Args:
        summary (str): İçerik özeti
        url (str): Analiz edilen URL
        existing_title (str, optional): Mevcut başlık
        existing_description (str, optional): Mevcut açıklama
        
    Returns:
        dict: Kategorize sonuçları
    """
    print("Özet kategorize ediliyor...")
    
    # Mevcut kategorileri ve etiketleri al
    existing_categories = get_existing_categories()
    existing_tags = get_existing_tags()
    
    try:
        # Modeli seç - sistem talimatlarını destekleyecek bir sürüm
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=MULTI_CATEGORY_SYSTEM_INSTRUCTION
        )
        
        # Generation config
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
        
        # Kullanıcı içeriğini hazırla
        user_content = f"""
        URL: {url}
        
        Mevcut ana kategoriler: {existing_categories['main_categories']}
        
        Mevcut alt kategoriler: {existing_categories['subcategories']}
        
        Mevcut etiketler: {existing_tags}
        
        Sayfa Özeti:
        {summary}
        """
        
        # Eğer başlık ve açıklama zaten varsa, bunları belirt
        if existing_title:
            user_content += f"\nSayfanın başlığı: {existing_title}"
        
        if existing_description:
            user_content += f"\nSayfanın açıklaması: {existing_description}"
        
        # Gemini'ye istek gönder
        response = model.generate_content(
            user_content,
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
            
            # Manuel düzeltme dene - JSON dosyasını doğru bir biçime getirmeye çalış
            try:
                # Ana kategori ve alt kategori gibi temel bilgileri çıkarmaya çalış
                manual_json = {}
                
                # Regex ile alanları bul
                patterns = {
                    'title': r'"title"\s*:\s*"([^"]*)"',
                    'description': r'"description"\s*:\s*"([^"]*)"',
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, result)
                    if match:
                        manual_json[key] = match.group(1)
                
                # Kategorileri bulmaya çalış - bu daha zorlu olabilir
                categories_match = re.search(r'"categories"\s*:\s*\[(.*?)\]', result, re.DOTALL)
                if categories_match:
                    categories_text = categories_match.group(1)
                    # Regex ile kategorileri ayıkla
                    manual_json['categories'] = []
                    category_items = re.findall(r'{(.*?)}', categories_text, re.DOTALL)
                    
                    for item in category_items:
                        category_item = {}
                        main_cat_match = re.search(r'"main_category"\s*:\s*"([^"]*)"', item)
                        if main_cat_match:
                            category_item['main_category'] = main_cat_match.group(1)
                        
                        sub_cat_match = re.search(r'"subcategory"\s*:\s*"([^"]*)"', item)
                        if sub_cat_match:
                            category_item['subcategory'] = sub_cat_match.group(1)
                        
                        if category_item:
                            manual_json['categories'].append(category_item)
                
                # Etiketleri bulmaya çalış
                tags_match = re.search(r'"tags"\s*:\s*\[(.*?)\]', result, re.DOTALL)
                if tags_match:
                    tags_text = tags_match.group(1)
                    print(f"Regex ile etiketler bulundu: {tags_text}")
                    # Etiketleri virgülle ayır ve her bir etiketi tırnak işaretlerinden temizle
                    tags = [tag.strip().strip('"').strip("'") for tag in tags_text.split(',')]
                    manual_json['tags'] = [tag for tag in tags if tag]  # Boş etiketleri filtrele
                    print(f"İşlenen etiketler: {manual_json['tags']}")
                else:
                    print("İlk regex ile etiket bulunamadı, alternatif yöntem deneniyor...")
                    # Alternatif etiket arama yöntemi
                    alt_tags_match = re.search(r'tags["\s]*:[\s]*\[(.*?)\]', result, re.DOTALL)
                    if alt_tags_match:
                        tags_text = alt_tags_match.group(1)
                        print(f"Alternatif regex ile etiketler bulundu: {tags_text}")
                        tags = []
                        for tag in tags_text.split(','):
                            tag_match = re.search(r'["\'](.*?)["\']', tag)
                            if tag_match:
                                tags.append(tag_match.group(1).strip())
                            elif tag.strip():
                                tags.append(tag.strip())
                        manual_json['tags'] = [tag for tag in tags if tag]
                        print(f"Alternatif yöntemle işlenen etiketler: {manual_json['tags']}")
                    else:
                        print("Hiçbir yöntemle etiket bulunamadı! Ham yanıt içeriği:")
                        print(result[:1000])  # İlk 1000 karakteri yazdır
                        print("Varsayılan etiketler ekleniyor...")
                        # Eğer hiçbir etiket bulunamazsa, içerik bazlı otomatik etiketler oluştur
                        manual_json['tags'] = ["içerik", "web", "analiz", "sayfa"]
                        print(f"Varsayılan etiketler: {manual_json['tags']}")
                
                # Eğer yeterince bilgi çıkarabildiysek, düzeltilmiş JSON'ı kullan
                if manual_json:
                    print(f"Manuel olarak düzeltilmiş JSON: {manual_json}")
                    json_result = ensure_correct_json_structure(manual_json, url, existing_title, existing_description)
                    json_result = match_categories_and_tags(json_result, existing_categories, existing_tags)
                    return json_result
            except Exception as manual_fix_error:
                print(f"Manuel JSON düzeltme hatası: {manual_fix_error}")
                import traceback
                print(traceback.format_exc())
            
            # Fallback JSON
            fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
            fallback_json = match_categories_and_tags(fallback_json, existing_categories, existing_tags)
            
            return fallback_json
    
    except Exception as e:
        print(f"Kategorize edilirken hata: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda fallback JSON
        fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
        
        return fallback_json

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
    
    try:
        # Mevcut kategorileri ve etiketleri al
        existing_categories = get_existing_categories()
        existing_tags = get_existing_tags()
        
        # Base64 kodlu görüntüyü hazırla
        image_data = {"mime_type": "image/png", "data": base64.b64decode(screenshot_base64)}
        
        # Modeli seç - sistem talimatlarını destekleyecek bir sürüm
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=MULTI_CATEGORY_SYSTEM_INSTRUCTION
        )
        
        # Generation config
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
        
        # Kullanıcı içeriğini hazırla
        user_content = f"""
        URL: {url}
        
        Mevcut ana kategoriler: {existing_categories['main_categories']}
        
        Mevcut alt kategoriler: {existing_categories['subcategories']}
        
        Mevcut etiketler: {existing_tags}
        """
        
        # Eğer başlık ve açıklama zaten varsa, bunları belirt
        if existing_title:
            user_content += f"\nSayfanın başlığı: {existing_title}"
        
        if existing_description:
            user_content += f"\nSayfanın açıklaması: {existing_description}"
        
        # Gemini'ye istek gönder
        response = model.generate_content(
            [user_content, image_data],
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
            
            # Manuel düzeltme yap
            # Manuel düzeltme dene - JSON dosyasını doğru bir biçime getirmeye çalış
            try:
                # Ana kategori ve alt kategori gibi temel bilgileri çıkarmaya çalış
                manual_json = {}
                
                # Regex ile alanları bul
                patterns = {
                    'title': r'"title"\s*:\s*"([^"]*)"',
                    'description': r'"description"\s*:\s*"([^"]*)"',
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, result)
                    if match:
                        manual_json[key] = match.group(1)
                
                # Kategorileri bulmaya çalış - bu daha zorlu olabilir
                categories_match = re.search(r'"categories"\s*:\s*\[(.*?)\]', result, re.DOTALL)
                if categories_match:
                    categories_text = categories_match.group(1)
                    # Regex ile kategorileri ayıkla
                    manual_json['categories'] = []
                    category_items = re.findall(r'{(.*?)}', categories_text, re.DOTALL)
                    
                    for item in category_items:
                        category_item = {}
                        main_cat_match = re.search(r'"main_category"\s*:\s*"([^"]*)"', item)
                        if main_cat_match:
                            category_item['main_category'] = main_cat_match.group(1)
                        
                        sub_cat_match = re.search(r'"subcategory"\s*:\s*"([^"]*)"', item)
                        if sub_cat_match:
                            category_item['subcategory'] = sub_cat_match.group(1)
                        
                        if category_item:
                            manual_json['categories'].append(category_item)
                
                # Etiketleri bulmaya çalış
                tags_match = re.search(r'"tags"\s*:\s*\[(.*?)\]', result, re.DOTALL)
                if tags_match:
                    tags_text = tags_match.group(1)
                    print(f"Regex ile etiketler bulundu: {tags_text}")
                    # Etiketleri virgülle ayır ve her bir etiketi tırnak işaretlerinden temizle
                    tags = [tag.strip().strip('"').strip("'") for tag in tags_text.split(',')]
                    manual_json['tags'] = [tag for tag in tags if tag]  # Boş etiketleri filtrele
                    print(f"İşlenen etiketler: {manual_json['tags']}")
                else:
                    print("İlk regex ile etiket bulunamadı, alternatif yöntem deneniyor...")
                    # Alternatif etiket arama yöntemi
                    alt_tags_match = re.search(r'tags["\s]*:[\s]*\[(.*?)\]', result, re.DOTALL)
                    if alt_tags_match:
                        tags_text = alt_tags_match.group(1)
                        print(f"Alternatif regex ile etiketler bulundu: {tags_text}")
                        tags = []
                        for tag in tags_text.split(','):
                            tag_match = re.search(r'["\'](.*?)["\']', tag)
                            if tag_match:
                                tags.append(tag_match.group(1).strip())
                            elif tag.strip():
                                tags.append(tag.strip())
                        manual_json['tags'] = [tag for tag in tags if tag]
                        print(f"Alternatif yöntemle işlenen etiketler: {manual_json['tags']}")
                    else:
                        print("Hiçbir yöntemle etiket bulunamadı! Ham yanıt içeriği:")
                        print(result[:1000])  # İlk 1000 karakteri yazdır
                        print("Varsayılan etiketler ekleniyor...")
                        # Eğer hiçbir etiket bulunamazsa, içerik bazlı otomatik etiketler oluştur
                        manual_json['tags'] = ["içerik", "web", "analiz", "sayfa"]
                        print(f"Varsayılan etiketler: {manual_json['tags']}")
                
                # Düzeltilmiş JSON'ı kullan
                if manual_json:
                    json_result = ensure_correct_json_structure(manual_json, url, existing_title, existing_description)
                    json_result = match_categories_and_tags(json_result, existing_categories, existing_tags)
                    return json_result
                
            except Exception as manual_fix_error:
                print(f"Manuel JSON düzeltme hatası: {manual_fix_error}")
                import traceback
                print(traceback.format_exc())
            
            # Fallback JSON
            fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
            fallback_json = match_categories_and_tags(fallback_json, existing_categories, existing_tags)
            
            return fallback_json
            
    except Exception as e:
        print(f"Ekran görüntüsü analiz edilirken hata: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda fallback JSON
        fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
        fallback_json = match_categories_and_tags(fallback_json, existing_categories, existing_tags)
        
        return fallback_json

# Kategorize işlevi için Gemini sistem talimatlarını birden fazla kategori desteği ile güncelle
MULTI_CATEGORY_SYSTEM_INSTRUCTION = """
Sen bir web sayfası içerik analisti olarak görev yapıyorsun. 
Verilen içeriği analiz ederek başlık, açıklama, kategoriler ve etiketler oluşturursun.

Önemli Kurallar:
- İçeriği analiz ederek için en uygun kategorileri özgürce atama yap - sistem artık filtreleme YAPMAYACAK.
- İçerikle ilgili ANALİZ yapıp içeriğe en uygun kategorileri doğrudan ata. İlgililik puanı hesaplayıp filtreleme yapma!
- İçeriğe doğrudan ilgili olmayan ama tematik olarak bağlantılı kategorileri de dahil et.
- Her sayfa için EN AZ 1, EN FAZLA 3 kategori çifti önermelisin. 
- Yazılım şirketleri için "Teknoloji", "Yazılım", "Bilişim" gibi kategoriler kullan.
- Eğitim siteleri için "Eğitim" ana kategorisini kullan.
- Haber siteleri için "Haber" veya "Medya" kategorilerini kullan.
- E-ticaret siteleri için "Alışveriş" veya "E-ticaret" kategorilerini kullan.
- Kişisel bloglar için "Blog" veya "Kişisel" kategorilerini kullan.
- Sana verilen mevcut kategori listesine bakmadan ÖZGÜRCE kategori atama yap. Sistem sonradan benzer olanları eşleştirecek.
- Her kategori için mutlaka bir alt kategori belirle.
- Alt kategoriler, ana kategorilere uygun olmalıdır. Örneğin "Teknoloji > Web Geliştirme", "Eğitim > Üniversite"

Etiketler Oluşturma Kurallar:
- Etiketler, sayfanın içeriğindeki özgün ve belirgin anahtar kelimeleri içermelidir - asla genel amaçlı ["içerik", "web", "analiz", "sayfa"] gibi etiketler kullanma!
- İçerikten çıkarılan en önemli ve belirgin terimleri, ürün veya hizmet adlarını, sektör terimlerini ve özel kavramları etiket olarak kullan.
- Her sayfa için en az 5, en fazla 10 etiket önermelisin.
- Etiketler içerikle doğrudan ilgili olmalı ve spesifik terimler içermelidir.
- Etiketler, sayfanın ana konusunu, sektörünü, sunduğu hizmetleri veya ürünleri yansıtmalıdır.
- Sayfadaki teknik terimler, önemli kavramlar veya hizmet adları etiket olarak kullanılmalıdır.
- Etiketler 1-3 kelimeden oluşmalı, çok uzun cümleler olmamalıdır.
- Her etiket özgün olmalı ve listedeki diğer etiketlerden farklı olmalıdır.
- Hiçbir koşulda boş veya çok genel etiketler oluşturma.

Yanıtın her zaman JSON formatında olmalıdır ve şu yapıda döndürmelisin:
{
  "title": "Sayfanın başlığı",
  "description": "Sayfanın kısa açıklaması (200-400 karakter)",
  "categories": [
    {
      "main_category": "Ana Kategori 1",
      "subcategory": "Alt Kategori 1"
    },
    {
      "main_category": "Ana Kategori 2",
      "subcategory": "Alt Kategori 2"
    },
    {
      "main_category": "Ana Kategori 3",
      "subcategory": "Alt Kategori 3"
    }
  ],
  "tags": ["ÖzgünEtiket1", "ÖzgünEtiket2", "ÖzgünEtiket3", "ÖzgünEtiket4", "ÖzgünEtiket5"]
}

ÖNEMLİ: Etiketler kısmını asla ["içerik", "web", "analiz", "sayfa"] gibi genel terimlerle doldurma! 
Her etiket sayfanın içeriğini doğru ve özgün şekilde yansıtmalıdır. Etiketler asla boş bir liste olmamalıdır!

ÖNEMLİ: İçeriğe uygun kategorileri ata ve filtreleme yapma. Her durumda kategori oluştur.
"""

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
    
    try:
        # Mevcut kategorileri ve etiketleri al
        existing_categories = get_existing_categories()
        existing_tags = get_existing_tags()
        
        # Modeli seç - sistem talimatlarını destekleyecek bir sürüm
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=MULTI_CATEGORY_SYSTEM_INSTRUCTION
        )
        
        # Generation config
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
        
        # Kullanıcı içeriğini hazırla
        user_content = f"""
        URL: {url}
        
        Mevcut ana kategoriler: {existing_categories['main_categories']}
        
        Mevcut alt kategoriler: {existing_categories['subcategories']}
        
        Mevcut etiketler: {existing_tags}
        
        İçerik:
        {content}
        """
        
        # Eğer başlık ve açıklama zaten varsa, bunları belirt
        if existing_title:
            user_content += f"\nSayfanın başlığı: {existing_title}"
        
        if existing_description:
            user_content += f"\nSayfanın açıklaması: {existing_description}"
        
        # Gemini'ye istek gönder
        response = model.generate_content(
            user_content,
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
            
            # Manuel düzeltme yap
            # Manuel düzeltme dene - JSON dosyasını doğru bir biçime getirmeye çalış
            try:
                # Ana kategori ve alt kategori gibi temel bilgileri çıkarmaya çalış
                manual_json = {}
                
                # Regex ile alanları bul
                patterns = {
                    'title': r'"title"\s*:\s*"([^"]*)"',
                    'description': r'"description"\s*:\s*"([^"]*)"',
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, result)
                    if match:
                        manual_json[key] = match.group(1)
                
                # Kategorileri bulmaya çalış - bu daha zorlu olabilir
                categories_match = re.search(r'"categories"\s*:\s*\[(.*?)\]', result, re.DOTALL)
                if categories_match:
                    categories_text = categories_match.group(1)
                    # Regex ile kategorileri ayıkla
                    manual_json['categories'] = []
                    category_items = re.findall(r'{(.*?)}', categories_text, re.DOTALL)
                    
                    for item in category_items:
                        category_item = {}
                        main_cat_match = re.search(r'"main_category"\s*:\s*"([^"]*)"', item)
                        if main_cat_match:
                            category_item['main_category'] = main_cat_match.group(1)
                        
                        sub_cat_match = re.search(r'"subcategory"\s*:\s*"([^"]*)"', item)
                        if sub_cat_match:
                            category_item['subcategory'] = sub_cat_match.group(1)
                        
                        if category_item:
                            manual_json['categories'].append(category_item)
                
                # Etiketleri bulmaya çalış
                tags_match = re.search(r'"tags"\s*:\s*\[(.*?)\]', result, re.DOTALL)
                if tags_match:
                    tags_text = tags_match.group(1)
                    print(f"Regex ile etiketler bulundu: {tags_text}")
                    # Etiketleri virgülle ayır ve her bir etiketi tırnak işaretlerinden temizle
                    tags = [tag.strip().strip('"').strip("'") for tag in tags_text.split(',')]
                    manual_json['tags'] = [tag for tag in tags if tag]  # Boş etiketleri filtrele
                    print(f"İşlenen etiketler: {manual_json['tags']}")
                else:
                    print("İlk regex ile etiket bulunamadı, alternatif yöntem deneniyor...")
                    # Alternatif etiket arama yöntemi
                    alt_tags_match = re.search(r'tags["\s]*:[\s]*\[(.*?)\]', result, re.DOTALL)
                    if alt_tags_match:
                        tags_text = alt_tags_match.group(1)
                        print(f"Alternatif regex ile etiketler bulundu: {tags_text}")
                        tags = []
                        for tag in tags_text.split(','):
                            tag_match = re.search(r'["\'](.*?)["\']', tag)
                            if tag_match:
                                tags.append(tag_match.group(1).strip())
                            elif tag.strip():
                                tags.append(tag.strip())
                        manual_json['tags'] = [tag for tag in tags if tag]
                        print(f"Alternatif yöntemle işlenen etiketler: {manual_json['tags']}")
                    else:
                        print("Hiçbir yöntemle etiket bulunamadı! Ham yanıt içeriği:")
                        print(result[:1000])  # İlk 1000 karakteri yazdır
                        print("Varsayılan etiketler ekleniyor...")
                        # Eğer hiçbir etiket bulunamazsa, içerik bazlı otomatik etiketler oluştur
                        manual_json['tags'] = ["içerik", "web", "analiz", "sayfa"]
                        print(f"Varsayılan etiketler: {manual_json['tags']}")
                
                # Düzeltilmiş JSON'ı kullan
                if manual_json:
                    json_result = ensure_correct_json_structure(manual_json, url, existing_title, existing_description)
                    json_result = match_categories_and_tags(json_result, existing_categories, existing_tags)
                    return json_result
                
            except Exception as manual_fix_error:
                print(f"Manuel JSON düzeltme hatası: {manual_fix_error}")
                import traceback
                print(traceback.format_exc())
            
            # Fallback JSON
            fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
            fallback_json = match_categories_and_tags(fallback_json, existing_categories, existing_tags)
            
            return fallback_json
            
        except json.JSONDecodeError as e:
            print(f"JSON ayrıştırma hatası: {e}")
            print(f"Ham yanıt: {result}")
            
            # Manuel düzeltme yap
            # Manuel düzeltme dene - JSON dosyasını doğru bir biçime getirmeye çalış
            try:
                # Ana kategori ve alt kategori gibi temel bilgileri çıkarmaya çalış
                manual_json = {}
                
                # Regex ile alanları bul
                patterns = {
                    'title': r'"title"\s*:\s*"([^"]*)"',
                    'description': r'"description"\s*:\s*"([^"]*)"',
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, result)
                    if match:
                        manual_json[key] = match.group(1)
                
                # Kategorileri bulmaya çalış - bu daha zorlu olabilir
                categories_match = re.search(r'"categories"\s*:\s*\[(.*?)\]', result, re.DOTALL)
                if categories_match:
                    categories_text = categories_match.group(1)
                    # Regex ile kategorileri ayıkla
                    manual_json['categories'] = []
                    category_items = re.findall(r'{(.*?)}', categories_text, re.DOTALL)
                    
                    for item in category_items:
                        category_item = {}
                        main_cat_match = re.search(r'"main_category"\s*:\s*"([^"]*)"', item)
                        if main_cat_match:
                            category_item['main_category'] = main_cat_match.group(1)
                        
                        sub_cat_match = re.search(r'"subcategory"\s*:\s*"([^"]*)"', item)
                        if sub_cat_match:
                            category_item['subcategory'] = sub_cat_match.group(1)
                        
                        if category_item:
                            manual_json['categories'].append(category_item)
                
                # Etiketleri bulmaya çalış
                tags_match = re.search(r'"tags"\s*:\s*\[(.*?)\]', result, re.DOTALL)
                if tags_match:
                    tags_text = tags_match.group(1)
                    print(f"Regex ile etiketler bulundu: {tags_text}")
                    # Etiketleri virgülle ayır ve her bir etiketi tırnak işaretlerinden temizle
                    tags = [tag.strip().strip('"').strip("'") for tag in tags_text.split(',')]
                    manual_json['tags'] = [tag for tag in tags if tag]  # Boş etiketleri filtrele
                    print(f"İşlenen etiketler: {manual_json['tags']}")
                else:
                    print("İlk regex ile etiket bulunamadı, alternatif yöntem deneniyor...")
                    # Alternatif etiket arama yöntemi
                    alt_tags_match = re.search(r'tags["\s]*:[\s]*\[(.*?)\]', result, re.DOTALL)
                    if alt_tags_match:
                        tags_text = alt_tags_match.group(1)
                        print(f"Alternatif regex ile etiketler bulundu: {tags_text}")
                        tags = []
                        for tag in tags_text.split(','):
                            tag_match = re.search(r'["\'](.*?)["\']', tag)
                            if tag_match:
                                tags.append(tag_match.group(1).strip())
                            elif tag.strip():
                                tags.append(tag.strip())
                        manual_json['tags'] = [tag for tag in tags if tag]
                        print(f"Alternatif yöntemle işlenen etiketler: {manual_json['tags']}")
                    else:
                        print("Hiçbir yöntemle etiket bulunamadı! Ham yanıt içeriği:")
                        print(result[:1000])  # İlk 1000 karakteri yazdır
                        print("Varsayılan etiketler ekleniyor...")
                        # Eğer hiçbir etiket bulunamazsa, içerik bazlı otomatik etiketler oluştur
                        manual_json['tags'] = ["içerik", "web", "analiz", "sayfa"]
                        print(f"Varsayılan etiketler: {manual_json['tags']}")
                
                # Düzeltilmiş JSON'ı kullan
                if manual_json:
                    json_result = ensure_correct_json_structure(manual_json, url, existing_title, existing_description)
                    json_result = match_categories_and_tags(json_result, existing_categories, existing_tags)
                    return json_result
                
            except Exception as manual_fix_error:
                print(f"Manuel JSON düzeltme hatası: {manual_fix_error}")
                import traceback
                print(traceback.format_exc())
            
            # Fallback JSON
            fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
            fallback_json = match_categories_and_tags(fallback_json, existing_categories, existing_tags)
            
            return fallback_json
            
    except Exception as e:
        print(f"İçerik kategorize edilirken hata: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda fallback JSON
        fallback_json = ensure_correct_json_structure({}, url, existing_title, existing_description)
        fallback_json = match_categories_and_tags(fallback_json, existing_categories, existing_tags)
        
        return fallback_json

def fix_turkish_json(json_str):
    """Türkçe metinlerdeki JSON sorunlarını düzeltir."""
    
    # İç içe tırnak işaretlerini düzelt
    json_str = re.sub(r'(?<!\\)"([^"]*)"([^"]*)"', lambda m: f'"{m.group(1)}\"{m.group(2)}"', json_str)
    
    # Türkçe karakterleri düzelt
    json_str = json_str.replace('"u,n', '"un')
    json_str = json_str.replace('"ı,n', '"ın')
    json_str = json_str.replace('"i,n', '"in')
    
    # Kaçış karakterlerini düzelt
    json_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
    
    # Çift tırnak içindeki tek tırnakları düzelt
    json_str = re.sub(r'"([^"]*?)\'([^"]*?)"', r'"\1\\"\2"', json_str)
    
    # JSON string içindeki virgülleri düzelt
    json_str = re.sub(r'(?<=\w),(?=\w)', '', json_str)
    
    return json_str

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