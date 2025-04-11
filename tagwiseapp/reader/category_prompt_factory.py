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