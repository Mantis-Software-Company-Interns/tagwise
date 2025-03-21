/**
 * Admin Panel için JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin JS loaded');
    
    // Temizleme butonuna tıklandığında onay iste
    const cleanBtn = document.querySelector('.clean-btn');
    if (cleanBtn) {
        cleanBtn.addEventListener('click', function(e) {
            if (!confirm('Kullanılmayan tüm etiketleri ve kategorileri silmek istediğinizden emin misiniz?')) {
                e.preventDefault();
            }
        });
    }
    
    // Delete All Bookmarks modal functionality
    const deleteAllBtn = document.getElementById('deleteAllBookmarksBtn');
    const deleteAllModal = document.getElementById('deleteAllBookmarksModal');
    
    console.log('Delete All Button exists:', !!deleteAllBtn);
    console.log('Delete Modal exists:', !!deleteAllModal);
    
    if (deleteAllBtn && deleteAllModal) {
        // Open modal when delete all button is clicked
        deleteAllBtn.addEventListener('click', function() {
            console.log('Delete All button clicked');
            deleteAllModal.style.display = 'flex';
            deleteAllModal.classList.add('active'); // Add active class for CSS transitions
            document.body.style.overflow = 'hidden'; // Prevent scrolling when modal is open
        });
        
        // Modal içindeki butonlar
        const closeModalBtn = deleteAllModal.querySelector('.close-btn');
        const cancelBtn = deleteAllModal.querySelector('.cancel-btn');
        const deleteForm = deleteAllModal.querySelector('form');
        
        console.log('Close button exists:', !!closeModalBtn);
        console.log('Cancel button exists:', !!cancelBtn);
        console.log('Delete form exists:', !!deleteForm);
        
        // Helper function to close modal
        function closeModal() {
            deleteAllModal.style.display = 'none';
            deleteAllModal.classList.remove('active');
            document.body.style.overflow = ''; // Re-enable scrolling
        }
        
        // Close modal with X button
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', function() {
                console.log('Close button clicked');
                closeModal();
            });
        }
        
        // Close modal with Cancel button
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                console.log('Cancel button clicked');
                closeModal();
            });
        }
        
        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === deleteAllModal) {
                console.log('Clicked outside modal');
                closeModal();
            }
        });
        
        // Handle form submission
        if (deleteForm) {
            deleteForm.addEventListener('submit', function(e) {
                console.log('Delete form submitted');
                // Additional confirmation if needed
                if (!confirm('Bu işlem tüm bookmarkları kalıcı olarak silecektir. Devam etmek istediğinizden emin misiniz?')) {
                    e.preventDefault();
                    return false;
                }
                
                // Close modal after confirmation
                closeModal();
            });
        }
    }
}); 