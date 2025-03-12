// Tag Utilities
// Handles tag formatting and manipulation

const TagUtils = {
    formatTag(tagText) {
        // Convert tag to lowercase and remove # prefix
        return tagText.toLowerCase().replace(/^#/, '');
    },
    
    addTag(container, tagText) {
        const formattedTag = this.formatTag(tagText);
        const tagElement = document.createElement('span');
        tagElement.className = 'tag';
        tagElement.textContent = formattedTag;
        container.appendChild(tagElement);
    },
    
    editTags(card) {
        const tagsContainer = card.querySelector('.tags');
        const currentTags = Array.from(tagsContainer.querySelectorAll('.tag'))
            .map(tag => tag.textContent);
        
        // Show current tags in edit modal
        console.log('Current tags:', currentTags);
        
        // Use formatTag function when editing tags
        // Modal implementation...
    },
    
    createTagItem(tag) {
        return `
            <div class="tag-item">
                ${tag}
                <button class="remove-btn" onclick="TagUtils.removeItem(this, 'tag')">
                    <i class="material-icons">close</i>
                </button>
            </div>
        `;
    },
    
    createTagLink(tag) {
        return `
            <a href="tagged-bookmarks.html?tag=${encodeURIComponent(tag)}" 
               class="tag">
                ${tag}
            </a>
        `;
    },
    
    removeItem(button, type) {
        button.closest(`.${type}-item`).remove();
    }
}; 