"""Django settings for LiveDev agency site backend."""
from pathlib import Path
import os

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
# Local: ../dev-agency-site-new ; Docker: /app/frontend (see Dockerfile)
FRONTEND_DIR = Path(os.getenv('FRONTEND_DIR', str(REPO_ROOT / 'dev-agency-site-new')))

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-insecure-change-me')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]
BEHIND_HTTPS_PROXY = os.getenv('BEHIND_HTTPS_PROXY', '0') == '1'
if not DEBUG and SECRET_KEY == 'dev-insecure-change-me':
    raise ImproperlyConfigured('Set a strong SECRET_KEY for production')

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'content',
    'leads',
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'livedev'),
        'USER': os.getenv('POSTGRES_USER', 'livedev'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'livedev'),
        'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}

# Small shared file cache: enough for this site and consistent across workers.
CACHES = {
    'default': {
        # Shared by all Gunicorn workers without requiring Redis for this small site.
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.getenv('CACHE_DIR', '/tmp/livedev-cache'),
        'TIMEOUT': 300,
        'OPTIONS': {'MAX_ENTRIES': 5000},
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Production TLS is terminated by the bundled Nginx container. These settings
# remain disabled for the familiar local runserver workflow.
if BEHIND_HTTPS_PROXY:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Minsk'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 4 * 1024 * 1024

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000,http://localhost').split(',')
    if o.strip()
]

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

CACHE_TTL_SHOWCASE = int(os.getenv('CACHE_TTL_SHOWCASE', '300'))
CACHE_TTL_SETTINGS = int(os.getenv('CACHE_TTL_SETTINGS', '120'))
CACHE_TTL_GEO = int(os.getenv('CACHE_TTL_GEO', '86400'))
LEAD_RATE_LIMIT = int(os.getenv('LEAD_RATE_LIMIT', '5'))
ANALYTICS_RATE_LIMIT = int(os.getenv('ANALYTICS_RATE_LIMIT', '60'))

UNFOLD = {
    'SITE_TITLE': 'LiveDev Admin',
    'SITE_HEADER': 'LiveDev',
    'SITE_SUBHEADER': 'Контент · контакты · аналитика',
    'SITE_SYMBOL': 'rocket_launch',
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': False,
    # Не фиксируем THEME — иначе Unfold прячет переключатель светлая/тёмная
    'COLORS': {
        'primary': {
            '50': '239 246 255',
            '100': '219 234 254',
            '200': '191 219 254',
            '300': '147 197 253',
            '400': '96 165 250',
            '500': '44 123 255',
            '600': '37 99 235',
            '700': '29 78 216',
            '800': '30 64 175',
            '900': '30 58 138',
            '950': '23 37 84',
        },
    },
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': False,
        'navigation': [
            {
                'title': 'Контент',
                'separator': True,
                'items': [
                    {
                        'title': 'Разделы витрины',
                        'icon': 'category',
                        'link': lambda request: '/admin/content/showcasecategory/',
                    },
                    {
                        'title': 'Карточки проектов',
                        'icon': 'photo_library',
                        'link': lambda request: '/admin/content/showcaseitem/',
                    },
                ],
            },
            {
                'title': 'Заявки',
                'separator': True,
                'items': [
                    {
                        'title': 'Заявки с сайта',
                        'icon': 'mail',
                        'link': lambda request: '/admin/leads/lead/',
                    },
                ],
            },
            {
                'title': 'Аналитика',
                'separator': True,
                'items': [
                    {
                        'title': 'Визиты',
                        'icon': 'monitoring',
                        'link': lambda request: '/admin/analytics/pagevisit/',
                    },
                    {
                        'title': 'Интерес к продуктам',
                        'icon': 'insights',
                        'link': lambda request: '/admin/analytics/productinterest/',
                    },
                ],
            },
            {
                'title': 'Настройки',
                'separator': True,
                'items': [
                    {
                        'title': 'Контакты и счётчики',
                        'icon': 'settings',
                        'link': lambda request: '/admin/core/sitesettings/',
                    },
                ],
            },
        ],
    },
}
