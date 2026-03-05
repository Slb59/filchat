# config.settings.dev.py

from .base import *

DEBUG = True

ENVIRONMENT = "dev"

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
INTERNAL_IPS = ["127.0.0.1",]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
