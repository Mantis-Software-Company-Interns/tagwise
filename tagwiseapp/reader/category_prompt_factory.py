"""
Category Prompt Factory Module

This module provides functions for generating category prompts for LLMs.
"""

import json
from typing import List, Dict, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CategoryPromptFactory:
    """
    Factory class for creating category prompts for LLMs.
    """
    
    @staticmethod
    def create_category_prompt(content: str, url: str, 
                               existing_title: Optional[str] = None,
                               existing_description: Optional[str] = None,
                               existing_categories: Optional[List[Dict[str, Any]]] = None,
                               existing_tags: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        İçerik kategorilendirme için LLM promptu oluşturur.
        
        Args:
            content (str): İçerik metni
            url (str): URL
            existing_title (str, optional): Mevcut başlık
            existing_description (str, optional): Mevcut açıklama
            existing_categories (List[Dict], optional): Mevcut kategoriler
            existing_tags (List[Dict], optional): Mevcut etiketler
            
        Returns:
            str: LLM promptu
        """
        # Truncate content if too long
        MAX_CONTENT_LENGTH = 15000
        if len(content) > MAX_CONTENT_LENGTH:
            logger.info(f"Content too long ({len(content)} chars), truncating to {MAX_CONTENT_LENGTH}")
            content = content[:MAX_CONTENT_LENGTH] + "..."
        
        # Format existing categories for the prompt
        category_examples = ""
        if existing_categories:
            # Get main categories
            main_categories = [cat for cat in existing_categories if cat.get('is_main', False)]
            
            # Format category examples
            if main_categories:
                category_examples = "Mevcut kategori örnekleri:\n"
                for main_cat in main_categories[:10]:  # Limit to 10 examples
                    main_name = main_cat.get('name', '')
                    # Get subcategories for this main category
                    sub_cats = [
                        cat.get('name', '') for cat in existing_categories 
                        if cat.get('parent_id') == main_cat.get('id') and not cat.get('is_main', True)
                    ]
                    
                    if sub_cats:
                        category_examples += f"- {main_name}: {', '.join(sub_cats[:5])}\n"
                    else:
                        category_examples += f"- {main_name}\n"
        
        # Format existing tags for the prompt
        tag_examples = ""
        if existing_tags:
            tag_examples = "Mevcut etiket örnekleri:\n"
            tag_list = [tag.get('name', '') for tag in existing_tags[:20]]  # Limit to 20 examples
            tag_examples += ", ".join(tag_list)
        
        # Build the prompt
        prompt = f"""
        Bu bir web sayfası içeriğidir. Lütfen bu içeriği analiz edip kategorilere ayır ve etiketle.
        
        URL: {url}
        
        {"Mevcut başlık: " + existing_title if existing_title else ""}
        {"Mevcut açıklama: " + existing_description if existing_description else ""}
        
        {category_examples}
        
        {tag_examples}
        
        İçerik:
        {content}
        
        Lütfen aşağıdaki JSON formatında bir yanıt oluştur:
        ```json
        {{
            "title": "Sayfanın başlığı",
            "description": "Sayfanın kısa açıklaması",
            "categories": [
                {{ "main": "Ana kategori adı", "sub": "Alt kategori adı" }}
            ],
            "tags": ["etiket1", "etiket2", "etiket3"]
        }}
        ```
        
        Kategoriler için ana ve alt kategori yapısını kullan. Her kategori için main ve sub alanı olmalı.
        Etiketler için sayfayı en iyi tanımlayan 3-7 arasında etiket belirle.
        Yanıt yalnızca JSON formatında olmalıdır, başka açıklama ekleme.
        """
        
        logger.info(f"Created category prompt for URL: {url}")
        return prompt
    
    @staticmethod
    def create_screenshot_category_prompt(url: str, 
                                        existing_title: Optional[str] = None,
                                        existing_description: Optional[str] = None,
                                        existing_categories: Optional[List[Dict[str, Any]]] = None,
                                        existing_tags: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Ekran görüntüsü kategorilendirme için LLM promptu oluşturur.
        
        Args:
            url (str): URL
            existing_title (str, optional): Mevcut başlık
            existing_description (str, optional): Mevcut açıklama
            existing_categories (List[Dict], optional): Mevcut kategoriler
            existing_tags (List[Dict], optional): Mevcut etiketler
            
        Returns:
            str: LLM promptu
        """
        # Format existing categories for the prompt
        category_examples = ""
        if existing_categories:
            # Get main categories
            main_categories = [cat for cat in existing_categories if cat.get('is_main', False)]
            
            # Format category examples
            if main_categories:
                category_examples = "Mevcut kategori örnekleri:\n"
                for main_cat in main_categories[:10]:  # Limit to 10 examples
                    main_name = main_cat.get('name', '')
                    # Get subcategories for this main category
                    sub_cats = [
                        cat.get('name', '') for cat in existing_categories 
                        if cat.get('parent_id') == main_cat.get('id') and not cat.get('is_main', True)
                    ]
                    
                    if sub_cats:
                        category_examples += f"- {main_name}: {', '.join(sub_cats[:5])}\n"
                    else:
                        category_examples += f"- {main_name}\n"
        
        # Format existing tags for the prompt
        tag_examples = ""
        if existing_tags:
            tag_examples = "Mevcut etiket örnekleri:\n"
            tag_list = [tag.get('name', '') for tag in existing_tags[:20]]  # Limit to 20 examples
            tag_examples += ", ".join(tag_list)
        
        # Build the prompt
        prompt = f"""
        Bu bir web sayfasının ekran görüntüsüdür. Lütfen bu görüntüyü analiz edip kategorilere ayır ve etiketle.
        
        URL: {url}
        
        {"Mevcut başlık: " + existing_title if existing_title else ""}
        {"Mevcut açıklama: " + existing_description if existing_description else ""}
        
        {category_examples}
        
        {tag_examples}
        
        Lütfen aşağıdaki JSON formatında bir yanıt oluştur:
        ```json
        {{
            "title": "Sayfanın başlığı",
            "description": "Sayfanın kısa açıklaması",
            "categories": [
                {{ "main": "Ana kategori adı", "sub": "Alt kategori adı" }}
            ],
            "tags": ["etiket1", "etiket2", "etiket3"]
        }}
        ```
        
        Kategoriler için ana ve alt kategori yapısını kullan. Her kategori için main ve sub alanı olmalı.
        Etiketler için sayfayı en iyi tanımlayan 3-7 arasında etiket belirle.
        Yanıt yalnızca JSON formatında olmalıdır, başka açıklama ekleme.
        
        Görüntüdeki metinleri ve görselleri dikkate alarak en doğru kategorilemeyi yap.
        """
        
        logger.info(f"Created screenshot category prompt for URL: {url}")
        return prompt
    
    @staticmethod
    def create_youtube_prompt(url: str, 
                              title: Optional[str] = None,
                              description: Optional[str] = None,
                              channel_name: Optional[str] = None,
                              transcript: Optional[str] = None,
                              keywords: Optional[List[str]] = None,
                              existing_categories: Optional[List[Dict[str, Any]]] = None,
                              existing_tags: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        YouTube video kategorilendirme için LLM promptu oluşturur.
        
        Args:
            url (str): YouTube video URL'si
            title (str, optional): Video başlığı
            description (str, optional): Video açıklaması
            channel_name (str, optional): Kanal adı
            transcript (str, optional): Video altyazısı/transkripsiyonu
            keywords (List[str], optional): Video anahtar kelimeleri
            existing_categories (List[Dict], optional): Mevcut kategoriler
            existing_tags (List[Dict], optional): Mevcut etiketler
            
        Returns:
            str: LLM promptu
        """
        logger.info(f"Created YouTube category prompt for URL: {url}")
        
        # Format kategori listesini (main ve sub olarak)
        categories_list = []
        if existing_categories:
            main_categories = [cat.get('name') for cat in existing_categories if cat.get('is_main', False)]
            subcategories = [cat.get('name') for cat in existing_categories if not cat.get('is_main', False)]
            
            categories_list.append("Mevcut kategori listesi:")
            for main_cat in main_categories:
                sub_cats = [sub for sub in subcategories if any(
                    s.get('parent_id') == m.get('id') 
                    for m in existing_categories if m.get('name') == main_cat and m.get('is_main', False)
                    for s in existing_categories if s.get('name') == sub and not s.get('is_main', False)
                )]
                
                if sub_cats:
                    categories_list.append(f"- {main_cat} > {', '.join(sub_cats)}")
            
        # Format etiket listesini
        tags_list = []
        if existing_tags:
            tags_list = [tag.get('name') for tag in existing_tags]
            
        
        # Prompt oluştur
        prompt_parts = []
        
        prompt_parts.append(f"Lütfen aşağıdaki YouTube videosunu analiz et ve içeriğine uygun kategoriler ve etiketler belirle:")
        prompt_parts.append(f"Video URL: {url}")
        
        if title:
            prompt_parts.append(f"Video Başlığı: {title}")
        
        if channel_name:
            prompt_parts.append(f"Kanal Adı: {channel_name}")
            
        if description:
            prompt_parts.append(f"Video Açıklaması: {description}")
            
        if keywords and len(keywords) > 0:
            prompt_parts.append(f"Video Etiketleri: {', '.join(keywords)}")
            
        if transcript:
            # Transcript'i kısalt (çok uzun olabilir)
            if len(transcript) > 2000:
                shortened_transcript = transcript[:2000] + "... (kısaltıldı)"
            else:
                shortened_transcript = transcript
                
            prompt_parts.append(f"Video Altyazısı/Transkripsiyonu: {shortened_transcript}")

        # Örnek kategoriler ekle (yardımcı olmak için)
        prompt_parts.append("\nPopüler kategorilere örnekler:")
        prompt_parts.append("- Eğlence > Dizi/Film")
        prompt_parts.append("- Eğlence > Müzik")
        prompt_parts.append("- Eğlence > Oyun")
        prompt_parts.append("- Eğitim > Programlama")
        prompt_parts.append("- Eğitim > Bilim")
        prompt_parts.append("- Yaşam > Seyahat")
        prompt_parts.append("- Yaşam > Yemek")
        prompt_parts.append("- Spor > Futbol")
        prompt_parts.append("- Sağlık > Fitness")
        
        # Kategori eşleştirme talimatı ekle
        if categories_list:
            prompt_parts.append("\n".join(categories_list))
        
        # Video içeriğine uygun en az 1, en fazla 3 kategori belirle
        prompt_parts.append("\nÖnemli: Lütfen bu video içeriğine uygun en az 1, en fazla 3 kategori belirle.")
        prompt_parts.append("Her kategori bir ana kategori (main) ve bir alt kategori (sub) içermeli.")
        
        # Etiket belirle
        prompt_parts.append("\nAyrıca video içeriğine uygun en az 5, en fazla 10 etiket belirle.")
        
        # Tüm bilgileri JSON formatında döndür
        prompt_parts.append("\nYanıtını şu formatta ver:")
        prompt_parts.append('''
{
  "title": "Video başlığı",
  "description": "Video açıklaması",
  "categories": [
    {"main": "Ana Kategori 1", "sub": "Alt Kategori 1"},
    {"main": "Ana Kategori 2", "sub": "Alt Kategori 2"}
  ],
  "tags": ["etiket1", "etiket2", "etiket3", "etiket4", "etiket5"]
}
        ''')
        
        return "\n\n".join(prompt_parts) 