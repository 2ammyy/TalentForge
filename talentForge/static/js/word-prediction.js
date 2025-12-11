// static/js/word-prediction.js
class IntelligentWordPredictor {
    constructor(options = {}) {
        this.options = {
            apiEndpoint: '/word_prediction/predict/',
            learnEndpoint: '/word_prediction/learn/',
            debounceTime: 150,
            maxSuggestions: 3,
            minChars: 1,
            enableLearning: true,
            showDebug: false,
            ...options
        };
        
        this.cache = new Map();
        this.userId = this.getUserId();
        this.setupEventListeners();
        this.log('Intelligent Word Predictor initialized');
    }
    
    getUserId() {
        // Extract user ID from Django template or meta tag
        const userElement = document.querySelector('[data-user-id]');
        return userElement ? userElement.dataset.userId : null;
    }
    
    setupEventListeners() {
        // Listen for input events on all text inputs and textareas
        document.addEventListener('input', (e) => {
            const target = e.target;
            if (target.tagName === 'INPUT' && target.type === 'text' || 
                target.tagName === 'TEXTAREA') {
                this.handleInput(target);
            }
        });
        
        // Listen for suggestions being selected
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('word-suggestion')) {
                this.handleSuggestionClick(e.target);
            }
        });
    }
    
    async handleInput(inputElement) {
        const text = inputElement.value;
        const cursorPos = inputElement.selectionStart;
        
        // Check conditions
        if (text.length < this.options.minChars) {
            this.hideSuggestions();
            return;
        }
        
        // Get text before cursor
        const textBeforeCursor = text.substring(0, cursorPos);
        
        // Debounce
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(async () => {
            const suggestions = await this.getPredictions(textBeforeCursor);
            if (suggestions.length > 0) {
                this.showSuggestions(inputElement, suggestions);
            } else {
                this.hideSuggestions();
            }
        }, this.options.debounceTime);
    }
    
    async getPredictions(text) {
        // Check cache first
        const cacheKey = `${text}_${this.userId}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }
        
        try {
            const params = new URLSearchParams({
                text: text,
                num_suggestions: this.options.maxSuggestions
            });
            
            const response = await fetch(`${this.options.apiEndpoint}?${params}`);
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.cache.set(cacheKey, data.suggestions);
                
                // Limit cache size
                if (this.cache.size > 100) {
                    const firstKey = this.cache.keys().next().value;
                    this.cache.delete(firstKey);
                }
                
                this.log(`Predictions for "${text}":`, data.suggestions);
                return data.suggestions;
            }
            
            return [];
            
        } catch (error) {
            console.error('Prediction error:', error);
            return [];
        }
    }
    
    showSuggestions(inputElement, suggestions) {
        // Remove existing suggestions
        this.hideSuggestions();
        
        // Create suggestions container
        const container = document.createElement('div');
        container.className = 'word-suggestions-container';
        container.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            min-width: 150px;
            max-width: 300px;
        `;
        
        // Position container near cursor
        const rect = inputElement.getBoundingClientRect();
        const cursorPos = inputElement.selectionStart;
        const textBeforeCursor = inputElement.value.substring(0, cursorPos);
        
        // Create a temporary span to measure text width
        const tempSpan = document.createElement('span');
        tempSpan.style.cssText = `
            position: absolute;
            white-space: pre;
            font: getComputedStyle(inputElement).font;
            visibility: hidden;
        `;
        tempSpan.textContent = textBeforeCursor;
        document.body.appendChild(tempSpan);
        
        const textWidth = tempSpan.offsetWidth;
        document.body.removeChild(tempSpan);
        
        // Calculate position
        const leftPos = rect.left + textWidth;
        const topPos = rect.bottom + 5;
        
        container.style.left = `${leftPos}px`;
        container.style.top = `${topPos}px`;
        
        // Add suggestions
        suggestions.forEach((suggestion, index) => {
            const suggestionElement = document.createElement('div');
            suggestionElement.className = 'word-suggestion';
            suggestionElement.textContent = suggestion;
            suggestionElement.style.cssText = `
                padding: 8px 12px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
                transition: background-color 0.2s;
            `;
            suggestionElement.dataset.suggestion = suggestion;
            suggestionElement.dataset.index = index;
            
            // Hover effect
            suggestionElement.addEventListener('mouseenter', () => {
                suggestionElement.style.backgroundColor = '#f5f5f5';
            });
            suggestionElement.addEventListener('mouseleave', () => {
                suggestionElement.style.backgroundColor = '';
            });
            
            container.appendChild(suggestionElement);
        });
        
        // Add header
        const header = document.createElement('div');
        header.textContent = 'Suggestions:';
        header.style.cssText = `
            padding: 8px 12px;
            font-size: 12px;
            color: #666;
            border-bottom: 1px solid #eee;
            background: #f9f9f9;
        `;
        container.insertBefore(header, container.firstChild);
        
        // Store reference to input element
        container.dataset.targetInputId = inputElement.id || 
                                         `input_${Date.now()}`;
        if (!inputElement.id) {
            inputElement.id = container.dataset.targetInputId;
        }
        
        // Add to document
        document.body.appendChild(container);
        this.currentSuggestions = container;
        this.currentInput = inputElement;
    }
    
    hideSuggestions() {
        if (this.currentSuggestions) {
            this.currentSuggestions.remove();
            this.currentSuggestions = null;
            this.currentInput = null;
        }
    }
    
    async handleSuggestionClick(suggestionElement) {
        const suggestion = suggestionElement.dataset.suggestion;
        const inputElement = this.currentInput;
        const originalText = inputElement.value;
        const cursorPos = inputElement.selectionStart;
        
        // Get text before and after cursor
        const textBefore = originalText.substring(0, cursorPos);
        const textAfter = originalText.substring(cursorPos);
        
        // Insert suggestion with space
        const newText = textBefore + suggestion + ' ';
        inputElement.value = newText + textAfter;
        
        // Move cursor to end of inserted text
        const newCursorPos = newText.length;
        inputElement.setSelectionRange(newCursorPos, newCursorPos);
        
        // Focus back on input
        inputElement.focus();
        
        // Send learning data to server
        if (this.options.enableLearning && this.userId) {
            await this.learnFromSelection(textBefore.trim(), suggestion);
        }
        
        // Hide suggestions
        this.hideSuggestions();
        
        // Trigger input event for further predictions
        inputElement.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    async learnFromSelection(text, selected) {
        try {
            const response = await fetch(this.options.learnEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    text: text,
                    selected: selected
                })
            });
            
            if (response.ok) {
                this.log(`Learned: "${selected}" for context "${text}"`);
            }
        } catch (error) {
            console.error('Learning error:', error);
        }
    }
    
    getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }
    
    log(...args) {
        if (this.options.showDebug) {
            console.log('[WordPredictor]', ...args);
        }
    }
    
    // Public API methods
    async predict(text) {
        return await this.getPredictions(text);
    }
    
    clearCache() {
        this.cache.clear();
    }
    
    destroy() {
        this.hideSuggestions();
        clearTimeout(this.debounceTimer);
        // Remove event listeners
        document.removeEventListener('input', this.handleInput);
        document.removeEventListener('click', this.handleSuggestionClick);
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.wordPredictor = new IntelligentWordPredictor({
        showDebug: false, // Set to true for debugging
        maxSuggestions: 3
    });
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IntelligentWordPredictor;
}

