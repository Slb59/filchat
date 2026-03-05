import pathlib
import os
import environ  # type: ignore

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

# Recherche du fichier .env
ENV_FILE = os.environ.get("ENV_FILE")
if ENV_FILE:
    env.read_env(ENV_FILE)
else:
    env.read_env(str(BASE_DIR / ".env"))


VERSION_FILE = BASE_DIR / "VERSION"
with open(VERSION_FILE, "r") as f:
    VERSION = f.read().strip()


def get_version():
    """Retourne la version de l'application"""
    return VERSION
