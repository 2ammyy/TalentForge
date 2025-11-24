// talentForge\static\js\main.js

// ========== FONCTIONS GLOBALES ==========

// Fonctions globales
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing TalentForge...');
    
    // Fonctions existantes
    autoDismissAlerts();
    initTooltips();
    initPostCreation();
    initMessagingFeatures();
    initPostFilters();
    initPalestineFlag();
    
    // Nouvelles fonctions pour les posts
    initPostDropdowns();
    initPostReactions();
    
    // Debug: Vérifier l'état des posts et dropdowns
    setTimeout(() => {
        debugPostPage();
    }, 1000);
});

// Auto-dismiss des alertes après 5 secondes
function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (error) {
                console.log('Alert auto-dismissed');
            }
        }, 5000);
    });
}

// Initialisation des tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Toggle password visibility
function togglePassword(inputId, button) {
    const passwordInput = document.getElementById(inputId);
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        button.innerHTML = '🙈';
    } else {
        passwordInput.type = 'password';
        button.innerHTML = '👁️';
    }
}

// CSRF Token pour les requêtes AJAX
function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

// Toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0`;
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// ========== FONCTIONNALITÉS DE CRÉATION DE POSTS ==========

function initPostCreation() {
    const postForm = document.getElementById('postForm');
    if (!postForm) return;

    const postTypeSelect = document.getElementById('id_type');
    const dynamicSections = document.getElementById('dynamic-sections');
    const defaultSection = document.getElementById('default-section');
    const jobSection = document.getElementById('job-section');
    const charCounter = document.getElementById('charCounter');
    const contentTextarea = document.getElementById('id_content');
    const charCount = document.getElementById('charCount');
    const fileInputs = {
        image: document.getElementById('id_image'),
        video: document.getElementById('id_video')
    };
    const filePreviews = document.getElementById('filePreviews');
    const submitBtn = document.getElementById('submitBtn');
    
    if (postTypeSelect && dynamicSections) {
        // Gestion du changement de type de post
        postTypeSelect.addEventListener('change', function() {
            updateFormForPostType(this.value);
        });
        
        function updateFormForPostType(type) {
            // Masquer toutes les sections
            if (defaultSection) defaultSection.style.display = 'none';
            if (jobSection) jobSection.style.display = 'none';
            if (charCounter) charCounter.style.display = 'block';
            
            // Reset file inputs when type changes
            Object.values(fileInputs).forEach(input => {
                if (input) input.value = '';
            });
            if (filePreviews) filePreviews.innerHTML = '';
            
            // Afficher la section appropriée
            switch(type) {
                case 'text':
                case 'image':
                case 'video':
                    if (defaultSection) defaultSection.style.display = 'block';
                    updatePlaceholder(type);
                    break;
                case 'job':
                    if (jobSection) jobSection.style.display = 'block';
                    if (charCounter) charCounter.style.display = 'none';
                    updateJobPlaceholders();
                    break;
            }
        }
        
        function updatePlaceholder(type) {
            if (!contentTextarea) return;
            switch(type) {
                case 'text':
                    contentTextarea.placeholder = "What's on your mind?";
                    break;
                case 'image':
                    contentTextarea.placeholder = "Describe your image...";
                    break;
                case 'video':
                    contentTextarea.placeholder = "Describe your video...";
                    break;
            }
        }
        
        function updateJobPlaceholders() {
            if (contentTextarea) {
                contentTextarea.placeholder = "Describe the job responsibilities, requirements, and what makes this opportunity special...";
            }
        }
        
        // Character counter
        if (contentTextarea && charCount) {
            contentTextarea.addEventListener('input', function() {
                const length = this.value.length;
                charCount.textContent = length;
                
                if (length > 5000) {
                    charCount.style.color = '#dc3545';
                    if (submitBtn) submitBtn.disabled = true;
                } else {
                    charCount.style.color = '#666';
                    if (submitBtn) submitBtn.disabled = false;
                }
            });
        }
        
        // File preview handling
        Object.keys(fileInputs).forEach(type => {
            const input = fileInputs[type];
            if (input && filePreviews) {
                input.addEventListener('change', function(e) {
                    const file = e.target.files[0];
                    if (file) {
                        createFilePreview(file, type);
                    }
                });
            }
        });
        
        function createFilePreview(file, type) {
            const preview = document.createElement('div');
            preview.className = 'file-preview';
            
            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-file';
            removeBtn.innerHTML = '×';
            removeBtn.onclick = function() {
                preview.remove();
                if (fileInputs[type]) fileInputs[type].value = '';
            };
            
            if (type === 'image' && file.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                preview.appendChild(img);
            } else if (type === 'video' && file.type.startsWith('video/')) {
                const video = document.createElement('video');
                video.src = URL.createObjectURL(file);
                video.controls = true;
                video.style.maxWidth = '200px';
                preview.appendChild(video);
            } else {
                const docIcon = document.createElement('div');
                docIcon.innerHTML = `📄 ${file.name}`;
                docIcon.style.padding = '1rem';
                preview.appendChild(docIcon);
            }
            
            preview.appendChild(removeBtn);
            filePreviews.appendChild(preview);
        }
        
        // Initialize form based on current type
        if (postTypeSelect.value) {
            updateFormForPostType(postTypeSelect.value);
        }
    }
}

