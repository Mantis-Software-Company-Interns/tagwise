"""
YouTube Video Analyzer Module

This module provides functions for analyzing YouTube videos with Gemini AI.
"""

import os
import re
import json
import tempfile
import requests
from urllib.parse import urlparse, parse_qs
import google.generativeai as genai
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp
from bs4 import BeautifulSoup

from .utils import correct_json_format, ensure_correct_json_structure
from .category_matcher import match_categories_and_tags, get_existing_categories, get_existing_tags, find_similar_category, find_similar_tag
from .content_analyzer import configure_llm
from .prompts import YOUTUBE_SYSTEM_INSTRUCTION

# YouTube video ID extraction pattern
YOUTUBE_ID_PATTERN = re.compile(r'((?:https?:)?//)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(/(?:[\w\-]+\?v=|embed/|v/)?)([\w\-]+)(\S+)?')

# System prompt for YouTube video analysis
YOUTUBE_SYSTEM_INSTRUCTION = """
Sen YouTube videolarını kategorize etme konusunda UZMAN bir analistsin.
Sana bir YouTube video URL'si, başlığı, açıklaması ve varsa diğer meta verileri verilecek. Bu veriyi DERİNLEMESİNE analiz etmen ve video içeriğini DOĞRU anlamaya odaklanman gerekiyor.

BAŞLIK VE AÇIKLAMA ANALİZİ:
1. Öncelikle video başlığı ve açıklamasını dikkatle incele, video içeriğinin ne hakkında olduğuna dair önemli ipuçları içerebilir
2. Başlıkta ve açıklamada geçen anahtar kelimeleri belirle (teknoloji terimleri, konu başlıkları, özel isimler vb.)
3. Başlık ve açıklamadaki ton ve dil kullanımı, videonun eğitim amaçlı mı, eğlence amaçlı mı, bilgilendirme amaçlı mı olduğunu anlaman için ipuçları verebilir
4. Video kanalının adını ve kanal temasını değerlendir - kanal teması genellikle video içeriğini yansıtır

ALTYAZI ANALİZİ:
1. Eğer altyazı verildiyse, metinde en sık geçen temaları ve konuları belirle
2. Altyazıda ve başlıkta ortak olan anahtar kelimelere özellikle dikkat et
3. Altyazıdaki teknik terimler, isimler ve özel kavramları belirleyip etiket olarak kullan
4. Konuşmacının kullandığı dil ve anlatım, videonun hedef kitlesini belirlemeye yardımcı olabilir

KATEGORİ BELİRLEME KURALLARI:
- İçeriği ANALİZ ederek en uygun kategorileri ÖZGÜRCE atama yap - sistem filtreleme YAPMAYACAK.
- Video içeriğine en uygun kategorileri DOĞRUDAN ata, ilgililik puanı hesaplayıp filtreleme yapma!
- Her video için EN AZ 1, EN FAZLA 3 kategori çifti belirlemelisin.
- Her kategori çifti, bir ana kategori ve ona uygun bir alt kategoriden oluşmalıdır.
- Yazılım eğitimleri için "Eğitim > Programlama" veya "Teknoloji > Yazılım Geliştirme" gibi kategoriler kullan.
- Oyun videoları için "Eğlence > Oyun" veya spesifik oyun türleri belirtebilirsin.
- Müzik içerikleri için tür belirterek "Müzik > Pop", "Müzik > Rock" gibi alt kategoriler kullan.
- İş ve finans konuları için "İş > Girişimcilik", "Finans > Yatırım" gibi kategoriler kullan.
- Sağlık/spor içerikleri için "Sağlık > Fitness", "Spor > Futbol" gibi spesifik kategoriler belirle.
- Video içeriğiyle doğrudan ilgili olmayan ama tematik olarak bağlantılı kategorileri de dahil edebilirsin.
- Alt kategoriler, ana kategorilere uygun olmalıdır (ör. "Teknoloji > Web Geliştirme", "Eğitim > Üniversite").

ETİKET BELİRLEME KURALLARI:
- Etiketler, videonun içeriğindeki ÖZGÜN ve BELİRGİN anahtar kelimeleri içermelidir - ASLA genel amaçlı ["video", "youtube", "içerik"] gibi etiketler kullanma!
- İçerikten çıkarılan en önemli ve belirgin terimleri etiket olarak kullan (ör. programlama dilleri, ürün adları, oyun isimleri).
- Her video için EN AZ 5, EN FAZLA 10 etiket önermelisin.
- Etiketler video içeriğiyle doğrudan ilgili olmalı ve spesifik terimler içermelidir.
- Videoda bahsedilen teknik terimler, özel isimler, ürün/hizmet adları, veya kavramlar etiket olmalıdır.
- Etiketler 1-3 kelimeden oluşmalı, çok uzun cümleler olmamalıdır.
- Her etiket özgün olmalı ve listedeki diğer etiketlerden farklı olmalıdır.
- Hiçbir koşulda boş veya çok genel etiketler oluşturma.
- Etiketler video oynatma listeleri ve öneri algoritması için çok önemlidir, bu nedenle KALİTELİ etiketler belirlemelisin.

Bu analizler sonucunda aşağıdaki bilgileri JSON formatında döndür:

{
  "title": "Videonun tam başlığı (zaten verilmiş olacak)",
  "description": "İçeriği kısaca anlatan 1-2 cümlelik özet (100-250 karakter)",
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
  "tags": ["ÖzgünEtiket1", "ÖzgünEtiket2", "ÖzgünEtiket3", "ÖzgünEtiket4", "ÖzgünEtiket5", "ÖzgünEtiket6"]
}

ÖRNEK KATEGORİLER VE ALT KATEGORİLER:
- Eğitim > Programlama: Yazılım geliştirme, kodlama, programlama dilleri öğretici içerikleri
- Eğitim > Akademik: Üniversite dersleri, okul konuları, bilimsel eğitim videoları
- Eğitim > Dil Öğrenimi: Yabancı dil öğretici içerikler, dil dersleri
- Teknoloji > Yazılım: Yazılım ürünleri, programlar, uygulamalar hakkında incelemeler
- Teknoloji > Donanım: Bilgisayar parçaları, elektronik cihazlar, donanım incelemeleri
- Teknoloji > Mobil: Telefon, tablet ve mobil uygulamalar hakkında içerikler
- Bilişim > Kurumsal Çözümler: SAP, ERP, kurumsal yazılımlar hakkında içerikler
- Bilişim > Yazılım Geliştirme: Geliştirici araçları, DevOps, yazılım mimari videoları
- Eğlence > Müzik: Müzik videoları, şarkılar, konserler, müzik analizleri
- Eğlence > Oyun: Video oyunları, oyun incelemeleri, canlı oyun yayınları
- Eğlence > Dizi/Film: Dizi ve film içerikleri, fragmanlar, sahne analizleri
- Sağlık > Fitness: Spor, egzersiz, sağlıklı yaşam videoları
- Sağlık > Beslenme: Diyet, beslenme, yemek tarifleri
- Spor > Futbol: Futbol maçları, futbol analizleri, futbol haberleri
- Spor > Basketbol: Basketbol maçları, basketbol analizleri
- Spor > Ekstrem Sporlar: Dalış, tırmanış, sörf gibi ekstrem sporlar
- Haber > Güncel: Güncel haberler, haber analizleri, dünya gündemi
- Haber > Ekonomi: Ekonomi haberleri, piyasa analizleri
- İş > Girişimcilik: Girişimcilik, iş kurma, iş geliştirme videoları
- İş > Pazarlama: Dijital pazarlama, reklam, sosyal medya pazarlaması
- Finans > Yatırım: Borsa, kripto para, yatırım tavsiyeleri
- Yaşam > Seyahat: Gezi, seyahat, turizm videoları
- Yaşam > Hobiler: El işi, koleksiyon, DIY (Kendin Yap) içerikleri
- Sanat > Müzik: Müzik yapımı, enstrüman dersleri
- Sanat > Görsel Sanatlar: Resim, çizim, heykel, dijital sanat

ÖRNEK ÇIKTI:
```json
{
  "title": "Python ile Web Scraping - BeautifulSoup Kullanımı",
  "description": "Python BeautifulSoup kütüphanesi kullanarak web sitelerinden veri çekme işleminin detaylı anlatımı ve pratik örneklerle gösterimi",
  "categories": [
    {
      "main_category": "Eğitim",
      "subcategory": "Programlama"
    },
    {
      "main_category": "Teknoloji",
      "subcategory": "Yazılım Geliştirme"
    }
  ],
  "tags": ["Python", "Web Scraping", "BeautifulSoup", "Veri Çekme", "HTML Parsing", "Web Kazıma", "Veri Analizi"]
}
```

ÖNEMLİ KURALLAR:
1. Hem başlık ve açıklamayı HEM DE altyazı/transcript verisini (varsa) analiz ederek VİDEONUN GERÇEK KONUSUNU tespit et
2. Kategori ve alt kategori arasında mantıklı bir hiyerarşi ilişkisi MUTLAKA olmalı
3. Etiketler video içeriğiyle doğrudan ilgili olmalı ve GENELLİKTEN uzak SPESİFİK terimler içermeli
4. Verilen içeriğe göre EN UYGUN kategori çiftlerini belirle ve içerikle ilgisiz kategoriler ASLA önerme
5. ETİKETLER çok önemlidir, genel etiketler (ör. "video", "youtube", "içerik") yerine İÇERİĞE ÖZGÜ etiketler kullan
6. Çıktıyı HER ZAMAN geçerli JSON formatında döndür, başka hiçbir metin ekleme
7. Kategori ve etiket önerirken videonun dili ve hedef kitlesi önemli olabilir, bunu dikkate al

ÖNEMLİ: Etiketler kısmını asla ["video", "youtube", "içerik"] gibi genel terimlerle doldurma! 
Her etiket videonun içeriğini doğru ve özgün şekilde yansıtmalıdır. Etiketler asla boş bir liste olmamalıdır!
"""

