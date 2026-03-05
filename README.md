# Description

Ce projet a pour objectif de découper un fil de chatgpt en plusieurs fichiers markdown. Ces fichiers seront ensuite utilisable dans un coffre obsidian.
Les fichiers en entrée doivent être au format `.txt` et doivent contenir le texte du fil de chatgpt.
Les fichiers en sortie seront générés dans le dossier output. Chaque fil lu en entrée générerar un dossier dans output.

# instructions en développement
## Usages

activer l'environnement python : 
```bash
source .venv/bin/activate
```

### Mode ligne de commande
execution du script avec génération d'un fichier zip:
```bash
python filchat.py input O
```

option possible : --force -> vide automatiquement le dossier output

### Lancement en développement

#### en version 0.1 (Web)
```bash
make run-front
make run
```

mkdir -p staticfiles static
python manage.py collectstatic
python manage.py compress
chmod -R 755 staticfiles static


👉 http://127.0.0.1:8000/django-admin/  (Django admin)
👉 http://127.0.0.1:8000/admin/  (Wagtail admin)
👉 http://127.0.0.1:8000/  (site)

## git commandes

git add . : ajoute tous les fichiers modifiés dans le dépôt
git commit -m "message" : commite les changements dans le dépôt
git push origin HEAD : push les changements dans le dépôt

## installation de nouvelles librairies

uv add <nom de la librairie>

### pour extraire le code
uv add gitingest
uv run gitingest . -o tests/output/digest.txt -i "*.py *.css *.js"

# Instructions pour le build

## creation du fichier zip
./build.sh
utilise le fichier 7z de /build pour télécharger dans le dossier d'installation et lance le script install.sh
Le répertoire d'installation pourrait être secretbox dans journalling par exemple

## creation de l'executable

### installation sous /opt/filchat
sudo ./install.sh
Ce fichier installe un service sur un système linux pour que l'application puisse être accédée depuis le web.

### compte system dédie
sudo useradd -r -s /usr/sbin/nologin filchat
sudo chown -R filchat:filchat /opt/filchat

### pour un service global (multi user)
copier ficlchat.service dans /etc/systemd/system

### test après installation
systemctl status filchat
ls /opt/filchat/data/prod/db.sqlite3
curl http://localhost:9000

### problème lié à l'espace disque mangé
sudo du -xh / | sort -h | tail -30
sudo pacman -Sc


# Evolutions

## Elements à développer

## Problèmes à résoudre

- Revoir crash sur pc du bas
- Les tableaux ne sont pas correctement formatés.

# Versions

[[./documentation/versions.md]]
