#!/usr/bin/env python
"""
Gemini API ayarlarını komut satırından yapılandırmak için CLI aracı.
"""

import os
import sys
import django
import time

# Django ortamını başlat
def setup_django():
    # Django projesinin ana dizinini bul
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)  # tagwiseapp'in üst dizini
    
    # Django ayarlarını yükle
    if project_dir not in sys.path:
        sys.path.append(project_dir)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tagwisebackend.settings')
    
    # Django'yu başlat
    django.setup()
    print("Django ortamı başlatıldı.")

# Django ortamını başlat
setup_django()

# Gemini config'i içe aktar
from tagwiseapp.config_manager import config as gemini_config

def main():
    """Ana fonksiyon."""
    print("Gemini API Ayarları Yapılandırma Aracı")
    print("--------------------------------------")
    
    # Kullanıcıya seçenekler sun
    print("\nNe yapmak istersiniz?")
    print("1. Mevcut ayarları görüntüle")
    print("2. Ayarları yapılandır")
    print("3. Ayarları varsayılanlara sıfırla")
    print("4. Çıkış")
    
    choice = input("\nSeçiminiz (1-4): ").strip()
    
    if choice == "1":
        show_current_settings()
    elif choice == "2":
        configure_settings()
    elif choice == "3":
        reset_settings()
    elif choice == "4":
        print("Programdan çıkılıyor...")
        return
    else:
        print("Geçersiz seçim. Lütfen 1-4 arasında bir değer girin.")
        main()  # Ana menüye dön

def show_current_settings():
    """Mevcut ayarları görüntüler."""
    print("\nMevcut Gemini API Ayarları:")
    print("--------------------------")
    
    current_config = gemini_config.config
    
    print(f"\nTemel Ayarlar:")
    print(f"  Temperature: {current_config.get('temperature', 0.4)}")
    print(f"  Top P: {current_config.get('top_p', 0.95)}")
    print(f"  Top K: {current_config.get('top_k', 40)}")
    print(f"  Max Output Tokens: {current_config.get('max_output_tokens', 2048)}")
    
    print(f"\nGüvenlik Ayarları:")
    safety_settings = current_config.get('safety_settings', {})
    safety_labels = {
        'block_none': 'Engelleme Yok',
        'block_low_and_above': 'Düşük ve Üzeri Engelle',
        'block_medium_and_above': 'Orta ve Üzeri Engelle',
        'block_high_only': 'Sadece Yüksek Engelle'
    }
    
    print(f"  Taciz İçeriği: {safety_labels.get(safety_settings.get('harassment', 'block_medium_and_above'), 'Orta ve Üzeri Engelle')}")
    print(f"  Nefret Söylemi: {safety_labels.get(safety_settings.get('hate_speech', 'block_medium_and_above'), 'Orta ve Üzeri Engelle')}")
    print(f"  Cinsel İçerik: {safety_labels.get(safety_settings.get('sexually_explicit', 'block_medium_and_above'), 'Orta ve Üzeri Engelle')}")
    print(f"  Tehlikeli İçerik: {safety_labels.get(safety_settings.get('dangerous', 'block_medium_and_above'), 'Orta ve Üzeri Engelle')}")
    
    # Ana menüye dön
    input("\nAna menüye dönmek için Enter tuşuna basın...")
    main()

