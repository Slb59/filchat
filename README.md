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

### Mode interface

#### en version 0.0 (PySide6)
```bash 
python filchat.py
```

#### en version 0.1 (Web)
```bash
make run
```

👉 http://127.0.0.1:8000/django-admin/  (Wagtail admin)
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
gitingest . -o tests/output/digest.txt -i "*.py *.css *.js"

# Instructions pour le build

## creation de l'executable
./build.sh > build.log
On obtient une archive .tar.gz contenant l'exécutable
On obtient aussi un dossier dist-prod contenant le code compilé
On obtient aussi un fichier dockerfile
Pour vérifier un conteneur existant : docker ps -a | grep filchat

# Evolutions

## Elements à développer

## Problèmes à résoudre

- Revoir crash sur pc du bas
- Les tableaux ne sont pas correctement formatés.

# Versions

[[./documentation/versions.md]]
