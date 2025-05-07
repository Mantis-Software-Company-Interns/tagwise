"""
Category Matcher Module

This module provides functions for matching categories and tags.
"""

import logging
from typing import List, Dict, Optional, Any
import re
from difflib import SequenceMatcher
from .django_setup import setup_django

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def similarity_ratio(a: str, b: str) -> float:
    """
    İki metin arasındaki benzerlik oranını hesaplar.
    
    Args:
        a (str): Birinci metin
        b (str): İkinci metin
        
    Returns:
        float: Benzerlik oranı (0.0 - 1.0)
    """
    # Convert to lowercase for case-insensitive comparison
    a = a.lower().strip()
    b = b.lower().strip()
    
    # Calculate similarity ratio
    return SequenceMatcher(None, a, b).ratio()

def find_similar_category(category_name: str, existing_categories: List[Dict[str, Any]], 
                          is_main_category: bool = True, 
                          accept_new: bool = False,
                          parent_category_id: Optional[int] = None,
                          min_similarity: float = 0.8) -> Optional[Dict[str, Any]]:
    """
    Mevcut kategoriler içinde benzer bir kategori arar.
    
    Args:
        category_name (str): Aranacak kategori adı
        existing_categories (List[Dict]): Mevcut kategoriler listesi
        is_main_category (bool): Ana kategori mi alt kategori mi
        accept_new (bool): Benzer kategori bulunamazsa yeni kategori oluşturulsun mu
        parent_category_id (int, optional): Üst kategori ID'si
        min_similarity (float): Minimum benzerlik oranı (0.0 - 1.0)
        
    Returns:
        Dict: Eşleşen kategori bilgisi veya None
    """
    if not category_name or not existing_categories:
        return None
    
    category_name = category_name.strip()
    
    # Filter categories by type (main or sub)
    filtered_categories = [
        cat for cat in existing_categories 
        if (is_main_category and cat.get('is_main', False)) or 
           (not is_main_category and not cat.get('is_main', True))
    ]
    
    # If we're looking for a sub-category with a parent, filter further
    if not is_main_category and parent_category_id:
        filtered_categories = [
            cat for cat in filtered_categories 
            if cat.get('parent_id') == parent_category_id
        ]
    
    # Look for exact match first
    for category in filtered_categories:
        if category.get('name', '').lower() == category_name.lower():
            logger.info(f"Found exact match for category: {category_name}")
            return category
    
    # Look for similar matches
    best_match = None
    best_score = 0.0
    
    for category in filtered_categories:
        score = similarity_ratio(category.get('name', ''), category_name)
        if score > min_similarity and score > best_score:
            best_match = category
            best_score = score
    
    if best_match:
        logger.info(f"Found similar match for category: {category_name} -> {best_match.get('name')} (score: {best_score:.2f})")
        return best_match
    
    # If we accept new categories, return a new category structure
    if accept_new:
        logger.info(f"Creating new category: {category_name}")
        return {
            'id': None,
            'name': category_name,
            'is_main': is_main_category,
            'parent_id': parent_category_id
        }
    
    return None

def find_similar_tag(tag_name: str, existing_tags: List[Dict[str, Any]], 
                     accept_new: bool = False,
                     min_similarity: float = 0.8) -> Optional[Dict[str, Any]]:
    """
    Mevcut etiketler içinde benzer bir etiket arar.
    
    Args:
        tag_name (str): Aranacak etiket adı
        existing_tags (List[Dict]): Mevcut etiketler listesi
        accept_new (bool): Benzer etiket bulunamazsa yeni etiket oluşturulsun mu
        min_similarity (float): Minimum benzerlik oranı (0.0 - 1.0)
        
    Returns:
        Dict: Eşleşen etiket bilgisi veya None
    """
    if not tag_name or not existing_tags:
        return None
    
    tag_name = tag_name.strip()
    
    # Look for exact match first
    for tag in existing_tags:
        if tag.get('name', '').lower() == tag_name.lower():
            logger.info(f"Found exact match for tag: {tag_name}")
            return tag
    
    # Look for similar matches
    best_match = None
    best_score = 0.0
    
    for tag in existing_tags:
        score = similarity_ratio(tag.get('name', ''), tag_name)
        if score > min_similarity and score > best_score:
            best_match = tag
            best_score = score
    
    if best_match:
        logger.info(f"Found similar match for tag: {tag_name} -> {best_match.get('name')} (score: {best_score:.2f})")
        return best_match
    
    # If we accept new tags, return a new tag structure
    if accept_new:
        logger.info(f"Creating new tag: {tag_name}")
        return {
            'id': None,
            'name': tag_name
        }
    
    return None

def get_existing_categories(user=None):
    """
    Veritabanındaki mevcut kategorileri getirir.
    
    Bu fonksiyon Django modelleri kullanarak veritabanından kategori listesini çeker.
    
    Args:
        user: Kullanıcı objesi, eğer belirtilirse sadece bu kullanıcıya ait kategoriler getirilir
    
    Returns:
        List[Dict]: Kategori listesi
    """
    try:
        # Import Django models
        from django.apps import apps
        Category = apps.get_model('tagwiseapp', 'Category')
        
        # Get categories based on user filter
        query = Category.objects.all()
        if user:
            # Kullanıcıya özel kategorileri ve genel (user=None) kategorileri getir
            query = query.filter(user__in=[user, None])
        
        # Get all categories
        categories = []
        for cat in query:
            categories.append({
                'id': cat.id,
                'name': cat.name,
                'is_main': cat.parent_id is None,
                'parent_id': cat.parent_id,
                'user_id': cat.user_id
            })
        
        return categories
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return []

