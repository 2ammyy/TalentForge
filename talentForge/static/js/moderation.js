// static/js/moderation.js
document.addEventListener('DOMContentLoaded', function() {
    // Find post and comment textareas
    const textareas = document.querySelectorAll('textarea[name="content"], textarea[name="comment"]');
    
    textareas.forEach(textarea => {
        // Add warning container
        const warningDiv = document.createElement('div');
        warningDiv.className = 'toxicity-warning alert alert-danger mt-2';
        warningDiv.style.display = 'none';
        warningDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span class="warning-text"></span>
            <small class="d-block mt-1">Please modify your text before posting.</small>
        `;
        textarea.parentNode.insertBefore(warningDiv, textarea.nextSibling);
        
        // Find submit button
        const form = textarea.closest('form');
        const submitBtn = form ? form.querySelector('button[type="submit"]') : null;
        
        // Check content as user types
        let debounceTimer;
        textarea.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(checkContent, 800);
            
            if (submitBtn) submitBtn.disabled = false;
        });
        
        function checkContent() {
            const content = textarea.value.trim();
            
            if (content.length < 5) {
                warningDiv.style.display = 'none';
                if (submitBtn) submitBtn.disabled = false;
                return;
            }
            
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Check toxicity
            fetch('/posts/check-toxicity/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken,
                },
                body: 'content=' + encodeURIComponent(content)
            })
            .then(response => response.json())
            .then(data => {
                if (data.is_toxic) {
                    // Show warning
                    warningDiv.querySelector('.warning-text').textContent = 
                        `Inappropriate content detected (${(data.score * 100).toFixed(0)}% confidence)`;
                    warningDiv.style.display = 'block';
                    
                    // Disable submit button
                    if (submitBtn) {
                        submitBtn.disabled = true;
                        submitBtn.title = "Cannot submit: Content contains inappropriate language";
                    }
                    
                    textarea.style.borderColor = '#dc3545';
                } else {
                    warningDiv.style.display = 'none';
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.title = "";
                    }
                    textarea.style.borderColor = '';
                }
            });
        }
        
        // Final check on form submission
        if (form) {
            form.addEventListener('submit', function(e) {
                const content = textarea.value.trim();
                if (content.length >= 5) {
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                    
                    // Quick synchronous check
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', '/posts/check-toxicity/', false);
                    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                    xhr.setRequestHeader('X-CSRFToken', csrfToken);
                    xhr.send('content=' + encodeURIComponent(content));
                    
                    if (xhr.status === 200) {
                        const response = JSON.parse(xhr.responseText);
                        if (response.is_toxic) {
                            e.preventDefault();
                            alert(`Cannot submit: Content contains inappropriate language (${(response.score * 100).toFixed(0)}% confidence)`);
                        }
                    }
                }
            });
        }
    });
});