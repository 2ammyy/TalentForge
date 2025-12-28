// talentForge\static\js\main.js - VERSION COMPLÈTE AMÉLIORÉE

// ========== INITIALISATION GLOBALE ==========
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 Initializing TalentForge Creative Platform...');
    
    // Fonctions de base
    autoDismissAlerts();
    initTooltips();
    initCreativeThemeToggle();
    
    // Fonctionnalités créatives
    initPostCreation();
    initArtisticDropdowns();
    initCreativeReactions();
    initArtisticFilters();
    initCreativeMessaging();
    initArtisticVideos();
    initCreativeGallery();
    
    // Fonctions utilitaires
    initCreativeAnimations();
    initCreativeModals();
    initCreativeNotifications();
    
    // Debug et monitoring
    debugCreativePlatform();
    
    console.log('✅ TalentForge Creative Platform initialized successfully!');
});

// ========== FONCTIONS DE BASE AMÉLIORÉES ==========

// Auto-dismiss des alertes avec animation
function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                // Animation de sortie
                alert.style.opacity = '1';
                let opacity = 1;
                const fadeOut = setInterval(() => {
                    opacity -= 0.05;
                    alert.style.opacity = opacity;
                    if (opacity <= 0) {
                        clearInterval(fadeOut);
                        bsAlert.close();
                    }
                }, 50);
            } catch (error) {
                console.log('Alert auto-dismissed');
            }
        }, 5000);
    });
}

// Initialisation des tooltips créatifs
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            animation: true,
            delay: { "show": 100, "hide": 100 }
        });
    });
}

// Toggle password avec animation
function togglePassword(inputId, button) {
    const passwordInput = document.getElementById(inputId);
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        button.innerHTML = '🙈';
        button.style.transform = 'rotate(180deg)';
    } else {
        passwordInput.type = 'password';
        button.innerHTML = '👁️';
        button.style.transform = 'rotate(0deg)';
    }
    
    // Animation
    button.style.transition = 'transform 0.3s ease';
    setTimeout(() => {
        button.style.transform = '';
    }, 300);
}

// ========== THÈME CRÉATIF ==========

function initCreativeThemeToggle() {
    const themeToggle = document.querySelector('.creative-mode-toggle');
    const themeButtons = document.querySelectorAll('[data-theme]');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.body.dataset.theme || 'default';
            const themes = ['default', 'painter', 'designer', 'photographer', 'musician'];
            const currentIndex = themes.indexOf(currentTheme);
            const nextTheme = themes[(currentIndex + 1) % themes.length];
            
            // Appliquer le nouveau thème
            applyCreativeTheme(nextTheme, this);
        });
    }
    
    // Boutons de thème spécifiques
    themeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const theme = this.dataset.theme;
            applyCreativeTheme(theme, this);
        });
    });
}

function applyCreativeTheme(theme, buttonElement) {
    // Retirer tous les thèmes
    document.body.classList.remove('theme-painter', 'theme-designer', 'theme-photographer', 'theme-musician');
    
    // Appliquer le nouveau thème
    if (theme !== 'default') {
        document.body.classList.add(`theme-${theme}`);
    }
    
    // Mettre à jour l'attribut data-theme
    document.body.dataset.theme = theme;
    
    // Animation du bouton
    if (buttonElement) {
        buttonElement.style.transform = 'rotate(360deg) scale(1.2)';
        buttonElement.style.transition = 'all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
        
        setTimeout(() => {
            buttonElement.style.transform = '';
            buttonElement.style.transition = '';
        }, 500);
    }
    
    // Sauvegarder la préférence
    localStorage.setItem('creative-theme', theme);
    
    // Notification
    showCreativeToast(`Switched to ${theme} theme!`, 'success');
}

// ========== CRÉATION DE POSTS CRÉATIFS ==========

