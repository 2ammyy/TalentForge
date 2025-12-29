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