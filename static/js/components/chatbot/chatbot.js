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
        this.conversationsList = document.querySelector('.conversations-list');
        this.currentChatTitle = document.getElementById('current-chat-title');
        this.editChatTitleBtn = document.querySelector('.edit-chat-title');
        
        // Create fullscreen button if not already exists
        if (!document.querySelector('.fullscreen-toggle')) {
            this.createFullscreenButton();
        }
        this.fullscreenToggle = document.querySelector('.fullscreen-toggle');
        
        // State
        this.isInitialized = false;
        this.isProcessing = false;
        this.apiError = false;
        this.isFullscreen = false;
        this.currentConversationId = null;
        
        // Bind methods
        this.toggleChatbot = this.toggleChatbot.bind(this);
        this.sendMessage = this.sendMessage.bind(this);
        this.handleInputKeypress = this.handleInputKeypress.bind(this);
        this.resetConversation = this.resetConversation.bind(this);
        this.toggleFullscreen = this.toggleFullscreen.bind(this);
        this.loadConversations = this.loadConversations.bind(this);
        this.toggleSidebar = this.toggleSidebar.bind(this);
        
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
        this.fullscreenToggle.addEventListener('click', this.toggleFullscreen);
        
        // Add event listener for new chat button
        const newChatBtn = document.querySelector('.new-chat-btn');
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => this.startNewConversation());
        }
        
        // Add sidebar toggle functionality
        const sidebarToggleBtn = document.querySelector('.toggle-sidebar-btn');
        if (sidebarToggleBtn) {
            sidebarToggleBtn.addEventListener('click', () => this.toggleSidebar());
        }
        
        // Add chat title edit functionality
        if (this.editChatTitleBtn) {
            this.editChatTitleBtn.addEventListener('click', () => this.editChatTitle());
        }
        
        // Log initial state for debugging
        console.log('Chatbot manager initialized');
        
        // Initialize chatbot backend - only when panel is first opened
        this.initializeLazy = true;
    }
    
    // Tam ekran düğmesini oluşturma
    createFullscreenButton() {
        const chatbotActions = document.querySelector('.chatbot-actions');
        if (chatbotActions) {
            const fullscreenButton = document.createElement('button');
            fullscreenButton.className = 'fullscreen-toggle';
            fullscreenButton.title = 'Tam Ekran';
            fullscreenButton.innerHTML = '<i class="material-icons">fullscreen</i>';
            
            // Düğmeyi resetChat düğmesinin yanına ekle
            chatbotActions.insertBefore(fullscreenButton, chatbotActions.firstChild);
        }
    }
    
    // Tam ekran modunu açıp kapatma
    toggleFullscreen() {
        this.isFullscreen = !this.isFullscreen;
        this.chatbotPanel.classList.toggle('fullscreen', this.isFullscreen);
        
        // İkon değiştirme
        const icon = this.fullscreenToggle.querySelector('i');
        if (this.isFullscreen) {
            icon.textContent = 'fullscreen_exit';
            this.fullscreenToggle.title = 'Tam Ekrandan Çık';
        } else {
            icon.textContent = 'fullscreen';
            this.fullscreenToggle.title = 'Tam Ekran';
        }
        
        // Mesaj alanını en alta kaydır (yeniden boyutlandırma sonrası)
        setTimeout(() => {
            this.scrollToBottom();
        }, 100);
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
            // Eğer tam ekran modundaysa, önce tam ekran modundan çık
            if (this.isFullscreen) {
                this.toggleFullscreen();
            }
            // If active, remove the active class to hide the panel
            this.chatbotPanel.classList.remove('active');
            console.log('Closing chatbot panel');
        } else {
            // If inactive, add the active class to show the panel
            this.chatbotPanel.classList.add('active');
            console.log('Opening chatbot panel');
            
            // Load conversations when opening
            this.loadConversations();
            
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
            // Kullanıcıya başlatma işlemi hakkında bilgi ver
            this.addTypingIndicator("Initializing the chatbot first...");
            
            await this.initializeChatbot();
            
            if (!this.isInitialized) {
                this.removeTypingIndicator();
                this.addBotMessage("I couldn't initialize properly. Please try refreshing the page or contact support if the issue persists.");
                return; // Failed to initialize
            }
            
            this.removeTypingIndicator();
        }
        
        // Eğer konuşma ID'si yoksa yeni bir konuşma başlat
        let isFirstMessage = false;
        if (!this.currentConversationId) {
            // Bilgilendirme mesajı ekle
            this.addTypingIndicator("Creating a new conversation...");
            
            const newConversation = await this.startNewConversation();
            
            this.removeTypingIndicator();
            
            if (!newConversation) {
                this.addBotMessage("Failed to create a new conversation. Please try again.");
                return;
            }
            isFirstMessage = true;
        } else {
            // Var olan bir konuşma için, bunun ilk mesaj olup olmadığını kontrol et
            isFirstMessage = document.querySelectorAll('.message:not(.typing)').length <= 1;
        }
        
        // Show user message
        this.addUserMessage(message);
        
        // Clear input
        this.chatInput.value = '';
        
        // Mark as processing (önce bunu yapalım ki kullanıcı birden fazla mesaj gönderemesin)
        this.isProcessing = true;
        
        // Bot mesajı için placeholder oluştur (typing göstergesi göstermek yerine)
        const botMessageElement = this.createEmptyBotMessage();
        
        try {
            // For modern browsers, use streaming response
            if (typeof ReadableStream !== 'undefined' && typeof TextDecoder !== 'undefined') {
                await this.sendStreamingMessage(message, isFirstMessage, botMessageElement);
            } else {
                // Fallback to traditional request for older browsers
                await this.sendTraditionalMessage(message, isFirstMessage);
            }
        } catch (error) {
            // Eğer bot mesajı hala düşünme animasyonu gösteriyorsa, hata mesajıyla değiştir
            if (botMessageElement) {
                const messageContent = botMessageElement.querySelector('.message-content');
                if (messageContent) {
                    messageContent.innerHTML = this.formatMessage('Sorry, I encountered an error connecting to the server. Please try again later.');
                }
            } else {
                // Remove typing indicator if exists
                this.removeTypingIndicator();
                
                // Add standard error message
                this.addBotMessage('Sorry, I encountered an error connecting to the server. Please try again later.');
            }
            
            console.error('Error sending message:', error);
            this.apiError = true;
        } finally {
            // Mark as not processing
            this.isProcessing = false;
        }
    }
    
    async sendStreamingMessage(message, isFirstMessage, botMessageElement) {
        try {
            // Başlık bildirim elementi için referans
            let titleNotificationElement = null;
            let conversationId = null;
            let sources = [];
            
            // Bot mesaj içeriğine referans
            const botMessageContent = botMessageElement.querySelector('.message-content');
            
            // Send request with stream flag
            const response = await fetch('/chatbot/ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.currentConversationId,
                    generate_title: isFirstMessage,
                    stream: true  // Request streaming response
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            // Basit içerik alanı oluştur
            if (botMessageContent) {
                // Clear thinking animation
                botMessageContent.innerHTML = '';
                
                // Basit metin konteynerı
                const formattedTextContainer = document.createElement('div');
                formattedTextContainer.className = 'streamed-content';
                botMessageContent.appendChild(formattedTextContainer);
            }
            
            // Timeout for response - eğer 15 saniye içinde yanıt gelmezse hata döndür
            let timeoutId = setTimeout(() => {
                if (botMessageContent && botMessageContent.querySelector('.thinking-animation')) {
                    // Hala düşünme animasyonu gösteriliyorsa, hata mesajı göster
                    botMessageContent.innerHTML = this.formatMessage("The server is taking too long to respond. Please try again.");
                }
            }, 15000);
            
            // Stream response processing
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let fullResponse = '';
            
            while (true) {
                const { done, value } = await reader.read();
                
                // Zamanlayıcıyı her veri alındığında sıfırla
                clearTimeout(timeoutId);
                
                if (done) {
                    break;
                }
                
                // Process chunks from the stream
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n').filter(line => line.trim());
                
                for (const line of lines) {
                    try {
                        const data = JSON.parse(line);
                        
                        // Handle different types of streaming data
                        switch (data.type) {
                            case 'metadata':
                                // Initial metadata with conversation ID
                                conversationId = data.conversation_id;
                                this.currentConversationId = conversationId;
                                break;
                                
                            case 'content':
                                // Simple approach: Just append the content and format
                                const contentChunk = data.chunk;
                                fullResponse += contentChunk;
                                
                                // Update the content directly - much simpler approach
                                if (botMessageContent) {
                                    const streamedContent = botMessageContent.querySelector('.streamed-content');
                                    if (streamedContent) {
                                        // Format and display the accumulated response so far
                                        streamedContent.innerHTML = this.formatMessage(fullResponse);
                                        
                                        // Apply highlight to new content for better UX
                                        streamedContent.classList.add('highlight-new');
                                        setTimeout(() => {
                                            streamedContent.classList.remove('highlight-new');
                                        }, 700); // Shorter highlight duration
                                    } else {
                                        // Fallback if container missing
                                        botMessageContent.innerHTML = this.formatMessage(fullResponse);
                                    }
                                }
                                
                                this.scrollToBottom();
                                break;
                                
                            case 'status':
                                // Status updates shown simply
                                if (isFirstMessage && data.message === "Generating title...") {
                                    // Title Generation notification - simple approach
                                    if (titleNotificationElement && titleNotificationElement.parentNode) {
                                        titleNotificationElement.remove();
                                    }
                                    
                                    // Create simple notification
                                    titleNotificationElement = document.createElement('div');
                                    titleNotificationElement.className = 'message bot title-notice';
                                    titleNotificationElement.innerHTML = `
                                        <i class="material-icons bot-icon">autorenew</i>
                                        <div class="message-content">
                                            <p>Creating a title...</p>
                                        </div>
                                    `;
                                    this.messagesContainer.appendChild(titleNotificationElement);
                                    this.scrollToBottom();
                                }
                                break;
                                
                            case 'title':
                                // Update title directly without animations
                                if (this.currentChatTitle) {
                                    this.currentChatTitle.textContent = data.title;
                                }
                                
                                // Show notification about the title
                                if (titleNotificationElement && titleNotificationElement.parentNode) {
                                    titleNotificationElement.innerHTML = `
                                        <i class="material-icons bot-icon">check_circle</i>
                                        <div class="message-content">
                                            <p>Created a title: <strong>${this.escapeHtml(data.title)}</strong></p>
                                        </div>
                                    `;
                                    
                                    // Auto-remove after short delay
                                    setTimeout(() => {
                                        if (titleNotificationElement && titleNotificationElement.parentNode) {
                                            titleNotificationElement.remove();
                                        }
                                    }, 3000);
                                }
                                break;
                                
                            case 'completion':
                                // Final data with sources
                                sources = data.sources || [];
                                
                                // Ensure the final formatting is applied
                                if (botMessageContent) {
                                    // Format the message one last time
                                    botMessageContent.innerHTML = this.formatMessage(fullResponse);
                                }
                                break;
                                
                            case 'error':
                                // Error in processing - simple display
                                if (botMessageContent) {
                                    botMessageContent.innerHTML = this.formatMessage(data.message);
                                }
                                console.error('Error from chatbot:', data.message);
                                
                                // Clean up any title notification
                                if (titleNotificationElement && titleNotificationElement.parentNode) {
                                    titleNotificationElement.remove();
                                }
                                break;
                        }
                    } catch (e) {
                        console.error('Error parsing streaming response:', e, line);
                    }
                }
            }
            
            // Add sources if any
            if (sources && sources.length > 0) {
                this.addSourcesMessage(sources);
            }
            
            // Clean up any remaining title notification
            if (titleNotificationElement && titleNotificationElement.parentNode) {
                titleNotificationElement.remove();
            }
            
            // Reload conversations list
            this.loadConversations();
            
        } catch (error) {
            // Clean up on error
            if (botMessageElement) {
                const messageContent = botMessageElement.querySelector('.message-content');
                if (messageContent) {
                    messageContent.innerHTML = this.formatMessage('Sorry, I encountered an error processing your request. Please try again later.');
                }
            }
            
            console.error('Error in streaming message:', error);
        }
    }
    
    async sendTraditionalMessage(message, isFirstMessage) {
        // Create a placeholder message
        const botMessageElement = this.createEmptyBotMessage();
        const botMessageContent = botMessageElement.querySelector('.message-content');
        
        try {
            const response = await fetch('/chatbot/ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.currentConversationId,
                    generate_title: isFirstMessage
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Update the placeholder message instead of creating a new one
                if (botMessageContent) {
                    botMessageContent.innerHTML = this.formatMessage(data.message);
                } else {
                    // Fallback if somehow the element was removed
                    this.addBotMessage(data.message);
                }
                
                // Add sources if any
                if (data.sources && data.sources.length > 0) {
                    this.addSourcesMessage(data.sources);
                }
                
                // Update conversation ID if it has changed
                if (data.conversation_id && this.currentConversationId !== data.conversation_id) {
                    this.currentConversationId = data.conversation_id;
                }
                
                // Update title silently
                if (data.conversation_title && this.currentChatTitle) {
                    this.currentChatTitle.textContent = data.conversation_title;
                    
                    // Show title notification only on first message
                    if (isFirstMessage) {
                        const titleNotice = document.createElement('div');
                        titleNotice.className = 'message bot title-notice';
                        titleNotice.innerHTML = `
                            <i class="material-icons bot-icon">check_circle</i>
                            <div class="message-content">
                                <p>Created a title: <strong>${this.escapeHtml(data.conversation_title)}</strong></p>
                            </div>
                        `;
                        this.messagesContainer.appendChild(titleNotice);
                        this.scrollToBottom();
                        
                        // Auto-remove after delay
                        setTimeout(() => {
                            titleNotice.classList.add('fading-out');
                            setTimeout(() => {
                                if (titleNotice.parentNode) {
                                    titleNotice.remove();
                                }
                            }, 500);
                        }, 3000);
                    }
                }
                
                // Reload conversations list
                this.loadConversations();
            } else {
                // Show error in the placeholder message
                if (botMessageContent) {
                    botMessageContent.innerHTML = this.formatMessage('Sorry, I encountered an error processing your request. ' + data.message);
                } else {
                    this.addBotMessage('Sorry, I encountered an error processing your request. ' + data.message);
                }
                
                console.error('Error from chatbot:', data.message);
                if (data.status === 'error') {
                    this.apiError = true;
                }
            }
        } catch (error) {
            // Show error in the placeholder message
            if (botMessageContent) {
                botMessageContent.innerHTML = this.formatMessage('Sorry, I encountered an error connecting to the server. Please try again later.');
            } else {
                this.addBotMessage('Sorry, I encountered an error connecting to the server. Please try again later.');
            }
            
            console.error('Error in traditional message:', error);
        }
    }
    
    createEmptyBotMessage() {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot';
        
        messageElement.innerHTML = `
            <i class="material-icons bot-icon">smart_toy</i>
            <div class="message-content">
                <div class="thinking-animation">
                    <span class="thinking-dot" style="--delay: 0s"></span>
                    <span class="thinking-dot" style="--delay: 0.1s"></span>
                    <span class="thinking-dot" style="--delay: 0.2s"></span>
                    <span class="thinking-text">Thinking</span>
                </div>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
        
        // Add CSS for the thinking animation if it doesn't exist
        if (!document.getElementById('thinking-animation-style')) {
            const style = document.createElement('style');
            style.id = 'thinking-animation-style';
            style.textContent = `
                .thinking-animation {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                .thinking-dot {
                    width: 8px;
                    height: 8px;
                    background-color: #2196F3;
                    border-radius: 50%;
                    display: inline-block;
                    animation: pulse-thinking 1.5s infinite ease-in-out;
                    animation-delay: var(--delay);
                }
                .thinking-text {
                    font-size: 14px;
                    color: #757575;
                    margin-left: 4px;
                }
                @keyframes pulse-thinking {
                    0%, 100% { transform: scale(0.75); opacity: 0.6; }
                    50% { transform: scale(1); opacity: 1; }
                }
                body.dark-mode .thinking-dot {
                    background-color: #64B5F6;
                }
                body.dark-mode .thinking-text {
                    color: #B0B0B0;
                }
            `;
            document.head.appendChild(style);
        }
        
        return messageElement;
    }
    
    addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user';
        
        messageElement.innerHTML = `
            <div class="message-content">
                ${this.formatMessage(message)}
            </div>
        `;
        
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot';
        
        messageElement.innerHTML = `
            <i class="material-icons bot-icon">smart_toy</i>
            <div class="message-content">
                ${this.formatMessage(message)}
            </div>
        `;
        
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addSourcesMessage(sources) {
        if (sources.length === 0) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot sources';
        
        // Limit initial visible sources if there are many
        const initialVisibleCount = 5;
        const hasMoreSources = sources.length > initialVisibleCount;
        
        let sourcesHtml = `
            <i class="material-icons bot-icon">link</i>
            <div class="message-content">
                <div class="sources-header">Sources: (${sources.length} bookmark${sources.length > 1 ? 's' : ''})</div>
                <ul class="sources-list">
        `;
        
        sources.forEach((source, index) => {
            const isHidden = index >= initialVisibleCount;
            sourcesHtml += `
                <li class="source-item${isHidden ? ' hidden-source' : ''}" data-source-index="${index}">
                    <a href="${this.escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">
                        ${this.escapeHtml(source.title)}
                    </a>
                </li>
            `;
        });
        
        sourcesHtml += '</ul>';
        
        // Add "Show more" button if needed
        if (hasMoreSources) {
            sourcesHtml += `
                <button type="button" class="show-more-sources">
                    Show ${sources.length - initialVisibleCount} more sources
                </button>
                <button type="button" class="show-less-sources" style="display: none;">
                    Show less
                </button>
            `;
        }
        
        sourcesHtml += '</div>';
        messageElement.innerHTML = sourcesHtml;
        
        this.messagesContainer.appendChild(messageElement);
        
        // Add event listeners for show more/less buttons
        if (hasMoreSources) {
            const showMoreBtn = messageElement.querySelector('.show-more-sources');
            const showLessBtn = messageElement.querySelector('.show-less-sources');
            
            showMoreBtn.addEventListener('click', () => {
                // Show all hidden sources
                const hiddenSources = messageElement.querySelectorAll('.hidden-source');
                hiddenSources.forEach(source => {
                    source.classList.remove('hidden-source');
                });
                // Toggle buttons
                showMoreBtn.style.display = 'none';
                showLessBtn.style.display = 'block';
            });
            
            showLessBtn.addEventListener('click', () => {
                // Hide sources again
                sources.forEach((_, index) => {
                    if (index >= initialVisibleCount) {
                        const sourceElement = messageElement.querySelector(`[data-source-index="${index}"]`);
                        if (sourceElement) {
                            sourceElement.classList.add('hidden-source');
                        }
                    }
                });
                // Toggle buttons
                showMoreBtn.style.display = 'block';
                showLessBtn.style.display = 'none';
            });
        }
        
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
        if (!text) return '';
        
        // HTML tag'lerini güvenli bir şekilde escape et
        text = this.escapeHtml(text);
        
        // Markdown formatlamasını uygula
        
        // 1. Bold (** ** veya __ __)
        text = text.replace(/\*\*(.*?)\*\*|__(.*?)__/g, '<strong class="format-animation">$1$2</strong>');
        
        // 2. Italik (* * veya _ _)
        text = text.replace(/\*(.*?)\*|_(.*?)_/g, '<em class="format-animation">$1$2</em>');
        
        // 3. Kod bloğu (``` ```)
        text = text.replace(/```([\s\S]*?)```/g, '<pre class="format-animation"><code>$1</code></pre>');
        
        // 4. Inline kod (` `)
        text = text.replace(/`([^`]+)`/g, '<code class="format-animation">$1</code>');
        
        // 5. Satır içi liste maddeleri
        text = text.replace(/^- (.*)/gm, '<li class="format-animation">$1</li>');
        text = text.replace(/^([0-9]+)\. (.*)/gm, '<li class="format-animation">$1. $2</li>');
        
        // 6. Başlıklar
        text = text.replace(/^### (.*)/gm, '<h3 class="format-animation">$1</h3>');
        text = text.replace(/^## (.*)/gm, '<h2 class="format-animation">$1</h2>');
        text = text.replace(/^# (.*)/gm, '<h1 class="format-animation">$1</h1>');
        
        // 7. URL'leri linkleştirme
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="format-animation">$1</a>');
        
        // Tekli/çiftli satır atlamaları için paragraf ve line break
        text = text.replace(/\n\n/g, '</p><p class="format-animation">');
        text = text.replace(/\n/g, '<br>');
        
        // Tüm metni başlangıçta ve sonunda <p> ile sarmala
        text = '<p class="format-animation">' + text + '</p>';
        
        return text;
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
    
    // Konuşma geçmişini yükleme metodu
    async loadConversations() {
        try {
            console.log('Loading conversations');
            
            // Mevcut konuşmalar listesinde bir yükleme göstergesi görüntüle
            if (this.conversationsList.children.length === 0) {
                this.conversationsList.innerHTML = '<div class="loading-conversations">Loading...</div>';
            }
            
            const response = await fetch('/chatbot/conversations/');
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Yükleme göstergesini kaldır
            const loadingIndicator = this.conversationsList.querySelector('.loading-conversations');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
            
            if (data.status === 'success') {
                // Önce aktif konuşmanın ID'sini sakla
                const activeConversationId = this.currentConversationId;
                
                if (data.conversations && data.conversations.length > 0) {
                    // Var olan konuşma öğelerini kontrol et ve gerekirse güncelle
                    const existingItems = {};
                    const conversationElements = this.conversationsList.querySelectorAll('.conversation-item');
                    
                    // Mevcut öğeleri haritala
                    conversationElements.forEach(item => {
                        existingItems[item.dataset.id] = item;
                    });
                    
                    // Yeni liste içeriğini hazırla
                    let updatedList = document.createDocumentFragment();
                    
                    // Konuşmaları ekle/güncelle
                    data.conversations.forEach(conversation => {
                        if (existingItems[conversation.id]) {
                            // Var olan öğeyi güncelle
                            const item = existingItems[conversation.id];
                            const titleEl = item.querySelector('.conversation-title');
                            if (titleEl && titleEl.textContent !== conversation.title) {
                                titleEl.textContent = conversation.title;
                            }
                            
                            // Aktif sınıfı doğru ayarla
                            if (activeConversationId === conversation.id) {
                                item.classList.add('active');
                            } else {
                                item.classList.remove('active');
                            }
                            
                            updatedList.appendChild(item);
                            delete existingItems[conversation.id];
                        } else {
                            // Yeni öğe oluştur
                            this.addConversationToList(conversation, updatedList);
                        }
                    });
                    
                    // Listeyi güncelle
                    this.conversationsList.innerHTML = '';
                    this.conversationsList.appendChild(updatedList);
                } else {
                    // Konuşma yoksa bilgi mesajı göster
                    this.conversationsList.innerHTML = '<div class="no-conversations">No conversations yet.</div>';
                }
            } else {
                // Hata durumunda liste boşsa bilgi mesajı göster
                if (this.conversationsList.children.length === 0) {
                    this.conversationsList.innerHTML = '<div class="no-conversations">Error loading conversations.</div>';
                }
                console.error('Error loading conversations:', data.message);
            }
        } catch (error) {
            // Hata durumunda liste boşsa bilgi mesajı göster
            if (this.conversationsList.children.length === 0) {
                this.conversationsList.innerHTML = '<div class="no-conversations">Error loading conversations.</div>';
            }
            console.error('Error loading conversations:', error);
        }
    }
    
    // Konuşmayı listeye ekleme metodu (güncellenmiş)
    addConversationToList(conversation, parentElement = null) {
        const conversationItem = document.createElement('div');
        conversationItem.className = 'conversation-item';
        conversationItem.dataset.id = conversation.id;
        
        if (this.currentConversationId === conversation.id) {
            conversationItem.classList.add('active');
        }
        
        conversationItem.innerHTML = `
            <div class="conversation-title">${this.escapeHtml(conversation.title)}</div>
            <div class="conversation-actions">
                <button type="button" class="conversation-action-btn rename-conversation" title="Rename">
                    <i class="material-icons">edit</i>
                </button>
                <button type="button" class="conversation-action-btn delete-conversation" title="Delete">
                    <i class="material-icons">delete</i>
                </button>
            </div>
        `;
        
        // Konuşmaya tıklama olayı ekle
        conversationItem.addEventListener('click', (e) => {
            if (!e.target.closest('.conversation-actions')) {
                this.loadConversation(conversation.id);
            }
        });
        
        // Silme butonu olayı
        const deleteBtn = conversationItem.querySelector('.delete-conversation');
        deleteBtn.addEventListener('click', () => {
            this.deleteConversation(conversation.id, conversationItem);
        });
        
        // Yeniden adlandırma butonu olayı
        const renameBtn = conversationItem.querySelector('.rename-conversation');
        renameBtn.addEventListener('click', () => {
            const titleEl = conversationItem.querySelector('.conversation-title');
            const currentTitle = titleEl.textContent;
            const newTitle = prompt('Enter new conversation title:', currentTitle);
            
            if (newTitle && newTitle !== currentTitle) {
                this.renameConversation(conversation.id, conversationItem, newTitle);
            }
        });
        
        // Eğer bir parentElement verildiyse, ona ekle
        if (parentElement) {
            parentElement.appendChild(conversationItem);
            return conversationItem;
        }
        
        // Aksi halde doğrudan listeye ekle
        this.conversationsList.appendChild(conversationItem);
        return conversationItem;
    }
    
    // Belirli bir konuşmayı yükle
    async loadConversation(conversationId) {
        if (this.isProcessing || this.currentConversationId === conversationId) return;
        
        this.isProcessing = true;
        
        try {
            // Aktif konuşma sınıfını güncelle
            const conversationItems = document.querySelectorAll('.conversation-item');
            conversationItems.forEach(item => {
                item.classList.remove('active');
                if (item.dataset.id === conversationId.toString()) {
                    item.classList.add('active');
                }
            });
            
            // Mesaj yükleme göstergesi
            this.messagesContainer.innerHTML = '';
            this.addTypingIndicator('Loading conversation...');
            
            const response = await fetch(`/chatbot/conversations/${conversationId}/`);
            
            // Yükleme göstergesini kaldır
            this.removeTypingIndicator();
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Mesajları temizle
                this.messagesContainer.innerHTML = '';
                
                // Konuşma ID'sini kaydet
                this.currentConversationId = conversationId;
                
                // Sohbet başlığını güncelle
                if (this.currentChatTitle) {
                    this.currentChatTitle.textContent = data.conversation.title || 'Current Chat';
                }
                
                // Mesajları ekle
                if (data.conversation.messages && data.conversation.messages.length > 0) {
                    data.conversation.messages.forEach(message => {
                        if (message.is_user) {
                            this.addUserMessage(message.content);
                        } else {
                            this.addBotMessage(message.content);
                        }
                    });
                } else {
                    // Hoş geldin mesajı
                    this.addBotMessage('Hello! I can help you search through your bookmarks. What are you looking for?');
                }
                
                // En alta kaydır
                this.scrollToBottom();
            } else {
                this.addBotMessage('Error loading conversation: ' + data.message);
                console.error('Error loading conversation:', data.message);
            }
        } catch (error) {
            this.messagesContainer.innerHTML = '';
            this.addBotMessage('Error loading conversation. Please try again later.');
            console.error('Error loading conversation:', error);
        } finally {
            this.isProcessing = false;
        }
    }
    
    // Konuşmayı sil
    async deleteConversation(conversationId, conversationEl) {
        if (this.isProcessing) return;
        
        if (!confirm('Are you sure you want to delete this conversation?')) {
            return;
        }
        
        this.isProcessing = true;
        
        try {
            const response = await fetch(`/chatbot/conversations/${conversationId}/delete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Öğeyi kaldır
                conversationEl.remove();
                
                // Aktif konuşmaydıysa mesajları temizle
                if (this.currentConversationId === conversationId) {
                    this.messagesContainer.innerHTML = '';
                    this.addBotMessage('Hello! I can help you search through your bookmarks. What are you looking for?');
                    this.currentConversationId = null;
                }
                
                // Konuşma listesi boşsa bilgi mesajı göster
                if (this.conversationsList.children.length === 0) {
                    this.conversationsList.innerHTML = '<div class="no-conversations">No conversations yet.</div>';
                }
            } else {
                alert('Error deleting conversation: ' + data.message);
                console.error('Error deleting conversation:', data.message);
            }
        } catch (error) {
            alert('Error deleting conversation. Please try again later.');
            console.error('Error deleting conversation:', error);
        } finally {
            this.isProcessing = false;
        }
    }
    
    // Konuşma başlığını düzenle
    editChatTitle() {
        // Eğer aktif konuşma yoksa, yeni bir konuşma başlat ve sonra düzenle
        if (!this.currentConversationId) {
            this.startNewConversation().then(() => {
                // Konuşma oluşturulduktan sonra başlığı düzenle
                setTimeout(() => this.editChatTitle(), 500);
            });
            return;
        }
        
        const currentTitle = this.currentChatTitle ? this.currentChatTitle.textContent : 'Current Chat';
        const newTitle = prompt('Enter a new title for this conversation:', currentTitle);
        
        if (!newTitle || newTitle === currentTitle) {
            return;
        }
        
        this.renameConversation(this.currentConversationId, null, newTitle);
    }
    
    // Konuşmayı yeniden adlandır (güncellendi)
    async renameConversation(conversationId, conversationEl, newTitle) {
        try {
            const response = await fetch(`/chatbot/conversations/${conversationId}/rename/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    title: newTitle
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Başlığı güncelle (eğer varsa)
                if (conversationEl) {
                    const titleEl = conversationEl.querySelector('.conversation-title');
                    if (titleEl) {
                        titleEl.textContent = newTitle;
                    }
                }
                
                // Listedeki tüm öğeleri kontrol et ve gerekirse güncelle
                if (!conversationEl) {
                    const allConversationItems = document.querySelectorAll('.conversation-item');
                    allConversationItems.forEach(item => {
                        if (item.dataset.id === conversationId.toString()) {
                            const titleEl = item.querySelector('.conversation-title');
                            if (titleEl) {
                                titleEl.textContent = newTitle;
                            }
                        }
                    });
                }
                
                // Eğer bu aktif konuşma ise, header'daki başlığı da güncelle
                if (this.currentConversationId === conversationId && this.currentChatTitle) {
                    this.currentChatTitle.textContent = newTitle;
                }
            } else {
                alert('Error renaming conversation: ' + data.message);
                console.error('Error renaming conversation:', data.message);
            }
        } catch (error) {
            alert('Error renaming conversation. Please try again later.');
            console.error('Error renaming conversation:', error);
        }
    }

    // Yeni konuşma başlat (güncellendi)
    async startNewConversation() {
        if (this.isProcessing) return;
        
        this.isProcessing = true;
        
        try {
            const response = await fetch('/chatbot/conversations/new/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Mesajları temizle
                this.messagesContainer.innerHTML = '';
                
                // Başlığı güncelle
                if (this.currentChatTitle) {
                    this.currentChatTitle.textContent = data.conversation.title || 'New Chat';
                }
                
                // Kullanıcı ID'sini güncelle
                this.currentConversationId = data.conversation.id;
                
                // Sidebarı kapat eğer açıksa (özellikle mobil görünümde)
                const sidebar = document.querySelector('.chatbot-sidebar');
                if (sidebar && sidebar.classList.contains('open')) {
                    this.toggleSidebar();
                }
                
                // Input'a odaklan
                if (this.chatInput) {
                    this.chatInput.focus();
                }
                
                // No conversations mesajını kaldır
                const noConversations = this.conversationsList.querySelector('.no-conversations');
                if (noConversations) {
                    noConversations.remove();
                }
                
                // Yeni konuşmayı listeye ekle
                this.addConversationToList(data.conversation);
                
                // Konuşmaların listesini yükle ve güncellemeleri göster
                this.loadConversations();
                
                // Hoş geldin mesajını ekle
                this.addBotMessage('Hello! I can help you search through your bookmarks. What are you looking for?');
                
                // En alta kaydır
                this.scrollToBottom();
                
                return data.conversation;
            } else {
                alert('Error creating new conversation: ' + data.message);
                console.error('Error creating new conversation:', data.message);
                return null;
            }
        } catch (error) {
            alert('Error creating new conversation. Please try again later.');
            console.error('Error creating new conversation:', error);
            return null;
        } finally {
            this.isProcessing = false;
        }
    }
    
    // Toggle sidebar visibility for mobile
    toggleSidebar() {
        const sidebar = document.querySelector('.chatbot-sidebar');
        const chatbotPanel = document.querySelector('.chatbot-panel');
        
        if (sidebar) {
            const isOpen = sidebar.classList.toggle('open');
            
            // Overlay oluştur veya kaldır
            if (isOpen) {
                // Overlay oluştur - sidebarın dışına tıklandığında kapanmasını sağlar
                const overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                overlay.addEventListener('click', () => this.toggleSidebar());
                chatbotPanel.appendChild(overlay);
                
                // Overlay fade-in animasyonu
                setTimeout(() => {
                    overlay.style.opacity = '1';
                }, 10);
            } else {
                // Overlay'i kaldır
                const overlay = document.querySelector('.sidebar-overlay');
                if (overlay) {
                    overlay.style.opacity = '0';
                    // Animasyon bittikten sonra kaldır
                    setTimeout(() => {
                        overlay.remove();
                    }, 300);
                }
            }
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