"""
Django Setup Module

This module provides functions for setting up the Django environment.
"""

import os
import sys
import django

def setup_django():
    """
    Set up the Django environment for standalone scripts.
    
    This function adds the project directory to the Python path and configures
    Django settings for use in standalone scripts.
    """
    # Django projesinin ana dizinini bul
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_dir)  # reader'ın üst dizini (tagwiseapp)
    project_dir = os.path.dirname(app_dir)  # tagwiseapp'in üst dizini
    
    # Django ayarlarını yükle
    if project_dir not in sys.path:
        sys.path.append(project_dir)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tagwisebackend.settings')
    
    # Django'yu başlat
    django.setup()
    print("Django ortamı başlatıldı.")

if __name__ == "__main__":
    # Test için
    setup_django()
    print("Django setup modülü test edildi.") 