function initPostCreation() {
    const postForm = document.getElementById('postForm');
    if (!postForm) return;

    const elements = {
        postTypeSelect: document.getElementById('id_type'),
        dynamicSections: document.getElementById('dynamic-sections'),
        defaultSection: document.getElementById('default-section'),
        jobSection: document.getElementById('job-section'),
        charCounter: document.getElementById('charCounter'),
        contentTextarea: document.getElementById('id_content'),
        charCount: document.getElementById('charCount'),
        fileInputs: {
            image: document.getElementById('id_image'),
            video: document.getElementById('id_video')
        },
        filePreviews: document.getElementById('filePreviews'),
        submitBtn: document.getElementById('submitBtn')
    };

    if (elements.postTypeSelect && elements.dynamicSections) {
        // Gestion du changement de type
        elements.postTypeSelect.addEventListener('change', function() {
            updateCreativeForm(this.value, elements);
        });
        
        // Initialisation
        if (elements.postTypeSelect.value) {
            updateCreativeForm(elements.postTypeSelect.value, elements);
        }
        
        // Compteur de caractères avec animation
        if (elements.contentTextarea && elements.charCount) {
            elements.contentTextarea.addEventListener('input', function() {
                const length = this.value.length;
                elements.charCount.textContent = length;
                
                // Animation du compteur
                elements.charCount.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    elements.charCount.style.transform = 'scale(1)';
                }, 300);
                
                // Limite et feedback visuel
                if (length > 5000) {
                    elements.charCount.style.color = '#dc3545';
                    elements.charCount.style.fontWeight = 'bold';
                    if (elements.submitBtn) elements.submitBtn.disabled = true;
                } else if (length > 4500) {
                    elements.charCount.style.color = '#ffc107';
                    elements.charCount.style.fontWeight = '600';
                    if (elements.submitBtn) elements.submitBtn.disabled = false;
                } else {
                    elements.charCount.style.color = '#28a745';
                    elements.charCount.style.fontWeight = 'normal';
                    if (elements.submitBtn) elements.submitBtn.disabled = false;
                }
            });
        }
        
        // Prévisualisation de fichiers avec animation
        Object.keys(elements.fileInputs).forEach(type => {
            const input = elements.fileInputs[type];
            if (input && elements.filePreviews) {
                input.addEventListener('change', function(e) {
                    const file = e.target.files[0];
                    if (file) {
                        createCreativeFilePreview(file, type, elements.filePreviews);
                    }
                });
            }
        });
        
        // Validation du formulaire
        postForm.addEventListener('submit', function(e) {
            if (!validateCreativePost(elements)) {
                e.preventDefault();
                showCreativeToast('Please fill in all required fields correctly.', 'error');
            }
        });
    }
}

function updateCreativeForm(type, elements) {
    // Animation de transition
    if (elements.dynamicSections) {
        elements.dynamicSections.style.opacity = '0.5';
        elements.dynamicSections.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            // Masquer toutes les sections
            if (elements.defaultSection) elements.defaultSection.style.display = 'none';
            if (elements.jobSection) elements.jobSection.style.display = 'none';
            
            // Afficher la section appropriée
            switch(type) {
                case 'text':
                case 'image':
                case 'video':
                    if (elements.defaultSection) {
                        elements.defaultSection.style.display = 'block';
                        updateCreativePlaceholder(type, elements.contentTextarea);
                    }
                    break;
                case 'job':
                    if (elements.jobSection) {
                        elements.jobSection.style.display = 'block';
                        updateJobPlaceholders(elements.contentTextarea);
                    }
                    break;
            }
            
            // Animation de retour
            elements.dynamicSections.style.opacity = '1';
            elements.dynamicSections.style.transform = 'translateY(0)';
            elements.dynamicSections.style.transition = 'all 0.3s ease';
        }, 200);
    }
    
    // Reset des prévisualisations
    if (elements.filePreviews) {
        elements.filePreviews.innerHTML = '';
        // Animation de nettoyage
        elements.filePreviews.style.opacity = '0';
        setTimeout(() => {
            elements.filePreviews.style.opacity = '1';
        }, 300);
    }
}

