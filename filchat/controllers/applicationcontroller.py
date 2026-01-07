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