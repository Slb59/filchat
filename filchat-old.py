import os
import sys
import zipfile
import shutil
import tkinter as tk
import threading
import queue
import logging
import ctypes
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext

logger = logging.getLogger("filchat")
logger.setLevel(logging.INFO)


class TkLogHandler(logging.Handler):
    def __init__(self, log_func):
        super().__init__()
        self.log_func = log_func

    def emit(self, record):
        msg = self.format(record)
        self.log_func(msg)


def lancer_interface():

    log_queue = queue.Queue()

    root = tk.Tk()
    root.title("FilChat – Découpe de conversations")
    root.geometry("600x400")

    dossier_input = tk.StringVar()
    option_archive = tk.BooleanVar()
    option_force = tk.BooleanVar()

    def poll_log_queue():
        try:
            while True:
                message = log_queue.get_nowait()
                console.insert(tk.END, message + "\n")
                console.see(tk.END)
        except queue.Empty:
            pass

        root.after(100, poll_log_queue)


    def choisir_dossier():
        path = filedialog.askdirectory()
        if path:
            dossier_input.set(path)

    def log(message):
        log_queue.put(message)

    def lancer_traitement():
        path = dossier_input.get()

        if not path:
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier d'entrée")
            return

        def worker():

            try:

                log("Traitement démarré…")

                traiter_dossier(
                    path,
                    generer_archive=option_archive.get(),
                    force=option_force.get()
                )

                log("Traitement terminé avec succès.")
                messagebox.showinfo("Succès", "Traitement terminé")

            except Exception as e:
                messagebox.showerror("Erreur", str(e))
                log(f"Erreur : {e}")


        
        threading.Thread(target=worker, daemon=True).start()

    # ---- UI ----

    frame = tk.Frame(root, padx=10, pady=10)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(frame, text="Dossier d'entrée").pack(anchor="w")
    tk.Entry(frame, textvariable=dossier_input).pack(fill=tk.X)
    tk.Button(frame, text="Parcourir…", command=choisir_dossier).pack(pady=5)

    tk.Checkbutton(frame, text="Générer une archive ZIP", variable=option_archive).pack(anchor="w")
    tk.Checkbutton(frame, text="Vider le dossier output (--force)", variable=option_force).pack(anchor="w")

    tk.Button(frame, text="Lancer le traitement", command=lancer_traitement).pack(pady=10)

    tk_handler = TkLogHandler(log)
    tk_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(tk_handler)

    console = scrolledtext.ScrolledText(frame, height=10)
    console.pack(fill=tk.BOTH, expand=True)

    poll_log_queue()

    root.mainloop()


def verifier_ou_vider_output(dossier_output, force = False):
    if not os.path.exists(dossier_output):
        return  # OK, il sera créé plus tard

    if os.listdir(dossier_output):
        if force:
            shutil.rmtree(dossier_output)
            # print(f"Dossier '{dossier_output}' vidé (--force)")
        else:
            raise RuntimeError(
                f"Le dossier '{dossier_output}' n'est pas vide.\n"
                f"Utilisez --force pour vider le dossier automatiquement."
            )



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

    logger.info(f"{len(questions)} fichiers Markdown générés dans : {dossier_sortie}")

def normalize_name(filename):
    """Transforme 'goudron bitimeux.txt' → 'goudron_bitimeux'"""
    name = os.path.splitext(filename)[0]
    return name.strip().lower().replace(" ", "_")


def traiter_dossier(dossier_input, generer_archive=False, force=False):
    if not os.path.isdir(dossier_input):
        raise ValueError("Le dossier d'entrée est invalide")

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


if __name__ == "__main__":

    if len(sys.argv) > 1:  # Mode ligne de commande

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

        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)

        logger.addHandler(console_handler)

        
        traiter_dossier(dossier_input, generer_archive, force)

    else:  # Mode interface

        lancer_interface()