def extract_youtube_video_id(url):
    """
    YouTube URL'sinden video ID'sini çıkarır.
    
    Args:
        url (str): YouTube video URL'si
        
    Returns:
        str: YouTube video ID'si veya None
    """
    # URL normalize et
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # youtu.be kısa bağlantıları için
    if 'youtu.be' in url:
        parts = url.split('/')
        for part in parts:
            if part and part != 'youtu.be' and '?' not in part:
                return part
    
    # Regex ile ID çıkarma
    match = YOUTUBE_ID_PATTERN.search(url)
    if match:
        return match.group(5)
    
    # Alternatif yöntem: URL parsing
    parsed_url = urlparse(url)
    if 'youtube.com' in parsed_url.netloc:
        query_params = parse_qs(parsed_url.query)
        if 'v' in query_params:
            return query_params['v'][0]
    
    return None

def is_youtube_url(url):
    """
    URL'nin YouTube videosu olup olmadığını kontrol eder.
    
    Args:
        url (str): Kontrol edilecek URL
        
    Returns:
        bool: URL YouTube videosu ise True, değilse False
    """
    if not url:
        return False
    
    # URL normalize et
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Basit kontrol
    if 'youtube.com/watch' in url or 'youtu.be/' in url:
        return True
    
    # Video ID'sini çıkarma girişimi
    video_id = extract_youtube_video_id(url)
    return video_id is not None