// ========== FONCTIONNALITÉS DE MESSAGERIE ==========

function initMessagingFeatures() {
    // Auto-scroll vers le bas dans les conversations
    const messagesList = document.querySelector('.messages-list');
    if (messagesList) {
        messagesList.scrollTop = messagesList.scrollHeight;
    }
    
    // Auto-focus sur le champ de message
    const messageInput = document.querySelector('textarea[name="content"]');
    if (messageInput) {
        messageInput.focus();
    }
    
    // Marquer les messages comme lus
    markMessagesAsRead();
}

function markMessagesAsRead() {
    // Implémentation pour marquer les messages comme lus via AJAX
    const unreadMessages = document.querySelectorAll('.conversation-item.unread');
    if (unreadMessages.length > 0) {
        // Ici vous pouvez ajouter une requête AJAX pour marquer comme lus
        console.log('Marking messages as read...');
    }
}

// ========== FONCTIONS POUR LES DROPDOWNS DES POSTS ==========

function initPostDropdowns() {
    console.log('🎯 Initializing post dropdowns...');
    
    // Vérifier si Bootstrap est disponible
    if (typeof bootstrap !== 'undefined') {
        console.log('✅ Bootstrap loaded, initializing dropdowns with Bootstrap');
        
        // Initialiser tous les dropdowns avec Bootstrap
        const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
        console.log(`🔍 Found ${dropdownToggles.length} dropdown toggles`);
        
        dropdownToggles.forEach((toggle, index) => {
            try {
                const dropdown = new bootstrap.Dropdown(toggle);
                
                // Debug events
                toggle.addEventListener('show.bs.dropdown', function() {
                    console.log('📂 Dropdown opening:', this);
                });
                
                toggle.addEventListener('shown.bs.dropdown', function() {
                    console.log('✅ Dropdown opened successfully');
                });
                
            } catch (error) {
                console.error('❌ Error initializing dropdown:', error);
            }
        });
        
    } else {
        console.log('⚠️ Bootstrap not available, using vanilla JS for dropdowns');
        initVanillaDropdowns();
    }
}

// Solution de secours vanilla JS
function initVanillaDropdowns() {
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const dropdownMenu = this.nextElementSibling;
            const isVisible = dropdownMenu.style.display === 'block';
            
            // Fermer tous les autres dropdowns
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.style.display = 'none';
            });
            
            // Ouvrir/fermer le dropdown actuel
            if (!isVisible) {
                dropdownMenu.style.display = 'block';
                console.log('📂 Vanilla dropdown opened');
            }
        });
    });
    
    // Fermer les dropdowns en cliquant ailleurs
    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.style.display = 'none';
        });
    });
    
    // Empêcher la fermeture quand on clique dans le dropdown
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
}

