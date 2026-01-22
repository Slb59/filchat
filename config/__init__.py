import pathlib

import environ  # type: ignore

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

env.read_env(str(BASE_DIR / ".env"))


VERSION_FILE = BASE_DIR / "VERSION"
with open(VERSION_FILE, "r") as f:
    VERSION = f.read().strip()


def get_version():
    """Retourne la version de l'application"""
    return VERSION
