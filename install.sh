#!/usr/bin/env bash
set -e

APP_PORT="9000"
APP_NAME="filchat"
APP_USER="filchat"
APP_BASE="/opt/filchat"
VENV_DIR="$APP_BASE/.venv"
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
pacman -Sy --noconfirm \
  python \
  python-virtualenv \
  base-devel \
  curl

# -------------------------
# 3. Utilisateur système
# -------------------------
if ! id "$APP_USER" >/dev/null 2>&1; then
  echo "▶ Création de l'utilisateur système $APP_USER"
  useradd --system --home "$APP_BASE" --shell /usr/sbin/nologin "$APP_USER"
fi

rm -rf "$APP_BASE"
mkdir -p "$APP_BASE"
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
rsync -av --delete --exclude-from='.installignore' ./ "$APP_BASE/"

# -------------------------
# 6. Environnement Python
# -------------------------
echo "▶ Création du venv"
chown -R "$APP_USER:$APP_USER" "$APP_BASE"
sudo -u "$APP_USER" uv venv "$VENV_DIR" --clear

echo "▶ Nettoyage du cache Python"
cd "$APP_BASE"
source .venv/bin/activate
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "▶ Installation des dépendances Python"
# export PATH="$VENV_DIR/bin:\$PATH"

uv sync --refresh

# -------------------------
# 7. Base de données
# -------------------------
echo "▶ Migrations Django"
python manage.py migrate --noinput

# -------------------------
# 8. Service systemd
# -------------------------
echo "▶ Installation du service systemd"

cat > /etc/systemd/system/filchat.service <<EOF
[Unit]
Description=FilChat (Django)
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_BASE
ExecStart=$VENV_DIR/bin/python manage.py runserver 127.0.0.1:$APP_PORT
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable filchat
systemctl restart filchat

# -------------------------
# 9. Fin
# -------------------------
echo
echo "✅ FilChat est installé et démarré"
echo "🌐 Ouvrir : http://localhost:8000"
echo "📋 Statut : systemctl status filchat"