function createCreativeFilePreview(file, type, container) {
    const preview = document.createElement('div');
    preview.className = 'creative-file-preview';
    preview.style.cssText = `
        position: relative;
        margin: 1rem 0;
        padding: 1rem;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 12px;
        border: 2px dashed rgba(102, 126, 234, 0.3);
        animation: slideIn 0.3s ease;
    `;
    
    // Bouton de suppression avec animation
    const removeBtn = document.createElement('button');
    removeBtn.className = 'creative-remove-file';
    removeBtn.innerHTML = '×';
    removeBtn.style.cssText = `
        position: absolute;
        top: -8px;
        right: -8px;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #dc3545;
        color: white;
        border: none;
        cursor: pointer;
        font-size: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
    `;
    
    removeBtn.onclick = function() {
        // Animation de suppression
        preview.style.transform = 'scale(0.8) translateY(10px)';
        preview.style.opacity = '0';
        setTimeout(() => {
            preview.remove();
            const input = document.getElementById(`id_${type}`);
            if (input) input.value = '';
        }, 300);
    };
    
    removeBtn.onmouseenter = function() {
        this.style.transform = 'scale(1.2) rotate(90deg)';
    };
    
    removeBtn.onmouseleave = function() {
        this.style.transform = 'scale(1) rotate(0deg)';
    };
    
    // Contenu de la prévisualisation
    if (type === 'image' && file.type.startsWith('image/')) {
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.style.cssText = `
            max-width: 200px;
            max-height: 150px;
            border-radius: 8px;
            object-fit: cover;
            display: block;
            margin: 0 auto;
        `;
        preview.appendChild(img);
    } else if (type === 'video' && file.type.startsWith('video/')) {
        const video = document.createElement('video');
        video.src = URL.createObjectURL(file);
        video.controls = true;
        video.muted = true;
        video.style.cssText = `
            max-width: 200px;
            max-height: 150px;
            border-radius: 8px;
            object-fit: cover;
            display: block;
            margin: 0 auto;
        `;
        preview.appendChild(video);
    } else {
        const docIcon = document.createElement('div');
        docIcon.innerHTML = `
            <div style="text-align: center; padding: 1rem;">
                <i class="fas fa-file fa-3x" style="color: #667eea; margin-bottom: 0.5rem;"></i>
                <div style="font-size: 0.9rem; color: #666; word-break: break-all;">
                    ${file.name}
                </div>
                <div style="font-size: 0.8rem; color: #999; margin-top: 0.25rem;">
                    ${(file.size / 1024 / 1024).toFixed(2)} MB
                </div>
            </div>
        `;
        preview.appendChild(docIcon);
    }
    
    preview.appendChild(removeBtn);
    container.appendChild(preview);
}

// ========== DROPDOWNS ARTISTIQUES ==========

function initArtisticDropdowns() {
    console.log('🎨 Initializing artistic dropdowns...');
    
    // Vérifier Bootstrap
    if (typeof bootstrap !== 'undefined') {
        const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
        
        dropdownToggles.forEach((toggle, index) => {
            try {
                const dropdown = new bootstrap.Dropdown(toggle, {
                    offset: [0, 10],
                    boundary: 'viewport',
                    reference: 'toggle'
                });
                
                // Animation d'ouverture
                toggle.addEventListener('show.bs.dropdown', function() {
                    const menu = this.nextElementSibling;
                    if (menu) {
                        menu.style.opacity = '0';
                        menu.style.transform = 'translateY(-10px) scale(0.95)';
                    }
                });
                
                toggle.addEventListener('shown.bs.dropdown', function() {
                    const menu = this.nextElementSibling;
                    if (menu) {
                        menu.style.opacity = '1';
                        menu.style.transform = 'translateY(0) scale(1)';
                        menu.style.transition = 'all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
                    }
                });
                
            } catch (error) {
                console.error('❌ Error initializing dropdown:', error);
                initVanillaCreativeDropdowns();
            }
        });
    } else {
        initVanillaCreativeDropdowns();
    }
}

function initVanillaCreativeDropdowns() {
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const dropdownMenu = this.nextElementSibling;
            const isVisible = dropdownMenu.style.display === 'block';
            
            // Fermer tous les autres dropdowns avec animation
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                if (menu !== dropdownMenu) {
                    menu.style.opacity = '0';
                    menu.style.transform = 'translateY(-10px) scale(0.95)';
                    setTimeout(() => {
                        menu.style.display = 'none';
                    }, 300);
                }
            });
            
            // Ouvrir/fermer le dropdown actuel
            if (!isVisible) {
                dropdownMenu.style.display = 'block';
                // Animation d'entrée
                setTimeout(() => {
                    dropdownMenu.style.opacity = '1';
                    dropdownMenu.style.transform = 'translateY(0) scale(1)';
                }, 10);
            } else {
                // Animation de sortie
                dropdownMenu.style.opacity = '0';
                dropdownMenu.style.transform = 'translateY(-10px) scale(0.95)';
                setTimeout(() => {
                    dropdownMenu.style.display = 'none';
                }, 300);
            }
        });
    });
    
    // Fermer les dropdowns en cliquant ailleurs
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.style.opacity = '0';
                menu.style.transform = 'translateY(-10px) scale(0.95)';
                setTimeout(() => {
                    menu.style.display = 'none';
                }, 300);
            });
        }
    });
}

