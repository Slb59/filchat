"""MainWindow : Interface Qt pure"""


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
        self.line_edit_path.setPlaceholderText(
            "Saisissez le chemin ou utilisez Parcourir..."
        )
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
            self.show_error(
                f"Erreur lors de la sélection:\n{str(e)}\n\nUtilisez la saisie manuelle."
            )

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
                    self,
                    "Traitement en cours",
                    "Un traitement est en cours. Quitter ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.controller.worker_thread.quit()
                    self.controller.worker_thread.wait(2000)
                    event.accept()
                else:
                    event.ignore()
                    return
        event.accept()
