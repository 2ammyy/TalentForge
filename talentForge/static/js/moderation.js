// static/js/moderation.js - MODERATION SYSTEM
class ContentModerator {
    constructor(options = {}) {
        // Configuration
        this.config = {
            inputSelector: options.inputSelector || '[data-moderation="true"]',
            endpoint: options.endpoint || '/check_content_safety/',
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
        
        // Créer la fenêtre d'alerte
        this.createAlertModal();
        
        // Attacher aux champs de formulaire
        this.attachToInputs();
        
        // Intercepter les soumissions de formulaire
        this.interceptFormSubmissions();
        
        console.log('✅ Content Moderator ready');
    }
    
    createAlertModal() {
        // Vérifier si la modal existe déjà
        if (document.getElementById('contentModerationModal')) return;
        
        const modalHTML = `
        <div class="content-moderation-modal" id="contentModerationModal">
            <div class="moderation-modal-overlay" id="moderationModalOverlay"></div>
            <div class="moderation-modal-container">
                <div class="moderation-modal-header">
                    <h3 class="modal-title">
                        <span class="modal-icon" id="modalIcon">⚠️</span>
                        <span id="modalTitle">Content Review</span>
                    </h3>
                    <button class="modal-close-btn" id="modalCloseBtn">
                        <span class="close-icon">✕</span>
                    </button>
                </div>
                
                <div class="moderation-modal-body">
                    <div class="alert-message" id="modalMessage">
                        Your content may violate our community guidelines. Please review and edit before proceeding.
                    </div>
                    
                    <div class="action-buttons">
                        <button class="btn-close-modal" id="btnCloseModal">
                            I understand
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Ajouter les événements
        document.getElementById('modalCloseBtn').addEventListener('click', () => this.hideModal());
        document.getElementById('moderationModalOverlay').addEventListener('click', () => this.hideModal());
        document.getElementById('btnCloseModal').addEventListener('click', () => this.hideModal());
        
        // Ajouter les styles CSS
        this.addModalStyles();
    }
    
    addModalStyles() {
        const style = document.createElement('style');
        style.textContent = `
        .content-moderation-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 9999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .moderation-modal-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(2px);
        }
        
        .moderation-modal-container {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 90%;
            max-width: 450px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
            animation: modalSlideIn 0.3s ease-out;
        }
        
        @keyframes modalSlideIn {
            from { 
                opacity: 0; 
                transform: translate(-50%, -60%);
            }
            to { 
                opacity: 1; 
                transform: translate(-50%, -50%);
            }
        }
        
        .moderation-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .modal-title {
            margin: 0;
            font-size: 1.4rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .modal-icon {
            font-size: 1.6rem;
        }
        
        .modal-close-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.1rem;
            transition: background 0.2s;
        }
        
        .modal-close-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .close-icon {
            line-height: 1;
        }
        
        .moderation-modal-body {
            padding: 24px;
        }
        
        .alert-message {
            font-size: 1rem;
            line-height: 1.5;
            margin-bottom: 20px;
            color: #333;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #1890ff;
            text-align: center;
        }
        
        .action-buttons {
            text-align: center;
        }
        
        .btn-close-modal {
            background: #1890ff;
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.95rem;
            transition: all 0.2s;
        }
        
        .btn-close-modal:hover {
            background: #1479d8;
            transform: translateY(-1px);
        }
        
        /* Styles pour les champs */
        .toxic-field {
            border: 2px solid #dc3545 !important;
            background-color: #fff5f5 !important;
        }
        
        .warning-field {
            border: 2px solid #ffc107 !important;
            background-color: #fff9db !important;
        }
        
        .moderation-feedback {
            margin-top: 8px;
            font-size: 0.875rem;
            padding: 8px 12px;
            border-radius: 4px;
            display: none;
        }
        
        .moderation-feedback.toxic {
            background: #fff5f5;
            border-left: 3px solid #dc3545;
            color: #dc3545;
        }
        
        .moderation-feedback.warning {
            background: #fff9db;
            border-left: 3px solid #ffc107;
            color: #856404;
        }
        
        .moderation-feedback.safe {
            background: #d4edda;
            border-left: 3px solid #28a745;
            color: #155724;
        }
        `;
        
        document.head.appendChild(style);
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
                                score: result.score
                            });
                        }
                    }
                }
                
                // Bloquer la soumission si contenu très toxique
                if (toxicFields.length > 0) {
                    e.preventDefault();
                    
                    // Afficher la modal d'alerte unique
                    this.showModal();
                    
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
            // Afficher la fenêtre modale pour contenu toxique
            this.showModal();
            
            // Mettre en évidence le champ
            const severity = result.score > this.config.blockThreshold ? 'toxic' : 'warning';
            this.highlightField(input, severity, result.score);
            
            // Afficher le feedback local (sans score)
            if (feedback) {
                feedback.className = `moderation-feedback ${severity}`;
                if (severity === 'toxic') {
                    feedback.innerHTML = `<div><strong>🚫 Content blocked:</strong> Please revise your message to comply with community guidelines.</div>`;
                } else {
                    feedback.innerHTML = `<div><strong>⚠️ Warning:</strong> Your content may need review.</div>`;
                }
                feedback.style.display = 'block';
            }
            
            // Désactiver la soumission si nécessaire
            this.toggleSubmission(input, result.score > this.config.blockThreshold);
            
        } else {
            // Contenu acceptable
            this.clearWarning(input);
            
            if (feedback) {
                feedback.className = 'moderation-feedback safe';
                feedback.innerHTML = `<div><strong>✅ Safe:</strong> Content meets community guidelines</div>`;
                feedback.style.display = 'block';
                setTimeout(() => { feedback.style.display = 'none'; }, 3000);
            }
        }
    }
    
    showModal() {
        const modal = document.getElementById('contentModerationModal');
        
        // Afficher la modal
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Fermer automatiquement après 8 secondes
        setTimeout(() => this.hideModal(), 8000);
    }
    
    hideModal() {
        const modal = document.getElementById('contentModerationModal');
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
    
    highlightField(input, severity, score) {
        // Retirer les anciennes classes
        input.classList.remove('toxic-field', 'warning-field');
        
        // Ajouter la nouvelle classe
        if (severity === 'toxic' || score > this.config.blockThreshold) {
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
            feedback.innerHTML = `<div>Checking content...</div>`;
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
            submitBtn.title = 'Please revise your message to comply with community guidelines.';
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
}

// Exposer la classe globalement
window.ContentModerator = ContentModerator;

// Initialisation automatique
document.addEventListener('DOMContentLoaded', function() {
    window.contentModerator = new ContentModerator();
});