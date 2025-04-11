"""
Text Prompt Module

This module provides the system instruction for text analysis with LangChain.
"""

# System instruction for text analysis
TEXT_SYSTEM_INSTRUCTION = """
Lütfen bu web sayfasının içeriğini analiz ederek aşağıdaki bilgileri JSON formatında döndür:

1. Sayfanın başlığı (title)
2. Sayfanın detaylı bir açıklaması (description) - Uzunluğa dikkat etmeden, sayfanın içeriğini kapsamlı bir şekilde özetleyen bir açıklama yaz
3. Sayfanın içeriğine uygun kategoriler ve alt kategoriler (en az 2-3 kategori öner)
4. Sayfanın içeriğiyle ilgili anahtar kelimeler/etiketler (tags)

Önemli Kurallar:
- Açıklama (description) alanı için uzunluk sınırlaması yoktur. Sayfanın içeriğini en iyi şekilde temsil eden, detaylı bir özet yaz.
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

İçerik Türü ve Uygun Kategori Örnekleri:
- Yazılım şirketi: Teknoloji > Yazılım Geliştirme, İş Dünyası > Kurumsal Çözümler, Bilişim > Dijital Hizmetler
- E-ticaret sitesi: Alışveriş > Online Mağaza, E-ticaret > Ürün Satışı, Tüketici > Alışveriş Deneyimi
- Haber sitesi: Haber > Güncel Haberler, Medya > Haber Portalı, Bilgi > Güncel Bilgiler
- Eğitim platformu: Eğitim > Online Kurslar, Eğitim > Eğitim Teknolojileri, Kişisel Gelişim > Öğrenme
- Kişisel blog: Blog > Kişisel Deneyimler, Kişisel > Yaşam Tarzı, Sosyal > Kişisel Paylaşımlar
- Sağlık sitesi: Sağlık > Tıbbi Bilgiler, Sağlık > Sağlıklı Yaşam, Yaşam > Sağlık Önerileri
- Finans sitesi: Finans > Yatırım, Ekonomi > Finansal Hizmetler, İş Dünyası > Finans Yönetimi

Yanıtını tam olarak aşağıdaki JSON formatında ver, LangChain tarafından doğrudan işlenebilmesi için bu yapıya kesinlikle uy:

```json
{
  "title": "Sayfa Başlığı",
  "description": "Sayfanın detaylı açıklaması - uzunluk sınırı olmadan, içeriği kapsamlı şekilde özetleyen bir metin",
  "categories": [
    {
      "main": "Ana Kategori 1",
      "sub": "Alt Kategori 1"
    },
    {
      "main": "Ana Kategori 2",
      "sub": "Alt Kategori 2"
    },
    {
      "main": "Ana Kategori 3",
      "sub": "Alt Kategori 3"
    }
  ],
  "tags": ["etiket1", "etiket2", "etiket3", "etiket4", "etiket5", "etiket6", "etiket7", "etiket8", "etiket9", "etiket10"]
}
```

ÖNEMLİ:
1. JSON çıktında `categories` içindeki objelerde `main_category` ve `subcategory` değil, `main` ve `sub` alanları kullanmalısın.
2. Yanıtında kesinlikle ekstra metin olmamalı, sadece geçerli JSON formatı olmalıdır.
3. Çift tırnak işaretlerini (") kullan, tek tırnak işaretlerini (') kullanma.
4. Çıktı tamamen bu formatla eşleşmeli ve geçerli JSON olmalıdır.

Lütfen kategori ve alt kategori seçimlerinde mevcut kategorileri kullanmaya çalış. Eğer mevcut kategoriler arasında uygun bir eşleşme bulamazsan, içeriğe uygun yeni kategori öner.

Önemli: İçeriğin kısmen ilgili olabileceği kategorileri de öner. Her sayfa için en az 2-3 kategori önermeye çalış. Eğer içerik çok spesifik değilse, daha genel kategorileri de kullanabilirsin.
"""

IMAGE_SYSTEM_INSTRUCTION = """
Lütfen bu web sayfasını analiz ederek aşağıdaki bilgileri JSON formatında döndür:

1. Sayfanın başlığı (title)
2. Sayfanın detaylı bir açıklaması (description) - Uzunluğa dikkat etmeden, sayfanın içeriğini kapsamlı bir şekilde özetleyen bir açıklama yaz
3. Sayfanın içeriğine uygun kategoriler ve alt kategoriler (en az 2-3 kategori öner)
4. Sayfanın içeriğiyle ilgili anahtar kelimeler/etiketler (tags)

Önemli Kurallar:
- Açıklama (description) alanı için uzunluk sınırlaması yoktur. Sayfanın içeriğini en iyi şekilde temsil eden, detaylı bir özet yaz.
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

Yanıtını tam olarak aşağıdaki JSON formatında ver, LangChain tarafından doğrudan işlenebilmesi için bu yapıya kesinlikle uy:

```json
{
  "title": "Sayfa Başlığı",
  "description": "Sayfanın detaylı açıklaması - uzunluk sınırı olmadan, içeriği kapsamlı şekilde özetleyen bir metin",
  "categories": [
    {
      "main": "Ana Kategori 1",
      "sub": "Alt Kategori 1"
    },
    {
      "main": "Ana Kategori 2",
      "sub": "Alt Kategori 2"
    },
    {
      "main": "Ana Kategori 3",
      "sub": "Alt Kategori 3"
    }
  ],
  "tags": ["etiket1", "etiket2", "etiket3", "etiket4", "etiket5", "etiket6", "etiket7", "etiket8", "etiket9", "etiket10"]
}
```

ÖNEMLİ:
1. JSON çıktında `categories` içindeki objelerde `main_category` ve `subcategory` değil, `main` ve `sub` alanları kullanmalısın.
2. Yanıtında kesinlikle ekstra metin olmamalı, sadece geçerli JSON formatı olmalıdır.
3. Çift tırnak işaretlerini (") kullan, tek tırnak işaretlerini (') kullanma.
4. Çıktı tamamen bu formatla eşleşmeli ve geçerli JSON olmalıdır.

Lütfen kategori ve alt kategori seçimlerinde mevcut kategorileri kullanmaya çalış. Eğer mevcut kategoriler arasında uygun bir eşleşme bulamazsan, içeriğe uygun yeni kategori öner.

Önemli: İçeriğin kısmen ilgili olabileceği kategorileri de öner. Her sayfa için en az 2-3 kategori önermeye çalış. Eğer içerik çok spesifik değilse, daha genel kategorileri de kullanabilirsin.

Görüntüdeki metinleri ve görselleri dikkate alarak en doğru kategorilemeyi yap.
""" 