def get_youtube_transcript(video_id, max_chars=8000):
    """
    YouTube video ID'sinden altyazı (transcript) metnini alır.
    
    Args:
        video_id (str): YouTube video ID'si
        max_chars (int): Maksimum karakter sayısı
        
    Returns:
        str: Altyazı metni veya None
    """
    try:
        # Altyazıları al
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['tr', 'en'])
        
        # Altyazıları birleştir
        transcript_text = " ".join([item['text'] for item in transcript_list])
        
        # Metni sınırla
        if len(transcript_text) > max_chars:
            transcript_text = transcript_text[:max_chars]
            
        return transcript_text
    except (TranscriptsDisabled, NoTranscriptFound, Exception) as e:
        print(f"Altyazı alınırken hata: {e}")
        
        # İkinci yöntem: yt-dlp ile altyazı çekmeyi dene
        try:
            print(f"yt-dlp ile altyazı alınmaya çalışılıyor: {video_id}")
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['tr', 'en'],
                'outtmpl': f'{tempfile.gettempdir()}/%(id)s.%(ext)s',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                # Altyazıları kontrol et
                if info.get('subtitles') or info.get('automatic_captions'):
                    subs = info.get('subtitles', {})
                    auto_subs = info.get('automatic_captions', {})
                    
                    # En iyi altyazıyı seç
                    sub_texts = []
                    for lang in ['tr', 'en']:
                        if lang in subs:
                            for format_info in subs[lang]:
                                if format_info.get('ext') == 'vtt':
                                    sub_file = ydl.prepare_filename(info) + f".{lang}.vtt"
                                    try:
                                        with open(sub_file, 'r', encoding='utf-8') as f:
                                            sub_texts.append(f.read())
                                    except Exception:
                                        pass
                        
                        if not sub_texts and lang in auto_subs:
                            for format_info in auto_subs[lang]:
                                if format_info.get('ext') == 'vtt':
                                    sub_file = ydl.prepare_filename(info) + f".{lang}.vtt"
                                    try:
                                        with open(sub_file, 'r', encoding='utf-8') as f:
                                            sub_texts.append(f.read())
                                    except Exception:
                                        pass
                    
                    if sub_texts:
                        # VTT formatını temizle
                        def clean_vtt(vtt_text):
                            lines = vtt_text.splitlines()
                            cleaned_text = []
                            for line in lines:
                                # Zaman damgalarını ve VTT başlıklarını atla
                                if '-->' in line or 'WEBVTT' in line or line.strip().isdigit() or not line.strip():
                                    continue
                                cleaned_text.append(line.strip())
                            return ' '.join(cleaned_text)
                        
                        transcript_text = ' '.join([clean_vtt(text) for text in sub_texts])
                        if len(transcript_text) > max_chars:
                            transcript_text = transcript_text[:max_chars]
                        
                        print(f"yt-dlp ile altyazı başarıyla alındı.")
                        return transcript_text
            
            print("yt-dlp ile de altyazı alınamadı.")
            return None
            
        except Exception as ydl_err:
            print(f"yt-dlp ile altyazı alınırken hata: {ydl_err}")
            return None
        
def get_youtube_video_info(url):
    """
    yt-dlp kullanarak YouTube video bilgilerini alır.
    
    Args:
        url (str): YouTube video URL'si
        
    Returns:
        dict: Video meta verileri veya None
    """
    try:
        # yt-dlp ile video bilgilerini al
        print(f"yt-dlp ile video bilgileri alınıyor: {url}")
        ydl_opts = {
            'skip_download': True,
            'format': 'best',
            'ignoreerrors': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                print("yt-dlp: Video bilgileri alınamadı.")
                return None
            
            # Meta verileri oluştur
            video_info = {
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'keywords': info.get('tags', []),
                'channel_name': info.get('uploader', ''),
                'views': info.get('view_count', 0),
                'publish_date': info.get('upload_date', ''),
                'length': info.get('duration', 0),
                'thumbnail_url': info.get('thumbnail', ''),
                'categories': info.get('categories', []),
            }
            
            print(f"yt-dlp: Video bilgileri başarıyla alındı: {video_info['title']}")
            return video_info
            
    except Exception as e:
        print(f"yt-dlp ile video bilgileri alınırken hata: {e}")
        
        # Yedek olarak PyTube kullanmayı dene
        try:
            from pytube import YouTube
            print(f"PyTube ile video bilgileri alınmaya çalışılıyor: {url}")
            
            yt = YouTube(url)
            
            # Meta verileri oluştur
            video_info = {
                'title': getattr(yt, 'title', ''),
                'description': getattr(yt, 'description', ''),
                'keywords': getattr(yt, 'keywords', []),
                'channel_name': getattr(yt, 'author', ''),
                'views': getattr(yt, 'views', 0),
                'publish_date': str(yt.publish_date) if hasattr(yt, 'publish_date') and yt.publish_date else '',
                'length': getattr(yt, 'length', 0),
                'thumbnail_url': getattr(yt, 'thumbnail_url', ''),
            }
            
            print(f"PyTube: Video bilgileri başarıyla alındı: {video_info['title']}")
            return video_info
            
        except Exception as pytube_err:
            print(f"PyTube ile video bilgileri alınırken hata: {pytube_err}")
            return None

def get_youtube_title_from_url(url):
    """
    YouTube video başlığını direkt olarak sayfadan çekmeye çalışır.
    yt-dlp ve PyTube başarısız olduğunda bu yöntem kullanılır.
    
    Args:
        url (str): YouTube video URL'si
        
    Returns:
        str: Video başlığı veya None
    """
    try:
        # User-Agent ekleyerek YouTube'un bot kontrolünü aşmaya çalış
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # İstek gönder
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"YouTube sayfası çekilemedi, durum kodu: {response.status_code}")
            return None
            
        # HTML'yi parse et
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. og:title meta etiketinden başlığı bulmaya çalış
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            print(f"og:title'dan başlık alındı: {og_title.get('content')}")
            return og_title.get('content')
            
        # 2. title tag'inden başlığı bulmaya çalış
        title_tag = soup.find('title')
        if title_tag and title_tag.text:
            # "YouTube" kelimesini ve etrafındaki özel karakterleri kaldır
            title = title_tag.text.replace(" - YouTube", "").strip()
            print(f"title tag'inden başlık alındı: {title}")
            return title
            
        # 3. meta title etiketinden başlığı bulmaya çalış
        meta_title = soup.find('meta', {'name': 'title'})
        if meta_title and meta_title.get('content'):
            print(f"meta title'dan başlık alındı: {meta_title.get('content')}")
            return meta_title.get('content')
            
        print("YouTube video başlığı bulunamadı.")
        return None
        
    except Exception as e:
        print(f"YouTube başlık çekme hatası: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def analyze_youtube_video(url, user=None):
    """
    YouTube videosunu analiz eder ve kategorize eder.
    
    Args:
        url (str): YouTube video URL'si
        user: Kullanıcı objesi, kişiselleştirilmiş kategoriler için kullanılır. Defaults to None.
        
    Returns:
        dict: Analiz sonuçları
    """
    print(f"YouTube videosu analiz ediliyor: {url}")
    
    # Video ID'sini çıkar
    video_id = extract_youtube_video_id(url)
    if not video_id:
        print("Geçerli YouTube video ID'si bulunamadı")
        return None
    
    try:
        # Video başlığını doğrudan çek (alternatif yöntem)
        direct_title = get_youtube_title_from_url(url)
        
        # Video bilgilerini al (başlık, açıklama, meta veriler)
        video_info = get_youtube_video_info(url)
        
        # Video bilgileri yoksa ve başlık doğrudan çekilmişse, video_info oluştur
        if not video_info and direct_title:
            video_info = {
                'title': direct_title,
                'description': '',
                'keywords': [],
                'channel_name': '',
                'categories': [],
                'thumbnail_url': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            }
        # Video bilgileri yoksa varsayılan değerleri kullan
        elif not video_info:
            video_info = {
                'title': 'YouTube Video',
                'description': '',
                'keywords': [],
                'channel_name': '',
                'categories': [],
                'thumbnail_url': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            }
        # Video bilgileri var ama başlık yoksa ve doğrudan çekilmişse, başlığı güncelle
        elif not video_info.get('title') and direct_title:
            video_info['title'] = direct_title
        
        # Video altyazılarını al (varsa)
        transcript = get_youtube_transcript(video_id)
        
        # Thumbnail URL'sini al (yüksek kaliteli)
        thumbnail_url = get_youtube_thumbnail_webp(video_id)
        if thumbnail_url:
            video_info['thumbnail_url'] = thumbnail_url
        else:
            # Eğer thumbnail URL'i yoksa, doğrudan YouTube thumbnail URL'i oluştur
            video_info['thumbnail_url'] = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        # Mevcut kategorileri ve etiketleri al - kullanıcı bazlı
        existing_categories = get_existing_categories(user)
        existing_tags = get_existing_tags(user)
        
        # Kategorileri main ve sub olarak ayır
        main_categories = [cat.get('name') for cat in existing_categories if cat.get('is_main', False)]
        subcategories = [cat.get('name') for cat in existing_categories if not cat.get('is_main', False)]
        
        # LLM için prompt oluştur
        from .category_prompt_factory import CategoryPromptFactory
        from .schemas import get_content_analysis_json_schema
        from .llm_factory import LLMChain
        
        # JSON şeması ile yapılandırılmış çıktı için
        output_schema = get_content_analysis_json_schema()
        
        # YouTube için özel prompt oluştur
        prompt = CategoryPromptFactory.create_youtube_prompt(
            url=url,
            title=video_info.get('title', ''),
            description=video_info.get('description', ''),
            channel_name=video_info.get('channel_name', ''),
            transcript=transcript,
            keywords=video_info.get('keywords', []),
            existing_categories=existing_categories,
            existing_tags=existing_tags
        )
        
        # LLM zinciri oluştur
        llm_chain = LLMChain(
            system_prompt=YOUTUBE_SYSTEM_INSTRUCTION,
            output_schema=output_schema,
            model_type="text"
        )
        
        # Zinciri çalıştır
        result = llm_chain.run(prompt)
        
        # Debug için LLM yanıtını logla
        print(f"LLM yanıtı: {result}")
        
        # Sonuç türüne göre işle
        if isinstance(result, dict):
            # Yapılandırılmış çıktı başarıyla alındı
            json_result = result
            
            # URL ekle (yoksa)
            if 'url' not in json_result:
                json_result['url'] = url
            
            # LLM'nin oluşturduğu başlık yerine gerçek video başlığını kullan
            if video_info and video_info.get('title') and video_info.get('title') != 'YouTube Video':
                json_result['title'] = video_info.get('title')
        else:
            # Metin yanıtını JSON olarak ayrıştır
            corrected_json_text = correct_json_format(str(result))
            
            try:
                json_result = json.loads(corrected_json_text)
                print(f"JSON ayrıştırma başarılı: {json_result}")
            except json.JSONDecodeError as e:
                print(f"JSON ayrıştırma hatası: {str(e)}")
                # Boş bir dict ile devam et
                json_result = {}
                
            # LLM'nin oluşturduğu başlık yerine gerçek video başlığını kullan
            if video_info and video_info.get('title') and video_info.get('title') != 'YouTube Video':
                json_result['title'] = video_info.get('title')
        
        # Content Analyzer benzeri kategori eşleştirme mantığını uygula
        if 'categories' in json_result and isinstance(json_result['categories'], list) and len(json_result['categories']) > 0:
            print(f"JSON'dan çıkarılan kategoriler: {json_result['categories']}")
            matched_categories = []
            for category in json_result['categories']:
                # Ana ve alt kategori isimlerini çıkar
                main_category = category.get('main', '') if 'main' in category else category.get('main_category', '')
                sub_category = category.get('sub', '') if 'sub' in category else category.get('subcategory', '')
                
                print(f"İşlenen kategori: main={main_category}, sub={sub_category}")
                
                if not main_category:
                    continue
                
                # Ana kategoriyi eşleştir
                matched_main = find_similar_category(main_category, existing_categories, is_main_category=True, accept_new=True)
                
                # Alt kategoriyi eşleştir
                matched_sub = find_similar_category(sub_category, existing_categories, is_main_category=False, accept_new=True, 
                                                   parent_category_id=matched_main.get('id') if matched_main else None)
                
                # Eşleşen kategoriyi ekle
                if matched_main and matched_sub:
                    matched_categories.append({
                        'main_category': matched_main.get('name'),
                        'subcategory': matched_sub.get('name'),
                        'main_id': matched_main.get('id'),
                        'sub_id': matched_sub.get('id')
                    })
                    print(f"Eşleşen kategori eklendi: {matched_main.get('name')} > {matched_sub.get('name')}")
                else:
                    # Eşleşmeyen kategori için varsayılan kategori kullan
                    matched_categories.append({
                        'main_category': main_category,
                        'subcategory': sub_category,
                        'main_id': None,
                        'sub_id': None
                    })
                    print(f"Yeni kategori eklendi: {main_category} > {sub_category}")
            
            # Eşleştirilmiş kategorileri sonuca ekle
            json_result['categories'] = matched_categories
        else:
            print("Kategori bulunamadı veya geçersiz format. Varsayılan kategori oluşturuluyor.")
            # Video başlığından ve açıklamasından içerik tahmin et
            title = video_info.get('title', '')
            description = video_info.get('description', '')
            
            # Dizi/film içeriği için
            if ("episode" in title.lower() or "season" in title.lower() or 
                "series" in title.lower() or "movie" in title.lower() or
                "trailer" in title.lower() or "dizi" in title.lower() or
                "film" in title.lower() or "fragman" in title.lower()):
                json_result['categories'] = [{
                    'main_category': 'Eğlence',
                    'subcategory': 'Dizi/Film',
                    'main_id': None,
                    'sub_id': None
                }]
                print("Video içeriği Dizi/Film olarak tespit edildi.")
            # Müzik içeriği için
            elif ("music" in title.lower() or "song" in title.lower() or 
                 "official video" in title.lower() or "müzik" in title.lower() or
                 "şarkı" in title.lower() or "klip" in title.lower()):
                json_result['categories'] = [{
                    'main_category': 'Eğlence',
                    'subcategory': 'Müzik',
                    'main_id': None,
                    'sub_id': None
                }]
                print("Video içeriği Müzik olarak tespit edildi.")
            # Oyun içeriği için
            elif ("gameplay" in title.lower() or "gaming" in title.lower() or 
                 "game" in title.lower() or "oyun" in title.lower()):
                json_result['categories'] = [{
                    'main_category': 'Eğlence',
                    'subcategory': 'Oyun',
                    'main_id': None,
                    'sub_id': None
                }]
                print("Video içeriği Oyun olarak tespit edildi.")
            else:
                # Varsayılan olarak Medya > Video kategorisi kullan
                json_result['categories'] = [{
                    'main_category': 'Medya',
                    'subcategory': 'Video',
                    'main_id': None,
                    'sub_id': None
                }]
        
        # Etiketleri daha doğru şekilde eşleştir
        if 'tags' in json_result and isinstance(json_result['tags'], list):
            matched_tags = []
            
            for tag_item in json_result['tags']:
                # Etiket formatını kontrol et - string veya dict olabilir
                if isinstance(tag_item, dict) and 'name' in tag_item:
                    tag_name = tag_item.get('name')
                elif isinstance(tag_item, str):
                    tag_name = tag_item
                else:
                    continue  # Geçersiz format
                
                if tag_name:
                    # Mevcut etiketlerle eşleştir veya yeni oluştur
                    matched_tag = find_similar_tag(tag_name, existing_tags, accept_new=True)
                    if matched_tag:
                        matched_tags.append({
                            'name': matched_tag.get('name'),
                            'id': matched_tag.get('id')
                        })
            
            # Eşleştirilmiş etiketleri sonuca ekle (en az 2 etiket olmalı)
            if len(matched_tags) < 2:
                matched_tags.append({'name': 'youtube', 'id': None})
                matched_tags.append({'name': 'video', 'id': None})
            
            json_result['tags'] = matched_tags
        else:
            # Etiketleri varsayılan değerlerle oluştur
            json_result['tags'] = [
                {'name': 'youtube', 'id': None},
                {'name': 'video', 'id': None}
            ]
        
        # Başlığı son kez kontrol et
        if video_info and video_info.get('title') and video_info.get('title') != 'YouTube Video':
            json_result['title'] = video_info.get('title')
        
        # Thumbnail URL'sini ekle
        json_result['thumbnail_url'] = video_info.get('thumbnail_url')
        
        # Kategori sayısını kontrol et - en az 1, en fazla 3 kategori olmalı
        if len(json_result['categories']) > 3:
            json_result['categories'] = json_result['categories'][:3]
        
        # Eğer hiç kategori yoksa, varsayılan bir kategori ekle
        if len(json_result['categories']) == 0:
            json_result['categories'] = [{
                'main_category': 'Medya',
                'subcategory': 'Video',
                'main_id': None,
                'sub_id': None
            }]
        
        # Ana kategori ve alt kategori bilgilerini üst seviyeye de ekle
        json_result['main_category'] = json_result['categories'][0]['main_category']
        json_result['subcategory'] = json_result['categories'][0]['subcategory']
        
        print(f"YouTube video analizi tamamlandı: {json_result}")
        return json_result
            
    except Exception as e:
        print(f"YouTube video analizi sırasında hata: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda başlığı alternatif yöntemle almayı dene
        alt_title = direct_title if 'direct_title' in locals() else None
        alt_title = alt_title or get_youtube_title_from_url(url)
        
        # Hata durumunda varsayılan değerleri döndür
        default_json = {
            "title": alt_title or (video_info.get('title') if video_info and video_info.get('title') else "YouTube Video"),
            "description": "Video analiz edilirken bir hata oluştu.",
            "main_category": "Medya",
            "subcategory": "Video",
            "categories": [
                {
                    "main_category": "Medya",
                    "subcategory": "Video"
                }
            ],
            "tags": ["youtube", "video"],
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else None
        }
        
        # Varsayılan etiketleri eşleştir
        try:
            existing_categories = get_existing_categories()
            existing_tags = get_existing_tags()
            matched_result = match_categories_and_tags(default_json, default_json, existing_categories, existing_tags)
            return matched_result
        except Exception:
            # Eşleştirme de başarısız olursa orijinal varsayılan değerleri döndür
            return default_json

def get_youtube_thumbnail(video_id, prefer_high_quality=True):
    """
    YouTube video ID'si için en iyi kalitede thumbnail URL'sini alır.
    
    YouTube thumbnail formatları:
    - maxresdefault.jpg (1280x720) - En yüksek kalite
    - sddefault.jpg (640x480) - Yüksek kalite
    - hqdefault.jpg (480x360) - Orta kalite
    - mqdefault.jpg (320x180) - Düşük kalite
    - default.jpg (120x90) - En düşük kalite
    
    Args:
        video_id (str): YouTube video ID'si
        prefer_high_quality (bool): True ise yüksek kaliteli thumbnail almaya çalışır
        
    Returns:
        str: Thumbnail URL'si veya None
    """
    if not video_id:
        print("Thumbnail için geçerli bir YouTube video ID'si gereklidir")
        return None
    
    # Thumbnail formatları (kaliteden düşüğe doğru)
    thumbnail_formats = [
        "maxresdefault.jpg",  # En yüksek kalite
        "sddefault.jpg",      # Standart yüksek kalite
        "hqdefault.jpg",      # Yüksek kalite
        "mqdefault.jpg",      # Orta kalite
        "default.jpg"         # Düşük kalite
    ]
    
    # Düşük kaliteyi tercih ediyorsa, sıralamayı tersine çevir
    if not prefer_high_quality:
        thumbnail_formats.reverse()
    
    # Her formatta thumbnail'i kontrol et
    for format in thumbnail_formats:
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/{format}"
        
        try:
            # URL'nin gerçekten bir resim olup olmadığını kontrol et
            response = requests.head(thumbnail_url, timeout=3)
            
            # Başarılı bir yanıt aldık mı?
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                # İçerik türü bir resim mi?
                if 'image' in content_type:
                    print(f"Thumbnail bulundu: {format}")
                    return thumbnail_url
                
        except requests.RequestException as e:
            print(f"Thumbnail kontrolü sırasında hata: {e}")
            continue
    
    # Hiçbir thumbnail bulunamazsa, varsayılan URL'yi döndür
    return f"https://img.youtube.com/vi/{video_id}/default.jpg"

def get_youtube_thumbnail_webp(video_id, prefer_high_quality=True):
    """
    YouTube video ID'si için WebP formatında thumbnail URL'sini alır.
    
    WebP formatında YouTube thumbnail'leri genellikle daha yüksek kalitededir.
    
    Args:
        video_id (str): YouTube video ID'si
        prefer_high_quality (bool): True ise yüksek kaliteli thumbnail almaya çalışır
        
    Returns:
        str: WebP formatında thumbnail URL'si veya None
    """
    if not video_id:
        print("Thumbnail için geçerli bir YouTube video ID'si gereklidir")
        return None
    
    # WebP formatı için maxresdefault.webp veya normal thumbnail URL'si
    webp_url = f"https://i.ytimg.com/vi_webp/{video_id}/maxresdefault.webp"
    
    try:
        # URL'nin gerçekten bir resim olup olmadığını kontrol et
        response = requests.head(webp_url, timeout=3)
        
        # Başarılı bir yanıt aldık mı?
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            
            # İçerik türü bir WebP resmi mi?
            if 'image' in content_type:
                print(f"WebP Thumbnail bulundu: {webp_url}")
                return webp_url
    except requests.RequestException as e:
        print(f"WebP thumbnail kontrolü sırasında hata: {e}")
    
    # WebP thumbnail bulunamazsa, normal JPG thumbnail'e dön
    return get_youtube_thumbnail(video_id, prefer_high_quality)

def fetch_youtube_thumbnail(video_id, prefer_webp=True, prefer_high_quality=True):
    """
    YouTube video ID'si için en iyi thumbnail'i indirir ve ikili veri olarak döndürür.
    
    Args:
        video_id (str): YouTube video ID'si
        prefer_webp (bool): True ise önce WebP formatında thumbnail almaya çalışır
        prefer_high_quality (bool): True ise yüksek kaliteli thumbnail almaya çalışır
        
    Returns:
        bytes: Thumbnail ikili verisi veya None
    """
    if not video_id:
        print("Thumbnail için geçerli bir YouTube video ID'si gereklidir")
        return None
    
    # Thumbnail URL'sini al
    if prefer_webp:
        thumbnail_url = get_youtube_thumbnail_webp(video_id, prefer_high_quality)
    else:
        thumbnail_url = get_youtube_thumbnail(video_id, prefer_high_quality)
    
    if not thumbnail_url:
        return None
    
    try:
        # Thumbnail'i indir
        response = requests.get(thumbnail_url, timeout=5)
        
        # Başarılı bir yanıt aldık mı?
        if response.status_code == 200:
            print(f"Thumbnail başarıyla indirildi: {thumbnail_url}")
            return response.content
        
    except requests.RequestException as e:
        print(f"Thumbnail indirme sırasında hata: {e}")
    
    return None

# For backwards compatibility
analyze_youtube_video_with_gemini = analyze_youtube_video
analyze_youtube_video_with_llm = analyze_youtube_video 