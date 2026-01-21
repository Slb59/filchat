""" ProcessingWorker : Gère le threading
Fait le lien entre l'interface et la logique métier
"""

import traceback

from PySide6.QtCore import QObject, Signal
from filchat.models.processingjob import ProcessingJob


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