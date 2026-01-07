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
cat > "$DEST_DIR/README.txt" << 'EOF'
FilChat - Découpe de conversations
===================================

UTILISATION :
1. Double-cliquez sur FilChat pour lancer l'application
2. Sélectionnez un dossier contenant des fichiers .txt de conversations
3. Cochez les options souhaitées :
   - Générer une archive ZIP : crée un fichier .zip avec tous les résultats
   - Vider le dossier output : efface le contenu existant avant traitement
4. Cliquez sur "Lancer le traitement"

Les fichiers Markdown générés se trouvent dans le dossier "output"
(créé à l'emplacement où vous lancez l'application).

SUPPORT :
Pour toute question, contactez le développeur.
EOF

# Rendre l'exécutable... exécutable
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
    echo "🐳 Construction de l'image Docker pour $APP_NAME..."

    # Créer un Dockerfile
    cat > Dockerfile << 'EOF'
FROM ubuntu:22.04

# Installer les dépendances système
RUN apt update && apt install -y \
    python3 \
    python3-pip \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-randr0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    xvfb

# Installer PySide6
RUN pip install PySide6

# Copier l'exécutable et les fichiers nécessaires
COPY dist-prod/filchat /filchat
COPY dist-prod/README.txt /README.txt

# Lancer l'application avec Xvfb (pour éviter les problèmes d'affichage)
CMD ["sh", "-c", "Xvfb :1 -screen 0 1024x768x16 & export DISPLAY=:1 && /filchat"]
EOF

    # Construire l'image Docker
    docker buildx build --load -t "filchat:latest" .

    # Nettoyer le Dockerfile
    rm Dockerfile

    echo "✅ Image Docker construite : $APP_NAME:latest"
    echo "💡 Pour lancer le conteneur, utilisez :"
    echo "    docker run -it --rm -e DISPLAY=$DISPLAY -e QT_QPA_PLATFORM=xcb -v /tmp/.X11-unix:/tmp/.X11-unix filchat:latest"
fi