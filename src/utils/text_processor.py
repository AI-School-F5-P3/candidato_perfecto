from deep_translator import GoogleTranslator
from typing import List, Dict
import re

class TextProcessor:
    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='es')
        
        # Spanish-focused skill variations
        self.skill_synonyms = {
            'python': ['programación python', 'desarrollo python', 'python programming'],
            'machine learning': ['aprendizaje automático', 'aprendizaje de máquina', 'ml'],
            'deep learning': ['aprendizaje profundo', 'redes neuronales'],
            'tensorflow': ['tf', 'tensor flow'],
            'análisis de datos': ['data analysis', 'analítica de datos'],
            'procesamiento de lenguaje natural': ['nlp', 'pln', 'procesamiento del lenguaje'],
            'gestión de proyectos': ['project management', 'dirección de proyectos'],
            'cloud computing': ['computación en la nube', 'servicios cloud']
        }
        
        # Comprehensive Spanish education levels
        self.education_levels = {
            'doctorado': ['phd', 'doctor', 'ph.d', 'doctorado', 'tesis doctoral'],
            'master': ['máster', 'maestría', 'msc', 'ms', 'posgrado', 'postgrado'],
            'grado': ['licenciatura', 'ingeniería', 'ingeniero', 'graduado', 'bs', 'bsc'],
            'grado_tecnico': ['ingeniería técnica', 'diplomatura', 'fp superior']
        }

    def translate_to_spanish(self, text: str) -> str:
        """Translate text to Spanish if it's not already in Spanish"""
        try:
            return self.translator.translate(text)
        except:
            return text

    def extract_years_experience(self, text: str) -> str:
        """Extract and standardize years of experience"""
        patterns = [
            (r'(\d+)\+?\s*(?:año|year)', r'\1_years_experience'),
            (r'(\d+)\s*-\s*\d+\s*(?:año|year)', lambda m: f"{m.group(1)}_years_experience"),
            (r'mas de (\d+)\s*(?:año|year)', r'\1_years_experience'),
            (r'mínimo (\d+)\s*(?:año|year)', r'\1_years_experience'),
            (r'al menos (\d+)\s*(?:año|year)', r'\1_years_experience')
        ]
        
        text = text.lower()
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        return text

    def standardize_education(self, text: str) -> str:
        """Standardize education terms to Spanish standard format"""
        text = text.lower()
        for std_level, variations in self.education_levels.items():
            if any(var in text for var in variations):
                return std_level
        return text

    def normalize_skill(self, skill: str) -> str:
        """Normalize skill variations to standard Spanish form"""
        skill = skill.lower().strip()
        for standard_skill, variations in self.skill_synonyms.items():
            if skill in variations or skill == standard_skill:
                return standard_skill
        return skill

    def process_text(self, text: str) -> str:
        """Complete text processing pipeline"""
        if not text:
            return ""
        
        # Ensure text is in Spanish
        text = self.translate_to_spanish(str(text))
        
        # Apply standardizations
        text = self.extract_years_experience(text)
        text = re.sub(r'(gestión|management)', 'gestión', text, flags=re.IGNORECASE)
        text = re.sub(r'(desarrollo|development)', 'desarrollo', text, flags=re.IGNORECASE)
        
        return text

def extract_years_number(text: str) -> int:
    pattern = r'(\d+)\s*(?:años?|years?|_years_experience)'
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else 0