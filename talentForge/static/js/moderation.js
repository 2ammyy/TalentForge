// static/js/moderation.js
class ContentModerator {
    constructor(options = {}) {
        // Configuration
        this.config = {
            inputSelector: options.inputSelector || '[data-moderation="true"]',
            endpoint: options.endpoint || '/api/check-content-safety/',
            minLength: options.minLength || 3,
            checkInterval: options.checkInterval || 800,
            warningThreshold: options.warningThreshold || 0.6,
            blockThreshold: options.blockThreshold || 0.8,
            ...options
        };
        
        // État
        this.debounceTimer = null;
        this.lastCheckedText = '';
        this.activeInput = null;
        
        // Initialisation
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Content Moderator');
        
        // Attacher aux champs de formulaire
        this.attachToInputs();
        
        // Intercepter les soumissions de formulaire
        this.interceptFormSubmissions();
        
        console.log('✅ Content Moderator ready');
    }
    
    attachToInputs() {
        const inputs = document.querySelectorAll(this.config.inputSelector);
        
        inputs.forEach(input => {
            // Ajouter attribut data-moderation si non présent
            if (!input.hasAttribute('data-moderation')) {
                input.setAttribute('data-moderation', 'true');
            }
            
            // Événements
            input.addEventListener('input', this.debounceCheck.bind(this, input));
            input.addEventListener('blur', this.clearWarning.bind(this, input));
            input.addEventListener('focus', () => { this.activeInput = input; });
            
            // Ajouter un conteneur pour les feedbacks
            if (!input.nextElementSibling?.classList.contains('moderation-feedback')) {
                const feedback = document.createElement('div');
                feedback.className = 'moderation-feedback';
                input.parentNode.insertBefore(feedback, input.nextSibling);
            }
        });
        
        console.log(`📝 Monitoring ${inputs.length} input field(s)`);
    }
    
