# TagWise API Kullanım Rehberi

Bu doküman, Tagwise API servislerinin kullanımını açıklar. Bu API, harici sistemlerin (örneğin blog siteleri) TagWise'ın içerik kategorizasyon özelliklerini kullanarak bookmarklar oluşturmasına olanak tanır.

## Kimlik Doğrulama

Tüm API çağrıları için API anahtarı kullanılarak kimlik doğrulaması yapılmalıdır. API anahtarınızı yönetici panelinden alabilirsiniz.

API anahtarını HTTP isteğinin `X-API-Key` başlığında göndermelisiniz:

```
X-API-Key: YOUR_API_KEY_HERE
```

## API Endpoint'leri

### 1. İçerik Kategorizasyonu

İçeriği analiz ederek kategori ve etiket önerilerini almak için kullanılır. İçerik veritabanına kaydedilmez.

**Endpoint:** `/api/categorize/`  
**Method:** POST  
**Parametreler:**

```json
{
  "content": "İçerik metni burada olacak",
  "url": "https://example.com/blog-post",
  "title": "İçerik başlığı",
  "format": "flat",
  "external_categories": ["Kategori1", "Kategori2"]
}
```

**Yanıt:**

```json
{
  "categories": [
    {
      "id": 1,
      "name": "Programlama"
    },
    {
      "id": 2,
      "name": "Python"
    }
  ],
  "tags": ["python", "programlama", "yazılım"]
}
```

### 2. Bookmark Oluşturma

Harici bir sistemden gelen içeriği analiz ederek kategori ve etiket önerileri yapar ve içeriği bookmark olarak kaydeder.

**Endpoint:** `/api/create-bookmark/`  
**Method:** POST  
**Parametreler:**

```json
{
  "url": "https://example.com/blog-post",
  "title": "Blog Post Başlığı",
  "content": "İçerik metni burada olacak...",
  "description": "İçerik açıklaması (opsiyonel)",
  "external_categories": ["Kategori1", "Kategori2"],
  "external_tags": ["etiket1", "etiket2"]
}
```

**Yanıt:**

```json
{
  "success": true,
  "bookmark_id": 123,
  "url": "https://example.com/blog-post",
  "title": "Blog Post Başlığı",
  "description": "İçerik açıklaması",
  "analysis_result": {
    "categories": [
      {
        "main": "Teknoloji",
        "sub": "Yazılım",
        "main_id": 1,
        "sub_id": 2
      },
      {
        "main": "Eğitim",
        "sub": "Programlama",
        "main_id": 3,
        "sub_id": 4
      }
    ],
    "tags": [
      {
        "name": "python",
        "id": 1
      },
      {
        "name": "web",
        "id": 2
      },
      {
        "name": "django",
        "id": 3
      }
    ],
    "title": "Blog Post Başlığı",
    "description": "Django ve Flask kullanarak web uygulamaları geliştirme"
  }
}
```

### 3. Kategori Listesi

Sistemdeki tüm kategorileri listeler.

**Endpoint:** `/api/category-list/`  
**Method:** GET  
**Yanıt:**

```json
{
  "main_categories": [
    {
      "id": 1,
      "name": "Teknoloji",
      "subcategories": [
        {
          "id": 2,
          "name": "Yazılım"
        },
        {
          "id": 3,
          "name": "Donanım"
        }
      ]
    }
  ]
}
```

## Örnek Curl Komutları

### Kategorize Etme

```bash
curl -X POST \
  https://your-domain.com/api/categorize/ \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: YOUR_API_KEY_HERE' \
  -d '{
    "content": "Python programlama dili ile web uygulamaları geliştirme hakkında bir blog yazısı...",
    "url": "https://example.com/python-web-development",
    "title": "Python ile Web Geliştirme"
  }'
```

### Bookmark Oluşturma

```bash
curl -X POST \
  https://your-domain.com/api/create-bookmark/ \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: YOUR_API_KEY_HERE' \
  -d '{
    "url": "https://example.com/python-web-development",
    "title": "Python ile Web Geliştirme",
    "content": "Python programlama dili ile web uygulamaları geliştirme hakkında bir blog yazısı...",
    "description": "Django ve Flask kullanarak web uygulamaları geliştirme",
    "external_tags": ["python", "web", "django"]
  }'
```

### Kategori Listesi Alma

```bash
curl -X GET \
  https://your-domain.com/api/category-list/ \
  -H 'X-API-Key: YOUR_API_KEY_HERE'
```

## Hata Kodları

- **400**: İstek parametreleri geçersiz
- **401**: Kimlik doğrulama başarısız
- **403**: API anahtarı yetkisiz
- **500**: Sunucu hatası

## Notlar

- API anahtarlarının güvenliği kullanıcı sorumluluğundadır
- Günlük istek limitleri uygulanabilir
- İçerik uzunluğu maksimum 100,000 karakter olabilir 