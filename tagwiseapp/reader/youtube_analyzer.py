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

from .utils import correct_json_format, ensure_correct_json_structure
from .category_matcher import match_categories_and_tags, get_existing_categories, get_existing_tags
from .gemini_analyzer import configure_gemini

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

def analyze_youtube_video(url):
    """
    YouTube videosunu analiz eder ve kategorize eder.
    
    Args:
        url (str): YouTube video URL'si
        
    Returns:
        dict: Analiz sonuçları
    """
    print(f"YouTube videosu analiz ediliyor: {url}")
    
    # Video ID'sini çıkar
    video_id = extract_youtube_video_id(url)
    if not video_id:
        print("Geçerli YouTube video ID'si bulunamadı")
        return None
    
    # API anahtarını yükle ve Gemini'yi yapılandır
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not configure_gemini(api_key):
        print("Gemini API yapılandırılamadı")
        return None
    
    try:
        # Video bilgilerini al (başlık, açıklama, meta veriler)
        video_info = get_youtube_video_info(url)
        
        # Video altyazılarını al (varsa)
        transcript = get_youtube_transcript(video_id)
        
        # Video bilgileri yoksa varsayılan değerleri kullan
        if not video_info:
            video_info = {
                'title': 'YouTube Video',
                'description': '',
                'keywords': [],
                'channel_name': '',
                'categories': [],
                'thumbnail_url': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            }
            
        # Thumbnail URL'sini al (yüksek kaliteli)
        thumbnail_url = get_youtube_thumbnail_webp(video_id)
        if thumbnail_url:
            video_info['thumbnail_url'] = thumbnail_url
        else:
            # Eğer thumbnail URL'i yoksa, doğrudan YouTube thumbnail URL'i oluştur
            video_info['thumbnail_url'] = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        # Mevcut kategorileri ve etiketleri al
        existing_categories = get_existing_categories()
        existing_tags = get_existing_tags()
        
        # System instruction'ı güncelleyerek mevcut kategori ve etiketleri ekle
        custom_system_instruction = YOUTUBE_SYSTEM_INSTRUCTION + f"""

MEVCUT ANA KATEGORİLER: {existing_categories['main_categories']}

MEVCUT ALT KATEGORİLER: {existing_categories['subcategories']}

MEVCUT ETİKETLER: {existing_tags}
"""
        
        # Modeli seç
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=custom_system_instruction
        )   
        
        # Generation config
        generation_config = {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
        
        # Prompt hazırla - video bilgileri ve transcript'i daha vurgulu bir şekilde içerir
        prompt = f"""
YOUTUBE VİDEO ANALİZİ:

Video URL: {url}

VİDEO BAŞLIĞI: "{video_info['title']}"

VİDEO AÇIKLAMASI:
```
{video_info['description'][:750]}{"..." if len(video_info['description']) > 750 else ""}
```

Kanal: {video_info['channel_name']}
Orijinal Etiketler: {video_info['keywords'][:10] if video_info['keywords'] else 'Belirtilmemiş'}
YouTube Kategorileri: {video_info.get('categories', [])}
İzlenme: {video_info.get('views', 'Bilinmiyor')}
Yayın Tarihi: {video_info.get('publish_date', 'Bilinmiyor')}

"""
        
        # Transcript varsa ekle
        if transcript:
            prompt += f"""
VİDEO ALTYAZISI (TRANSKRİPT):
```
{transcript[:1000]}{"..." if len(transcript) > 1000 else ""}
```
"""
        else:
            prompt += "Video için altyazı (transcript) bulunamadı."
            
        prompt += """

Lütfen yukarıdaki bilgilere göre videoyu analiz et ve uygun kategoriler ve etiketler belirle.
"""
        
        # Gemini'ye istek gönder
        print(f"YouTube videosu analiz ediliyor: {url} (başlık, açıklama ve transcript verileriyle)")
        response = model.generate_content(
            prompt,
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
            json_result = ensure_correct_json_structure(json_result, url)
            
            # Kategorileri ve etiketleri eşleştir
            json_result = match_categories_and_tags(json_result, existing_categories, existing_tags)
            
            # Thumbnail URL'sini ekle
            json_result['thumbnail_url'] = video_info.get('thumbnail_url')
            
            # Kategori sayısını kontrol et - en az 1, en fazla 3 kategori olmalı
            if 'categories' in json_result and isinstance(json_result['categories'], list):
                # Eğer 3'ten fazla kategori varsa, sadece ilk 3'ünü al
                if len(json_result['categories']) > 3:
                    json_result['categories'] = json_result['categories'][:3]
                
                # Eğer hiç kategori yoksa, varsayılan bir kategori ekle
                if len(json_result['categories']) == 0:
                    json_result['categories'] = [{
                        'main_category': 'Medya',
                        'subcategory': 'Video'
                    }]
                    json_result['main_category'] = 'Medya'
                    json_result['subcategory'] = 'Video'
            
            print(f"YouTube video analizi tamamlandı: {json_result}")
            return json_result
            
        except json.JSONDecodeError as json_err:
            print(f"JSON ayrıştırma hatası: {json_err}")
            print(f"Ham yanıt: {result}")
            
            # Manuel JSON oluşturma girişimi - video bilgilerini kullan
            manual_json = {
                "title": video_info['title'],
                "description": video_info['description'][:150] + "..." if len(video_info['description']) > 150 else video_info['description'],
                "main_category": "Medya",
                "subcategory": "Video",
                "tags": video_info['keywords'][:5] if video_info['keywords'] else ["youtube", "video"],
                "thumbnail_url": video_info.get('thumbnail_url'),
            }
            
            # Başlık için regex
            title_match = re.search(r'"title"\s*:\s*"([^"]+)"', result)
            if title_match:
                manual_json['title'] = title_match.group(1)
            
            # Açıklama için regex
            desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', result)
            if desc_match:
                manual_json['description'] = desc_match.group(1)
            
            # Ana kategori için regex
            main_cat_match = re.search(r'"main_category"\s*:\s*"([^"]+)"', result)
            if main_cat_match:
                manual_json['main_category'] = main_cat_match.group(1)
            
            # Alt kategori için regex
            sub_cat_match = re.search(r'"subcategory"\s*:\s*"([^"]+)"', result)
            if sub_cat_match:
                manual_json['subcategory'] = sub_cat_match.group(1)
            
            # Etiketler için regex
            tags_match = re.search(r'"tags"\s*:\s*\[\s*([^\]]+)\s*\]', result)
            if tags_match:
                tags_text = tags_match.group(1)
                # Etiketleri virgülle ayır ve her bir etiketi tırnak işaretlerinden temizle
                tags = [tag.strip().strip('"').strip("'") for tag in tags_text.split(',')]
                manual_json['tags'] = [tag for tag in tags if tag]  # Boş etiketleri filtrele
            
            # Manuel JSON için kategorileri ayarla
            manual_json['categories'] = [{
                'main_category': manual_json.get('main_category', 'Medya'),
                'subcategory': manual_json.get('subcategory', 'Video')
            }]
            
            return manual_json
            
    except Exception as e:
        print(f"YouTube video analizi sırasında hata: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Hata durumunda varsayılan değerleri döndür
        return {
            "title": "YouTube Video",
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