// ========== FONCTIONS POUR LES RÉACTIONS ==========

function initPostReactions() {
    document.querySelectorAll('.reaction-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const postId = this.dataset.postId;
            const reactionType = this.dataset.reactionType;
            
            if (postId) {
                addReaction(postId, reactionType, this);
            } else {
                console.error('❌ No post ID found for reaction');
            }
        });
    });
}

function addReaction(postId, reactionType, buttonElement) {
    console.log('❤️ Adding reaction for post:', postId);
    
    // Optimistic UI update
    buttonElement.classList.add('liked');
    const originalHTML = buttonElement.innerHTML;
    buttonElement.innerHTML = '<i class="fas fa-heart"></i> Liked!';
    buttonElement.disabled = true;
    
    fetch(`/posts/reaction/${postId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            'reaction_type': reactionType
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const reactionCount = document.querySelector(`#reaction-count-${postId}`);
            if (reactionCount) {
                reactionCount.textContent = data.total_reactions;
                reactionCount.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    reactionCount.style.transform = 'scale(1)';
                }, 300);
            }
        } else {
            resetReactionButton(buttonElement, originalHTML);
            showToast('Error adding reaction: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('💥 Reaction error:', error);
        resetReactionButton(buttonElement, originalHTML);
        showToast('Error adding reaction. Please try again.', 'error');
    });
}

function resetReactionButton(buttonElement, originalHTML) {
    buttonElement.classList.remove('liked');
    buttonElement.innerHTML = originalHTML;
    buttonElement.disabled = false;
}

// ========== FONCTIONS DE FILTRES ==========

function initPostFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const postCards = document.querySelectorAll('.post-card');
    
    if (filterButtons.length > 0 && postCards.length > 0) {
        filterButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const filter = this.dataset.filter;
                
                filterButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                postCards.forEach(card => {
                    if (filter === 'all' || card.dataset.postType === filter) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }
}

// ========== FONCTIONS DE SUIVI D'APPLICATIONS ==========

function trackJobApplication(jobTitle, company, emailService) {
    console.log(`📧 Application started for: ${jobTitle} at ${company} via ${emailService}`);
    // Ici vous pouvez ajouter du tracking analytics
}

// ========== FONCTION POUR L'ANIMATION DU DRAPEAU PALESTINE ==========

function initPalestineFlag() {
    const flag = document.querySelector('.palestine-flag');
    if (flag) {
        // Animation au survol
        flag.addEventListener('mouseenter', () => {
            flag.style.animation = 'wave 0.8s ease-in-out infinite';
        });
        
        flag.addEventListener('mouseleave', () => {
            flag.style.animation = 'wave 3s ease-in-out infinite';
        });

        // Effet de clic
        flag.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Créer un effet de particules
            createFlagParticles();
        });
    }
}

