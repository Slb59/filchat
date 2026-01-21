""" ProcessingJob : Représente un travail complet avec validation 
Testabilité:
python# Test du Model (sans Qt)
job = ProcessingJob("/path/input")
job.execute()
"""

import os
import shutil
from datetime import datetime


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