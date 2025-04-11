"""
Django management command to analyze URLs.
"""

from django.core.management.base import BaseCommand, CommandError
from tagwiseapp.reader.main import analyze_url
from tagwiseapp.reader.utils import load_api_key
from tagwiseapp.reader.content_analyzer import configure_llm

class Command(BaseCommand):
    help = 'Analyze URLs and categorize them'

    def add_arguments(self, parser):
        parser.add_argument('urls', nargs='*', help='URLs to analyze')
        parser.add_argument('-f', '--file', help='File containing URLs (one per line)')
        parser.add_argument('-i', '--interactive', action='store_true', help='Run in interactive mode')
        parser.add_argument('--debug', action='store_true', help='Enable debug output')

    def handle(self, *args, **options):
        # API anahtarını yükle ve LLM'yi yapılandır
        api_key = load_api_key()
        if not configure_llm(api_key):
            raise CommandError("LLM API yapılandırılamadı.")
        
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
            self.stdout.write("Web Sayfası Kategori Analizi")
            self.stdout.write("----------------------------")
            self.stdout.write("URL'leri girin (birden fazla URL için her satıra bir URL yazın, bitirmek için boş satır girin):")
            
            while True:
                url = input().strip()
                if not url:
                    break
                urls.append(url)
        
        if not urls:
            self.stdout.write(self.style.WARNING("URL girilmedi."))
            return
        
        self.stdout.write(f"{len(urls)} URL analiz edilecek...")
        
        results = []
        for url in urls:
            self.stdout.write(f"Analiz ediliyor: {url}")
            result = analyze_url(url)
            results.append(result)
            self.stdout.write(self.style.SUCCESS(f"Analiz tamamlandı: {url}"))
        
        self.stdout.write("\nANALİZ SONUÇLARI:")
        self.stdout.write("================")
        for result in results:
            self.stdout.write(result) 