"""
FilChat - Application de découpe de conversations
Architecture MVC (Model-View-Controller)
"""

import os
import sys
import zipfile
import shutil
import logging
import traceback
from datetime import datetime
from typing import Optional, Callable, List, Tuple
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QCheckBox, QLabel, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import QThread, Signal, QObject, Qt


# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger("filchat")
logger.setLevel(logging.DEBUG)

log_file = os.path.join(os.path.expanduser("."), "filchat_debug.log")
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


# =============================================================================
# MODEL - Logique métier pure
# =============================================================================

class ChatProcessor:
    """Modèle : Gère le traitement des fichiers de chat"""
    
    @staticmethod
    def normalize_name(filename: str) -> str:
        """Transforme 'goudron bitimeux.txt' → 'goudron_bitimeux'"""
        name = os.path.splitext(filename)[0]
        return name.strip().lower().replace(" ", "_")
    
    @staticmethod
    def parse_chat_file(filepath: str) -> List[Tuple[str, str]]:
        """Parse un fichier de chat et retourne une liste de (question, réponse)"""
        with open(filepath, "r", encoding="utf-8") as f:
            lignes = f.readlines()
        
        questions = []
        current_question = None
        current_answer = None
        mode = None
        
        for ligne in lignes:
            if "Vous avez dit :" in ligne:
                if current_question is not None and current_answer is not None:
                    questions.append((current_question.strip(), current_answer.strip()))
                current_question = ""
                current_answer = ""
                mode = "question"
                continue
            
            if "ChatGPT a dit :" in ligne:
                mode = "answer"
                continue
            
            if mode == "question":
                current_question += ligne
            elif mode == "answer":
                current_answer += ligne
        
        # Dernier bloc
        if current_question is not None and current_answer is not None:
            questions.append((current_question.strip(), current_answer.strip()))
        
        return questions
    
    @staticmethod
    def save_as_markdown(question: str, answer: str, output_path: str):
        """Sauvegarde une paire question/réponse en Markdown"""
        contenu = f"""---
categorie:
date: {datetime.now().strftime('%Y-%m-%d')}
---

# Question
{question}

# Réponse
{answer}
"""
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(contenu)
    
    @staticmethod
    def create_archive(source_dir: str, archive_name: str):
        """Crée une archive ZIP d'un dossier"""
        with zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    chemin_fichier = os.path.join(root, file)
                    arcname = os.path.relpath(chemin_fichier, source_dir)
                    zipf.write(chemin_fichier, arcname)


class ProcessingJob:
    """Modèle : Représente un travail de traitement"""
    
    def __init__(self, input_dir: str, output_dir: str = "output", 
                 generate_archive: bool = False, force_clean: bool = False):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.generate_archive = generate_archive
        self.force_clean = force_clean
        self.processor = ChatProcessor()
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Valide les paramètres du job"""
        if not self.input_dir:
            return False, "Le dossier d'entrée n'est pas défini"
        
        if not os.path.isdir(self.input_dir):
            return False, f"Le dossier '{self.input_dir}' n'existe pas"
        
        return True, None
    
    def prepare_output_directory(self):
        """Prépare le dossier de sortie"""
        if not os.path.exists(self.output_dir):
            return
        
        if os.listdir(self.output_dir):
            if self.force_clean:
                logger.info(f"Suppression du dossier '{self.output_dir}' (force activé)")
                shutil.rmtree(self.output_dir)
            else:
                raise RuntimeError(
                    f"Le dossier '{self.output_dir}' n'est pas vide.\n"
                    f"Cochez l'option 'Vider le dossier output' ou videz-le manuellement."
                )
    
    def execute(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Exécute le traitement"""
        self.prepare_output_directory()
        os.makedirs(self.output_dir, exist_ok=True)
        
        fichiers_traites = 0
        
        for fichier in os.listdir(self.input_dir):
            if not fichier.lower().endswith(".txt"):
                continue
            
            if progress_callback:
                progress_callback(f"📄 Traitement de {fichier}...")
            
            chemin_fichier = os.path.join(self.input_dir, fichier)
            nom_dossier = self.processor.normalize_name(fichier)
            chemin_sortie = os.path.join(self.output_dir, nom_dossier)
            
            os.makedirs(chemin_sortie, exist_ok=True)
            
            # Parser et sauvegarder
            questions = self.processor.parse_chat_file(chemin_fichier)
            
            for index, (q, r) in enumerate(questions, start=1):
                nom_fichier = f"{datetime.now().strftime('%Y%m%d')}-{index:03d}.md"
                chemin = os.path.join(chemin_sortie, nom_fichier)
                self.processor.save_as_markdown(q, r, chemin)
            
            logger.info(f"{len(questions)} fichiers générés pour {fichier}")
            fichiers_traites += 1
        
        if progress_callback:
            progress_callback(f"✅ {fichiers_traites} fichier(s) traité(s)")
        
        if self.generate_archive:
            if progress_callback:
                progress_callback("📦 Génération de l'archive ZIP...")
            
            date_du_jour = datetime.now().strftime("%Y%m%d")
            nom_archive = f"{date_du_jour}.zip"
            chemin_archive = os.path.join(os.getcwd(), nom_archive)
            
            self.processor.create_archive(self.output_dir, chemin_archive)
            logger.info(f"Archive générée : {nom_archive}")
            
            if progress_callback:
                progress_callback("✅ Archive créée avec succès")