def get_existing_tags(user=None):
    """
    Veritabanındaki mevcut etiketleri getirir.
    
    Bu fonksiyon Django modelleri kullanarak veritabanından etiket listesini çeker.
    
    Args:
        user: Kullanıcı objesi, eğer belirtilirse sadece bu kullanıcıya ait etiketler getirilir
    
    Returns:
        List[Dict]: Etiket listesi
    """
    try:
        # Import Django models
        from django.apps import apps
        Tag = apps.get_model('tagwiseapp', 'Tag')
        
        # Get tags based on user filter
        query = Tag.objects.all()
        if user:
            # Kullanıcıya özel etiketleri ve genel (user=None) etiketleri getir
            query = query.filter(user__in=[user, None])
        
        # Get all tags
        tags = []
        for tag in query:
            tags.append({
                'id': tag.id,
                'name': tag.name,
                'user_id': tag.user_id
            })
        
        return tags
    except Exception as e:
        logger.error(f"Error fetching tags: {str(e)}")
        return []

def match_categories_and_tags(categories_data, tags_data, existing_categories=None, existing_tags=None):
    """
    Kategorileri ve etiketleri veritabanındaki mevcut verilerle eşleştirir.
    
    Args:
        categories_data (mixed): Kategori listesi veya kategori içeren JSON verisi
        tags_data (mixed): Etiket listesi veya etiket içeren JSON verisi
        existing_categories (List, optional): Mevcut kategorilerin listesi
        existing_tags (List, optional): Mevcut etiketlerin listesi
        
    Returns:
        tuple or dict: Eşleştirilmiş kategoriler ve etiketler
    """
    # Get existing categories and tags if not provided
    if existing_categories is None:
        existing_categories = get_existing_categories()
    
    if existing_tags is None:
        existing_tags = get_existing_tags()
    
    # Data can be a JSON object or list
    is_json_object = False
    
    # Check if categories_data is a JSON object
    if isinstance(categories_data, dict):
        is_json_object = True
        categories = categories_data.get('categories', [])
        # Backward compatibility for older format
        if not categories and 'main_category' in categories_data:
            main_cat = categories_data.get('main_category')
            sub_cat = categories_data.get('subcategory', '')
            categories = [{'main': main_cat, 'sub': sub_cat}]
    else:
        # Assume it's already a list of categories
        categories = categories_data
    
    # Check if tags_data is a JSON object
    if isinstance(tags_data, dict):
        tags = tags_data.get('tags', [])
    elif is_json_object:
        # If the first argument was a JSON object, extract tags from it
        tags = categories_data.get('tags', [])
    else:
        # Assume it's already a list of tags
        tags = tags_data
    
    # Convert "main_category" format to "main" format if needed
    processed_categories = []
    for cat in categories:
        if isinstance(cat, dict):
            if 'main' in cat and 'sub' in cat:
                processed_categories.append(cat)
            elif 'main_category' in cat:
                processed_categories.append({
                    'main': cat.get('main_category', ''),
                    'sub': cat.get('subcategory', '')
                })
    
    # Match categories
    matched_categories = []
    for category in processed_categories:
        if isinstance(category, dict) and 'main' in category and 'sub' in category:
            main_cat = category.get('main', '')
            sub_cat = category.get('sub', '')
            
            # Match main category
            matched_main = find_similar_category(main_cat, existing_categories, is_main_category=True, accept_new=True)
            
            # Match sub category
            matched_sub = find_similar_category(sub_cat, existing_categories, is_main_category=False, 
                                               accept_new=True, parent_category_id=matched_main.get('id') if matched_main else None)
            
            matched_categories.append({
                'main': matched_main.get('name') if matched_main else main_cat,
                'sub': matched_sub.get('name') if matched_sub else sub_cat,
                'main_id': matched_main.get('id') if matched_main else None,
                'sub_id': matched_sub.get('id') if matched_sub else None
            })
    
    # Match tags
    matched_tags = []
    for tag_item in tags:
        # Handle different tag formats
        if isinstance(tag_item, dict) and 'name' in tag_item:
            tag_name = tag_item.get('name')
        elif isinstance(tag_item, str):
            tag_name = tag_item
        else:
            continue
            
        if tag_name:
            matched_tag = find_similar_tag(tag_name, existing_tags, accept_new=True)
            if matched_tag:
                matched_tags.append({
                    'name': matched_tag.get('name'),
                    'id': matched_tag.get('id')
                })
    
    # If input was a JSON object, update it and return
    if is_json_object:
        result = categories_data.copy()
        result['categories'] = matched_categories
        result['tags'] = matched_tags
        return result
    
    # Otherwise return tuple of matched items
    return matched_categories, matched_tags

if __name__ == "__main__":
    # Test için
    setup_django()
    
    # Mevcut kategorileri ve etiketleri al
    categories = get_existing_categories()
    tags = get_existing_tags()
    
    print(f"Mevcut ana kategoriler: {categories}")
    print(f"Mevcut etiketler: {tags}")
    
    # Kategori eşleştirme testi
    test_category = "Teknoloji"
    matched = find_similar_category(test_category, categories, is_main_category=True)
    print(f"Test kategori: '{test_category}' -> Eşleşen: {matched}")
    
    # Etiket eşleştirme testi
    test_tag = "Python"
    matched = find_similar_tag(test_tag, tags)
    print(f"Test etiket: '{test_tag}' -> Eşleşen: {matched}")
    
    # JSON eşleştirme testi
    test_json = {
        "title": "Test Başlık",
        "description": "Test Açıklama",
        "main_category": "Teknoloji",
        "subcategory": "Yazılım",
        "tags": ["Python", "Django", "Web"]
    }
    
    matched_categories, matched_tags = match_categories_and_tags(test_json, test_json)
    print(f"Eşleştirilmiş kategoriler: {matched_categories}")
    print(f"Eşleştirilmiş etiketler: {matched_tags}") 