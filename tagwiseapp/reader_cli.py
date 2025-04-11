#!/usr/bin/env python
"""
Reader CLI

This script provides a command-line interface for the reader package.
"""

import sys
import argparse
import os

# Add the project directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
if project_dir not in sys.path:
    sys.path.append(project_dir)

from tagwiseapp.reader.django_setup import setup_django
from tagwiseapp.reader.main import analyze_url
from tagwiseapp.reader.utils import load_api_key
from tagwiseapp.reader.content_analyzer import configure_llm

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Analyze URLs and categorize them.')
    parser.add_argument('urls', nargs='*', help='URLs to analyze')
    parser.add_argument('-f', '--file', help='File containing URLs (one per line)')
    parser.add_argument('-i', '--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    return parser.parse_args()

def main_cli():
    """Main CLI function."""
    args = parse_args()
    
    # Django ortamını başlat
    setup_django()
    
    # API anahtarını yükle ve LLM'yi yapılandır
    api_key = load_api_key()
    if not configure_llm(api_key):
        print("LLM API yapılandırılamadı.")
        sys.exit(1)
    
    urls = []
    
    # URLs from command-line arguments
    if args.urls:
        urls.extend(args.urls)
    
    # URLs from file
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip()]
                urls.extend(file_urls)
        except Exception as e:
            print(f"Dosya okuma hatası: {e}")
            sys.exit(1)
    
    # Interactive mode
    if args.interactive or (not urls and not args.file):
        print("Web Sayfası Kategori Analizi")
        print("----------------------------")
        print("URL'leri girin (birden fazla URL için her satıra bir URL yazın, bitirmek için boş satır girin):")
        
        while True:
            url = input().strip()
            if not url:
                break
            urls.append(url)
    
    if not urls:
        print("URL girilmedi.")
        return
    
    print(f"{len(urls)} URL analiz edilecek...")
    
    results = []
    for url in urls:
        result = analyze_url(url)
        results.append(result)
    
    print("\nANALİZ SONUÇLARI:")
    print("================")
    for result in results:
        print(result)

if __name__ == "__main__":
    main_cli() 