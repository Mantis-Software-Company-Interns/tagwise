"""
Screenshot Module

This module provides functions for capturing screenshots of web pages using Selenium.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capture_screenshot(url):
    """
    Selenium ile URL'nin ekran görüntüsünü alır.
    
    Args:
        url (str): Ekran görüntüsü alınacak sayfanın URL'si
        
    Returns:
        bytes or None: Başarılı olursa ekran görüntüsü bytes olarak, başarısız olursa None
    """
    # Add https:// protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        print(f"URL'ye protokol eklendi: {url}")
        
    print(f"Selenium ile ekran görüntüsü alınıyor: {url}")
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(("tag name", "body"))
        )
        
        screenshot = driver.get_screenshot_as_png()
        return screenshot
        
    except WebDriverException as e:
        print(f"Selenium WebDriver hatası: {e}")
        return None
    except TimeoutException as e:
        print(f"Sayfa yükleme zaman aşımı: {e}")
        return None
    except Exception as e:
        print(f"Ekran görüntüsü alırken beklenmeyen hata: {str(e)}")
        return None
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    # Test için
    test_url = "www.example.com"  # Protocol missing
    screenshot = capture_screenshot(test_url)
    if screenshot:
        print(f"Ekran görüntüsü başarıyla alındı. Boyut: {len(screenshot)} bytes")
        # Test için görüntüyü kaydet
        with open("test_screenshot.png", "wb") as f:
            f.write(screenshot)
        print("Ekran görüntüsü test_screenshot.png olarak kaydedildi.")
    else:
        print("Ekran görüntüsü alınamadı.") 