# =============================================================================
# CONTROLLER - Gère la logique applicative et le threading
# =============================================================================

class ProcessingWorker(QObject):
    """Controller : Exécute le traitement dans un thread séparé"""
    
    finished = Signal()
    progress = Signal(str)
    error = Signal(str)
    
    def __init__(self, job: ProcessingJob):
        super().__init__()
        self.job = job
    
    def run(self):
        """Exécute le job"""
        try:
            logger.info(f"Traitement démarré - input={self.job.input_dir}")
            self.progress.emit("Traitement démarré…")
            
            # Exécuter le job avec callback de progression
            self.job.execute(progress_callback=self.progress.emit)
            
            self.progress.emit("Traitement terminé avec succès.")
            logger.info("Traitement terminé avec succès")
            
        except RuntimeError as e:
            logger.warning(f"Erreur métier: {str(e)}")
            self.error.emit(str(e))
        except Exception as e:
            logger.error(f"Erreur inattendue: {str(e)}")
            logger.error(traceback.format_exc())
            self.error.emit(f"Erreur inattendue: {str(e)}")
        finally:
            self.finished.emit()


class ApplicationController:
    """Controller principal de l'application"""
    
    def __init__(self, view):
        self.view = view
        self.worker = None
        self.worker_thread = None
    
    def start_processing(self, input_dir: str, generate_archive: bool, force_clean: bool):
        """Démarre un traitement"""
        # Créer le job
        job = ProcessingJob(input_dir, generate_archive=generate_archive, force_clean=force_clean)
        
        # Valider
        valid, error_msg = job.validate()
        if not valid:
            self.view.show_error(error_msg)
            return
        
        # Désactiver l'interface
        self.view.set_controls_enabled(False)
        
        # Nettoyer le thread précédent
        if self.worker_thread and self.worker_thread.isRunning():
            logger.warning("Thread précédent encore actif")
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        # Créer et configurer le worker
        self.worker_thread = QThread()
        self.worker = ProcessingWorker(job)
        self.worker.moveToThread(self.worker_thread)
        
        # Connecter les signaux
        self.worker.progress.connect(self.view.add_log)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.cleanup_worker)
        
        # Démarrer
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()
        
        logger.info("Thread de traitement démarré")
    
    def on_error(self, message: str):
        """Gère les erreurs"""
        self.view.add_log(f"❌ Erreur : {message}")
        self.view.show_error(message)
        self.view.set_controls_enabled(True)
    
    def on_finished(self):
        """Gère la fin du traitement"""
        self.view.add_log("✅ Traitement terminé")
        self.view.set_controls_enabled(True)
    
    def cleanup_worker(self):
        """Nettoie le worker"""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None