// ========== RÉACTIONS CRÉATIVES ==========

function initCreativeReactions() {
    document.querySelectorAll('.reaction-btn, .like-btn, .art-reaction-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const postId = this.dataset.postId;
            const reactionType = this.dataset.reactionType || 'like';
            
            if (postId) {
                addCreativeReaction(postId, reactionType, this);
            }
        });
    });
}

function addCreativeReaction(postId, reactionType, buttonElement) {
    console.log(`🎨 Adding ${reactionType} reaction for post:`, postId);
    
    // Sauvegarder l'état original
    const originalHTML = buttonElement.innerHTML;
    const originalClass = buttonElement.className;
    
    // Animation optimiste
    buttonElement.classList.add('liked', 'active');
    buttonElement.innerHTML = `
        <i class="fas fa-heartbeat"></i>
        <span>Loving...</span>
    `;
    buttonElement.disabled = true;
    
    // Animation de particules
    createReactionParticles(buttonElement, reactionType);
    
    // Envoyer la requête
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
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Mise à jour réussie
            buttonElement.innerHTML = `
                <i class="fas fa-heart"></i>
                <span>Loved!</span>
            `;
            
            // Mettre à jour le compteur
            updateCreativeReactionCount(postId, data.total_reactions);
            
            // Animation de succès
            buttonElement.style.animation = 'pulse 0.5s ease';
            setTimeout(() => {
                buttonElement.style.animation = '';
                buttonElement.disabled = false;
            }, 500);
            
            // Notification
            showCreativeToast('Reaction added successfully!', 'success');
            
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('💥 Reaction error:', error);
        
        // Revenir à l'état précédent
        buttonElement.className = originalClass;
        buttonElement.innerHTML = originalHTML;
        buttonElement.disabled = false;
        
        // Animation d'erreur
        buttonElement.style.animation = 'shake 0.5s ease';
        setTimeout(() => {
            buttonElement.style.animation = '';
        }, 500);
        
        showCreativeToast('Error adding reaction. Please try again.', 'error');
    });
}

function createReactionParticles(element, reactionType) {
    const rect = element.getBoundingClientRect();
    const emojis = {
        'like': ['❤️', '💖', '💕', '💗'],
        'applause': ['👏', '🙌', '🎉', '✨'],
        'star': ['⭐', '🌟', '💫', '⚡'],
        'default': ['🎨', '✨', '🌟', '💫']
    };
    
    const particles = emojis[reactionType] || emojis.default;
    
    for (let i = 0; i < 8; i++) {
        const particle = document.createElement('div');
        particle.textContent = particles[Math.floor(Math.random() * particles.length)];
        particle.style.cssText = `
            position: fixed;
            font-size: ${20 + Math.random() * 15}px;
            pointer-events: none;
            z-index: 9999;
            left: ${rect.left + rect.width / 2}px;
            top: ${rect.top + rect.height / 2}px;
            opacity: 1;
            transform: translate(-50%, -50%);
            transition: all 1s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        `;
        
        document.body.appendChild(particle);
        
        // Animation
        setTimeout(() => {
            const angle = Math.random() * Math.PI * 2;
            const distance = 50 + Math.random() * 100;
            const x = Math.cos(angle) * distance;
            const y = Math.sin(angle) * distance;
            
            particle.style.transform = `translate(calc(-50% + ${x}px), calc(-50% + ${y}px)) scale(0)`;
            particle.style.opacity = '0';
            
            setTimeout(() => {
                particle.remove();
            }, 1000);
        }, 10);
    }
}

// ========== FILTRES ARTISTIQUES ==========

function initArtisticFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn, .creative-filter-btn');
    const postCards = document.querySelectorAll('.post-card, .art-masonry-item, .pin');
    
    if (filterButtons.length > 0 && postCards.length > 0) {
        filterButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const filter = this.dataset.filter || 'all';
                
                // Animation du bouton
                filterButtons.forEach(b => {
                    b.classList.remove('active');
                    b.style.transform = 'scale(1)';
                });
                this.classList.add('active');
                this.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 300);
                
                // Filtrer les cartes avec animation
                let visibleCount = 0;
                postCards.forEach(card => {
                    const matchesFilter = filter === 'all' || card.dataset.postType === filter || card.dataset.artType === filter;
                    
                    if (matchesFilter) {
                        visibleCount++;
                        card.style.display = 'block';
                        // Animation d'entrée
                        card.style.animation = 'slideIn 0.5s ease backwards';
                        card.style.animationDelay = `${visibleCount * 0.05}s`;
                    } else {
                        // Animation de sortie
                        card.style.animation = 'fadeOut 0.3s ease forwards';
                        setTimeout(() => {
                            card.style.display = 'none';
                            card.style.animation = '';
                        }, 300);
                    }
                });
                
                // Notification
                if (visibleCount === 0) {
                    showCreativeToast('No posts found for this filter.', 'info');
                }
            });
        });
    }
}

// ========== GALERIE CRÉATIVE ==========

function initCreativeGallery() {
    // Initialiser Masonry si présent
    const masonryGrids = document.querySelectorAll('.art-masonry-grid, .pinterest-grid');
    masonryGrids.forEach(grid => {
        initMasonryLayout(grid);
    });
    
    // Gestion du chargement infini
    initInfiniteGallery();
    
    // Lightbox pour images
    initCreativeLightbox();
}

function initMasonryLayout(grid) {
    function arrangeMasonry() {
        const containerWidth = grid.offsetWidth;
        let columns = 1;
        
        if (containerWidth >= 1400) columns = 4;
        else if (containerWidth >= 1024) columns = 3;
        else if (containerWidth >= 768) columns = 2;
        
        grid.style.columnCount = columns;
        
        // Animation des éléments
        const items = grid.querySelectorAll('.pin, .art-masonry-item');
        items.forEach((item, index) => {
            item.style.animationDelay = `${index * 0.1}s`;
            item.classList.add('animate__animated', 'animate__fadeInUp');
        });
    }
    
    // Initial arrangement
    arrangeMasonry();
    
    // Rearrange on resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(arrangeMasonry, 250);
    });
}

// ========== MESSAGERIE CRÉATIVE ==========

function initCreativeMessaging() {
    // Auto-scroll vers le bas
    const messagesList = document.querySelector('.messages-list');
    if (messagesList) {
        messagesList.scrollTop = messagesList.scrollHeight;
        // Animation douce
        messagesList.style.scrollBehavior = 'smooth';
    }
    
    // Auto-focus avec animation
    const messageInput = document.querySelector('textarea[name="content"]');
    if (messageInput) {
        messageInput.focus();
        messageInput.style.transform = 'scale(1.02)';
        setTimeout(() => {
            messageInput.style.transform = 'scale(1)';
            messageInput.style.transition = 'transform 0.3s ease';
        }, 300);
    }
    
    // Mark messages as read avec animation
    markMessagesAsRead();
    
    // Typing indicator
    initTypingIndicator();
}

function initTypingIndicator() {
    const messageInput = document.querySelector('textarea[name="content"]');
    if (messageInput) {
        let typingTimer;
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.style.cssText = `
            display: none;
            padding: 0.5rem 1rem;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 20px;
            font-size: 0.9rem;
            color: #666;
            margin: 0.5rem 0;
            animation: pulse 1.5s infinite;
        `;
        typingIndicator.textContent = 'Typing...';
        
        messageInput.parentNode.appendChild(typingIndicator);
        
        messageInput.addEventListener('input', function() {
            typingIndicator.style.display = 'block';
            clearTimeout(typingTimer);
            typingTimer = setTimeout(() => {
                typingIndicator.style.display = 'none';
            }, 1000);
        });
    }
}

// ========== VIDÉOS ARTISTIQUES ==========

