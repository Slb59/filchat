#!/usr/bin/env bash
set -e

APP_NAME="filchat"
BASE_DIR="$(dirname "$(readlink -f "$0")")"
BUILD_DIR="$BASE_DIR/build"

# Lire la version
if [[ ! -f VERSION ]]; then
  echo "❌ Fichier VERSION introuvable"
  exit 1
fi

VERSION="$(tr -d '[:space:]' < VERSION)"

if [[ -z "$VERSION" ]]; then
  echo "❌ VERSION est vide"
  exit 1
fi

ARCHIVE_NAME="${APP_NAME}-${VERSION}.7z"

echo "▶ Build FilChat version $VERSION"
echo "▶ Archive : $ARCHIVE_NAME"

echo "▶ Nettoyage"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/app"

echo "▶ Copie des fichiers applicatifs"
rsync -av --exclude-from='.buildignore' ./ "$BUILD_DIR/app/"

echo "▶ Copie des fichiers d'installation "
cp install.sh "$BUILD_DIR"
cp VERSION "$BUILD_DIR"

echo "▶ Création de l’archive dans $BUILD_DIR"
cd "$BUILD_DIR/app"
7z a "$BUILD_DIR"/"$ARCHIVE_NAME" .
GLOBAL_ARCHIVE_NAME="$BUILD_DIR"/"$VERSION"_"$APP_NAME"_"$(date +%Y.%m.%d)"_linux.7z
7z a "$GLOBAL_ARCHIVE_NAME" "$BUILD_DIR"/VERSION
7z a "$GLOBAL_ARCHIVE_NAME" "$BUILD_DIR"/install.sh
7z a "$GLOBAL_ARCHIVE_NAME" "$BUILD_DIR"/"$ARCHIVE_NAME"

echo "✔ Archive créée : $ARCHIVE_NAME"