def configure_settings():
    """Ayarları yapılandırır."""
    print("\nGemini API Ayarlarını Yapılandır")
    print("-------------------------------")
    
    # Mevcut ayarları göster
    current_config = gemini_config.config
    print("\nMevcut Ayarlar:")
    print(f"Temperature: {current_config.get('temperature', 0.4)}")
    print(f"Top P: {current_config.get('top_p', 0.95)}")
    print(f"Top K: {current_config.get('top_k', 40)}")
    print(f"Max Output Tokens: {current_config.get('max_output_tokens', 2048)}")
    
    print("\nAyarları değiştirmek için yeni değerleri girin (değiştirmek istemediğiniz ayarlar için boş bırakın):")
    
    # Yeni değerleri al
    new_config = {}
    
    temp = input(f"Temperature (0.0-1.0) [{current_config.get('temperature', 0.4)}]: ").strip()
    if temp:
        try:
            temp_value = float(temp)
            if 0.0 <= temp_value <= 1.0:
                new_config['temperature'] = temp_value
            else:
                print("Geçersiz değer. Temperature 0.0 ile 1.0 arasında olmalıdır.")
        except ValueError:
            print("Geçersiz değer. Lütfen bir sayı girin.")
    
    top_p = input(f"Top P (0.0-1.0) [{current_config.get('top_p', 0.95)}]: ").strip()
    if top_p:
        try:
            top_p_value = float(top_p)
            if 0.0 <= top_p_value <= 1.0:
                new_config['top_p'] = top_p_value
            else:
                print("Geçersiz değer. Top P 0.0 ile 1.0 arasında olmalıdır.")
        except ValueError:
            print("Geçersiz değer. Lütfen bir sayı girin.")
    
    top_k = input(f"Top K (1-100) [{current_config.get('top_k', 40)}]: ").strip()
    if top_k:
        try:
            top_k_value = int(top_k)
            if 1 <= top_k_value <= 100:
                new_config['top_k'] = top_k_value
            else:
                print("Geçersiz değer. Top K 1 ile 100 arasında olmalıdır.")
        except ValueError:
            print("Geçersiz değer. Lütfen bir tam sayı girin.")
    
    max_tokens = input(f"Max Output Tokens (1-8192) [{current_config.get('max_output_tokens', 2048)}]: ").strip()
    if max_tokens:
        try:
            max_tokens_value = int(max_tokens)
            if 1 <= max_tokens_value <= 8192:
                new_config['max_output_tokens'] = max_tokens_value
            else:
                print("Geçersiz değer. Max Output Tokens 1 ile 8192 arasında olmalıdır.")
        except ValueError:
            print("Geçersiz değer. Lütfen bir tam sayı girin.")
    
    # Güvenlik ayarları
    print("\nGüvenlik Ayarları:")
    safety_settings = {}
    safety_options = [
        ('block_none', 'Engelleme Yok'),
        ('block_low_and_above', 'Düşük ve Üzeri Engelle'),
        ('block_medium_and_above', 'Orta ve Üzeri Engelle'),
        ('block_high_only', 'Sadece Yüksek Engelle')
    ]
    
    # Mevcut güvenlik ayarlarını göster
    current_safety = current_config.get('safety_settings', {})
    
    # Taciz İçeriği
    print("\nTaciz İçeriği için engelleme seviyesi:")
    for i, (value, label) in enumerate(safety_options, 1):
        print(f"{i}. {label}" + (" (mevcut)" if current_safety.get('harassment') == value else ""))
    
    choice = input("Seçiminiz (1-4, boş bırakırsanız değişmez): ").strip()
    if choice and choice.isdigit() and 1 <= int(choice) <= 4:
        safety_settings['harassment'] = safety_options[int(choice) - 1][0]
    
    # Nefret Söylemi
    print("\nNefret Söylemi için engelleme seviyesi:")
    for i, (value, label) in enumerate(safety_options, 1):
        print(f"{i}. {label}" + (" (mevcut)" if current_safety.get('hate_speech') == value else ""))
    
    choice = input("Seçiminiz (1-4, boş bırakırsanız değişmez): ").strip()
    if choice and choice.isdigit() and 1 <= int(choice) <= 4:
        safety_settings['hate_speech'] = safety_options[int(choice) - 1][0]
    
    # Cinsel İçerik
    print("\nCinsel İçerik için engelleme seviyesi:")
    for i, (value, label) in enumerate(safety_options, 1):
        print(f"{i}. {label}" + (" (mevcut)" if current_safety.get('sexually_explicit') == value else ""))
    
    choice = input("Seçiminiz (1-4, boş bırakırsanız değişmez): ").strip()
    if choice and choice.isdigit() and 1 <= int(choice) <= 4:
        safety_settings['sexually_explicit'] = safety_options[int(choice) - 1][0]
    
    # Tehlikeli İçerik
    print("\nTehlikeli İçerik için engelleme seviyesi:")
    for i, (value, label) in enumerate(safety_options, 1):
        print(f"{i}. {label}" + (" (mevcut)" if current_safety.get('dangerous') == value else ""))
    
    choice = input("Seçiminiz (1-4, boş bırakırsanız değişmez): ").strip()
    if choice and choice.isdigit() and 1 <= int(choice) <= 4:
        safety_settings['dangerous'] = safety_options[int(choice) - 1][0]
    
    # Güvenlik ayarlarını ekle
    if safety_settings:
        new_config['safety_settings'] = safety_settings
    
    # Ayarları güncelle
    if new_config:
        gemini_config.update_config(new_config)
        print("\nAyarlar başarıyla güncellendi.")
    else:
        print("\nHerhangi bir ayar değiştirilmedi.")
    
    # Ana menüye dön
    input("\nAna menüye dönmek için Enter tuşuna basın...")
    main()

def reset_settings():
    """Ayarları varsayılanlara sıfırlar."""
    print("\nAyarları Varsayılanlara Sıfırla")
    print("------------------------------")
    
    confirm = input("Tüm ayarları varsayılan değerlere sıfırlamak istediğinizden emin misiniz? (e/h): ").strip().lower()
    
    if confirm == 'e':
        gemini_config.reset_to_defaults()
        print("Ayarlar varsayılan değerlere sıfırlandı.")
    else:
        print("İşlem iptal edildi.")
    
    # Ana menüye dön
    input("\nAna menüye dönmek için Enter tuşuna basın...")
    main()

if __name__ == "__main__":
    main() 