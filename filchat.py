import os
import sys
import zipfile
import shutil
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QCheckBox, QLabel, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import QThread, Signal, Slot, QObject

# Configuration du logger
logger = logging.getLogger("filchat")
logger.setLevel(logging.INFO)

class Worker(QObject):
    finished = Signal()
    log_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, path, generer_archive, force):
        super().__init__()
        self.path = path
        self.generer_archive = generer_archive
        self.force = force

    def run(self):
        try:
            self.log_signal.emit("Traitement démarré…")
            traiter_dossier(self.path, self.generer_archive, self.force)
            self.log_signal.emit("Traitement terminé avec succès.")
            self.finished.emit()
        except Exception as e:
            self.error_signal.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FilChat – Découpe de conversations")
        self.setGeometry(100, 100, 600, 400)

        # Variables
        self.dossier_input = ""
        self.option_archive = False
        self.option_force = False

        # Widgets
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Dossier d'entrée
        input_layout = QHBoxLayout()
        self.label_path = QLabel("Dossier d'entrée :")
        self.line_edit_path = QLineEdit()
        self.button_browse = QPushButton("Parcourir…")
        self.button_browse.clicked.connect(self.choisir_dossier)
        input_layout.addWidget(self.label_path)
        input_layout.addWidget(self.line_edit_path)
        input_layout.addWidget(self.button_browse)
        layout.addLayout(input_layout)

        # Options
        self.check_archive = QCheckBox("Générer une archive ZIP")
        self.check_force = QCheckBox("Vider le dossier output (--force)")
        layout.addWidget(self.check_archive)
        layout.addWidget(self.check_force)

        # Bouton de traitement
        self.button_run = QPushButton("Lancer le traitement")
        self.button_run.clicked.connect(self.lancer_traitement)
        layout.addWidget(self.button_run)

        # Console de logs
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

        # Configuration du logger
        self.tk_handler = TkLogHandler(self.log)
        self.tk_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(self.tk_handler)

    def choisir_dossier(self):
        path = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier")
        if path:
            self.dossier_input = path
            self.line_edit_path.setText(path)

    def log(self, message):
        self.console.append(message)

    def lancer_traitement(self):
        path = self.line_edit_path.text()
        if not path:
            QMessageBox.critical(self, "Erreur", "Veuillez sélectionner un dossier d'entrée")
            return

        self.worker_thread = QThread()
        self.worker = Worker(
            path,
            self.check_archive.isChecked(),
            self.check_force.isChecked()
        )
        self.worker.moveToThread(self.worker_thread)

        # Connexions des signaux
        self.worker.log_signal.connect(self.log)
        self.worker.error_signal.connect(self.show_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater) 
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        # self.worker.finished.connect(self.show_success)

        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def show_error(self, message):
        QMessageBox.critical(self, "Erreur", message)

    def show_success(self):
        QMessageBox.information(self, "Succès", "Traitement terminé")

class TkLogHandler(logging.Handler):
    def __init__(self, log_func):
        super().__init__()
        self.log_func = log_func

    def emit(self, record):
        msg = self.format(record)
        self.log_func(msg)

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
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
