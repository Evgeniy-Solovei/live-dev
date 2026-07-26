"""Fast isolated settings for local and CI tests; production still uses PostgreSQL."""

from .settings import *  # noqa: F403


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'livedev-tests',
    },
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
SECURE_SSL_REDIRECT = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
