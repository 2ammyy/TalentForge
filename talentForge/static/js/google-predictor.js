// CSS-POWERED WORD PREDICTOR (FINAL VERSION)
console.log("🎯 Word Predictor Active");

(function() {
    'use strict';
    
    const API_URL = '/word_prediction/predict/';
    let currentTextarea = null;
    let currentSuggestion = '';
    
    // Initialize
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(init, 1000);
    });
    
    function init() {
        console.log('🔍 Setting up word predictor...');
        
        // Find main content textarea
        const textarea = document.querySelector('#id_content, textarea[name="content"]');
        if (!textarea) {
            console.log('📭 No textarea found');
            return;
        }
        
        console.log('📝 Found:', textarea.id);
        setupPredictor(textarea);
    }
    
    function setupPredictor(textarea) {
        if (textarea.dataset.predictorSetup) return;
        textarea.dataset.predictorSetup = 'true';
        
        // Add container for prediction
        const container = document.createElement('div');
        container.className = 'predictor-wrapper';
        container.style.cssText = `
            position: relative;
            width: 100%;
            display: inline-block;
        `;
        
        // Wrap textarea
        const parent = textarea.parentNode;
        parent.insertBefore(container, textarea);
        container.appendChild(textarea);
        
        // Create prediction element
        const prediction = document.createElement('div');
        prediction.className = 'word-prediction';
        prediction.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            color: #888;
            font: inherit;
            line-height: inherit;
            padding: inherit;
            margin: inherit;
            border: inherit;
            background: transparent;
            z-index: 1;
            display: none;
            overflow: hidden;
            white-space: pre-wrap;
            box-sizing: border-box;
        `;
        
        container.appendChild(prediction);
        
        // Make textarea see-through
        textarea.style.backgroundColor = 'rgba(255, 255, 255, 0.7)';
        textarea.style.position = 'relative';
        textarea.style.zIndex = '2';
        
        // Add events
        let debounceTimer;
        
        textarea.addEventListener('input', (e) => {
            currentTextarea = textarea;
            clearTimeout(debounceTimer);
            
            const text = textarea.value;
            const cursor = textarea.selectionStart;
            const beforeCursor = text.substring(0, cursor);
            const lastSpace = beforeCursor.lastIndexOf(' ');
            const currentWord = beforeCursor.substring(lastSpace + 1);
            
            console.log(`⌨️ Word: "${currentWord}"`);
            
            if (currentWord.length < 2) {
                hidePrediction();
                return;
            }
            
            debounceTimer = setTimeout(async () => {
                try {
                    const response = await fetch(
                        `${API_URL}?text=${encodeURIComponent(currentWord)}&num_suggestions=1`
                    );
                    
                    if (!response.ok) {
                        console.log('❌ API error:', response.status);
                        return;
                    }
                    
                    const data = await response.json();
                    
                    if (data.success && data.suggestions?.[0]) {
                        const suggestion = data.suggestions[0];
                        
                        if (suggestion.toLowerCase().startsWith(currentWord.toLowerCase())) {
                            currentSuggestion = suggestion;
                            showPrediction(currentWord, suggestion);
                        } else {
                            hidePrediction();
                        }
                    } else {
                        hidePrediction();
                    }
                } catch (error) {
                    console.error('💥 Error:', error);
                    hidePrediction();
                }
            }, 300);
        });
        
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Tab' && currentSuggestion) {
                e.preventDefault();
                acceptPrediction();
            }
            
            if (e.key === 'Escape') {
                hidePrediction();
            }
        });
        
        textarea.addEventListener('blur', () => {
            setTimeout(hidePrediction, 200);
        });
        
        function showPrediction(typedWord, suggestion) {
            const completion = suggestion.substring(typedWord.length);
            if (!completion) {
                hidePrediction();
                return;
            }
            
            // Get cursor position
            const text = textarea.value;
            const cursor = textarea.selectionStart;
            const beforeCursor = text.substring(0, cursor);
            const lastSpace = beforeCursor.lastIndexOf(' ');
            const wordStart = lastSpace === -1 ? 0 : lastSpace + 1;
            
            // Build prediction text
            const beforeWord = text.substring(0, wordStart);
            const displayHTML = beforeWord + 
                              `<span style="opacity: 0">${typedWord}</span>` +
                              `<span style="color: #666; font-style: italic">${completion}</span>` +
                              `<span style="color: #aaa; font-size: 0.8em; margin-left: 5px">(Tab ↵)</span>`;
            
            prediction.innerHTML = displayHTML;
            prediction.style.display = 'block';
            
            console.log(`🟢 Showing: ${typedWord} → ${suggestion}`);
            
            // Force it to stay visible
            setTimeout(() => {
                if (prediction.style.display === 'block') {
                    console.log('✅ Prediction still visible');
                } else {
                    console.log('⚠️ Prediction was hidden, forcing show');
                    prediction.style.display = 'block';
                }
            }, 100);
        }
        
        function hidePrediction() {
            prediction.style.display = 'none';
            prediction.innerHTML = '';
            currentSuggestion = '';
        }
        
        function acceptPrediction() {
            const text = textarea.value;
            const cursor = textarea.selectionStart;
            const beforeCursor = text.substring(0, cursor);
            const lastSpace = beforeCursor.lastIndexOf(' ');
            const wordStart = lastSpace === -1 ? 0 : lastSpace + 1;
            
            // Insert suggestion
            textarea.value = text.substring(0, wordStart) + 
                           currentSuggestion + ' ' + 
                           text.substring(cursor);
            
            // Move cursor
            const newPos = wordStart + currentSuggestion.length + 1;
            setTimeout(() => {
                textarea.selectionStart = textarea.selectionEnd = newPos;
                textarea.focus();
            }, 10);
            
            console.log(`✅ Inserted: "${currentSuggestion}"`);
            
            hidePrediction();
            
            // Trigger next prediction
            setTimeout(() => {
                textarea.dispatchEvent(new Event('input'));
            }, 50);
        }
        
        console.log('✅ Predictor setup complete');
    }
    
})();