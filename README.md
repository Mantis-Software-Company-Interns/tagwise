# TagWise - Akıllı Yer İmi Yönetim Sistemi

TagWise, web sayfalarınızı akıllıca organize etmenizi, kategorilendirmenizi ve etiketlemenizi sağlayan modern bir yer imi yönetim sistemidir.

## Özellikler

- 📑 Yer imlerini kategoriler ve alt kategorilerle organize etme
- 🏷️ Etiketleme sistemi ile kolay erişim
- 📸 Web sayfası önizleme görüntüleri
- 📚 Koleksiyonlar oluşturma ve yönetme
- 👤 Kullanıcı profili ve tercihler
- 🔍 Gelişmiş arama ve filtreleme özellikleri

## Kurulum

1. Projeyi klonlayın:
```bash
git clone https://github.com/yourusername/tagwise.git
cd tagwise
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac için
# veya
venv\Scripts\activate  # Windows için
```

3. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

4. Veritabanı migrationlarını yapın:
```bash
python manage.py migrate
```

5. Superuser oluşturun:
```bash
python manage.py createsuperuser
```

6. Uygulamayı çalıştırın:
```bash
python manage.py runserver
```

## Ortam Değişkenleri

Projenin düzgün çalışması için aşağıdaki ortam değişkenlerini `.env` dosyasında tanımlamanız gerekmektedir:

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug modu (True/False)
- `ALLOWED_HOSTS`: İzin verilen host adresleri
- `DATABASE_URL`: Veritabanı bağlantı URL'i (opsiyonel)

## Teknolojiler

- Django
- SQLite (varsayılan veritabanı)
- HTML/CSS/JavaScript
- Bootstrap

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

## Katkıda Bulunma

1. Bu repository'yi fork edin
2. Feature branch'i oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'inizi push edin (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun