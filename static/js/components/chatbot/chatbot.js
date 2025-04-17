/**
 * Chatbot functionality for TagWise
 * Connects the chatbot UI to the backend RAG system
 */

class ChatbotManager {
    constructor() {
        // Elements
        this.chatbotToggle = document.querySelector('.chatbot-toggle');
        this.chatbotPanel = document.querySelector('.chatbot-panel');
        this.closeChat = document.querySelector('.close-chat');
        this.resetChat = document.querySelector('.reset-chat');
        this.messagesContainer = document.querySelector('.chatbot-messages');
        this.chatInput = document.querySelector('.chatbot-input input');
        this.sendButton = document.querySelector('.send-message');
        
        // State
        this.isInitialized = false;
        this.isProcessing = false;
        this.apiError = false;
        
        // Bind methods
        this.toggleChatbot = this.toggleChatbot.bind(this);
        this.sendMessage = this.sendMessage.bind(this);
        this.handleInputKeypress = this.handleInputKeypress.bind(this);
        this.resetConversation = this.resetConversation.bind(this);
        
        // Initialize
        this.init();
    }
    
    init() {
        // Add event listeners
        this.chatbotToggle.addEventListener('click', this.toggleChatbot);
        this.closeChat.addEventListener('click', this.toggleChatbot);
        this.sendButton.addEventListener('click', this.sendMessage);
        this.chatInput.addEventListener('keypress', this.handleInputKeypress);
        this.resetChat.addEventListener('click', this.resetConversation);
        
        // Log initial state for debugging
        console.log('Chatbot manager initialized');
        
        // Initialize chatbot backend - only when panel is first opened
        this.initializeLazy = true;
    }
    
    async initializeChatbot() {
        // Prevent multiple initializations
        if (this.isInitialized || this.isProcessing) return;
        
        this.isProcessing = true;
        
        // Show loading message
        this.addTypingIndicator('Initializing chatbot...');
        
        try {
            console.log('Initializing chatbot backend');
            const response = await fetch('/chatbot/init/');
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            this.removeTypingIndicator();
            
            if (data.status === 'success') {
                this.isInitialized = true;
                this.apiError = false;
                console.log('Chatbot initialized successfully');
            } 
            else if (data.status === 'warning') {
                this.isInitialized = true; // we can still use it
                this.apiError = false;
                console.warn('Chatbot initialized with warnings:', data.message);
                this.addBotMessage('Note: ' + data.message);
            }
            else {
                this.apiError = true;
                console.error('Failed to initialize chatbot:', data.message);
                this.addBotMessage('Sorry, I had trouble loading your bookmarks. ' + data.message);
            }
        } catch (error) {
            this.removeTypingIndicator();
            this.apiError = true;
            console.error('Error initializing chatbot:', error);
            this.addBotMessage('Sorry, I had trouble connecting to the server. Please try again later.');
        } finally {
            this.isProcessing = false;
        }
    }
    
    toggleChatbot(event) {
        // Prevent default behavior if it's a button
        if (event) {
            event.preventDefault();
        }
        
        // Toggle active class
        const isActive = this.chatbotPanel.classList.contains('active');
        
        if (isActive) {
            // If active, remove the active class to hide the panel
            this.chatbotPanel.classList.remove('active');
            console.log('Closing chatbot panel');
        } else {
            // If inactive, add the active class to show the panel
            this.chatbotPanel.classList.add('active');
            console.log('Opening chatbot panel');
            
            // Focus on input field when opening
            setTimeout(() => {
                this.chatInput.focus();
                this.scrollToBottom();
            }, 100);
            
            // Lazy initialize on first open
            if (this.initializeLazy) {
                this.initializeLazy = false;
                this.initializeChatbot();
            }
        }
    }
    
    handleInputKeypress(event) {
        if (event.key === 'Enter') {
            this.sendMessage();
        }
    }
    
