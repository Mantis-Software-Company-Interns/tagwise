"""
Content Analyzer Module

This module provides functions for analyzing content with LangChain.
Replaces the gemini_analyzer.py with a provider-agnostic implementation.
"""

import json
import base64
import logging
from typing import Dict, Optional, Any, List, Union
import re
import os

# Local imports
from .llm_factory import LLMChain
from .utils import correct_json_format, ensure_correct_json_structure
from .category_matcher import (
    match_categories_and_tags, 
    get_existing_categories, 
    get_existing_tags,
    find_similar_category,
    find_similar_tag
)
from .html_utils import clean_html_content, MAX_CONTENT_LENGTH
from .prompts import TEXT_SYSTEM_INSTRUCTION, IMAGE_SYSTEM_INSTRUCTION
from .category_prompt_factory import CategoryPromptFactory
from .llm_factory import LLMFactory
from .settings import get_model_config
from .schemas import ContentAnalysisModel, get_content_analysis_json_schema

# Import LangChain message types for invoking LLMs
from langchain_core.messages import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def configure_llm(api_key=None, provider=None):
    """
    Configure LLM settings for content analysis.
    
    Args:
        api_key (str, optional): API key for the LLM provider.
        provider (str, optional): The LLM provider name (gemini, openai, anthropic)
        
    Returns:
        bool: True if configuration is successful, False otherwise
    """
    try:
        # Set API key based on provider or default
        if provider is None:
            provider = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
        
        if api_key:
            if provider == "gemini":
                os.environ["GEMINI_API_KEY"] = api_key
                logger.info("Gemini API anahtarı ayarlandı.")
            elif provider == "openai":
                os.environ["OPENAI_API_KEY"] = api_key
                logger.info("OpenAI API anahtarı ayarlandı.")
            elif provider == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = api_key
                logger.info("Anthropic API anahtarı ayarlandı.")
            else:
                logger.warning(f"Bilinmeyen provider: {provider}, varsayılan olarak Gemini kullanılıyor.")
                os.environ["GEMINI_API_KEY"] = api_key
                logger.info("Gemini API anahtarı ayarlandı.")
        
        # Test the configuration by creating an LLM instance
        LLMFactory.create_llm(provider=provider)
        logger.info(f"LLM yapılandırması başarılı. Provider: {provider}")
        return True
        
    except Exception as e:
        logger.error(f"LLM yapılandırılırken hata oluştu: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def generate_summary_from_screenshot(screenshot_base64: str, url: str) -> str:
    """
    Ekran görüntüsünden içerik özeti oluşturur.
    
    Args:
        screenshot_base64 (str): Base64 kodlanmış ekran görüntüsü
        url (str): Analiz edilen URL
        
    Returns:
        str: İçerik özeti
    """
    logger.info("Ekran görüntüsünden özet oluşturuluyor...")
    
    try:
        # System instruction
        system_instruction = """
        Sen bir web sayfası analisti olarak görev yapıyorsun. 
        Verilen görüntüleri analiz ederek kapsamlı özetler oluşturursun. 
        Özetlerin, sayfanın ana konusunu, amacını, hedef kitlesini ve önemli bilgileri içermelidir.
        Özetini oluştururken kelime sayısı sınırlaması olmadan, sayfayı en iyi şekilde anlatacak kapsamlı bir özet yaz.
        """
        
        # Initialize LLM chain
        chain = LLMChain(system_prompt=system_instruction, model_type="flash")
        
        # User content
        user_content = f"""
        Bu bir web sayfasının ekran görüntüsüdür. Lütfen bu sayfanın içeriğini analiz edip kapsamlı bir özet oluştur.
        Özet için herhangi bir kelime sınırlaması yok, sayfayı en iyi şekilde anlatan detaylı bir özet yaz.
        
        URL: {url}
        """
        
        # Process the image
        image_data = chain.process_image(screenshot_base64)
        
        # Run chain
        summary = chain.run(user_content, image_data=image_data)
        
        logger.info(f"Ekran görüntüsünden özet oluşturuldu: {summary[:100]}...")
        return summary
        
    except Exception as e:
        logger.error(f"Ekran görüntüsünden özet oluşturulurken hata: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Hata durumunda boş özet
        return f"URL: {url} için ekran görüntüsünden özet oluşturulamadı."


def generate_summary_from_content(content: str, url: str) -> str:
    """
    HTML içeriğinden özet oluşturur.
    
    Args:
        content (str): HTML içeriği
        url (str): Analiz edilen URL
        
    Returns:
        str: İçerik özeti
    """
    logger.info("HTML içeriğinden özet oluşturuluyor...")
    
    try:
        # System instruction
        system_instruction = """
        Sen bir web sayfası analisti olarak görev yapıyorsun. 
        Verilen HTML içeriğini analiz ederek kapsamlı özetler oluşturursun. 
        Özetlerin, sayfanın ana konusunu, amacını, hedef kitlesini ve önemli bilgileri içermelidir.
        Özetini oluştururken kelime sayısı sınırlaması olmadan, sayfayı en iyi şekilde anlatacak kapsamlı bir özet yaz.
        """
        
        # Initialize LLM chain
        chain = LLMChain(system_prompt=system_instruction)
        
        # User content
        user_content = f"""
        Bu bir web sayfasının içeriğidir. Lütfen bu içeriği analiz edip kapsamlı bir özet oluştur.
        Özet için herhangi bir kelime sınırlaması yok, sayfayı en iyi şekilde anlatan detaylı bir özet yaz.
        
        URL: {url}
        
        İçerik:
        {content}
        """
        
        # Run chain
        summary = chain.run(user_content)
        
        logger.info(f"HTML içeriğinden özet oluşturuldu: {summary[:100]}...")
        return summary
        
    except Exception as e:
        logger.error(f"HTML içeriğinden özet oluşturulurken hata: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Hata durumunda boş özet
        return f"URL: {url} için HTML içeriğinden özet oluşturulamadı."


def categorize_content(content: str, url: str, existing_title: Optional[str] = None, existing_description: Optional[str] = None, use_structured_output: bool = True) -> Dict:
    """
    HTML içeriğini kategorize eder ve etiketler.

    Args:
        content (str): HTML içeriği
        url (str): URL adresi
        existing_title (Optional[str], optional): Mevcut başlık. Defaults to None.
        existing_description (Optional[str], optional): Mevcut açıklama. Defaults to None.
        use_structured_output (bool, optional): Whether to use structured output. Defaults to True.

    Returns:
        Dict: Kategorize edilmiş sonuçlar
    """
    try:
        print(f"Kategorilendirme başlatılıyor... URL: {url}")
        
        # HTML içerikteki HTML etiketlerini temizle
        clean_text = clean_html_content(content)
        
        # Temizlenmiş metni kısalt
        if len(clean_text) > MAX_CONTENT_LENGTH:
            clean_text = clean_text[:MAX_CONTENT_LENGTH]
        
        if existing_title:
            # Kullanıcı için daha anlamlı bir başlık kullan
            print(f"Var olan başlık kullanılıyor: {existing_title}")
        
        if existing_description:
            # Kullanıcı için daha anlamlı bir açıklama kullan
            print(f"Var olan açıklama kullanılıyor: {existing_description}")
        
        # LLM ayarlarını yükle
        settings = get_model_config()
        
        # Kategori verilerini yükle
        existing_categories = get_existing_categories()
        tags = get_existing_tags()
        
        # Kategori ve etiketler için LLM prompt'u hazırla
        prompt = CategoryPromptFactory.create_category_prompt(
            content=clean_text,
            url=url,
            existing_title=existing_title,
            existing_description=existing_description,
            existing_categories=existing_categories,
            existing_tags=tags
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"Sending categorization request to LLM for URL: {url}")
        
        try:
            if use_structured_output:
                # Use structured output with JSON schema
                output_schema = get_content_analysis_json_schema()
                
                # Create LLMChain with structured output
                llm_chain = LLMChain(
                    system_prompt=TEXT_SYSTEM_INSTRUCTION,
                    output_schema=output_schema,
                    model_type="text"
                )
                
                # Run the chain
                structured_result = llm_chain.run(prompt)
                
                # Check if we got a structured output or a string
                if isinstance(structured_result, dict):
                    logger.info("Successfully received structured output")
                    # Add URL if not present
                    if 'url' not in structured_result:
                        structured_result['url'] = url
                    
                    # Structured output already has the right format,
                    # but we still need to match categories and tags with existing ones
                    result = structured_result
                else:
                    logger.warning("Structured output failed, falling back to text parsing")
                    # Fallback to text parsing
                    corrected_json_text = correct_json_format(str(structured_result))
                    json_result = json.loads(corrected_json_text)
                    result = ensure_correct_json_structure(json_result, url, existing_title, existing_description)
            else:
                # Use traditional approach
                llm = LLMFactory.create_llm(
                    provider=settings.get('provider', 'gemini'),
                    model_name=settings.get('model_name', 'gemini-2.0-flash'),
                    temperature=0.2
                )
                
                # Invoke LLM
                response = llm.invoke([HumanMessage(content=prompt)])
                
                # Extract content from response
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
                    
                logger.info(f"Received response from LLM, length: {len(response_text)}")
                
                # LLM yanıtını JSON formatına çevirir
                corrected_json_text = correct_json_format(response_text)
                
                # JSON metnini dict'e dönüştür
                try:
                    json_result = json.loads(corrected_json_text)
                    logger.info("Successfully parsed JSON from LLM response")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {str(e)}")
                    # Boş bir dict ile devam et
                    json_result = {}
            
            # Kategori eşleştirme için veritabanındaki kategorilerle karşılaştır
            if result.get('categories'):
                matched_categories = []
                for category in result.get('categories', []):
                    main_category = category.get('main', '')
                    sub_category = category.get('sub', '')
                    
                    # Ana kategoriyi eşleştir
                    matched_main = find_similar_category(main_category, existing_categories, is_main_category=True, accept_new=True)
                    
                    # Alt kategoriyi eşleştir
                    matched_sub = find_similar_category(sub_category, existing_categories, is_main_category=False, accept_new=True, parent_category_id=matched_main.get('id') if matched_main else None)
                    
                    matched_categories.append({
                        'main': matched_main.get('name') if matched_main else main_category,
                        'sub': matched_sub.get('name') if matched_sub else sub_category,
                        'main_id': matched_main.get('id') if matched_main else None,
                        'sub_id': matched_sub.get('id') if matched_sub else None
                    })
                
                # Eşleştirilmiş kategorileri sonuca ekle
                result['categories'] = matched_categories
            
            # Etiketleri eşleştir
            if result.get('tags'):
                matched_tags = []
                existing_tags = get_existing_tags()
                
                for tag_item in result.get('tags', []):
                    # Etiket formatını kontrol et - string veya dict olabilir
                    if isinstance(tag_item, dict) and 'name' in tag_item:
                        tag_name = tag_item.get('name')
                    elif isinstance(tag_item, str):
                        tag_name = tag_item
                    else:
                        continue  # Geçersiz format
                    
                    if tag_name:
                        matched_tag = find_similar_tag(tag_name, existing_tags, accept_new=True)
                        if matched_tag:
                            matched_tags.append({
                                'name': matched_tag.get('name'),
                                'id': matched_tag.get('id')
                            })
                
                # Eşleştirilmiş etiketleri sonuca ekle
                result['tags'] = matched_tags
            
            return result
        except Exception as e:
            logger.error(f"Error during categorization: {str(e)}")
            # Hata durumunda boş bir sonuç döndür
            default_result = {
                'url': url,
                'title': existing_title or '',
                'description': existing_description or '',
                'categories': [{
                    'main': 'Genel',
                    'sub': 'Diğer',
                    'main_id': None,
                    'sub_id': None
                }],
                'tags': [{
                    'name': 'genel',
                    'id': None
                }]
            }
            return default_result
            
    except Exception as e:
        print(f"İçerik kategorilendirme hatası: {str(e)}")
        # Hata durumunda boş bir sonuç döndür
        default_result = {
            'url': url,
            'title': existing_title or '',
            'description': existing_description or '',
            'categories': [{
                'main': 'Genel',
                'sub': 'Diğer',
                'main_id': None,
                'sub_id': None
            }],
            'tags': [{
                'name': 'genel',
                'id': None
            }]
        }
        return default_result


def analyze_screenshot(screenshot_base64: str, url: str, existing_title: Optional[str] = None, existing_description: Optional[str] = None, use_structured_output: bool = True) -> Dict:
    """
    Ekran görüntüsünü analiz eder ve kategorize eder.

    Args:
        screenshot_base64 (str): Base64 formatında ekran görüntüsü
        url (str): URL adresi
        existing_title (Optional[str], optional): Mevcut başlık. Defaults to None.
        existing_description (Optional[str], optional): Mevcut açıklama. Defaults to None.
        use_structured_output (bool, optional): Whether to use structured output. Defaults to True.

    Returns:
        Dict: Analiz sonuçları
    """
    try:
        print(f"Ekran görüntüsü analizi başlatılıyor... URL: {url}")
        
        # LLM ayarlarını yükle
        settings = get_model_config()
        
        # Kategori verilerini yükle
        existing_categories = get_existing_categories()
        tags = get_existing_tags()
        
        # Multimodal LLM için prompt hazırla
        prompt = CategoryPromptFactory.create_screenshot_category_prompt(
            url=url,
            existing_title=existing_title,
            existing_description=existing_description,
            existing_categories=existing_categories,
            existing_tags=tags
        )
        
        # İstek gönder ve cevabı al
        logger = logging.getLogger(__name__)
        logger.info(f"Sending screenshot analysis request to LLM for URL: {url}")
        
        try:
            # Vision models typically don't support structured output as well,
            # but we can try with JSON schema
            output_schema = get_content_analysis_json_schema() if use_structured_output else None
            
            # Create LLM chain with optional structured output
            llm_chain = LLMChain(
                system_prompt=IMAGE_SYSTEM_INSTRUCTION, 
                model_type="vision",
                output_schema=output_schema if use_structured_output else None
            )
            
            # Process the image
            image_data = llm_chain.process_image(screenshot_base64)
            
            # Run chain
            response = llm_chain.run(prompt, image_data=image_data)
            
            # Handle the response based on its type
            if use_structured_output and isinstance(response, dict):
                logger.info("Successfully received structured output from vision model")
                # Add URL if not present
                if 'url' not in response:
                    response['url'] = url
                json_result = response
            else:
                # Need to parse as text
                logger.info(f"Received text response from LLM, length: {len(str(response))}")
                
                # LLM yanıtını JSON formatına çevirir
                corrected_json_text = correct_json_format(str(response))
                
                # JSON metnini dict'e dönüştür
                try:
                    json_result = json.loads(corrected_json_text)
                    logger.info("Successfully parsed JSON from LLM response")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {str(e)}")
                    # Boş bir dict ile devam et
                    json_result = {}
            
            # JSON yapısının doğru olduğundan emin ol
            result = ensure_correct_json_structure(json_result, url, existing_title, existing_description)
            
            # Kategori eşleştirme için veritabanındaki kategorilerle karşılaştır
            if result.get('categories'):
                matched_categories = []
                for category in result.get('categories', []):
                    main_category = category.get('main', '')
                    sub_category = category.get('sub', '')
                    
                    # Ana kategoriyi eşleştir
                    matched_main = find_similar_category(main_category, existing_categories, is_main_category=True, accept_new=True)
                    
                    # Alt kategoriyi eşleştir
                    matched_sub = find_similar_category(sub_category, existing_categories, is_main_category=False, accept_new=True, parent_category_id=matched_main.get('id') if matched_main else None)
                    
                    matched_categories.append({
                        'main': matched_main.get('name') if matched_main else main_category,
                        'sub': matched_sub.get('name') if matched_sub else sub_category,
                        'main_id': matched_main.get('id') if matched_main else None,
                        'sub_id': matched_sub.get('id') if matched_sub else None
                    })
                
                # Eşleştirilmiş kategorileri sonuca ekle
                result['categories'] = matched_categories
            
            # Etiketleri eşleştir
            if result.get('tags'):
                matched_tags = []
                existing_tags = get_existing_tags()
                
                for tag_item in result.get('tags', []):
                    # Etiket formatını kontrol et - string veya dict olabilir
                    if isinstance(tag_item, dict) and 'name' in tag_item:
                        tag_name = tag_item.get('name')
                    elif isinstance(tag_item, str):
                        tag_name = tag_item
                    else:
                        continue  # Geçersiz format
                    
                    if tag_name:
                        matched_tag = find_similar_tag(tag_name, existing_tags, accept_new=True)
                        if matched_tag:
                            matched_tags.append({
                                'name': matched_tag.get('name'),
                                'id': matched_tag.get('id')
                            })
                
                # Eşleştirilmiş etiketleri sonuca ekle
                result['tags'] = matched_tags
            
            # Başlık ve açıklama yoksa, OpenAI'a sor
            if (not result.get('title') or not result.get('description')):
                print("Başlık veya açıklama bulunamadı, OpenAI'dan talep ediliyor...")
                
                try:
                    # Başlık ve açıklama için OpenAI
                    summary = generate_summary_from_screenshot(screenshot_base64, url)
                    
                    # Sonuçları birleştir
                    if not result.get('title') and "title:" in summary.lower():
                        title_match = re.search(r'title:(.*?)(?:description:|$)', summary, re.IGNORECASE | re.DOTALL)
                        if title_match:
                            result['title'] = title_match.group(1).strip()
                    
                    if not result.get('description') and "description:" in summary.lower():
                        desc_match = re.search(r'description:(.*?)$', summary, re.IGNORECASE | re.DOTALL)
                        if desc_match:
                            result['description'] = desc_match.group(1).strip()
                    
                    print(f"OpenAI'dan alınan başlık: {result.get('title')}")
                    print(f"OpenAI'dan alınan açıklama: {result.get('description')}")
                    
                except Exception as e:
                    print(f"OpenAI özet hatası: {str(e)}")
            
            return result
        except Exception as e:
            logger.error(f"Error during screenshot analysis: {str(e)}")
            # Hata durumunda boş bir sonuç döndür
            default_result = {
                'url': url,
                'title': existing_title or '',
                'description': existing_description or '',
                'categories': [{
                    'main': 'Genel',
                    'sub': 'Diğer',
                    'main_id': None,
                    'sub_id': None
                }],
                'tags': [{
                    'name': 'genel',
                    'id': None
                }]
            }
            return default_result
            
    except Exception as e:
        print(f"Ekran görüntüsü analiz hatası: {str(e)}")
        # Hata durumunda boş bir sonuç döndür
        default_result = {
            'url': url,
            'title': existing_title or '',
            'description': existing_description or '',
            'categories': [{
                'main': 'Genel',
                'sub': 'Diğer',
                'main_id': None,
                'sub_id': None
            }],
            'tags': [{
                'name': 'genel',
                'id': None
            }]
        }
        return default_result


# For backwards compatibility
analyze_screenshot_with_gemini = analyze_screenshot
categorize_with_gemini = categorize_content 