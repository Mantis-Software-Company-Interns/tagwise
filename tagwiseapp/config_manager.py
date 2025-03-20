import os
import json
import logging
from pathlib import Path

# Logging yapılandırması
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiConfig:
    """Gemini API yapılandırma yöneticisi."""
    
    # Varsayılan yapılandırma
    DEFAULT_CONFIG = {
        'temperature': 0.4,
        'top_p': 0.95,
        'top_k': 40,
        'max_output_tokens': 2048,
        'safety_settings': {
            'harassment': 'block_medium_and_above',
            'hate_speech': 'block_medium_and_above',
            'sexually_explicit': 'block_medium_and_above',
            'dangerous': 'block_medium_and_above'  # 'dangerous_content' yerine 'dangerous' kullanıyoruz
        }
    }
    
    def __init__(self, config_file=None):
        """
        Gemini yapılandırma yöneticisini başlatır.
        
        Args:
            config_file (str, optional): Yapılandırma dosyasının yolu. Belirtilmezse varsayılan konum kullanılır.
        """
        # Yapılandırma dosyasının yolunu belirle
        if config_file is None:
            # Proje kök dizinini bul
            base_dir = Path(__file__).resolve().parent.parent
            self.config_file = os.path.join(base_dir, 'gemini_config.json')
        else:
            self.config_file = config_file
        
        # Yapılandırmayı yükle
        self.config = self._load_config()
    
    def _load_config(self):
        """
        Yapılandırma dosyasını yükler. Dosya yoksa varsayılan yapılandırmayı kullanır.
        
        Returns:
            dict: Yüklenen yapılandırma.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Eski güvenlik ayarlarını yeni formata dönüştür
                if 'safety_settings' in config:
                    if 'dangerous_content' in config['safety_settings']:
                        config['safety_settings']['dangerous'] = config['safety_settings'].pop('dangerous_content')
                
                logger.info(f"Yapılandırma dosyası yüklendi: {self.config_file}")
                return config
            else:
                # Dosya yoksa varsayılan yapılandırmayı kaydet
                self._save_config(self.DEFAULT_CONFIG)
                logger.info(f"Varsayılan yapılandırma oluşturuldu: {self.config_file}")
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Yapılandırma yüklenirken hata oluştu: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config):
        """
        Yapılandırmayı dosyaya kaydeder.
        
        Args:
            config (dict): Kaydedilecek yapılandırma.
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Yapılandırma dosyaya kaydedildi: {self.config_file}")
        except Exception as e:
            logger.error(f"Yapılandırma kaydedilirken hata oluştu: {e}")
    
    def update_config(self, new_config):
        """
        Mevcut yapılandırmayı günceller ve kaydeder.
        
        Args:
            new_config (dict): Yeni yapılandırma değerleri.
        """
        # Mevcut yapılandırmayı güncelle
        for key, value in new_config.items():
            if key == 'safety_settings' and isinstance(value, dict):
                # Güvenlik ayarlarını güncelle
                if 'safety_settings' not in self.config:
                    self.config['safety_settings'] = {}
                
                # Eski 'dangerous_content' anahtarını 'dangerous' olarak güncelle
                if 'dangerous_content' in value:
                    value['dangerous'] = value.pop('dangerous_content')
                
                for setting_key, setting_value in value.items():
                    self.config['safety_settings'][setting_key] = setting_value
            else:
                self.config[key] = value
        
        # Güncellenmiş yapılandırmayı kaydet
        self._save_config(self.config)
        logger.info("Yapılandırma güncellendi")
    
    def reset_to_defaults(self):
        """Yapılandırmayı varsayılan değerlere sıfırlar."""
        self.config = self.DEFAULT_CONFIG.copy()
        self._save_config(self.config)
        logger.info("Yapılandırma varsayılan değerlere sıfırlandı")
    
    def get_generation_config(self):
        """
        Gemini API için generation_config parametrelerini döndürür.
        
        Returns:
            dict: Generation config parametreleri.
        """
        return {
            'temperature': self.config.get('temperature', self.DEFAULT_CONFIG['temperature']),
            'top_p': self.config.get('top_p', self.DEFAULT_CONFIG['top_p']),
            'top_k': self.config.get('top_k', self.DEFAULT_CONFIG['top_k']),
            'max_output_tokens': self.config.get('max_output_tokens', self.DEFAULT_CONFIG['max_output_tokens']),
        }
    
    def get_safety_settings(self):
        """
        Gemini API için safety_settings parametrelerini döndürür.
        
        Returns:
            dict: Safety settings parametreleri.
        """
        default_safety = self.DEFAULT_CONFIG['safety_settings']
        config_safety = self.config.get('safety_settings', {})
        
        # Eski 'dangerous_content' anahtarını 'dangerous' olarak güncelle
        if 'dangerous_content' in config_safety:
            config_safety['dangerous'] = config_safety.pop('dangerous_content')
        
        # Varsayılan güvenlik ayarlarını kullan, ancak yapılandırmada belirtilen değerleri öncelikle kullan
        safety_settings = default_safety.copy()
        for key, value in config_safety.items():
            safety_settings[key] = value
        
        return safety_settings

# Singleton örneği oluştur
config = GeminiConfig() 