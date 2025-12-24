import os
import sys
import zipfile
import shutil
from datetime import datetime

def verifier_ou_vider_output(dossier_output, force = False):
    if not os.path.exists(dossier_output):
        return  # OK, il sera créé plus tard

    if os.listdir(dossier_output):
        if force:
            shutil.rmtree(dossier_output)
            print(f"Dossier '{dossier_output}' vidé (--force)")
        else:
            print(f"Erreur : le dossier '{dossier_output}' n'est pas vide.")
            print("Utilisez --force pour vider le dossier automatiquement.")
            sys.exit(1)


def creer_archive_output(dossier_output):
    date_du_jour = datetime.now().strftime("%Y%m%d")
    nom_archive = f"{date_du_jour}.zip"
    chemin_archive = os.path.join(os.getcwd(), nom_archive)

    with zipfile.ZipFile(chemin_archive, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(dossier_output):
            for file in files:
                chemin_fichier = os.path.join(root, file)
                arcname = os.path.relpath(chemin_fichier, dossier_output)
                zipf.write(chemin_fichier, arcname)

    print(f"Archive générée : {nom_archive}")


def decoupe_chat(fichier_source, dossier_sortie):
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
            # Si une question précédente existe déjà → l'enregistrer
            if current_question is not None and current_answer is not None:
                questions.append((current_question.strip(), current_answer.strip()))
            # Nouvelle question
            current_question = ""
            current_answer = ""
            mode = "question"
            continue

        if "ChatGPT a dit :" in ligne:
            mode = "answer"
            continue

        # On accumule selon le mode
        if mode == "question":
            current_question += ligne
        elif mode == "answer":
            current_answer += ligne

    # Dernier bloc
    if current_question is not None and current_answer is not None:
        questions.append((current_question.strip(), current_answer.strip()))

    # Génération des fichiers
    for index, (q, r) in enumerate(questions, start=1):
        nom_fichier = f"{datetime.now().strftime("%Y%m%d")}-{index:03d}.md"
        chemin = os.path.join(dossier_sortie, nom_fichier)

        contenu = f"""---
categorie:
date: {datetime.now().strftime("%Y-%m-%d")}
---

# Question
{q}

# Réponse
{r}
"""

        with open(chemin, "w", encoding="utf-8") as out:
            out.write(contenu)

    print(f"{len(questions)} fichiers Markdown générés dans : {dossier_sortie}")

def normalize_name(filename):
    """Transforme 'goudron bitimeux.txt' → 'goudron_bitimeux'"""
    name = os.path.splitext(filename)[0]
    return name.strip().lower().replace(" ", "_")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python3 filchat.py dossier_input [O/N]")
        sys.exit(1)
    
    dossier_input = sys.argv[1]
    generer_archive = False
    force = False

    # Analyse des paramètres
    for arg in sys.argv[2:]:
        if arg.upper() == "O":
            generer_archive = True
        elif arg.upper() == "N":
            generer_archive = False
        elif arg == "--force":
            force = True

    if not os.path.isdir(dossier_input):
        print(f"Erreur : {dossier_input} n'est pas un dossier")
        sys.exit(1)

    dossier_output = "output"
    verifier_ou_vider_output(dossier_output, force=force)
    os.makedirs(dossier_output, exist_ok=True)

    for fichier in os.listdir(dossier_input):
        if not fichier.lower().endswith(".txt"):
            continue
    
        chemin_fichier = os.path.join(dossier_input, fichier)
        nom_dossier = normalize_name(fichier)
        chemin_sortie = os.path.join(dossier_output, nom_dossier)
        decoupe_chat(chemin_fichier, chemin_sortie)

    if generer_archive:
        creer_archive_output(dossier_output)