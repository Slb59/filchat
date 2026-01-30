# config.settings.prod.py
from .base import *

DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "../data/prod/db.sqlite3",
    }
}

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# doit être modifié si déploiement sur serveur web
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
INTERNAL_IPS = ["127.0.0.1",]
