#!/bin/bash

# Script de compilation pour FilChat
# Usage: ./build.sh

set -e

APP_NAME="filchat"
VERSION=$(date +%Y.%m.%d)

echo "🔨 Compilation de $APP_NAME"

# Vérifier que PyInstaller est installé
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller n'est pas installé"
    echo "Installation : uv add pyinstaller"
    exit 1
fi

# Vérifier que Docker est installé (si on veut construire le conteneur)
BUILD_DOCKER=false
if command -v docker &> /dev/null; then
    read -p "🐳 Voulez-vous construire une image Docker pour FilChat ? (o/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[OoYy]$ ]]; then
        BUILD_DOCKER=true
        export DOCKER_BUILDKIT=0
    fi
fi

# Créer les dossiers de destination
DEST_DIR="./dist-prod"
VERSIONS_DIR="./versions"
mkdir -p "$DEST_DIR"
mkdir -p "$VERSIONS_DIR"
echo "📁 Dossier de destination : $DEST_DIR"

# Nettoyer les anciens builds
rm -rf build dist *.spec

# Compiler avec PyInstaller
pyinstaller --onefile \
    --windowed \
    --name "$APP_NAME" \
    --add-data "README.md:." \
    --hidden-import "PySide6" \
    --clean \
    filchat.py

# Copier l'exécutable
cp dist/$APP_NAME "$DEST_DIR/"

# Créer un fichier de version
echo "$VERSION" > "$DEST_DIR/VERSION.txt"

# Créer un README pour l'utilisateur
cp documentation/user.md "$DEST_DIR/README.txt"

# Rendre l'exécutable... exécutable :D
chmod +x "$DEST_DIR/$APP_NAME"

echo "✅ Compilation terminée !"
echo "📦 Exécutable disponible : $DEST_DIR/$APP_NAME"

# Créer une archive pour Dropbox
ARCHIVE_NAME="${APP_NAME}_${VERSION}_linux.tar.gz"
tar -czf "./versions/$ARCHIVE_NAME" -C "$DEST_DIR" .  # le . est obligatoire pour inclure le dossier
# cp "$ARCHIVE_NAME" "./versions/"
echo "📦 Archive créée : $ARCHIVE_NAME"
echo "💡 Vous pouvez maintenant copier cette archive dans Dropbox"

# --- Construction du conteneur Docker ---
if [ "$BUILD_DOCKER" = true ]; then
    echo "🐳 Création du Dockerfile pour $APP_NAME..."

    set -e

    # Construire l'image Docker
    docker build \
    --no-cache \
    -f Dockerfile.build \
    -t filchat-build \
    .

    # cree le conteneur temporaire
    CID=$(docker create filchat-build)

    # Créer le répertoire dist s'il n'existe pas
    mkdir -p dist

    # copie les fichiers depuis le conteneur
    docker cp "$CID:/filchat" ./dist/filchat
    docker cp "$CID:/filcaht-wrapper" ./dist/filchat-wrapper
    docker cp "$CID:/filchat.png" ./dist/filchat.png

    # supprime le conteneur temporaire
    docker rm "$CID"

    echo "✅ Image Docker construite : $APP_NAME:latest"
    echo "💡 Pour lancer le conteneur, utilisez :"
    echo "    docker run -it --rm -e DISPLAY=$DISPLAY -e QT_QPA_PLATFORM=xcb -v /tmp/.X11-unix:/tmp/.X11-unix $APP_NAME-build:latest -e QT_OPENGL=software"
fi