#!/bin/bash

# Script de compilation pour FilChat
# Usage: ./build.sh

set -e

APP_NAME="FilChat"
VERSION=$(date +%Y.%m.%d)

echo "🔨 Compilation de $APP_NAME"

# Vérifier que PyInstaller est installé
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller n'est pas installé"
    echo "Installation : uv add pyinstaller"
    exit 1
fi

# Créer les dossiers de destination
DEST_DIR="./dist-prod"
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

# Créer le dossier de destination
mkdir -p "$DEST_DIR"

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
tar -czf "$ARCHIVE_NAME" -C "$DEST_DIR" ./versions
echo "📦 Archive créée : $ARCHIVE_NAME"
echo "💡 Vous pouvez maintenant copier cette archive dans Dropbox"
