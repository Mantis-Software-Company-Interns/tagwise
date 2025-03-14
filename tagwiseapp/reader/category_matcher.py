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
    Veritabanında benzer bir kategori adı arar ve bulursa döndürür.
    Bulamazsa ve accept_new=True ise orijinal kategori adını döndürür.
    
    Args:
        category_name (str): Aranacak kategori adı
        is_main_category (bool): Ana kategori mi yoksa alt kategori mi
        accept_new (bool): Eşleşme bulunamazsa yeni kategori kabul edilsin mi
        
    Returns:
        bool: Yeni kategori mi (True) yoksa mevcut kategori mi
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