    interceptFormSubmissions() {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', async (e) => {
                // Vérifier tous les champs avant soumission
                const toxicFields = [];
                const inputs = form.querySelectorAll(this.config.inputSelector);
                
                for (const input of inputs) {
                    if (input.value.trim().length >= this.config.minLength) {
                        const result = await this.checkContent(input.value);
                        if (result.is_toxic && result.score > this.config.blockThreshold) {
                            toxicFields.push({
                                input: input,
                                score: result.score,
                                message: result.warning
                            });
                        }
                    }
                }
                
                // Bloquer la soumission si contenu très toxique
                if (toxicFields.length > 0) {
                    e.preventDefault();
                    
                    // Afficher l'alerte principale
                    const worstField = toxicFields.reduce((prev, current) => 
                        prev.score > current.score ? prev : current
                    );
                    
                    this.showAlert(
                        '🚫 Soumission bloquée',
                        `Contenu fortement inapproprié détecté. Score: ${(worstField.score * 100).toFixed(1)}%`,
                        worstField.score,
                        'danger'
                    );
                    
                    // Mettre en évidence les champs problématiques
                    toxicFields.forEach(field => {
                        this.highlightField(field.input, 'toxic', field.score);
                    });
                    
                    return false;
                }
            });
        });
    }
    
    debounceCheck(input) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.performCheck(input);
        }, this.config.checkInterval);
    }
    
    async performCheck(input) {
        const text = input.value.trim();
        
        // Vérifications basiques
        if (text.length < this.config.minLength || text === this.lastCheckedText) {
            this.clearWarning(input);
            return;
        }
        
        this.lastCheckedText = text;
        this.activeInput = input;
        
        // Afficher un indicateur de chargement
        this.showLoading(input);
        
        try {
            const result = await this.checkContent(text);
            this.handleCheckResult(input, result);
        } catch (error) {
            console.error('Moderation check failed:', error);
            this.clearWarning(input);
        }
    }
    
    async checkContent(text) {
        const response = await fetch(this.config.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({ text: text })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    handleCheckResult(input, result) {
        const feedback = input.nextElementSibling?.classList.contains('moderation-feedback') 
            ? input.nextElementSibling 
            : null;
        
        if (result.is_toxic) {
            // Déterminer le niveau de sévérité
            let severity = 'info';
            let icon = 'ℹ️';
            let title = 'Langage potentiellement offensant';
            
            if (result.score > this.config.blockThreshold) {
                severity = 'danger';
                icon = '🚫';
                title = 'Contenu bloqué';
            } else if (result.score > this.config.warningThreshold) {
                severity = 'warning';
                icon = '⚠️';
                title = 'Contenu inapproprié';
            }
            
            // Afficher l'alerte globale
            this.showAlert(title, result.warning, result.score, severity);
            
            // Mettre en évidence le champ
            this.highlightField(input, severity, result.score);
            
            // Afficher le feedback local
            if (feedback) {
                feedback.innerHTML = `
                    <div class="small text-${severity}">
                        <i class="fas fa-exclamation-circle me-1"></i>
                        ${result.warning}
                        <div class="toxicity-score-bar mt-1">
                            <div class="toxicity-score-fill score-${result.score > 0.8 ? 'high' : result.score > 0.6 ? 'medium' : 'low'}" 
                                 style="width: ${result.score * 100}%"></div>
                        </div>
                        <small>Toxicité: ${(result.score * 100).toFixed(1)}%</small>
                    </div>
                `;
                feedback.style.display = 'block';
            }
            
            // Désactiver la soumission si nécessaire
            this.toggleSubmission(input, result.score > this.config.blockThreshold);
            
        } else {
            // Contenu acceptable
            this.clearWarning(input);
            
            if (feedback) {
                feedback.innerHTML = `
                    <div class="small text-success">
                        <i class="fas fa-check-circle me-1"></i>
                        Contenu acceptable
                    </div>
                `;
                setTimeout(() => { feedback.style.display = 'none'; }, 2000);
            }
        }
    }
    
    showAlert(title, message, score, severity = 'warning') {
        const alert = document.getElementById('contentModerationAlert');
        if (!alert) return;
        
        // Mettre à jour le contenu
        alert.querySelector('.alert-title').textContent = title;
        alert.querySelector('.alert-message').textContent = message;
        alert.querySelector('.score-text').textContent = `Score: ${(score * 100).toFixed(1)}%`;
        
        // Mettre à jour la barre de score
        const scoreFill = alert.querySelector('.toxicity-score-fill');
        scoreFill.style.width = `${score * 100}%`;
        scoreFill.className = `toxicity-score-fill score-${score > 0.8 ? 'high' : score > 0.6 ? 'medium' : 'low'}`;
        
        // Mettre à jour l'icône
        const iconMap = {
            'danger': '🚫',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        alert.querySelector('.alert-icon').textContent = iconMap[severity] || '⚠️';
        
        // Appliquer les classes de sévérité
        alert.className = `content-moderation-alert ${severity}`;
        if (score > 0.7) {
            alert.classList.add('shake');
            setTimeout(() => alert.classList.remove('shake'), 500);
        }
        
        // Afficher
        alert.style.display = 'block';
        
        // Auto-fermeture
        setTimeout(() => {
            if (alert.style.display === 'block') {
                alert.style.display = 'none';
            }
        }, 8000);
    }
    
    highlightField(input, severity, score) {
        // Retirer les anciennes classes
        input.classList.remove('toxic-field', 'warning-field');
        
        // Ajouter la nouvelle classe
        if (severity === 'danger' || score > this.config.blockThreshold) {
            input.classList.add('toxic-field');
        } else if (severity === 'warning' || score > this.config.warningThreshold) {
            input.classList.add('warning-field');
        }
    }
    
    clearWarning(input) {
        input.classList.remove('toxic-field', 'warning-field');
        
        const feedback = input.nextElementSibling?.classList.contains('moderation-feedback') 
            ? input.nextElementSibling 
            : null;
        if (feedback) {
            feedback.style.display = 'none';
        }
        
        this.toggleSubmission(input, false);
    }
    
    showLoading(input) {
        const feedback = input.nextElementSibling?.classList.contains('moderation-feedback') 
            ? input.nextElementSibling 
            : null;
        if (feedback) {
            feedback.innerHTML = `
                <div class="small text-muted">
                    <i class="fas fa-spinner fa-spin me-1"></i>
                    Vérification en cours...
                </div>
            `;
            feedback.style.display = 'block';
        }
    }
    
    toggleSubmission(input, shouldDisable) {
        const form = input.closest('form');
        if (!form) return;
        
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (!submitBtn) return;
        
        if (shouldDisable) {
            submitBtn.disabled = true;
            submitBtn.classList.add('disabled');
            submitBtn.title = 'Contenu inapproprié détecté. Veuillez réviser votre message.';
        } else {
            submitBtn.disabled = false;
            submitBtn.classList.remove('disabled');
            submitBtn.title = '';
        }
    }
    
    getCsrfToken() {
        const name = 'csrftoken';
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
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Exposer la classe globalement
window.ContentModerator = ContentModerator;

// Initialisation automatique si configurée
if (document.currentScript?.hasAttribute('data-auto-init')) {
    document.addEventListener('DOMContentLoaded', function() {
        window.contentModerator = new ContentModerator();
    });
}