# =============================================================================
# VIEW - Interface graphique
# =============================================================================

class MainWindow(QMainWindow):
    """Vue principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.controller = None
        self.init_ui()
        logger.info("MainWindow initialisé")
    
    def set_controller(self, controller: ApplicationController):
        """Injecte le controller"""
        self.controller = controller
    
    def init_ui(self):
        """Initialise l'interface"""
        self.setWindowTitle("FilChat – Découpe de conversations")
        self.setGeometry(100, 100, 700, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # === Dossier d'entrée ===
        input_layout = QHBoxLayout()
        self.label_path = QLabel("Dossier d'entrée :")
        self.line_edit_path = QLineEdit()
        self.line_edit_path.setPlaceholderText("Saisissez le chemin ou utilisez Parcourir...")
        self.button_browse = QPushButton("Parcourir…")
        self.button_browse.clicked.connect(self.on_browse_clicked)
        
        input_layout.addWidget(self.label_path)
        input_layout.addWidget(self.line_edit_path)
        input_layout.addWidget(self.button_browse)
        layout.addLayout(input_layout)
        
        # === Bouton répertoire courant ===
        current_dir_layout = QHBoxLayout()
        self.button_use_current = QPushButton("Utiliser le répertoire courant/input")
        self.button_use_current.clicked.connect(self.on_use_current_clicked)
        current_dir_layout.addStretch()
        current_dir_layout.addWidget(self.button_use_current)
        layout.addLayout(current_dir_layout)
        
        # === Options ===
        self.check_archive = QCheckBox("Générer une archive ZIP")
        self.check_force = QCheckBox("Vider le dossier output (--force)")
        layout.addWidget(self.check_archive)
        layout.addWidget(self.check_force)
        
        # === Bouton traitement ===
        self.button_run = QPushButton("Lancer le traitement")
        self.button_run.clicked.connect(self.on_run_clicked)
        layout.addWidget(self.button_run)
        
        # === Console ===
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)
        
        # === Info ===
        log_info = QLabel(f"Log de debug : {log_file}")
        log_info.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(log_info)
    
    # === Gestion des événements ===
    
    def on_browse_clicked(self):
        """Ouvre le dialogue de sélection"""
        try:
            start_dir = os.path.expanduser("~")
            
            if self.line_edit_path.text():
                potential = self.line_edit_path.text().strip()
                if os.path.isdir(potential):
                    start_dir = potential
                elif os.path.isdir(os.path.dirname(potential)):
                    start_dir = os.path.dirname(potential)
            
            start_dir = os.path.normpath(os.path.abspath(start_dir))
            
            dialog = QFileDialog(self)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
            dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
            
            try:
                dialog.setDirectory(start_dir)
            except Exception as e:
                logger.warning(f"setDirectory échoué: {e}")
                dialog.setDirectory(os.path.expanduser("~"))
            
            dialog.setWindowTitle("Sélectionner un dossier")
            
            if dialog.exec() == QFileDialog.DialogCode.Accepted:
                selected = dialog.selectedFiles()
                if selected:
                    path = selected[0]
                    self.line_edit_path.setText(path)
                    self.add_log(f"📁 Dossier sélectionné : {path}")
        
        except Exception as e:
            logger.error(f"Erreur browse: {str(e)}")
            logger.error(traceback.format_exc())
            self.show_error(f"Erreur lors de la sélection:\n{str(e)}\n\nUtilisez la saisie manuelle.")
    
    def on_use_current_clicked(self):
        """Utilise le répertoire courant"""
        current = os.path.join(os.getcwd(), "input")
        self.line_edit_path.setText(current)
        self.add_log(f"📁 Répertoire défini : {current}")
    
    def on_run_clicked(self):
        """Lance le traitement"""
        if not self.controller:
            self.show_error("Controller non initialisé")
            return
        
        input_dir = self.line_edit_path.text().strip()
        generate_archive = self.check_archive.isChecked()
        force_clean = self.check_force.isChecked()
        
        self.controller.start_processing(input_dir, generate_archive, force_clean)
    
    # === Méthodes publiques pour le controller ===
    
    def add_log(self, message: str):
        """Ajoute un message dans la console"""
        self.console.append(message)
    
    def show_error(self, message: str):
        """Affiche une erreur"""
        self.add_log(f"❌ {message}")
        QMessageBox.critical(self, "Erreur", message)
    
    def set_controls_enabled(self, enabled: bool):
        """Active/désactive les contrôles"""
        self.button_run.setEnabled(enabled)
        self.button_browse.setEnabled(enabled)
        self.button_use_current.setEnabled(enabled)
        self.line_edit_path.setEnabled(enabled)
        self.check_archive.setEnabled(enabled)
        self.check_force.setEnabled(enabled)
    
    def closeEvent(self, event):
        """Gère la fermeture"""
        if self.controller and self.controller.worker_thread:
            if self.controller.worker_thread.isRunning():
                reply = QMessageBox.question(
                    self, "Traitement en cours",
                    "Un traitement est en cours. Quitter ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.controller.worker_thread.quit()
                    self.controller.worker_thread.wait(2000)
                    event.accept()
                else:
                    event.ignore()
                    return
        event.accept()


# =============================================================================
# APPLICATION
# =============================================================================

def main():
    try:
        logger.info("=" * 70)
        logger.info("=== Démarrage de FilChat (MVC) ===")
        logger.info(f"Python {sys.version}")
        logger.info(f"Répertoire: {os.getcwd()}")
        logger.info("=" * 70)
        
        app = QApplication(sys.argv)
        app.setApplicationName("FilChat")
        app.setApplicationVersion("2.0-MVC")
        
        # Créer la vue
        view = MainWindow()
        
        # Créer le controller et l'injecter dans la vue
        controller = ApplicationController(view)
        view.set_controller(controller)
        
        view.show()
        
        exit_code = app.exec()
        logger.info(f"=== Arrêt de FilChat (code: {exit_code}) ===")
        sys.exit(exit_code)
    
    except Exception as e:
        logger.critical(f"Erreur fatale: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

    ======================

    Architecture MVC implémentée
MODEL (Logique métier)

ChatProcessor : Traitement pur des fichiers (parse, save, archive)
ProcessingJob : Représente un travail complet avec validation
Aucune dépendance Qt - Peut être testé unitairement

VIEW (Interface graphique)

MainWindow : Interface Qt pure
Ne contient aucune logique métier
Expose des méthodes publiques pour le controller (add_log, show_error, set_controls_enabled)

CONTROLLER (Coordination)

ApplicationController : Coordonne Model et View
ProcessingWorker : Gère le threading
Fait le lien entre l'interface et la logique métier

✅ Avantages de cette architecture
1. Séparation des responsabilités
View  → "L'utilisateur a cliqué" → Controller
Controller → "Traite ces données" → Model  
Model → "Voici le résultat" → Controller
Controller → "Affiche ça" → View
2. Testabilité
python# Test du Model (sans Qt)
job = ProcessingJob("/path/input")
job.execute()

# Test du Controller (mock de la View)
controller = ApplicationController(mock_view)
controller.start_processing(...)
3. Réutilisabilité
Le ChatProcessor peut être utilisé dans :

Une CLI
Une API web
Un script batch

4. Maintenabilité

Chaque classe a une seule responsabilité
Modifications du Model sans toucher la View
Changement de l'UI sans toucher la logique

🔄 Comparaison
Avant (monolithique) :

Tout mélangé dans MainWindow
500+ lignes dans une classe
Impossible à tester unitairement

Après (MVC) :

3 couches distinctes
Chaque classe < 150 lignes
Testable indépendamment

📚 Pour aller plus loin
Voulez-vous que j'ajoute :

Des tests unitaires ?
Une classe Settings pour la configuration ?
Un système d'événements plus sophistiqué ?
Une couche de persistance (sauvegarder les préférences) ?