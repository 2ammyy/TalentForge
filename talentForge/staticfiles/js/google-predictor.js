// google-predictor.js - COMPLETE VERSION
console.log('=== GOOGLE-PREDICTOR.JS LOADING ===');
console.log('Loading time:', new Date().toLocaleTimeString());

// ========== ORIGINAL FUNCTIONS ==========
// Function to fetch predictions from server
function fetchPredictions(text, numSuggestions = 3) {
    console.log('Fetching predictions for:', text);
    
    fetch(`/word_prediction/predict/?text=${encodeURIComponent(text)}&num_suggestions=${numSuggestions}`)
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Prediction API response:', data);
            
            if (data.success && data.suggestions && data.suggestions.length > 0) {
                // Extract just the text from suggestions
                const predictions = data.suggestions.map(s => s.text);
                console.log('Parsed predictions:', predictions);
                
                // Show predictions in UI
                showPredictions(predictions);
                
                // Log service status for debugging
                if (data.service_status) {
                    console.log('Service status:', data.service_status);
                }
            } else {
                console.warn('No suggestions returned from API');
                showPredictions([]);
            }
        })
        .catch(error => {
            console.error('Error fetching predictions:', error);
            // Fallback to basic predictions
            const fallback = getFallbackPredictions(text);
            showPredictions(fallback);
        });
}

// Function to show predictions in UI
function showPredictions(predictions) {
    console.log('Showing predictions in UI:', predictions);
    
    const container = document.getElementById('predictions-container');
    if (!container) {
        console.warn('Predictions container not found');
        return;
    }
    
    container.innerHTML = '';
    
    if (predictions.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    predictions.forEach((prediction, index) => {
        const button = document.createElement('button');
        button.className = 'prediction-button';
        button.textContent = prediction;
        button.dataset.index = index;
        
        button.onclick = function() {
            acceptPrediction(prediction);
        };
        
        container.appendChild(button);
    });
    
    container.style.display = 'flex';
}

// Fallback function if API fails
function getFallbackPredictions(text) {
    text = text.toLowerCase().trim();
    
    // Basic fallback patterns
    const fallbacks = {
        '': ['the', 'i', 'you', 'a', 'to'],
        'i': ['am', 'have', 'want', 'need'],
        'you': ['are', 'can', 'have', 'should'],
        'he': ['is', 'was', 'has', 'said'],
        'she': ['is', 'was', 'has'],
        'we': ['are', 'can', 'have'],
        'they': ['are', 'have', 'were'],
        'hello': ['there', 'world', 'everyone'],
        'thank': ['you', 'god', 'goodness'],
        'good': ['morning', 'afternoon', 'evening']
    };
    
    // Check for exact matches
    if (fallbacks[text]) {
        return fallbacks[text];
    }
    
    // Check for partial matches
    for (const key in fallbacks) {
        if (text.startsWith(key)) {
            return fallbacks[key];
        }
    }
    
    // Default fallback
    return ['the', 'to', 'and', 'you', 'that'];
}

// Test the API directly
function testPredictionAPI() {
    console.log('Testing prediction API...');
    
    const testCases = ['he', 'hello', 'wan', 'thank', 'good'];
    
    testCases.forEach(text => {
        fetch(`/word_prediction/predict/?text=${encodeURIComponent(text)}&num_suggestions=3`)
            .then(response => response.json())
            .then(data => {
                console.log(`Test case "${text}":`, data);
            })
            .catch(error => {
                console.error(`Test case "${text}" failed:`, error);
            });
    });
}

// ========== NEW INITIALIZATION CODE ==========
// Auto-attach to content textarea
function initializeWordPredictor() {
    console.log('Initializing word predictor...');
    
    // Wait a bit for DOM to be fully loaded
    setTimeout(() => {
        const textarea = document.getElementById('id_content') || 
                        document.querySelector('textarea[name="content"]');
        
        if (textarea) {
            console.log('Found textarea for word prediction:', textarea);
            
            // Create predictions container
            let container = document.getElementById('predictions-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'predictions-container';
                container.className = 'predictions-container';
                textarea.parentNode.insertBefore(container, textarea.nextSibling);
            }
            
            // Set up input event
            let timeoutId;
            textarea.addEventListener('input', function(e) {
                clearTimeout(timeoutId);
                
                // Debounce the request
                timeoutId = setTimeout(() => {
                    const text = this.value;
                    const cursorPos = this.selectionStart;
                    
                    // Get the current word being typed
                    const textBeforeCursor = text.substring(0, cursorPos);
                    const words = textBeforeCursor.split(/\s+/);
                    const currentWord = words[words.length - 1] || '';
                    
                    console.log('Current word for prediction:', currentWord);
                    
                    if (currentWord.length > 0) {
                        fetchPredictions(currentWord, 5);
                    } else {
                        showPredictions([]);
                    }
                }, 200); // 200ms delay
            });
            
            // Handle clicks on predictions
            document.addEventListener('click', function(e) {
                if (e.target.classList.contains('prediction-button')) {
                    acceptPrediction(e.target.textContent, textarea);
                }
            });
            
            console.log('Word predictor initialized successfully');
        } else {
            console.warn('Textarea not found for word prediction');
        }
    }, 1000);
}

// Function to accept prediction
function acceptPrediction(prediction, textarea = null) {
    if (!textarea) {
        textarea = document.getElementById('id_content') || 
                  document.querySelector('textarea[name="content"]');
    }
    
    if (!textarea) return;
    
    const cursorPos = textarea.selectionStart;
    const text = textarea.value;
    const textBeforeCursor = text.substring(0, cursorPos);
    const textAfterCursor = text.substring(cursorPos);
    
    // Find the current word
    const words = textBeforeCursor.split(/\s+/);
    const currentWord = words[words.length - 1] || '';
    
    // Replace current word with prediction
    const newTextBefore = textBeforeCursor.substring(0, textBeforeCursor.length - currentWord.length);
    const newText = newTextBefore + prediction + ' ' + textAfterCursor;
    
    textarea.value = newText;
    
    // Move cursor after prediction + space
    const newCursorPos = cursorPos - currentWord.length + prediction.length + 1;
    textarea.setSelectionRange(newCursorPos, newCursorPos);
    textarea.focus();
    
    // Clear predictions
    showPredictions([]);
    
    // Send feedback to improve model
    sendFeedbackToServer(currentWord, prediction);
}

// Send feedback to server
function sendFeedbackToServer(prefix, acceptedWord) {
    fetch('/word_prediction/feedback/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            prefix: prefix,
            accepted_word: acceptedWord
        })
    }).catch(error => console.error('Feedback error:', error));
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing word predictor...');
    initializeWordPredictor();
    testPredictionAPI(); // Optional: keep test
});

// Export functions for testing
window.fetchPredictions = fetchPredictions;
window.showPredictions = showPredictions;
window.testPredictionAPI = testPredictionAPI;
window.initializeWordPredictor = initializeWordPredictor;
console.log('=== GOOGLE-PREDICTOR.JS LOADED SUCCESSFULLY ===');