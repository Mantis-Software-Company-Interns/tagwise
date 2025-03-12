function showTab(tabName) {
    // Tüm formları gizle
    document.querySelectorAll('.form').forEach(form => {
        form.classList.remove('active');
    });
    
    // Tüm tab butonlarından active sınıfını kaldır
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Seçili formu ve tab butonunu aktif yap
    document.getElementById(`${tabName}-form`).classList.add('active');
    document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
}

// Sayfa yüklendiğinde varsayılan olarak signin tabını göster
document.addEventListener('DOMContentLoaded', () => {
    showTab('signin');
}); 