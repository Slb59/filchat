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
