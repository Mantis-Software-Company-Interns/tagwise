#!/usr/bin/env python
"""
Test script for the YouTube Analyzer integration.
"""

import os
import json
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tagwisebackend.settings')
django.setup()

# Import the YouTube analyzer functions
from tagwiseapp.reader.youtube_analyzer import is_youtube_url, analyze_youtube_video

def test_youtube_analyzer():
    """
    Test the YouTube analyzer with a sample YouTube URL.
    """
    # Sample YouTube URL - feel free to change this to any public YouTube video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"Testing YouTube URL detection with: {test_url}")
    is_youtube = is_youtube_url(test_url)
    print(f"Is YouTube URL: {is_youtube}")
    
    if is_youtube:
        print(f"Analyzing YouTube video: {test_url}")
        result = analyze_youtube_video(test_url)
        
        if result:
            print("\nAnalysis Result:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Analysis failed.")
    else:
        print("URL is not recognized as a YouTube URL.")
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(f"Testing with provided URL: {test_url}")
        
        is_youtube = is_youtube_url(test_url)
        print(f"Is YouTube URL: {is_youtube}")
        
        if is_youtube:
            print(f"Analyzing YouTube video: {test_url}")
            result = analyze_youtube_video(test_url)
            
            if result:
                print("\nAnalysis Result:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print("Analysis failed.")
        else:
            print("URL is not recognized as a YouTube URL.")
    else:
        test_youtube_analyzer() 