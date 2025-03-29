
let currentSessionId = ''; // Change from const to let

document.addEventListener('DOMContentLoaded', () => {
    currentSessionId = document.getElementById('current-session').textContent || '';
    const welcomeMessage = "🙏 Namaskaram! Nenu CosmoGuru ni ✨\n\nUgadi panduga sandharbanga meeku naa hrudhayapurvaka subhakankshalu! 🎊 Emi sahaayam kaavali? 🌿";
    addMessage(welcomeMessage, 'ai');
});

// Add message to chat
function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    // Create icon container
    const iconContainer = document.createElement('div');
    iconContainer.className = 'message-icon';
    
    // Add icon based on message type
    const icon = document.createElement('i');
    switch(type) {
        case 'system':
            icon.className = 'fas fa-info-circle';
            break;
        case 'error':
            icon.className = 'fas fa-exclamation-triangle';
            break;
        case 'ai':
            icon.className = 'fas fa-brain'; // Changed to brain icon for AI
            break;
        case 'user':
            icon.className = 'fas fa-user-circle'; // Changed to user circle icon
            break;
    }
    
    iconContainer.appendChild(icon);
    
    // Create message content container
    const contentContainer = document.createElement('div');
    contentContainer.className = 'message-content';
    
    // Add text content
    const textSpan = document.createElement('span');
    textSpan.textContent = text;
    contentContainer.appendChild(textSpan);
    
    // Add timestamp
    const timeSpan = document.createElement('div');
    timeSpan.className = 'message-time';
    timeSpan.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    contentContainer.appendChild(timeSpan);
    
    // Assemble message
    if (type === 'user') {
        messageDiv.appendChild(contentContainer);
        messageDiv.appendChild(iconContainer);
    } else {
        messageDiv.appendChild(iconContainer);
        messageDiv.appendChild(contentContainer);
    }
    
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageDiv;
}

function addTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message ai-message';
    
    const iconContainer = document.createElement('div');
    iconContainer.className = 'message-icon';
    const icon = document.createElement('i');
    icon.className = 'fas fa-brain';
    iconContainer.appendChild(icon);
    
    const typingContainer = document.createElement('div');
    typingContainer.className = 'typing-indicator';
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'typing-dot';
        typingContainer.appendChild(dot);
    }
    
    indicator.appendChild(iconContainer);
    indicator.appendChild(typingContainer);
    
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return indicator;
}

// Handle sending messages
document.getElementById('send-button').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId
            })
        });
        
        // Remove typing indicator
        typingIndicator.remove();
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }
        
        if (data.response) {
            addMessage(data.response, 'ai');
        } else {
            throw new Error('No response received from server');
        }
    } catch (error) {
        console.error('Error:', error);
        typingIndicator.remove();
        addMessage(`Error: ${error.message}`, 'error');
    }
}

// Copy session ID
function copySessionId() {
    const sessionId = document.getElementById('current-session').textContent;
    const sessionBox = document.querySelector('.session-id-box');
    const sessionMask = document.querySelector('.session-id-mask');
    const copyIcon = document.querySelector('.copy-icon');
    
    navigator.clipboard.writeText(sessionId).then(() => {
        // Show success state
        sessionBox.classList.add('copied');
        copyIcon.className = 'fas fa-check copy-icon';
        sessionMask.textContent = 'Copied!';
        
        // Reset after 2 seconds
        setTimeout(() => {
            sessionBox.classList.remove('copied');
            copyIcon.className = 'fas fa-copy copy-icon';
            sessionMask.textContent = 'Session ID';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Load previous session
async function loadSession() {
    const sessionInput = document.getElementById('session-input');
    const sessionId = sessionInput.value.trim();
    
    if (!sessionId) {
        addMessage('Please enter a session ID', 'error');
        return;
    }
    
    // Show loading overlay
    const overlay = document.getElementById('session-loading-overlay');
    const loadingStatus = document.querySelector('.loading-status');
    const chatMessages = document.getElementById('chat-messages');
    
    overlay.classList.remove('hidden');
    setTimeout(() => overlay.classList.add('visible'), 10);
    
    try {
        const updateStatus = (message) => {
            loadingStatus.textContent = message;
        };
        
        updateStatus('Connecting to database...');
        await new Promise(resolve => setTimeout(resolve, 600));
        
        const response = await fetch('/get_history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load session');
        }
        
        updateStatus('Processing messages...');
        await new Promise(resolve => setTimeout(resolve, 400));
        
        // Clear existing messages except the overlay
        const messages = chatMessages.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
        
        if (data.history && Array.isArray(data.history)) {
            updateStatus('Restoring messages...');
            
            // Add messages with slight delay for smooth animation
            for (const msg of data.history) {
                await new Promise(resolve => setTimeout(resolve, 100));
                addMessage(msg.content, msg.type);
            }
            
            // Update current session
            currentSessionId = sessionId;
            document.getElementById('current-session').textContent = sessionId;
            sessionInput.value = '';
        }
        
        // Hide overlay with fade
        overlay.classList.remove('visible');
        setTimeout(() => overlay.classList.add('hidden'), 300);
        
    } catch (error) {
        console.error('Error:', error);
        loadingStatus.textContent = error.message || 'Failed to load chat history';
        await new Promise(resolve => setTimeout(resolve, 2000));
        overlay.classList.remove('visible');
        setTimeout(() => overlay.classList.add('hidden'), 300);
        addMessage('Error loading chat history. Please try again.', 'error');
    }
}

function retryLoadSession(sessionId) {
    const overlay = document.getElementById('session-loading-overlay');
    overlay.querySelector('.session-loading-content').classList.remove('error-state');
    document.getElementById('session-input').value = sessionId;
    loadSession();
}
