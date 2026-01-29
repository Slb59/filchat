#filchat.utils.py
import os
import zipfile
from datetime import datetime

def decoupe_chat(fichier_source, dossier_sortie):
    """Découpe un fichier de chat en plusieurs fichiers Markdown"""
    # Créer le dossier de sortie
    os.makedirs(dossier_sortie, exist_ok=True)

    with open(fichier_source, "r", encoding="utf-8") as f:
        lignes = f.readlines()
    
    questions = []
    current_question = None
    current_answer = None
    mode = None  # "question" ou "answer"

    for ligne in lignes:
        if "Vous avez dit :" in ligne:
            if current_question is not None and current_answer is not None:
                questions.append((current_question.strip(), current_answer.strip()))
            current_question = ""
            current_answer = ""
            mode = "question"
            continue
        if "ChatGpt a dit :" in ligne:
            mode = "answer"
            continue
        
        if mode == "question":
            current_question += ligne
        elif mode == "answer":
            current_answer += ligne
        
    if current_question is not None and current_answer is not None:
        questions.append((current_question.strip(), current_answer.strip()))
    
    # Génération des fichiers
    for index, (q, r) in enumerate(questions, start=1):
        nom_fichier = f"{datetime.now().strftime('%Y%m%d')}-{index:03d}.md"
        chemin = os.path.join(dossier_sortie, nom_fichier)
        contenu = f"""---
categorie:
date: {datetime.now().strftime('%Y-%m-%d')}
---

# Question
{q}

# Réponse
{r}
"""
        with open(chemin, "w", encoding="utf-8") as out:
            out.write(contenu)
        
def creer_archive_output(dossier_output):
    """Crée une archive ZIP du dossier output"""
    date_du_jour = datetime.now().strftime("%Y%m%d")
    nom_archive = f"{date_du_jour}.zip"
    chemin_archive = os.path.join(dossier_output, nom_archive)

    with zipfile.ZipFile(chemin_archive, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(dossier_output):
            for file in files:
                if not file.endswith(".zip"):
                    chemin_fichier = os.path.join(root, file)
                    arcname = os.path.relpath(chemin_fichier, dossier_output)
                    zipf.write(chemin_fichier, arcname)
    return chemin_archive
        
        
