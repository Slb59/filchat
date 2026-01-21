#!/usr/bin/env bash
set -e

# Créer les répertoires nécessaires
APPDIR="$HOME/Applications"
ICONDIR="$HOME/.local/share/icons"
DESKTOPDIR="$HOME/.local/share/applications"
DESKTOP="$HOME/Bureau"

mkdir -p "$APPDIR" "$ICONDIR" "$DESKTOPDIR"

# Copier l'exécutable
cp dist/filchat "$APPDIR/filchat"
chmod +x "$APPDIR/filchat"

# Copier l'icône
cp dist/filchat.png "$ICONDIR/filchat.png"

# creation du wrapper
cat > "$APPDIR/filchat-wrapper.sh" <<EOF
#!/bin/bash
xhost +local:root
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -e QT_OPENGL=software filchat-build:latest
xhost -local:root
EOF

chmod +x "$APPDIR/filchat-wrapper.sh"


# Créer le fichier .desktop pour le menu des applications
cat > "$DESKTOPDIR/filchat.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=FilChat
Comment=Application FilChat
TryExec=docker
Exec=$APPDIR/filchat-wrapper.sh
Icon=$ICONDIR/filchat.png
Terminal=false
Categories=Utility;
EOF

chmod +x "$DESKTOPDIR/filchat.desktop"

# Créer un raccourci sur le bureau
cat > "$DESKTOP/FilChat.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=FilChat
Comment=Application FilChat
TryExec=docker
Exec=$APPDIR/filchat-wrapper.sh
Icon=$ICONDIR/filchat.png
Terminal=false
Categories=Utility;
EOF

chmod +x "$DESKTOP/FilChat.desktop"

# Mettre à jour la base de données des icônes et des applications
update-desktop-database "$DESKTOPDIR"

# Créer un raccourci sur le bureau
echo "Filchat installé ✔"
