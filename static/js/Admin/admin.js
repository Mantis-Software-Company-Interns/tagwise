/**
 * Admin Panel için JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Temizleme butonuna tıklandığında onay iste
    const cleanBtn = document.querySelector('.clean-btn');
    if (cleanBtn) {
        cleanBtn.addEventListener('click', function(e) {
            if (!confirm('Kullanılmayan tüm etiketleri ve kategorileri silmek istediğinizden emin misiniz?')) {
                e.preventDefault();
            }
        });
    }
}); 