    async sendMessage() {
        // Get message text
        const message = this.chatInput.value.trim();
        
        // Don't send empty messages or if already processing or API error
        if (!message || this.isProcessing) return;
        
        if (this.apiError) {
            this.addBotMessage("I'm sorry, but I can't process your request right now due to a technical issue. Please try again later.");
            return;
        }
        
        // Make sure we're initialized
        if (!this.isInitialized) {
            await this.initializeChatbot();
            if (!this.isInitialized) {
                return; // Failed to initialize
            }
        }
        
        // Show user message
        this.addUserMessage(message);
        
        // Clear input
        this.chatInput.value = '';
        
        // Show typing indicator
        this.addTypingIndicator();
        
        // Mark as processing
        this.isProcessing = true;
        
        try {
            // Send message to backend
            const response = await fetch('/chatbot/ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    message: message
                })
            });
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Add bot response
                this.addBotMessage(data.message);
                
                // Add sources if any
                if (data.sources && data.sources.length > 0) {
                    this.addSourcesMessage(data.sources);
                }
            } else {
                this.addBotMessage('Sorry, I encountered an error processing your request. ' + data.message);
                console.error('Error from chatbot:', data.message);
                if (data.status === 'error') {
                    this.apiError = true;
                }
            }
        } catch (error) {
            // Remove typing indicator
            this.removeTypingIndicator();
            
            // Show error message
            this.addBotMessage('Sorry, I encountered an error connecting to the server. Please try again later.');
            console.error('Error sending message:', error);
            this.apiError = true;
        } finally {
            // Mark as not processing
            this.isProcessing = false;
        }
    }
    
    addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user';
        messageElement.innerHTML = `
            <div class="message-content">${this.escapeHtml(message)}</div>
        `;
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot';
        messageElement.innerHTML = `
            <i class="material-icons bot-icon">smart_toy</i>
            <div class="message-content">${this.formatMessage(message)}</div>
        `;
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addSourcesMessage(sources) {
        if (sources.length === 0) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot sources';
        
        let sourcesHtml = '<i class="material-icons bot-icon">link</i><div class="message-content"><div class="sources-header">Sources:</div><ul class="sources-list">';
        
        sources.forEach(source => {
            sourcesHtml += `
                <li class="source-item">
                    <a href="${this.escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">
                        ${this.escapeHtml(source.title)}
                    </a>
                </li>
            `;
        });
        
        sourcesHtml += '</ul></div>';
        messageElement.innerHTML = sourcesHtml;
        
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addTypingIndicator(message = null) {
        const indicatorElement = document.createElement('div');
        indicatorElement.className = 'message bot typing';
        let content = `
            <i class="material-icons bot-icon">smart_toy</i>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        if (message) {
            content = `
                <i class="material-icons bot-icon">smart_toy</i>
                <div class="message-content">
                    <div>${message}</div>
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
        }
        
        indicatorElement.innerHTML = content;
        indicatorElement.id = 'typing-indicator';
        this.messagesContainer.appendChild(indicatorElement);
        this.scrollToBottom();
    }
    
    removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatMessage(text) {
        // Convert URLs to links
        let formattedText = text.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        // Convert newlines to <br>
        formattedText = formattedText.replace(/\n/g, '<br>');
        
        return formattedText;
    }
    
    getCsrfToken() {
        // Get CSRF token from cookies
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrftoken=')) {
                return cookie.substring('csrftoken='.length, cookie.length);
            }
        }
        return '';
    }
    
    async resetConversation() {
        if (this.isProcessing) return;
        
        // Show loading
        this.isProcessing = true;
        this.addTypingIndicator('Resetting conversation...');
        
        try {
            const response = await fetch('/chatbot/reset/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            this.removeTypingIndicator();
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Clear messages except the first one (welcome message)
                while (this.messagesContainer.children.length > 1) {
                    this.messagesContainer.removeChild(this.messagesContainer.lastChild);
                }
                
                // Reset error state
                this.apiError = false;
                
                // Add reset confirmation
                this.addBotMessage('Conversation has been reset. How can I help you?');
            } else {
                console.error('Error resetting conversation:', data.message);
                this.addBotMessage('Sorry, I could not reset the conversation. ' + data.message);
            }
        } catch (error) {
            this.removeTypingIndicator();
            console.error('Error resetting conversation:', error);
            this.addBotMessage('Sorry, I could not reset the conversation due to a server error.');
        } finally {
            this.isProcessing = false;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait a short period to ensure all DOM elements are fully loaded
    setTimeout(() => {
        try {
            window.chatbotManager = new ChatbotManager();
            console.log('Chatbot manager loaded successfully');
        } catch (error) {
            console.error('Error initializing chatbot manager:', error);
        }
    }, 100);
}); 