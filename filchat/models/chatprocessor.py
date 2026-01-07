""" ChatProcessor : Traitement pur des fichiers (parse, save, archive) """

import os
import zipfile
from datetime import datetime


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