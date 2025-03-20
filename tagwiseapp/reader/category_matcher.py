"""
Category Matcher Module

This module provides functions for matching categories and tags with existing ones in the database.
"""

from difflib import SequenceMatcher
import re
from .django_setup import setup_django

def get_existing_categories():
    """
    Veritabanındaki tüm kategorileri alır.
    
    Returns:
        dict: Ana kategoriler ve alt kategoriler sözlüğü
    """
    try:
        # Django ortamını başlat
        import sys
        import django
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
        import sys
        import django
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

def find_similar_category(category_name, is_main_category=True, accept_new=True):
    """
    Verilen kategori adına en yakın kategoriyi bulur.
    Eğer yeterince benzer bir kategori bulunamazsa, yeni bir kategori oluşturulur.
    Artık her zaman bir kategori döndürür - benzer bulunamazsa orijinal kategoriyi döndürür.
    
    Args:
        category_name (str): Kategori adı
        is_main_category (bool): Ana kategori mi alt kategori mi
        accept_new (bool): Yeni kategori kabul edilsin mi
        
    Returns:
        tuple: (is_new, similar_category_name) - Yeni kategori mi, benzer kategori adı
    """
    if not category_name or not isinstance(category_name, str):
        return True, ""  # Boş veya geçersiz kategori adı
    
    # Kategori adını temizle
    category_name = category_name.strip()
    if not category_name:
        return True, ""  # Temizleme sonrası boş kategori adı
    
    # Veritabanından kategorileri al
    conn = None
    cursor = None
    existing_categories = []
    
    try:
        import sqlite3
        from django.conf import settings
        
        print(f"Benzer kategori aranıyor: '{category_name}', Ana kategori mi: {is_main_category}")
        
        # Ana kategori mi alt kategori mi kontrolü
        category_type = "Ana kategori" if is_main_category else "Alt kategori"
        
        # Veritabanı bağlantısını aç
        db_path = settings.DATABASES['default']['NAME']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQL sorgusu hazırla - ana kategoriler için parent_id IS NULL, alt kategoriler için parent_id IS NOT NULL
        if is_main_category:
            query = "SELECT id, name FROM tagwiseapp_category WHERE parent_id IS NULL"
        else:
            query = "SELECT id, name FROM tagwiseapp_category WHERE parent_id IS NOT NULL"
            
        # Sorguyu çalıştır
        cursor.execute(query)
        
        # Sonuçları al
        existing_categories = [(row[0], row[1]) for row in cursor.fetchall()]
        
        # Kategorileri yazdır
        print(f"Veritabanında bulunan kategoriler: {[cat[1] for cat in existing_categories]}")
        
        # Tam eşleşme kontrolü
        for cat_id, cat_name in existing_categories:
            if cat_name.lower() == category_name.lower():
                print(f"Tam eşleşme bulundu: '{cat_name}'")
                return False, cat_name
        
        # Yüksek benzerlik oranı için değişken
        threshold = 0.8  # %80 benzerlik eşiği
        
        # En yüksek benzerlik skorunu bul
        highest_score = 0
        most_similar = None
        
        for cat_id, cat_name in existing_categories:
            # Eğer kategorilerden biri boşsa atla
            if not cat_name or not category_name:
                continue
                
            # Levenshtein mesafesine dayalı benzerlik skoru (0-1 arası, 1 tam eşleşme)
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, cat_name.lower(), category_name.lower()).ratio()
            
            if similarity > highest_score:
                highest_score = similarity
                most_similar = cat_name
        
        # Eğer benzerlik yeterince yüksekse, mevcut kategoriyi kullan
        if highest_score >= threshold and most_similar:
            print(f"Yüksek benzerlik bulundu (%{highest_score*100:.1f}): '{category_name}' -> '{most_similar}'")
            return False, most_similar
        
        # Benzerlik düşükse veya hiç benzer kategori yoksa yeni kategori oluştur
        print(f"Benzer kategori bulunamadı veya benzerlik düşük (%{highest_score*100:.1f}). Yeni {category_type.lower()}: '{category_name}'")
        return True, category_name
    
    except Exception as e:
        print(f"Kategori benzerliği hesaplanırken hata oluştu: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda orijinal kategori adını döndür
        return True, category_name
        
    finally:
        # Veritabanı bağlantısını kapat
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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
    # Etiket geçerlilik kontrolü - None veya boş string kontrolü
    if not tag_name or not isinstance(tag_name, str):
        print(f"Geçersiz etiket: '{tag_name}', atlanıyor.")
        return False, ""
    
    # Etiket uzunluk kontrolü - Çok kısa etiketler reddedilir
    if len(tag_name.strip()) < 2:
        print(f"Etiket '{tag_name}' çok kısa, atlanıyor.")
        return False, ""
    
    # Etiket normalizasyonu - başında ve sonunda boşlukları kaldır
    tag_name = tag_name.strip()
    
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
        
        # Semantik eşdeğerlikler sözlüğü - etiketler için
        semantic_equivalents = {
            # Türkçe-İngilizce karşılıklar
            "yapay zeka": ["ai", "artificial intelligence", "machine learning", "ml"],
            "ai": ["yapay zeka", "artificial intelligence", "machine learning", "ml"],
            "yazılım": ["software", "programming", "coding"],
            "software": ["yazılım", "programming", "coding"],
            "teknoloji": ["technology", "tech"],
            "technology": ["teknoloji", "tech"],
            "bilgisayar": ["computer", "pc", "computing"],
            "computer": ["bilgisayar", "pc", "computing"],
            "veri": ["data", "bilgi"],
            "data": ["veri", "bilgi"],
            "bulut": ["cloud", "cloud computing"],
            "cloud": ["bulut", "cloud computing"],
            "internet": ["web", "çevrimiçi", "online"],
            "web": ["internet", "çevrimiçi", "online"],
            "mobil": ["mobile", "uygulamalar", "apps"],
            "mobile": ["mobil", "uygulamalar", "apps"],
            "oyun": ["game", "gaming"],
            "game": ["oyun", "gaming"],
            "iş": ["business", "work"],
            "business": ["iş", "work"],
            "finans": ["finance", "financial", "para"],
            "finance": ["finans", "financial", "para"],
            "sağlık": ["health", "healthcare", "medical"],
            "health": ["sağlık", "healthcare", "medical"],
            "haber": ["news", "haberler"],
            "news": ["haber", "haberler"],
            "eğitim": ["education", "learning", "öğrenme"],
            "education": ["eğitim", "learning", "öğrenme"],
            "bilim": ["science", "scientific"],
            "science": ["bilim", "scientific"],
            "sanat": ["art", "artistic"],
            "art": ["sanat", "artistic"],
            "güvenlik": ["security", "safety"],
            "security": ["güvenlik", "safety"],
            # Ekstra eşdeğerlikler - Yaygın kısaltmalar ve varyasyonlar
            "programlama": ["coding", "programming", "yazılım", "kod"],
            "ml": ["machine learning", "yapay öğrenme", "makine öğrenmesi"],
            "ios": ["apple", "iphone", "ipad"],
            "android": ["google", "mobile os"],
            "frontend": ["ui", "arayüz", "client side"],
            "backend": ["server", "sunucu", "api"],
            "veritabanı": ["database", "db", "veri tabanı"],
            "ux": ["user experience", "kullanıcı deneyimi"],
            "ui": ["user interface", "kullanıcı arayüzü"],
            "devops": ["development operations", "deployment", "ci/cd"],
            "python": ["py", "python language"],
            "javascript": ["js", "ecmascript"],
            "typescript": ["ts", "typed javascript"],
            "html": ["hypertext markup language", "html5"],
            "css": ["cascading style sheets", "styling"],
            "bulut bilişim": ["cloud computing", "cloud", "aws", "azure", "gcp"],
            "yapay sinir ağları": ["neural networks", "nn", "derin öğrenme"],
            "derin öğrenme": ["deep learning", "dl"],
            "doğal dil işleme": ["natural language processing", "nlp"],
            "büyük veri": ["big data", "hadoop", "spark"],
        }
        
        normalized_tag = tag_name.lower()
        
        # Tam eşleşme kontrolü (case insensitive)
        for tag_name_db in existing_tags:
            if tag_name_db and isinstance(tag_name_db, str) and tag_name_db.lower() == normalized_tag:
                print(f"Tam eşleşme bulundu: '{tag_name_db}'")
                return False, tag_name_db  # Mevcut etiket
        
        # Semantik eşdeğerlik kontrolü
        for tag_name_db in existing_tags:
            if not tag_name_db or not isinstance(tag_name_db, str):
                continue
                
            tag_db_lower = tag_name_db.lower()
            
            # Eğer etiket adı semantik eşdeğerlikler sözlüğünde varsa
            if tag_db_lower in semantic_equivalents and normalized_tag in semantic_equivalents[tag_db_lower]:
                print(f"Semantik eşdeğerlik bulundu: '{tag_name_db}' <- '{tag_name}'")
                return False, tag_name_db  # Mevcut etiket
                
            # Ters yönlü kontrol
            if normalized_tag in semantic_equivalents:
                if tag_db_lower in semantic_equivalents[normalized_tag]:
                    print(f"Semantik eşdeğerlik bulundu: '{tag_name_db}' -> '{tag_name}'")
                    return False, tag_name_db  # Mevcut etiket
        
        # En yüksek benzerlik oranını bul
        best_match = None
        best_ratio = 0
        
        for tag_name_db in existing_tags:
            if not tag_name_db or not isinstance(tag_name_db, str):
                continue
                
            # Benzerlik oranını hesapla
            ratio = SequenceMatcher(None, tag_name_db.lower(), normalized_tag).ratio()
            
            # Benzerlik oranı çok yüksekse kaydet (eşik değerini 0.9'a yükseltiyoruz)
            if ratio > 0.9 and ratio > best_ratio:
                best_match = tag_name_db
                best_ratio = ratio
        
        if best_match:
            print(f"Yüksek benzerlik eşleşmesi bulundu: '{best_match}' (benzerlik: {best_ratio:.2f})")
            return False, best_match  # Mevcut etiket
        
        # Kök kontrolü (etiketler için de)
        for tag_name_db in existing_tags:
            if not tag_name_db or not isinstance(tag_name_db, str) or len(tag_name_db) < 5:
                continue
                
            tag_db_lower = tag_name_db.lower()
            
            # Eğer biri diğerinin başlangıcı ise ve en az 5 karakter eşleşiyorsa
            # Ve ortak kök uzunluğu her iki kelimenin en az %85'i kadarsa (etiketlerde daha katı)
            if ((tag_db_lower.startswith(normalized_tag) or 
                normalized_tag.startswith(tag_db_lower)) and
               min(len(tag_db_lower), len(normalized_tag)) >= 5):
                
                # Ortak kök uzunluğunu hesapla
                common_root_length = 0
                for i in range(min(len(tag_db_lower), len(normalized_tag))):
                    if tag_db_lower[i] == normalized_tag[i]:
                        common_root_length += 1
                    else:
                        break
                
                # Ortak kök her iki kelimenin de en az %85'ini oluşturuyorsa eşleştir
                if (common_root_length / len(tag_db_lower) >= 0.85 and 
                    common_root_length / len(normalized_tag) >= 0.85):
                    print(f"Güçlü kök eşleşmesi bulundu: '{tag_name_db}' ve '{tag_name}'")
                    
                    # Daha kısa olanı tercih et
                    if len(tag_name_db) <= len(tag_name):
                        return False, tag_name_db  # Mevcut etiket
                    else:
                        return False, tag_name_db  # Yine de veritabanındaki etiketi tercih et
        
        # Eşleşme bulunamadı, yeni etiket olarak kabul et
        if accept_new:
            print(f"Yeterince benzer etiket bulunamadı, yeni etiket olarak kabul ediliyor: '{tag_name}'")
            return True, tag_name  # Yeni etiket olarak işaretle
        else:
            print(f"Eşleşme bulunamadı ve yeni etiket kabul edilmiyor, orijinal etiket kullanılıyor: '{tag_name}'")
            return False, tag_name  # Mevcut etiket olarak işaretle
    
    except Exception as e:
        print(f"Etiket eşleştirme sırasında hata oluştu: {e}")
        import traceback
        print(traceback.format_exc())
        return accept_new, tag_name  # Hata durumunda orijinal etiket adını döndür

def match_categories_and_tags(json_result, existing_categories=None, existing_tags=None):
    """
    Gemini AI tarafından önerilen kategorileri ve etiketleri
    veritabanındaki mevcut kategoriler ve etiketlerle eşleştirir.
    Tüm kategoriler doğrudan kabul edilir, ilgililik puanı kontrolü yapılmaz.
    Sadece var olan benzer kategorileri eşleştirir.
    
    Args:
        json_result (dict): Gemini AI'dan gelen sonuç
        existing_categories (dict, optional): Mevcut kategoriler
        existing_tags (list, optional): Mevcut etiketler
        
    Returns:
        dict: Eşleştirilmiş sonuç
    """
    print("Kategori ve etiket eşleştirme başlıyor...")
    
    # Mevcut kategori ve etiketler sağlanmamışsa, veritabanından al
    if existing_categories is None:
        existing_categories = get_existing_categories()
    
    if existing_tags is None:
        existing_tags = get_existing_tags()
    
    # Eğer sonuçta categories alanı yoksa, eski stilde main_category ve subcategory alanları kullanılıyordur
    if 'categories' not in json_result:
        json_result['categories'] = []
        
        # Eğer main_category alanı varsa, bir kategori öğesi oluştur
        if 'main_category' in json_result and json_result['main_category']:
            category_item = {'main_category': json_result['main_category']}
            if 'subcategory' in json_result and json_result['subcategory']:
                category_item['subcategory'] = json_result['subcategory']
            json_result['categories'].append(category_item)
    
    # Eşleştirilmiş kategorileri saklamak için liste
    matched_categories = []
    
    # Her ana kategori için alt kategorileri takip etmek için sözlük
    main_category_subcategories = {}
    
    # Her önerilen kategori için
    for category in json_result.get('categories', []):
        if 'main_category' not in category or not category['main_category']:
            continue
            
        main_category = category.get('main_category', '').strip()
        subcategory = category.get('subcategory', '').strip()
        
        if not main_category:
            continue
    
        # Ana kategoriyi eşleştir
        is_new_main, matched_main = find_similar_category(main_category, is_main_category=True)
        if not matched_main:
            # Eğer benzer kategori bulunamazsa orijinal kategoriyi kullan
            matched_main = main_category
            print(f"Benzer ana kategori bulunamadı, orijinal kategori kullanılıyor: '{main_category}'")
        
        # Alt kategoriyi eşleştir - eğer alt kategori belirtilmişse
        is_new_sub = False
        matched_sub = ''
        
        if subcategory:
            # Bu ana kategori için daha önce alt kategori eşleşip eşleşmediğini kontrol et
            if matched_main in main_category_subcategories:
                # Ana kategori daha önce bir alt kategori ile eşleşmişse, eklemeyi atla
                print(f"Ana kategori '{matched_main}' zaten '{main_category_subcategories[matched_main]}' alt kategorisiyle eşleşti, tekrar eşleşme yapılmayacak")
                continue
                
            is_new_sub, matched_sub = find_similar_category(subcategory, is_main_category=False)
            
            if not matched_sub:
                # Eğer benzer alt kategori bulunamazsa orijinal alt kategoriyi kullan
                matched_sub = subcategory
                print(f"Benzer alt kategori bulunamadı, orijinal alt kategori kullanılıyor: '{subcategory}'")
            
            if matched_sub:
                # Ana kategori-alt kategori çiftini kaydet
                main_category_subcategories[matched_main] = matched_sub
        
        # Kategori değişikliklerini logla
        if main_category != matched_main:
            print(f"Ana kategori eşleştirildi: '{main_category}' -> '{matched_main}'")
        
        if subcategory and subcategory != matched_sub:
            print(f"Alt kategori eşleştirildi: '{subcategory}' -> '{matched_sub}'")
            
        # Eşleştirilmiş kategoriyi ekle
        matched_category = {
            'main_category': matched_main,
            'subcategory': matched_sub
        }
        
        # HER KATEGORI DOĞRUDAN KABUL EDILIR - ilgililik puanı kontrolü YOK
        matched_categories.append(matched_category)
        print(f"Kategori eklendi: '{matched_main} > {matched_sub}'")
        
        # Eklenen kategorinin ilgililik puanını sadece bilgi amaçlı hesapla ve göster
        relevance_score = calculate_category_relevance(matched_category, json_result)
        print(f"'{matched_main} > {matched_sub}' kategorisi için ilgililik puanı (bilgi amaçlı): {relevance_score:.2f}")
    
    # En çok 3 kategori ekle
    max_categories = 3
    
    # En çok ilgili kategorileri seç (sadece 3'ten fazla kategori varsa)
    if len(matched_categories) > max_categories:
        print(f"Çok fazla kategori var ({len(matched_categories)}), sadece ilk {max_categories} tanesi seçilecek")
        # İlk 3 kategoriyi al (ilgililik puanına göre SIRALAMAK YOK)
        matched_categories = matched_categories[:max_categories]
    
    # Eğer hiç kategori önerilmediyse veya eşleşmediyse (ki bu durum artık çok nadir olmalı)
    # otomatik kategori oluştur
    if not matched_categories:
        print("Hiç kategori önerilmedi veya eşleşmedi, otomatik kategori oluşturuluyor...")
        
        # İçeriğin başlığını ve açıklamasını kullanarak otomatik kategori belirle
        title = json_result.get('title', '')
        description = json_result.get('description', '')
        
        # Başlık ve açıklamadan aday kategoriler belirle
        from collections import Counter
        import re
        
        # Yaygın kelimeler ve bağlaçları kaldır (stopwords)
        stopwords = ["ve", "veya", "ile", "için", "bu", "bir", "o", "de", "da", "ki", "ne", "ya", "çok", 
                     "nasıl", "en", "içinde", "üzerinde", "arasında", "olarak", "dolayı", "kadar", "önce", 
                     "sonra", "göre", "her", "the", "and", "or", "for", "in", "on", "at", "with", "from", 
                     "to", "a", "an", "by", "is", "are", "was", "were"]
        
        # Başlık ve açıklama metnini normalleştir
        combined_text = (title + " " + description).lower()
        # Noktalama işaretlerini kaldır
        combined_text = re.sub(r'[^\w\s]', ' ', combined_text)
        # Kelimelere böl
        words = combined_text.split()
        # Yaygın kelimeleri kaldır ve temizle
        filtered_words = [word.strip() for word in words if word.strip() and word.strip() not in stopwords and len(word.strip()) > 2]
        
        # En sık geçen anlamlı kelimeleri bul
        word_counter = Counter(filtered_words)
        common_words = word_counter.most_common(5)
        
        if common_words:
            # En sık geçen kelimeyi ana kategori olarak kullan
            auto_main_category = common_words[0][0].capitalize()
            
            # Eğer ikinci bir kelime varsa, alt kategori olarak kullan
            auto_subcategory = ""
            if len(common_words) > 1:
                auto_subcategory = common_words[1][0].capitalize()
            
            # Ana kategoriyi eşleştir - var olan bir kategoriye benzerlik ara
            is_new_main, matched_main = find_similar_category(auto_main_category, is_main_category=True)
            if not matched_main:
                matched_main = auto_main_category  # Benzer yoksa orijinal ismi kullan
            
            # Alt kategoriyi eşleştir - var olan bir alt kategoriye benzerlik ara
            is_new_sub = False
            matched_sub = ""
            if auto_subcategory:
                is_new_sub, matched_sub = find_similar_category(auto_subcategory, is_main_category=False)
                if not matched_sub:
                    matched_sub = auto_subcategory  # Benzer yoksa orijinal ismi kullan
            
            # Otomatik kategoriyi ekle
            auto_category = {
                'main_category': matched_main,
                'subcategory': matched_sub
            }
            
            matched_categories.append(auto_category)
            print(f"Otomatik kategori oluşturuldu: '{matched_main} > {matched_sub}'")
    
    # Etiket eşleştirme işlemi - tamamen yeni yaklaşım
    matched_tags = []
    
    # json_result'ta etiketler var mı kontrol et
    if 'tags' in json_result and isinstance(json_result['tags'], list) and json_result['tags']:
        # Eğer etiketler listesi varsayılan genel etiketleri ('içerik', 'web', 'analiz', 'sayfa') içeriyorsa,
        # Bu varsayılan etiketleri temizle ve özgün etiketler oluşturmaya çalış
        original_tags = json_result['tags']
        print(f"Orijinal etiketler: {original_tags}")
        
        # Varsayılan genel etiketlerin sayısını kontrol et
        default_tags = ['içerik', 'web', 'analiz', 'sayfa']
        default_tag_count = sum(1 for tag in original_tags if tag.lower() in default_tags)
        
        # Eğer etiketlerin çoğunluğu varsayılanlarsa, içerikten yeni özgün etiketler çıkar
        if default_tag_count > len(original_tags) / 2:
            print(f"Çoğunlukla varsayılan etiketler tespit edildi ({default_tag_count}/{len(original_tags)}), içerikten özgün etiketler çıkarılacak")
            
            # İçerikten özgün etiketler çıkarmak için title ve description kullanılır
            title = json_result.get('title', '')
            description = json_result.get('description', '')
            
            # İçerik bazlı otomatik etiketler oluştur (önceki generate_tags_from_content'ten daha gelişmiş versiyonu)
            auto_tags = extract_meaningful_tags_from_content(title, description)
            
            for tag in auto_tags:
                # Etiketi eşleştir
                is_new, matched_tag = find_similar_tag(tag, existing_tags)
                
                if matched_tag and matched_tag not in matched_tags:
                    matched_tags.append(matched_tag)
                    print(f"İçerikten çıkarılan etiket eklendi: '{matched_tag}'")
        else:
            # Orijinal etiketleri kullan (varsayılan olmayanları)
            for tag in original_tags:
                if not tag or not isinstance(tag, str):
                    continue
                    
                # Eğer varsayılan etiketse atla
                if tag.lower() in default_tags:
                    print(f"Varsayılan etiket '{tag}' atlanıyor")
                    continue
                    
                tag = tag.strip()
                if not tag:
                    continue
                
                # Etiketi eşleştir
                is_new, matched_tag = find_similar_tag(tag, existing_tags)
                
                if matched_tag and matched_tag not in matched_tags:
                    matched_tags.append(matched_tag)
                    
                    if tag != matched_tag:
                        print(f"Etiket eşleştirildi: '{tag}' -> '{matched_tag}'")
    
    # Eğer eşleşen etiket yoksa veya çok azsa, içerikten özgün etiketler oluştur
    if len(matched_tags) < 5:  # En az 5 etiket olmalı
        print(f"Yetersiz etiket sayısı ({len(matched_tags)}), içerikten ek etiketler oluşturuluyor...")
        title = json_result.get('title', '')
        description = json_result.get('description', '')
        
        # İçerik bazlı etiketler oluştur
        auto_tags = extract_meaningful_tags_from_content(title, description)
        
        # Mevcut etiketlere ek olarak
        for tag in auto_tags:
            if len(matched_tags) >= 10:  # En fazla 10 etiket
                break
                
            # Eğer bu etiket zaten listedeyse atla
            if tag.lower() in [t.lower() for t in matched_tags]:
                continue
                
            # Etiketi eşleştir
            is_new, matched_tag = find_similar_tag(tag, existing_tags)
            
            if matched_tag and matched_tag not in matched_tags:
                matched_tags.append(matched_tag)
                print(f"Ek içerik bazlı etiket eklendi: '{matched_tag}'")
    
    # Etiketleri güncelle
    json_result['tags'] = matched_tags
    
    # Kategorileri güncelle
    json_result['categories'] = matched_categories
    
    # Geri uyumluluk için ilk kategoriyi ana ve alt kategoriye kopyala
    if matched_categories:
        json_result['main_category'] = matched_categories[0]['main_category']
        json_result['subcategory'] = matched_categories[0]['subcategory']
    else:
        json_result['main_category'] = ""
        json_result['subcategory'] = ""
    
    print(f"Eşleştirme sonucu: {len(matched_categories)} kategori, {len(matched_tags)} etiket")
    return json_result

def extract_meaningful_tags_from_content(title, description):
    """
    İçerikten anlamlı ve özgün etiketler çıkarır.
    
    Args:
        title (str): İçerik başlığı
        description (str): İçerik açıklaması
        
    Returns:
        list: Anlamlı etiketler listesi
    """
    import re
    from collections import Counter
    
    # Başlık ve açıklamayı birleştir
    combined_text = (title + " " + description).lower()
    
    # Noktalama işaretlerini kaldır
    combined_text = re.sub(r'[^\w\s]', ' ', combined_text)
    
    # Stopwords - genel, yaygın, anlamsız kelimeler
    stopwords = ["ve", "veya", "ile", "için", "bu", "bir", "o", "de", "da", "ki", "ne", "ya", "çok", 
                "nasıl", "en", "içinde", "üzerinde", "arasında", "olarak", "dolayı", "kadar", "önce", 
                "sonra", "göre", "her", "the", "and", "or", "for", "in", "on", "at", "with", "from", 
                "to", "a", "an", "by", "is", "are", "was", "were", "içerik", "web", "analiz", "sayfa",
                "site", "website", "sitesi", "sayfası", "bilgi", "hakkında", "olarak", "için"]
    
    # 1, 2, 3 kelimeli ifadeleri çıkar
    all_phrases = []
    words = combined_text.split()
    
    # 1 kelimeli ifadeler (önce stopwords listesini kontrol et)
    single_words = [word for word in words if word.strip() and word not in stopwords and len(word) > 3]
    all_phrases.extend(single_words)
    
    # 2 kelimeli ifadeler
    for i in range(len(words) - 1):
        if words[i] not in stopwords or words[i+1] not in stopwords:  # En az bir anlamlı kelime içermeli
            phrase = words[i] + " " + words[i+1]
            all_phrases.append(phrase)
    
    # 3 kelimeli ifadeler
    for i in range(len(words) - 2):
        # En az bir anlamlı kelime içermeli
        if words[i] not in stopwords or words[i+1] not in stopwords or words[i+2] not in stopwords:
            phrase = words[i] + " " + words[i+1] + " " + words[i+2]
            all_phrases.append(phrase)
    
    # Çok kısa ifadeleri filtrele
    filtered_phrases = [phrase for phrase in all_phrases if len(phrase) > 3]
    
    # En sık geçen ifadeleri bul
    phrase_counter = Counter(filtered_phrases)
    common_phrases = phrase_counter.most_common(20)  # 20 aday etiket
    
    # Aday etiketleri temizle ve etiket haline getir
    candidate_tags = []
    for phrase, count in common_phrases:
        # Temizle ve ilk harfi büyüt (her kelime için)
        words_in_phrase = phrase.strip().split()
        capitalized_words = [word.capitalize() for word in words_in_phrase]
        clean_phrase = " ".join(capitalized_words)
        
        # Çok kısa veya çok uzun etiketleri filtrele
        if 3 < len(clean_phrase) < 30 and clean_phrase not in candidate_tags:
            candidate_tags.append(clean_phrase)
    
    # En özgün 10 etiketi döndür
    return candidate_tags[:10]

def calculate_category_relevance(category, json_result):
    """
    Kategori ilgililik puanını hesaplar.
    Bu fonksiyon artık sadece bilgi amaçlıdır ve kategoriler her durumda kabul edilir.
    
    Args:
        category (dict): Kategori bilgisi (main_category ve subcategory içerir)
        json_result (dict): JSON sonucu
        
    Returns:
        float: İlgililik puanı (0-1 arası)
    """
    # Başlangıç puanı
    score = 0.0
    
    # Ana kategori ve alt kategoriyi al
    main_category = category.get('main_category', '').lower()
    subcategory = category.get('subcategory', '').lower()
    
    # Başlık ve açıklamayı al
    title = json_result.get('title', '').lower()
    description = json_result.get('description', '').lower()
    
    # Basit ilgililik hesaplaması - sadece bilgi amaçlı
    # Ana kategori eşleşmeleri
    if main_category in title:
        score += 0.3
    elif main_category in description:
        score += 0.2
    
    # Alt kategori eşleşmeleri
    if subcategory and subcategory in title:
        score += 0.3
    elif subcategory and subcategory in description:
        score += 0.2
    
    # Etiketlerde geçiyor mu?
    tags = json_result.get('tags', [])
    for tag in tags:
        if main_category in tag.lower() or (subcategory and subcategory in tag.lower()):
            score += 0.2
            break
    
    # Toplam puan 1.0'ı aşabilir, bu durumda 1.0'a sabitle
    score = min(score, 1.0)
    
    return score

if __name__ == "__main__":
    # Test için
    setup_django()
    
    # Mevcut kategorileri ve etiketleri al
    categories = get_existing_categories()
    tags = get_existing_tags()
    
    print(f"Mevcut ana kategoriler: {categories['main_categories']}")
    print(f"Mevcut alt kategoriler: {categories['subcategories']}")
    print(f"Mevcut etiketler: {tags}")
    
    # Kategori eşleştirme testi
    test_category = "Teknoloji"
    is_new, matched = find_similar_category(test_category)
    print(f"Test kategori: '{test_category}' -> Yeni mi: {is_new}, Eşleşen: '{matched}'")
    
    # Etiket eşleştirme testi
    test_tag = "Python"
    is_new, matched = find_similar_tag(test_tag, tags)
    print(f"Test etiket: '{test_tag}' -> Yeni mi: {is_new}, Eşleşen: '{matched}'")
    
    # JSON eşleştirme testi
    test_json = {
        "title": "Test Başlık",
        "description": "Test Açıklama",
        "main_category": "Teknoloji",
        "subcategory": "Yazılım",
        "tags": ["Python", "Django", "Web"]
    }
    
    matched_json = match_categories_and_tags(test_json, categories, tags)
    print(f"Eşleştirilmiş JSON: {matched_json}") 