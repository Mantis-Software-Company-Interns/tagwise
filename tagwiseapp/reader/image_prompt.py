"""
Image Prompt Module

This module provides the system instruction for image analysis with Gemini AI.
"""

# System instruction for image analysis
IMAGE_SYSTEM_INSTRUCTION = """
Lütfen bu web sayfasını analiz ederek aşağıdaki bilgileri JSON formatında döndür:

1. Sayfanın başlığı (title)
2. Sayfanın kısa bir açıklaması (description)
3. Sayfanın içeriğine uygun kategoriler ve alt kategoriler (en az 2-3 kategori öner)
4. Sayfanın içeriğiyle ilgili anahtar kelimeler/etiketler (tags)

Önemli Kurallar:
- Kategorileri belirlerken sayfanın içeriğiyle ilgili olabilecek tüm kategorileri düşün. Doğrudan ilgili olmasa bile, kısmen ilgili olabilecek kategorileri de öner.
- Her sayfa için en az 2-3 kategori önermeye çalış.
- Yazılım şirketleri için "Teknoloji", "Yazılım", "Bilişim" gibi kategoriler kullan.
- Eğitim siteleri için "Eğitim" ana kategorisini kullan.
- Haber siteleri için "Haber" veya "Medya" kategorilerini kullan.
- E-ticaret siteleri için "Alışveriş" veya "E-ticaret" kategorilerini kullan.
- Kişisel bloglar için "Blog" veya "Kişisel" kategorilerini kullan.
- Sanat ve tasarım siteleri için "Sanat", "Tasarım" kategorilerini kullan.
- Her kategori için mutlaka bir alt kategori belirle.
- Etiketler, sayfanın içeriğindeki önemli anahtar kelimeleri içermeli.
- ÖNEMLİ: Aynı alt kategoriyi farklı ana kategorilere ATAMA. Her alt kategori yalnızca bir ana kategori altında olmalıdır.

Yanıtını aşağıdaki JSON formatında ver:

```json
{
  "title": "Sayfa Başlığı",
  "description": "Sayfanın kısa açıklaması",
  "categories": [
    {
      "main_category": "Ana Kategori 1",
      "subcategory": "Alt Kategori 1"
    },
    {
      "main_category": "Ana Kategori 2",
      "subcategory": "Alt Kategori 2"
    },
    {
      "main_category": "Ana Kategori 3",
      "subcategory": "Alt Kategori 3"
    }
  ],
  "tags": ["etiket1", "etiket2", "etiket3", "etiket4", "etiket5", "etiket6"]
}
```

Lütfen kategori ve alt kategori seçimlerinde mevcut kategorileri kullanmaya çalış. Eğer mevcut kategoriler arasında uygun bir eşleşme bulamazsan, içeriğe uygun yeni kategori öner.

Önemli: İçeriğin kısmen ilgili olabileceği kategorileri de öner. Her sayfa için en az 2-3 kategori önermeye çalış. Eğer içerik çok spesifik değilse, daha genel kategorileri de kullanabilirsin.
""" 