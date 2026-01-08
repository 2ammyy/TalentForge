"""
Django settings for talentForge project.
Production-optimized for Render Docker deployment.
"""

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Load environment variables
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== SECURITY & BASIC SETTINGS ====================
# SECURITY: Use environment variable, secure fallback
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_urlsafe(50))

# DEBUG: False in production
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# ALLOWED_HOSTS: Configure for Render
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
ALLOWED_HOSTS = []

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Always allow localhost and Render domains
ALLOWED_HOSTS.extend([
    'localhost',
    '127.0.0.1',
    '.onrender.com',
])

# Add your local IP for development only if DEBUG is True
if DEBUG:
    ALLOWED_HOSTS.extend(['web', 'nginx', '192.168.0.60'])

# ==================== APPLICATION DEFINITION ====================
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Your apps
    'base',
    'posts.apps.PostsConfig',
    'creator',
    'admin_app.apps.AdminAppConfig',
    'word_prediction',

    # Third-party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'corsheaders',
]

MIDDLEWARE = [
    # CORS must be first
    'corsheaders.middleware.CorsMiddleware',
    
    # Django security
    'django.middleware.security.SecurityMiddleware',
    
    # WhiteNoise for static files (MUST be after SecurityMiddleware)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    # Django core
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Allauth
    'allauth.account.middleware.AccountMiddleware',
]

# CORS Configuration
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
else:
    CORS_ALLOWED_ORIGINS = []
    if RENDER_EXTERNAL_HOSTNAME:
        CORS_ALLOWED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
    CORS_ALLOWED_ORIGINS.extend([
        'https://*.onrender.com',
    ])
    CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'talentForge.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'posts.context_processors.notifications_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'talentForge.wsgi.application'

# ==================== DATABASE CONFIGURATION ====================
# Priority 1: Use DATABASE_URL from Render
DATABASE_URL = os.environ.get('postgresql://talentforge_db_user:yhFVsrR8HY8NN8sad7n2cyxVx9r9AKNy@dpg-d5fr8595pdvs73fgp7p0-a/talentforge_db')

if DATABASE_URL:
    # Render PostgreSQL with optimizations
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,  # Persistent connections
            conn_health_checks=True,
            ssl_require=True,  # Always use SSL in production
        )
    }
    # Performance optimizations for production
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
    }
elif DEBUG:
    # Development: Use Amira's PostgreSQL or SQLite
    USE_LOCAL_POSTGRES = os.environ.get('USE_LOCAL_POSTGRES', 'False').lower() == 'true'
    
    if USE_LOCAL_POSTGRES:
        # Connect to Amira's PostgreSQL
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DB_NAME', 'djangodb'),
                'USER': os.environ.get('DB_USER', 'django_user'),
                'PASSWORD': os.environ.get('DB_PASSWORD', 'DjangoSecurePass123!'),
                'HOST': os.environ.get('DB_HOST', '192.168.0.60'),
                'PORT': os.environ.get('DB_PORT', '5432'),
                'OPTIONS': {
                    'connect_timeout': 5,
                }
            }
        }
    else:
        # Fallback to SQLite for development
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
else:
    # Production fallback (should not happen)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==================== STATIC & MEDIA FILES ====================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise configuration for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1 year cache for static files
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False

# Media files (Note: Render doesn't persist these between deploys)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# For production, consider using S3/Cloudinary for media storage
if not DEBUG:
    # Optional: Disable media uploads in production or use cloud storage
    # MEDIA_URL = 'https://your-s3-bucket.s3.amazonaws.com/'
    pass

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== EMAIL CONFIGURATION ====================
if DEBUG:
    # Development: console backend
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'talentforge.app@gmail.com'
    EMAIL_HOST_PASSWORD = 'qpzl bwho pojs axhh'  # WARNING: Use app password, not regular password
    DEFAULT_FROM_EMAIL = 'TalentForge <talentforge.app@gmail.com>'
else:
    # Production: use environment variables
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'TalentForge <noreply@talentforge.com>')

SERVER_EMAIL = EMAIL_HOST_USER

# ==================== ALLAUTH CONFIGURATION ====================
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Account settings
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # 'mandatory', 'optional', or 'none'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = False  # Changed to False for better security
SOCIALACCOUNT_STORE_TOKENS = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_REQUIRED = False

# URL settings
LOGIN_URL = 'base:login'
LOGIN_REDIRECT_URL = 'base:home'
LOGOUT_REDIRECT_URL = 'base:home'
ACCOUNT_LOGOUT_REDIRECT_URL = 'base:home'

# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ==================== SECURITY SETTINGS ====================
if DEBUG:
    # Development: relaxed security
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
else:
    # Production: maximum security
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'same-origin'
    CSRF_TRUSTED_ORIGINS = []
    
    if RENDER_EXTERNAL_HOSTNAME:
        CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
    CSRF_TRUSTED_ORIGINS.extend([
        'https://*.onrender.com',
    ])

# Messages framework
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Custom settings
TALENTFORGE = {
    'VERIFICATION_CODE_EXPIRY_MINUTES': 15,
    'MAX_LOGIN_ATTEMPTS': 5,
    'PASSWORD_RESET_TIMEOUT': 86400,
}

# ==================== AI SERVICES CONFIGURATION ====================
# OLLAMA Configuration (won't work on Render free tier)
OLLAMA_HOST = os.environ.get('OLLAMA_HOST')
OLLAMA_PORT = os.environ.get('OLLAMA_PORT', '11434')

# Only enable Ollama in development
if DEBUG and OLLAMA_HOST:
    OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama2')
else:
    OLLAMA_BASE_URL = None
    OLLAMA_MODEL = None
    # Log only in production
    if not DEBUG:
        print("INFO: OLLAMA is disabled in production. Use OpenAI API instead.")

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# ==================== PERFORMANCE OPTIMIZATIONS ====================
# Cache configuration (simple memory cache for free tier)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Use cached sessions in production for better performance
if not DEBUG:
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Database connection optimizations
if DATABASE_URL and not DEBUG:
    DATABASES['default']['CONN_MAX_AGE'] = 60  # Reuse connections for 60 seconds

# ==================== LOGGING CONFIGURATION ====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# ==================== ADDITIONAL SETTINGS ====================
# Ensure HTTPS in production
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Security headers
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'