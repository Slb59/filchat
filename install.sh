#!/usr/bin/env bash
set -e

APP_PORT="9000"
APP_NAME="secretbox"
APP_USER="root"
APP_BASE="/opt/secretbox"
DATA_DIR="/var/lib/secretbox"
APP_DIR="$APP_BASE/app"
VENV_DIR="$APP_DIR/.venv"
echo "▶ Installation de $APP_NAME"

# -------------------------
# 1. Vérifications
# -------------------------
if [ "$EUID" -ne 0 ]; then
  echo "❌ Ce script doit être lancé en root (sudo)"
  exit 1
fi

command -v python3 >/dev/null || {
  echo "❌ Python 3 requis"
  exit 1
}

# -------------------------
# 2. Dépendances système
# -------------------------
echo "▶ Installation des dépendances système"
if command -v pacman >/dev/null 2>&1; then
  # sudo pacman -Sy --noconfirm python python-virtualenv base-devel curl
  echo "le jeu pacman doit être desactivé!"

elif command -v apt >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y python3 python3-venv build-essential curl

elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y python3 python3-virtualenv @development-tools curl

else
  echo "Gestionnaire de paquets non supporté"
  exit 1
fi


# -------------------------
# 3. Utilisateur système
# -------------------------
if ! id "$APP_USER" >/dev/null 2>&1; then
  echo "▶ Création de l'utilisateur système $APP_USER"
  useradd --system --home "$APP_BASE" --shell /usr/sbin/nologin "$APP_USER"
fi

rm -rf "$VENV_DIR"
mkdir -p "$APP_DIR" "$DATA_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_BASE"

# -------------------------
# 4. Installation de uv
# -------------------------
if ! command -v uv >/dev/null; then
  echo "▶ Installation de uv"
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
fi

# -------------------------
# 5. Copie du projet
# -------------------------
echo "▶ Copie du projet"
# rsync -av --delete --exclude-from='.installignore' ./ "$APP_DIR/"
BASE_NAME="${DATA_DIR}/db.sqlite3"
if [ -f "${BASE_NAME}" ]; then
  cp "${BASE_NAME}" "${BASE_NAME}.${VERSION}.back"
  echo "▶ Fichier de base de données trouvé, une sauvegarde est créée dans ${BASE_NAME}.${VERSION}.back"
fi
VERSION="$(tr -d '[:space:]' < VERSION)"
ARCHIVE_NAME="${APP_NAME}-${VERSION}.7z"
echo "▶ Extraction de l'archive"
sudo 7z x "app.7z" -o"$APP_DIR" -y

# -------------------------
# 6. Environnement Python
# -------------------------
echo "▶ Création du venv"
chown -R "$APP_USER:$APP_USER" "$APP_BASE"
chmod -R 755 "$APP_BASE"
sudo -u "$APP_USER" uv venv "$VENV_DIR" --clear
chown -R "$APP_USER:$APP_USER" "$VENV_DIR"

echo "▶ Nettoyage du cache Python depuis $APP_DIR"
cd "$APP_DIR"
source .venv/bin/activate
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "▶ Installation des dépendances Python"
uv sync --refresh

# -------------------------
# 7. Variables d'environnement
# -------------------------
echo "▶ Création du .env"
if [ ! -f "$DATA_DIR/.env" ]; then
    echo "Création du .env production"
    NEWKEY=$("./djangokey.sh")
    cat > "$DATA_DIR/.env" <<EOF
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_SECRET_KEY=$NEWKEY
DATABASE_URL=sqlite:////$DATA_DIR/db.sqlite3
WAGTAIL_SITE_NAME=SecretBox
EOF
  chown "$APP_USER:$APP_USER" "$DATA_DIR/.env"
  chmod 600 "$DATA_DIR/.env"
fi

# -------------------------
# 8. Base de données
# -------------------------
echo "▶ Migrations Django"
export DJANGO_SETTINGS_MODULE=config.settings.prod
uv run manage.py migrate --noinput
uv run manage.py tailwind build
uv run manage.py collectstatic --noinput

# -------------------------
# 9. Service systemd
# -------------------------
echo "▶ Installation du service systemd"

cat > /etc/systemd/system/secretbox.service <<EOF
[Unit]
Description=SecretBox (Django)
After=network.target

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/gunicorn --bind 127.0.0.1:9000 config.wsgi:secretbox
Restart=always
EnvironmentFile=$DATA_DIR/.env
Environment=ENV_FILE=$DATA_DIR/.env
Environment=DJANGO_SETTINGS_MODULE=config.settings.prod

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable secretbox
systemctl restart secretbox
systemctl status secretbox

# -------------------------
# 10. Fin
# -------------------------
echo
echo "✅ FilChat est installé et démarré"
echo "🌐 Ouvrir : http://localhost:$APP_PORT"
echo "📋 Statut : systemctl status filchat"
