# Description

Ce projet a pour objectif de découper un fil de chatgpt en plusieurs fichiers markdown. Ces fichiers seront ensuite utilisable dans un coffre obsidian.
Les fichiers en entrée doivent être au format `.txt` et doivent contenir le texte du fil de chatgpt.
Les fichiers en sortie seront générés dans le dossier output. Chaque fil lu en entrée générerar un dossier dans output.

# Usages

activer l'environnement python : 
```bash
source .venv/bin/activate
```

## Mode ligne de commande
execution du script avec génération d'un fichier zip:
```bash
python filchat.py input O
```

option possible : --force -> vide automatiquement le dossier output

## Mode interface
```bash
python filchat.py
```

# git commandes

git add . : ajoute tous les fichiers modifiés dans le dépôt
git commit -m "message" : commite les changements dans le dépôt
git push origin HEAD : push les changements dans le dépôt

# installation de nouvelles librairies

uv add <nom de la librairie>

## pour extraire le code
uv add gitingest
gitingest . -o tests/output/digest.txt -i "*.py *.css *.js"

# creation de l'executable
pyinstaller --onefile filchat.py

# Evolutions possibles

- generer un programme executable

# Problèmes à résoudre

Les tableaux ne sont pas correctement formatés.

# Versions

20251224: generer un fichier zip correspondant à l'execution avec date et heure
20251226: ajout d'une interface graphique

- 0.0.1 : première version
