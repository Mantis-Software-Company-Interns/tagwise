/**
 * Gemini API Ayarları sayfası için JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Bilgi öğelerinin başlıklarına tıklama işlevselliği ekle
    const infoItems = document.querySelectorAll('.info-item h3');
    
    infoItems.forEach(item => {
        item.addEventListener('click', function() {
            // Bu başlığa ait içerik bölümünü bul
            const content = this.nextElementSibling;
            
            // İçerik görünür mü kontrol et
            const isVisible = content.style.display !== 'none';
            
            // Tüm içerikleri gizle
            document.querySelectorAll('.info-content').forEach(el => {
                el.style.display = 'none';
            });
            
            // Eğer içerik görünür değilse, göster
            if (!isVisible) {
                content.style.display = 'block';
            }
        });
    });
    
    // Sayfa yüklendiğinde tüm içerikleri gizle
    document.querySelectorAll('.info-content').forEach(el => {
        el.style.display = 'none';
    });
    
    // Form gönderildiğinde onay mesajı göster
    const form = document.querySelector('form');
    form.addEventListener('submit', function(e) {
        const isReset = e.submitter && e.submitter.name === 'reset';
        
        if (isReset) {
            if (!confirm('Tüm ayarları varsayılan değerlere sıfırlamak istediğinizden emin misiniz?')) {
                e.preventDefault();
            }
        }
    });
}); 