function initArtisticVideos() {
    document.querySelectorAll('video').forEach(video => {
        // Configuration créative
        video.muted = true;
        video.playsInline = true;
        video.loop = true;
        video.preload = "metadata";
        
        // Style artistique
        video.style.borderRadius = '12px';
        video.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.2)';
        
        // Événements avec animations
        video.addEventListener('play', function() {
            this.style.boxShadow = '0 15px 40px rgba(102, 126, 234, 0.3)';
            this.style.transform = 'scale(1.01)';
        });
        
        video.addEventListener('pause', function() {
            this.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.2)';
            this.style.transform = 'scale(1)';
        });
        
        // Auto-play intelligent
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    video.play().catch(e => {
                        // Fallback: show play button
                        const overlay = video.nextElementSibling;
                        if (overlay && overlay.classList.contains('video-hover-overlay')) {
                            overlay.style.opacity = '1';
                        }
                    });
                } else {
                    video.pause();
                }
            });
        }, { threshold: 0.3 });
        
        observer.observe(video);
        
        // Contrôles créatifs
        initCreativeVideoControls(video);
    });
}

// ========== ANIMATIONS CRÉATIVES ==========

function initCreativeAnimations() {
    // Animation des statistiques
    animateCreativeStats();
    
    // Animation des éléments au scroll
    initScrollAnimations();
    
    // Animation du chargement
    initLoadingAnimations();
}

function animateCreativeStats() {
    const statNumbers = document.querySelectorAll('.stat-number, .artist-stat-number');
    statNumbers.forEach(stat => {
        const target = parseInt(stat.textContent);
        if (!isNaN(target) && target > 0) {
            animateCounter(stat, target, 2000);
        }
    });
}

function animateCounter(element, target, duration) {
    let start = 0;
    const increment = target / (duration / 16);
    
    const timer = setInterval(() => {
        start += increment;
        if (start >= target) {
            element.textContent = target;
            clearInterval(timer);
            
            // Animation finale
            element.style.transform = 'scale(1.2)';
            element.style.color = '#667eea';
            setTimeout(() => {
                element.style.transform = 'scale(1)';
                element.style.color = '';
            }, 300);
        } else {
            element.textContent = Math.floor(start);
        }
    }, 16);
}

// ========== NOTIFICATIONS CRÉATIVES ==========

function initCreativeNotifications() {
    // Vérifier les nouvelles notifications
    checkNewNotifications();
    
    // Badge animé
    animateNotificationBadge();
}

// Add to your navbar script section
function checkNewNotifications() {
    try {
        if (window.location.pathname.includes('/notifications/')) {
            return;
        }
        
        fetch('/api/get-unread-counts/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('API not available');
                }
                return response.json();
            })
            .then(data => {
                // ... votre code existant ...
            })
            .catch(error => {
                // Ignorer silencieusement l'erreur
                console.log('Notifications not available:', error.message);
            });
    } catch (error) {
        console.log('Notifications check failed (ignoring)');
    }
}

// Appeler une fois au démarrage
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(checkNewNotifications, 2000);
});

// Check for new notifications every 30 seconds
setInterval(checkNewNotifications, 30000);

// Also check when page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(checkNewNotifications, 2000);
});
// ############################

function pulseNotificationIcon() {
    const notificationIcon = document.querySelector('.fa-bell');
    if (notificationIcon) {
        notificationIcon.style.animation = 'pulse 1s ease 3';
        setTimeout(() => {
            notificationIcon.style.animation = '';
        }, 3000);
    }
}

// ========== FONCTIONS UTILITAIRES AMÉLIORÉES ==========

