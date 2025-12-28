// static/js/google-predictor.js - Version avec DEBUG complet
console.log('🔧 Google Predictor loading...');

(function() {
    'use strict';
    
    const PREDICTOR_API = '/predict/';
    
    class GooglePredictor {
        constructor() {
            console.log('🎯 Google Predictor constructor called');
            this.currentInput = null;
            this.currentSuggestion = '';
            this.debounceTimer = null;
            
            this.init();
        }
        
        init() {
            console.log('✅ Google Predictor initializing...');
            
            // Attacher immédiatement
            this.attachToTextarea();
            
            // Observer pour les champs qui apparaissent plus tard
            this.observeForTextarea();
            
            // Également essayer après un délai
            setTimeout(() => {
                console.log('⏰ Delayed attachment attempt');
                this.attachToTextarea();
            }, 1000);
            
            // Et encore après 3 secondes
            setTimeout(() => {
                console.log('⏰ Second delayed attachment attempt');
                this.attachToTextarea();
            }, 3000);
        }
        
        attachToTextarea() {
            console.log('🔍 Looking for textarea...');
            
        static selectors = [
    // Basic elements
    'textarea',
    'input[type="text"]',
    'input[type="search"]',
    
    // Common IDs
    '#content',
    '#id_content',
    '#text',
    '#message',
    '#comment',
    '#post',
    '#description',
    '#body',
    '#editor',
    
    // Common names
    'textarea[name="content"]',
    'textarea[name="text"]',
    'textarea[name="message"]',
    'textarea[name="comment"]',
    'textarea[name="post"]',
    'textarea[name="description"]',
    'input[name="content"]',
    'input[name="text"]',
    
    // Common classes
    '.content-field',
    '.form-control',
    '.form-input',
    '.text-editor',
    '.editor',
    '.editable',
    '.textarea',
    '.input-text',
    '.content',
    '.post-content',
    '.message-text',
    '.comment-text',
    
    // Form contexts
    'form textarea',
    'form input[type="text"]',
    '.form textarea',
    '.form input[type="text"]',
    
    // Contenteditable
    '[contenteditable="true"]',
    
    // Data attributes
    '[data-predictor="true"]'
];',
            '[contenteditable="true"]',
            '.editable',
            '.editor',
            '.text-editor',
            'textarea[name="content"]',
            'textarea#id_content',
            '#id_content',
            '#content',
            '.content-field',
            'form textarea',
            'form input[type="text"]',
            '.form-control',
            '.form-input'
        ];
            
            for (const selector of selectors) {
                const textareas = document.querySelectorAll(selector);
                console.log(`  Checking selector "${selector}": found ${textareas.length} elements`);
                
                textareas.forEach((textarea, index) => {
                    if (!textarea.dataset.gpAttached) {
                        console.log(`    📝 Attaching to textarea #${index}:`, textarea);
                        this.setupTextarea(textarea);
                    } else {
                        console.log(`    ⏭️ Textarea #${index} already attached`);
                    }
                });
            }
        }
        
        observeForTextarea() {
            console.log('👀 Setting up MutationObserver...');
            
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.addedNodes.length) {
                        console.log('🔄 DOM changed, checking for new textareas...');
                        setTimeout(() => this.attachToTextarea(), 100);
                    }
                });
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
        
        setupTextarea(textarea) {
            try {
                console.log('🔧 Setting up textarea:', textarea);
                
                // Marquer comme attaché
                textarea.dataset.gpAttached = 'true';
                console.log('   ✓ Marked as attached');
                
                // Événements
                textarea.addEventListener('input', (e) => this.onInput(e));
                console.log('   ✓ Added input event');
                
                textarea.addEventListener('keydown', (e) => this.onKeyDown(e));
                console.log('   ✓ Added keydown event');
                
                // Mettre en place le placeholder pour la suggestion
                this.setupSuggestionDisplay(textarea);
                console.log('   ✓ Setup suggestion display');
                
                this.currentInput = textarea;
                console.log('   ✓ Set as current input');
                
            } catch (error) {
                console.error('❌ Error setting up textarea:', error);
            }
        }
        
        setupSuggestionDisplay(textarea) {
            // Créer un conteneur pour la suggestion
            const container = document.createElement('div');
            container.id = 'gp-suggestion-container';
            container.style.cssText = `
                position: absolute;
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                color: #666;
                display: none;
                z-index: 10000;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                font-family: Arial, sans-serif;
                pointer-events: none;
                white-space: nowrap;
            `;
            
            // Positionner près du textarea
            const rect = textarea.getBoundingClientRect();
            container.style.top = (rect.bottom + window.scrollY + 5) + 'px';
            container.style.left = (rect.left + window.scrollX) + 'px';
            
            document.body.appendChild(container);
            console.log('   📌 Created suggestion container');
        }
        
        onInput(e) {
            console.log('⌨️ Input event:', e.target.value);
            clearTimeout(this.debounceTimer);
            this.currentInput = e.target;
            
            const text = e.target.value;
            const cursorPos = e.target.selectionStart;
            
            // Prendre le mot en cours
            const textBefore = text.substring(0, cursorPos);
            const lastSpace = textBefore.lastIndexOf(' ');
            const currentWord = textBefore.substring(lastSpace + 1);
            
            console.log(`   Current word: "${currentWord}"`);
            
            if (currentWord.length < 1) {
                console.log('   Empty word, hiding suggestion');
                this.hideSuggestion();
                return;
            }
            
            this.debounceTimer = setTimeout(async () => {
                try {
                    console.log(`   🔍 Fetching suggestion for: "${currentWord}"`);
                    
                    const response = await fetch(
                        `${PREDICTOR_API}?text=${encodeURIComponent(currentWord)}&num_suggestions=1`
                    );
                    
                    console.log(`   Response status: ${response.status}`);
                    
                    if (!response.ok) {
                        console.log('   ❌ Bad response');
                        this.hideSuggestion();
                        return;
                    }
                    
                    const data = await response.json();
                    console.log('   📦 Response data:', data);
                    
                    if (data.success && data.suggestions && data.suggestions.length > 0) {
                        this.currentSuggestion = data.suggestions[0];
                        console.log(`   💡 Suggestion found: ${this.currentSuggestion}`);
                        this.showSuggestion(currentWord, this.currentSuggestion);
                    } else {
                        console.log('   ❌ No suggestions in response');
                        this.hideSuggestion();
                    }
                } catch (error) {
                    console.error('   💥 Fetch error:', error);
                    this.hideSuggestion();
                }
            }, 150);
        }
        
        showSuggestion(typedWord, suggestion) {
            console.log(`   🎯 Showing suggestion: ${typedWord} -> ${suggestion}`);
            
            const container = document.getElementById('gp-suggestion-container');
            if (!container) {
                console.log('   ❌ No suggestion container found');
                return;
            }
            
            // Vérifier la correspondance
            if (!suggestion.toLowerCase().startsWith(typedWord.toLowerCase())) {
                console.log('   ❌ Suggestion doesn\'t match typed word');
                this.hideSuggestion();
                return;
            }
            
            const completion = suggestion.substring(typedWord.length);
            if (!completion) {
                console.log('   ❌ No completion part');
                this.hideSuggestion();
                return;
            }
            
            // Mettre à jour le contenu
            container.innerHTML = `
                <span style="color: #333">${typedWord}</span>
                <span style="color: #666; font-style: italic">${completion}</span>
                <span style="color: #999; font-size: 11px; margin-left: 8px; background: #f0f0f0; padding: 2px 6px; border-radius: 3px; border: 1px solid #ddd;">Tab</span>
            `;
            
            // Positionner
            if (this.currentInput) {
                const rect = this.currentInput.getBoundingClientRect();
                container.style.top = (rect.bottom + window.scrollY + 5) + 'px';
                container.style.left = (rect.left + window.scrollX) + 'px';
                container.style.width = rect.width + 'px';
            }
            
            container.style.display = 'block';
            console.log('   ✅ Suggestion displayed');
        }
        
        onKeyDown(e) {
            if (!this.currentInput || !this.currentSuggestion) return;
            
            if (e.key === 'Tab') {
                console.log('   Tab pressed, accepting suggestion');
                e.preventDefault();
                
                const input = this.currentInput;
                const text = input.value;
                const cursorPos = input.selectionStart;
                
                // Remplacer le dernier mot
                const textBefore = text.substring(0, cursorPos);
                const lastSpace = textBefore.lastIndexOf(' ');
                const wordStart = (lastSpace === -1) ? 0 : lastSpace + 1;
                
                const newText = text.substring(0, wordStart) + 
                               this.currentSuggestion + ' ' + 
                               text.substring(cursorPos);
                
                input.value = newText;
                
                // Positionner le curseur
                const newPos = wordStart + this.currentSuggestion.length + 1;
                setTimeout(() => {
                    input.selectionStart = input.selectionEnd = newPos;
                    input.focus();
                }, 10);
                
                console.log(`   ✅ Inserted: ${this.currentSuggestion}`);
                
                this.hideSuggestion();
                
                // Déclencher nouvel input
                setTimeout(() => {
                    input.dispatchEvent(new Event('input'));
                }, 50);
            }
            
            if (e.key === 'Escape') {
                console.log('   Escape pressed, hiding suggestion');
                this.hideSuggestion();
            }
        }
        
        hideSuggestion() {
            const container = document.getElementById('gp-suggestion-container');
            if (container) {
                container.style.display = 'none';
            }
            this.currentSuggestion = '';
        }
    }
    
    // Initialisation
    console.log('🚀 Starting Google Predictor...');
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('📄 DOM fully loaded');
            window.googlePredictor = new GooglePredictor();
        });
    } else {
        console.log('📄 DOM already loaded');
        window.googlePredictor = new GooglePredictor();
    }
    
})();