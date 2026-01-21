import os
import sys
import zipfile
import shutil
import logging
import traceback
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QCheckBox, QLabel, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import QThread, Signal, QObject, Qt

# Force l'utilisation de X11
os.environ['QT_QPA_PLATFORM'] = 'xcb' 

# Configuration du logger
logger = logging.getLogger("filchat")
logger.setLevel(logging.DEBUG)

# Ajouter un handler fichier pour debug
log_file = os.path.join(os.path.expanduser("."), "filchat_debug.log")
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

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
            logger.info(f"Worker démarré - path={self.path}, archive={self.generer_archive}, force={self.force}")
            self.log_signal.emit("Traitement démarré…")
            traiter_dossier(self.path, self.generer_archive, self.force, self.log_signal)
            self.log_signal.emit("Traitement terminé avec succès.")
            logger.info("Worker terminé avec succès")
        except RuntimeError as e:
            # Erreur métier (dossier non vide, etc.) - pas de traceback
            logger.warning(f"Erreur métier: {str(e)}")
            logger.info("Émission du signal error_signal")
            self.error_signal.emit(str(e))
            logger.info("Signal error_signal émis")
        except Exception as e:
            # Erreur inattendue - traceback complet
            logger.error(f"Erreur inattendue: {str(e)}")
            logger.error(traceback.format_exc())
            logger.info("Émission du signal error_signal")
            self.error_signal.emit(f"Erreur inattendue: {str(e)}")
            logger.info("Signal error_signal émis")
        finally:
            # Toujours émettre finished
            logger.info("Worker: émission du signal finished")
            self.finished.emit()
            logger.info("Worker: signal finished émis")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FilChat – Découpe de conversations")
        self.setGeometry(100, 100, 600, 400)

        # Variables
        self.dossier_input = ""
        self.worker_thread = None
        self.worker = None

        # Widgets
        self.init_ui()

        logger.info("MainWindow initialisé")
        logger.info(f"Plateforme: {sys.platform}")
        logger.info(f"Version Qt: {QApplication.instance().applicationVersion()}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Dossier d'entrée
        input_layout = QHBoxLayout()
        self.label_path = QLabel("Dossier d'entrée :")
        self.line_edit_path = QLineEdit()
        self.line_edit_path.setPlaceholderText("Saisissez le chemin ou utilisez Parcourir...")
        self.button_browse = QPushButton("Parcourir…")
        self.button_browse.clicked.connect(self.choisir_dossier)
        input_layout.addWidget(self.label_path)
        input_layout.addWidget(self.line_edit_path)
        input_layout.addWidget(self.button_browse)
        layout.addLayout(input_layout)

        # Bouton pour définir le répertoire courant comme input
        current_dir_layout = QHBoxLayout()
        self.button_use_current = QPushButton("Utiliser le répertoire courant")
        self.button_use_current.clicked.connect(self.utiliser_repertoire_courant)
        # self.button_use_current.setStyleSheet("color: gray;")
        current_dir_layout.addStretch()
        current_dir_layout.addWidget(self.button_use_current)
        layout.addLayout(current_dir_layout)

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

        # Afficher le chemin du log
        log_info = QLabel(f"Log de debug : {log_file}")
        log_info.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(log_info)

        # Note: On ne connecte PAS le logger à la console pour éviter les problèmes de threading
        # Les messages importants passent par les signaux log_signal du Worker

    def utiliser_repertoire_courant(self):
        """Définit le répertoire de travail actuel comme dossier d'entrée"""
        try:
            current = os.getcwd()
            logger.info(f"Utilisation du répertoire courant: {current}")
            self.dossier_input = os.path.join(current, "input")
            self.line_edit_path.setText(self.dossier_input)
            self.console.append(f"Répertoire courant défini : {self.dossier_input}")
        except Exception as e:
            logger.error(f"Erreur dans utiliser_repertoire_courant: {str(e)}")
    
    
    def choisir_dossier(self):
        try:
            logger.info("Ouverture du dialog de sélection de dossier")
            start_dir = os.path.expanduser(".")
            if self.line_edit_path.text():
                start_dir = self.line_edit_path.text()
            logger.debug(f"Répertoire de départ: {start_dir}")
            
            # Options pour éviter les crashes sur certains systèmes
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            options |= QFileDialog.ShowDirsOnly

            logger.debug("Création du QFileDialog")
            
            # Méthode défensive : créer explicitement le dialogue
            # dialog = QFileDialog(self)
            # logger.debug("setFileMode")
            # dialog.setFileMode(QFileDialog.FileMode.Directory)
            # logger.debug("setOption- dontusenativedialog")
            # dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
            # logger.debug("setOption- showdirsonly")
            # dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
            # logger.debug(f"setDirectory - {start_dir}")
            start_dir = os.path.normpath(os.path.abspath(start_dir))
            # dialog.setDirectory(start_dir)
            # dialog.setWindowTitle("Sélectionner un dossier")
            path_selected = QFileDialog.getExistingDirectory(
                self, 
                "Sélectionner un dossier", 
                start_dir, 
                options=options
            )
            
            logger.debug("Affichage du dialogue")
            
            # Exécuter le dialogue
            # if dialog.exec() == QFileDialog.DialogCode.Accepted:
            #     selected = dialog.selectedFiles()
            #     if selected:
            #         path = selected[0]
            #         logger.info(f"Dossier sélectionné: {path}")
            #         self.dossier_input = path
            #         self.line_edit_path.setText(path)
            #         self.console.append(f"Dossier sélectionné : {path}")
            #     else:
            #         logger.info("Aucun dossier sélectionné")
            # else:
            #     logger.info("Sélection annulée par l'utilisateur")
            # logger.debug("Dialogue fermé proprement")

            if path_selected:
                logger.info(f"Dossier sélectionné: {path_selected}")
                self.dossier_input = path_selected
                self.line_edit_path.setText(path_selected)
                self.console.append(f"Dossier sélectionné : {path_selected}")
            else:
                logger.info("Sélection annulée par l'utilisateur")
            logger.debug("Dialogue fermé proprement")    
                
        except Exception as e:
            logger.error(f"Erreur dans choisir_dossier: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'ouvrir le sélecteur de fichiers.\n\n"
                f"Erreur: {str(e)}\n\n"
                f"Vous pouvez saisir le chemin manuellement dans le champ texte."
            )

    def log(self, message):
        """Ajoute un message dans la console de l'interface"""
        try:
            # NE PAS utiliser logger ici pour éviter la boucle infinie !
            # NE PAS utiliser repaint() car ça cause des erreurs de segmentation
            self.console.append(message)
            # Laisser Qt gérer le rafraîchissement automatiquement
        except Exception as e:
            # Logger uniquement en cas d'erreur (pas de récursion car c'est un ERROR)
            print(f"Erreur dans log: {str(e)}")  # Fallback sur print

    def lancer_traitement(self):
        try:
            logger.info("Lancement du traitement")
            path = self.line_edit_path.text().strip()
            if not path:
                QMessageBox.critical(self, "Erreur", "Veuillez sélectionner un dossier d'entrée")
                return
            if not os.path.isdir(path):
                QMessageBox.critical(self, "Erreur", f"Le dossier '{path}' n'existe pas")
                return
            
            # Désactiver les boutons pendant le traitement
            self.button_run.setEnabled(False)
            self.button_browse.setEnabled(False)
            self.button_use_current.setEnabled(False)

            # Nettoyer le thread précédent si existant
            if self.worker_thread and self.worker_thread.isRunning():
                logger.warning("Thread précédent encore actif, attente...")
                self.worker_thread.quit()
                self.worker_thread.wait()

            self.worker_thread = QThread()
            self.worker = Worker(
                path,
                self.check_archive.isChecked(),
                self.check_force.isChecked()
            )
            self.worker.moveToThread(self.worker_thread)

            # Connexions des signaux
            # IMPORTANT: Ne pas utiliser QueuedConnection car ça peut causer des segfaults
            # Qt gère automatiquement le bon type de connexion (AutoConnection)
            self.worker.log_signal.connect(self.log)
            self.worker.error_signal.connect(self.show_error)
            self.worker.finished.connect(self.on_traitement_termine)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker_thread.finished.connect(self.on_thread_finished)
            
            # Démarrer le thread
            self.worker_thread.started.connect(self.worker.run)
            self.worker_thread.start()

            logger.info("Thread de traitement démarré")
            
        except Exception as e:
            logger.error(f"Erreur dans lancer_traitement: {str(e)}")
            logger.error(traceback.format_exc())
            self.show_error(f"Erreur lors du lancement: {str(e)}")
            self.button_run.setEnabled(True)
            self.button_browse.setEnabled(True)
            self.button_use_current.setEnabled(True)

    def on_traitement_termine(self):
        """Appelé quand le traitement est terminé"""
        try:
            logger.info("Traitement terminé (signal reçu)")
            
            # Réactiver les boutons
            self.button_run.setEnabled(True)
            self.button_browse.setEnabled(True)
            self.button_use_current.setEnabled(True)
            
            logger.info("on_traitement_termine terminé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur dans on_traitement_termine: {str(e)}")
            logger.error(traceback.format_exc())
            # Essayer quand même de réactiver les boutons
            try:
                self.button_run.setEnabled(True)
                self.button_browse.setEnabled(True)
                self.button_use_current
            except:
                pass

    def on_thread_finished(self):
        """Appelé quand le thread est complètement terminé"""
        try:
            logger.info("Thread terminé, nettoyage...")
            
            # Utiliser deleteLater() qui est plus sûr en Qt
            if self.worker:
                logger.debug("Suppression du worker")
                self.worker.deleteLater()
                self.worker = None
            
            if self.worker_thread:
                logger.debug("Suppression du worker_thread")
                self.worker_thread.deleteLater()
                self.worker_thread = None
            
            logger.info("Nettoyage terminé")
            
        except Exception as e:
            logger.error(f"Erreur dans on_thread_finished: {str(e)}")
            logger.error(traceback.format_exc())

    def show_error(self, message):
        """Affiche une erreur (doit être appelé depuis le thread principal)"""
        try:
            logger.info(f"show_error appelé avec: {message}")
            
            # Ajouter le message dans la console
            try:
                self.console.append(f"Erreur : {message}")
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout dans la console: {str(e)}")
            
            # Afficher la boîte de dialogue (méthode simple)
            logger.info("Affichage de QMessageBox")
            QMessageBox.critical(self, "Erreur", message)
            logger.info("QMessageBox fermée")
            
            # Réactiver les boutons
            self.button_run.setEnabled(True)
            self.button_browse.setEnabled(True)
            self.button_use_current.setEnabled(True)
            logger.info("Boutons réactivés")
            
        except Exception as e:
            logger.error(f"Erreur dans show_error: {str(e)}")
            logger.error(traceback.format_exc())
            # En dernier recours, réactiver les boutons
            try:
                self.button_run.setEnabled(True)
                self.button_browse.setEnabled(True)
                self.button_use_current.setEnabled(True)
            except:
                pass

    def closeEvent(self, event):
        """Gérer la fermeture propre de l'application"""
        try:
            logger.info("Fermeture de l'application demandée")

            if self.worker_thread and self.worker_thread.isRunning():
                logger.info("Thread encore actif, attente de la fin...")
                reply = QMessageBox.question(
                    self,
                    "Traitement en cours",
                    "Un traitement est en cours. Voulez-vous vraiment quitter ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.worker_thread.quit()
                    self.worker_thread.wait(2000)  # Attendre max 2 secondes
                    event.accept()
                else:
                    event.ignore()
                    return

            logger.info("Application fermée proprement")
            event.accept()
        except Exception as e:
            logger.error(f"Erreur dans closeEvent: {str(e)}")
            event.accept()


def verifier_ou_vider_output(dossier_output, force=False):
    """
    Vérifie si le dossier output est vide ou le vide si force=True.
    Lève une RuntimeError si le dossier n'est pas vide et force=False.
    """
    if not os.path.exists(dossier_output):
        logger.debug(f"Dossier '{dossier_output}' n'existe pas encore (OK)")
        return  # OK, il sera créé plus tard

    contenu = os.listdir(dossier_output)
    if contenu:
        if force:
            logger.info(f"Suppression du dossier '{dossier_output}' (force activé)")
            shutil.rmtree(dossier_output)
            logger.info(f"Dossier '{dossier_output}' vidé avec succès")
        else:
            logger.warning(f"Dossier '{dossier_output}' non vide et force=False")
            raise RuntimeError(
                f"Le dossier '{dossier_output}' n'est pas vide.\n"
                f"Cochez l'option 'Vider le dossier output' ou videz-le manuellement."
            )
    else:
        logger.debug(f"Dossier '{dossier_output}' existe mais est vide (OK)")


def creer_archive_output(dossier_output):
    """Crée une archive ZIP du dossier output"""
    date_du_jour = datetime.now().strftime("%Y%m%d")
    nom_archive = f"{date_du_jour}.zip"
    chemin_archive = os.path.join(os.getcwd(), nom_archive)

    with zipfile.ZipFile(chemin_archive, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(dossier_output):
            for file in files:
                chemin_fichier = os.path.join(root, file)
                arcname = os.path.relpath(chemin_fichier, dossier_output)
                zipf.write(chemin_fichier, arcname)

    logger.info(f"Archive générée : {nom_archive}")


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

    logger.info(f"{len(questions)} fichiers Markdown générés dans : {dossier_sortie}")


def normalize_name(filename):
    """Transforme 'goudron bitimeux.txt' → 'goudron_bitimeux'"""
    name = os.path.splitext(filename)[0]
    return name.strip().lower().replace(" ", "_")


def traiter_dossier(dossier_input, generer_archive=False, force=False, log_signal=None):
    """Traite tous les fichiers .txt d'un dossier"""
    if not os.path.isdir(dossier_input):
        raise ValueError("Le dossier d'entrée est invalide")

    dossier_output = "output"

    # Vérifier/vider le dossier output
    verifier_ou_vider_output(dossier_output, force=force)
    os.makedirs(dossier_output, exist_ok=True)

    fichiers_traites = 0
    for fichier in os.listdir(dossier_input):
        if not fichier.lower().endswith(".txt"):
            continue

        chemin_fichier = os.path.join(dossier_input, fichier)
        nom_dossier = normalize_name(fichier)
        chemin_sortie = os.path.join(dossier_output, nom_dossier)
        
        logger.info(f"Traitement de {fichier}...")
        if log_signal:
            log_signal.emit(f"Traitement de {fichier}...")
        decoupe_chat(chemin_fichier, chemin_sortie)
        fichiers_traites += 1

    logger.info(f"{fichiers_traites} fichier(s) traité(s)")
    if log_signal:
        log_signal.emit(f"{fichiers_traites} fichier(s) traité(s)")

    if generer_archive:
        if log_signal:
            log_signal.emit("Génération de l'archive ZIP...")
        creer_archive_output(dossier_output)
        if log_signal:
            log_signal.emit("Archive créée avec succès")


def main():
    try:
        logger.info("=" * 70)
        logger.info("=== Démarrage de FilChat ===")
        logger.info(f"Python {sys.version}")
        logger.info(f"Répertoire de travail: {os.getcwd()}")
        logger.info("=" * 70)

        app = QApplication(sys.argv)
        app.setApplicationName("FilChat")
        app.setApplicationVersion("1.0")

        window = MainWindow()
        window.show()

        exit_code = app.exec()
        logger.info(f"=== Arrêt de FilChat (code: {exit_code}) ===")
        sys.exit(exit_code)

    except Exception as e:
        logger.critical(f"Erreur fatale: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()