// Toast notifications créatives
function showCreativeToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `creative-toast toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} border-0`;
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body d-flex align-items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Style créatif
    toast.style.cssText = `
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
        animation: slideInRight 0.3s ease;
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, {
        animation: true,
        autohide: true,
        delay: 3000
    });
    bsToast.show();
    
    // Animation de sortie
    toast.addEventListener('hidden.bs.toast', function() {
        this.style.animation = 'slideOutRight 0.3s ease forwards';
        setTimeout(() => this.remove(), 300);
    });
}

// Copy to clipboard avec animation
function copyToClipboard(text, buttonElement) {
    navigator.clipboard.writeText(text).then(() => {
        // Animation de succès
        if (buttonElement) {
            const originalHTML = buttonElement.innerHTML;
            buttonElement.innerHTML = '<i class="fas fa-check"></i> Copied!';
            buttonElement.style.background = '#28a745';
            buttonElement.style.transform = 'scale(1.1)';
            
            setTimeout(() => {
                buttonElement.innerHTML = originalHTML;
                buttonElement.style.background = '';
                buttonElement.style.transform = '';
            }, 2000);
        }
        showCreativeToast('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showCreativeToast('Failed to copy to clipboard', 'error');
    });
}

// ========== DÉBOGAGE ET MONITORING ==========

function debugCreativePlatform() {
    console.log('🔍 Debugging Creative Platform:');
    
    // Vérifier les composants
    const components = {
        posts: document.querySelectorAll('.post-card, .pin, .art-masonry-item').length,
        videos: document.querySelectorAll('video').length,
        dropdowns: document.querySelectorAll('.dropdown').length,
        buttons: document.querySelectorAll('.btn-artistic, .creative-filter-btn').length,
        forms: document.querySelectorAll('form').length
    };
    
    console.log('📊 Component Counts:', components);
    
    // Vérifier les ressources
    console.log('🎨 Current Theme:', document.body.dataset.theme || 'default');
    console.log('💫 Animation Support:', 'IntersectionObserver' in window);
    console.log('🎭 Creative Mode:', document.body.classList.contains('creative-mode'));
    
    // Performance monitoring
    if ('performance' in window) {
        const perf = performance.getEntriesByType('navigation')[0];
        if (perf) {
            console.log('⚡ Load Time:', Math.round(perf.loadEventEnd - perf.loadEventStart), 'ms');
        }
    }
}

// ========== GESTIONNAIRES D'ÉVÉNEMENTS GLOBAUX ==========

// Gestion des clics globaux
document.addEventListener('click', function(e) {
    // Réactions
    if (e.target.closest('.reaction-btn, .like-btn, .art-reaction-btn')) {
        const btn = e.target.closest('.reaction-btn, .like-btn, .art-reaction-btn');
        const postId = btn.dataset.postId;
        const reactionType = btn.dataset.reactionType || 'like';
        
        if (postId) {
            addCreativeReaction(postId, reactionType, btn);
        }
    }
    
    // Filtres
    if (e.target.closest('.filter-btn, .creative-filter-btn')) {
        e.preventDefault();
        // Géré par initArtisticFilters
    }
    
    // Vidéos
    if (e.target.closest('.video-play-btn, .art-video-btn')) {
        const btn = e.target.closest('.video-play-btn, .art-video-btn');
        const video = btn.closest('.video-container, .art-video-container').querySelector('video');
        toggleCreativeVideoPlay(video, btn);
    }
});

// Gestion du scroll
let lastScrollTop = 0;
window.addEventListener('scroll', function() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // Header animation
    const header = document.querySelector('header');
    if (header) {
        if (scrollTop > lastScrollTop && scrollTop > 100) {
            // Scrolling down
            header.style.transform = 'translateY(-100%)';
            header.style.transition = 'transform 0.3s ease';
        } else {
            // Scrolling up
            header.style.transform = 'translateY(0)';
        }
    }
    
    lastScrollTop = scrollTop;
    
    // Animation des éléments au scroll
    animateOnScroll();
});

// ========== FONCTIONS D'EXPORT ==========

// Exporter les fonctions principales pour une utilisation globale
window.TalentForge = {
    // Utilitaires
    showToast: showCreativeToast,
    copyToClipboard,
    animateCounter,
    
    // Thèmes
    applyCreativeTheme,
    
    // Animations
    createReactionParticles,
    animateOnScroll,
    
    // Validation
    validateEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    // Formatage
    formatDate: function(dateString) {
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString('en-US', options);
    },
    
    // Formattage de nombres
    formatNumber: function(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
};

// Initialisation finale
console.log('🚀 TalentForge Creative Platform Ready!');

// Animation CSS supplémentaire
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: scale(1);
        }
        to {
            opacity: 0;
            transform: scale(0.95);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
            transform: scale(1);
        }
        50% {
            opacity: 0.7;
            transform: scale(1.05);
        }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes borderRotate {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
`;
document.head.appendChild(style);