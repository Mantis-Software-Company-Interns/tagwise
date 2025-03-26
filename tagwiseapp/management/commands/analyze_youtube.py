"""
Django management command to analyze YouTube URLs.
"""

from django.core.management.base import BaseCommand, CommandError
from tagwiseapp.reader.youtube_analyzer import is_youtube_url, analyze_youtube_video, extract_youtube_video_id, fetch_youtube_thumbnail
from tagwiseapp.reader.utils import load_api_key
from tagwiseapp.reader.gemini_analyzer import configure_gemini
import json
import os
import uuid

class Command(BaseCommand):
    help = 'Analyze YouTube URLs and categorize them'

    def add_arguments(self, parser):
        parser.add_argument('urls', nargs='*', help='YouTube URLs to analyze')
        parser.add_argument('-f', '--file', help='File containing YouTube URLs (one per line)')
        parser.add_argument('-i', '--interactive', action='store_true', help='Run in interactive mode')
        parser.add_argument('--debug', action='store_true', help='Enable debug output')
        parser.add_argument('--download-thumbnails', action='store_true', help='Download thumbnails to local directory')
        parser.add_argument('--thumbnail-dir', default='thumbnails', help='Directory to save thumbnails (default: thumbnails)')

    def handle(self, *args, **options):
        # API anahtarını yükle ve Gemini'yi yapılandır
        api_key = load_api_key()
        if not configure_gemini(api_key):
            raise CommandError("Gemini API yapılandırılamadı.")
        
        # Thumbnail directory
        download_thumbnails = options['download_thumbnails']
        thumbnail_dir = options['thumbnail_dir']
        
        # Create thumbnail directory if needed
        if download_thumbnails:
            os.makedirs(thumbnail_dir, exist_ok=True)
            self.stdout.write(f"Thumbnails indiriliyor ve {thumbnail_dir} dizinine kaydediliyor.")
        
        urls = []
        
        # URLs from command-line arguments
        if options['urls']:
            urls.extend(options['urls'])
        
        # URLs from file
        if options['file']:
            try:
                with open(options['file'], 'r') as f:
                    file_urls = [line.strip() for line in f if line.strip()]
                    urls.extend(file_urls)
            except Exception as e:
                raise CommandError(f"Dosya okuma hatası: {e}")
        
        # Interactive mode
        if options['interactive'] or (not urls and not options['file']):
            self.stdout.write("YouTube Video Kategori Analizi")
            self.stdout.write("------------------------------")
            self.stdout.write("YouTube URL'lerini girin (birden fazla URL için her satıra bir URL yazın, bitirmek için boş satır girin):")
            
            while True:
                url = input().strip()
                if not url:
                    break
                urls.append(url)
        
        if not urls:
            self.stdout.write(self.style.WARNING("YouTube URL girilmedi."))
            return
        
        self.stdout.write(f"{len(urls)} YouTube URL analiz edilecek...")
        
        results = []
        youtube_urls_count = 0
        
        for url in urls:
            self.stdout.write(f"URL kontrolü: {url}")
            
            # YouTube URL kontrolü
            if not is_youtube_url(url):
                self.stdout.write(self.style.WARNING(f"Bu bir YouTube URL'si değil, atlanıyor: {url}"))
                continue
            
            youtube_urls_count += 1
            video_id = extract_youtube_video_id(url)
            self.stdout.write(f"YouTube URL analiz ediliyor: {url} (ID: {video_id})")
            
            # Thumbnail indir
            if download_thumbnails and video_id:
                thumbnail_data = fetch_youtube_thumbnail(video_id)
                if thumbnail_data:
                    filename = f"youtube_{video_id}_{str(uuid.uuid4())[:8]}.jpg"
                    thumbnail_path = os.path.join(thumbnail_dir, filename)
                    
                    with open(thumbnail_path, 'wb') as f:
                        f.write(thumbnail_data)
                    
                    self.stdout.write(self.style.SUCCESS(f"Thumbnail indirildi: {thumbnail_path}"))
            
            # YouTube video analizi
            result = analyze_youtube_video(url)
            
            if result:
                # Thumbnail URL'sini göster
                thumbnail_url = result.get('thumbnail_url')
                if thumbnail_url:
                    self.stdout.write(f"Thumbnail URL: {thumbnail_url}")
                
                results.append({
                    'url': url,
                    'result': result
                })
                self.stdout.write(self.style.SUCCESS(f"YouTube analizi tamamlandı: {url}"))
            else:
                self.stdout.write(self.style.ERROR(f"YouTube analizi başarısız oldu: {url}"))
        
        self.stdout.write("\nANALİZ SONUÇLARI:")
        self.stdout.write("================")
        
        if youtube_urls_count == 0:
            self.stdout.write(self.style.WARNING("Analiz edilecek geçerli YouTube URL'si bulunamadı."))
            return
            
        for item in results:
            self.stdout.write(f"\nURL: {item['url']}")
            self.stdout.write(f"Başlık: {item['result'].get('title', 'Belirtilmemiş')}")
            self.stdout.write(f"Açıklama: {item['result'].get('description', 'Belirtilmemiş')}")
            self.stdout.write(f"Ana Kategori: {item['result'].get('main_category', 'Belirtilmemiş')}")
            self.stdout.write(f"Alt Kategori: {item['result'].get('subcategory', 'Belirtilmemiş')}")
            self.stdout.write(f"Etiketler: {', '.join(item['result'].get('tags', []))}")
            
            # Thumbnail URL göster
            thumbnail_url = item['result'].get('thumbnail_url')
            if thumbnail_url:
                self.stdout.write(f"Thumbnail URL: {thumbnail_url}")
            
            if options['debug']:
                self.stdout.write("\nTüm Veri (JSON):")
                self.stdout.write(json.dumps(item['result'], indent=2, ensure_ascii=False)) 