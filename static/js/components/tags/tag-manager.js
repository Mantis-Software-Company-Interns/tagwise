// Tag Manager
// Handles tag operations (add, edit, delete)

const TagManager = {
    initialize() {
        // Initialize tag editing functionality
        this.setupTagEditing();
    },

    setupTagEditing() {
        // Edit tags button
        document.querySelectorAll('.edit-tags-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const card = btn.closest('.bookmark-card');
                if (card) {
                    this.editTags(card);
                }
            });
        });
    },

    editTags(card) {
        if (!card) return;
        
        const tagsContainer = card.querySelector('.card-tags');
        if (!tagsContainer) return;
        
        // Get current tags
        const currentTags = Array.from(tagsContainer.querySelectorAll('.tag')).map(tag => tag.textContent);
        
        // Prompt for new tags
        const newTagsInput = prompt('Edit tags (comma separated):', currentTags.join(', '));
        
        if (newTagsInput === null) return; // User cancelled
        
        // Process new tags
        const newTags = newTagsInput.split(',')
            .map(tag => tag.trim())
            .filter(tag => tag.length > 0);
        
        // Update bookmark with new tags
        this.updateBookmarkTags(card.dataset.id, newTags, card);
    },

    updateBookmarkTags(bookmarkId, tags, card) {
        if (!bookmarkId || !card) return;
        
        // Prepare data for submission
        const formData = new FormData();
        formData.append('id', bookmarkId);
        formData.append('tags', JSON.stringify(tags));
        
        // Send AJAX request
        fetch('/update-tags/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI
                const tagsContainer = card.querySelector('.card-tags');
                if (tagsContainer) {
                    tagsContainer.innerHTML = tags.map(tag => 
                        `<a href="/tags/?tag=${encodeURIComponent(tag)}" class="tag">${this.formatTag(tag)}</a>`
                    ).join('');
                }
                
                // Show success message
                alert('Tags updated successfully!');
            } else {
                alert('Error updating tags: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while updating tags.');
        });
    },

    formatTag(tagText) {
        // Format tag text (e.g., add # prefix if not present)
        if (!tagText.startsWith('#')) {
            return '#' + tagText;
        }
        return tagText;
    },

    addTag(container, tagText) {
        if (!container || !tagText) return;
        
        const formattedTag = this.formatTag(tagText);
        const tagElement = document.createElement('a');
        
        tagElement.href = `/tags/?tag=${encodeURIComponent(formattedTag)}`;
        tagElement.className = 'tag';
        tagElement.textContent = formattedTag;
        
        container.appendChild(tagElement);
    }
}; 