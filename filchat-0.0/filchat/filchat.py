"""
FilChat - Application de découpe de conversations
"""

import logging
import os
import sys
import traceback

from PySide6.QtWidgets import QApplication

# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger("filchat")
logger.setLevel(logging.DEBUG)

log_file = os.path.join(os.path.expanduser("."), "filchat_debug.log")
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

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