// Fonction pour créer des particules d'animation
function createFlagParticles() {
    const flag = document.querySelector('.palestine-flag');
    if (!flag) return;

    const flagRect = flag.getBoundingClientRect();
    const colors = ['#000000', '#FFFFFF', '#009736', '#E4312B'];
    
    for (let i = 0; i < 15; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: fixed;
            width: 4px;
            height: 4px;
            background-color: ${colors[Math.floor(Math.random() * colors.length)]};
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            left: ${flagRect.left + flagRect.width / 2}px;
            top: ${flagRect.top + flagRect.height / 2}px;
        `;
        
        document.body.appendChild(particle);
        
        // Animation de la particule
        const angle = Math.random() * Math.PI * 2;
        const velocity = 2 + Math.random() * 3;
        const vx = Math.cos(angle) * velocity;
        const vy = Math.sin(angle) * velocity;
        
        let opacity = 1;
        const animateParticle = () => {
            opacity -= 0.02;
            particle.style.opacity = opacity;
            particle.style.transform = `translate(${vx * (1 - opacity) * 50}px, ${vy * (1 - opacity) * 50}px)`;
            
            if (opacity > 0) {
                requestAnimationFrame(animateParticle);
            } else {
                particle.remove();
            }
        };
        
        animateParticle();
    }
}

// ========== FONCTIONS DE DÉBOGAGE ==========

// Fonction de débogage pour vérifier l'état de la page
function debugPostPage() {
    console.log('🐛 DEBUG Post Page:');
    
    // Vérifier les posts
    const posts = document.querySelectorAll('.post-card');
    console.log(`📝 Found ${posts.length} posts`);
    
    // Vérifier les dropdowns
    const dropdowns = document.querySelectorAll('.dropdown');
    console.log(`🎯 Found ${dropdowns.length} dropdowns`);
    
    // Vérifier les boutons de like
    const likeButtons = document.querySelectorAll('.like-btn');
    console.log(`❤️ Found ${likeButtons.length} like buttons`);
    
    // Vérifier Bootstrap
    if (typeof bootstrap !== 'undefined') {
        console.log('✅ Bootstrap is available');
    } else {
        console.error('❌ Bootstrap is NOT available');
    }
    
    // Vérifier l'utilisateur connecté
    const userElements = document.querySelectorAll('[data-user]');
    console.log(`👤 User elements: ${userElements.length}`);
    
    // Vérifier les IDs des posts
    posts.forEach((post, index) => {
        const postId = post.dataset.postId;
        const postType = post.dataset.postType;
        console.log(`📄 Post ${index + 1}: ID=${postId}, Type=${postType}`);
        
        // Vérifier que tous les liens ont le bon ID
        const links = post.querySelectorAll('a[href*="/posts/"]');
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && postId && !href.includes(postId)) {
                console.warn(`⚠️ Link mismatch: ${href} doesn't match post ID ${postId}`);
            }
        });
    });
}

// ========== GESTIONNAIRES D'ÉVÉNEMENTS GLOBAUX ==========

// Gestion des réactions
document.addEventListener('click', function(e) {
    if (e.target.closest('.reaction-btn')) {
        const btn = e.target.closest('.reaction-btn');
        const postId = btn.dataset.postId;
        const reactionType = btn.dataset.reactionType;
        
        if (postId && reactionType) {
            addReaction(postId, reactionType, btn);
        } else {
            console.error('❌ Missing post ID or reaction type');
        }
    }
});

// Gestion des applications d'emploi
document.addEventListener('click', function(e) {
    if (e.target.closest('.gmail-btn, .outlook-btn, .default-email-btn')) {
        const btn = e.target.closest('.gmail-btn, .outlook-btn, .default-email-btn');
        const jobCard = btn.closest('.job-details-content');
        if (jobCard) {
            const jobTitle = jobCard.querySelector('.job-title')?.textContent || 'Unknown Job';
            const company = jobCard.querySelector('.company-name')?.textContent || 'Unknown Company';
            const emailService = btn.classList.contains('gmail-btn') ? 'Gmail' : 
                               btn.classList.contains('outlook-btn') ? 'Outlook' : 'Default Email';
            
            trackJobApplication(jobTitle, company, emailService);
        }
    }
});

// Gestion des filtres de posts
document.addEventListener('DOMContentLoaded', function() {
    initPostFilters();
});

// ========== FONCTIONS UTILITAIRES ==========

// Fonction pour valider les emails
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Fonction pour formater les dates
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// Fonction pour copier le texte dans le presse-papier
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showToast('Failed to copy to clipboard', 'error');
    });
}

// Export des fonctions pour une utilisation globale (si nécessaire)
window.TalentForge = {
    showToast,
    copyToClipboard,
    formatDate,
    isValidEmail
};