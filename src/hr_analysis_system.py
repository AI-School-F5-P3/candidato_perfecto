"""Lógica principal del sistema de análisis de candidatos usando NLP y embeddings"""
from openai import AsyncOpenAI
from typing import Dict, List, Tuple, Optional, Any  # Add Any for debug_info
import numpy as np
from dataclasses import dataclass
import json
from abc import ABC, abstractmethod
from src.utils.utilities import setup_logging
from src.utils.file_handler import FileHandler
from langdetect import detect
import re
import logging  # Added this import
from src.config import Config  # Add this import
import pandas as pd  # << Added for debugging CSV creation
from src.utils.text_processor import TextProcessor
from src.utils.text_processor import extract_years_number

@dataclass
class PreferenciaReclutadorProfile:
    """Almacena las preferencias del reclutador"""
    habilidades_preferidas: List[str]
    raw_data: Optional[Dict] = None

@dataclass
class KillerProfile:
    """Almacena los criterios eliminatorios"""
    killer_habilidades: List[str]
    killer_experiencia: List[str]

@dataclass
class JobProfile:
    """Estructura estandarizada de requisitos del puesto"""
    nombre_vacante: str
    habilidades: List[str]
    experiencia: List[str]
    formacion: List[str]
    habilidades_preferidas: Optional[List[str]] = None

@dataclass
class CandidateProfile:
    """Estructura estandarizada del currículum"""
    nombre_candidato: str
    habilidades: List[str]
    experiencia: List[str]
    formacion: List[str]
    raw_data: Optional[Dict] = None

@dataclass
class MatchScore:
    """Representa los resultados de puntuación de coincidencia"""
    final_score: float
    component_scores: Dict[str, float]
    disqualified: bool = False
    disqualification_reasons: List[str] = None
    debug_info: Optional[Dict[str, Any]] = None  # New field for debug details

    def __post_init__(self):
        if self.disqualification_reasons is None:
            self.disqualification_reasons = []
        if self.debug_info is None:
            self.debug_info = {}


class IEmbeddingProvider(ABC):
    """Interfaz abstracta para proveedores de embeddings"""
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Obtiene el vector de embedding para el texto"""
        pass
    
class OpenAIEmbeddingProvider(IEmbeddingProvider):
    """Implementación OpenAI del proveedor de embeddings"""
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = Config.MODEL.embedding_model


    async def get_embedding(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

class TextAnalyzer:
    """Clase base para operaciones de análisis de texto"""
    def __init__(self, embedding_provider: IEmbeddingProvider):
        self.embedding_provider = embedding_provider

    def preprocess_text(self, text: str) -> str:
        """Preprocesa el texto para estandarización"""
        if not text:
            return ""
            
        # Ensure text is string
        text = str(text)
        
        # Estandariza formatos comunes
        text = re.sub(r'(\d+)\s*(años?|years?)', r'\1_years_experience', text, flags=re.IGNORECASE)
        text = re.sub(r'(master|máster|maestría)', 'masters_degree', text, flags=re.IGNORECASE)
        text = re.sub(r'(licenciatura|grado|degree)', 'bachelors_degree', text, flags=re.IGNORECASE)
        text = re.sub(r'(programación|programming)', 'programming', text, flags=re.IGNORECASE)
        text = re.sub(r'(desarrollo|development)', 'development', text, flags=re.IGNORECASE)
        text = re.sub(r'(gestión|management)', 'management', text, flags=re.IGNORECASE)
        
        return text

    async def calculate_semantic_similarity(self, text1: List[str], text2: List[str]) -> float:
        """Calcula la similitud semántica entre dos listas de texto usando embeddings (cosine similarity)"""
        if not text1 or not text2:
            logging.warning("Empty text lists provided for similarity calculation")
            return 0.0

        text1 = [str(t) for t in text1 if t]
        text2 = [str(t) for t in text2 if t]
        if not text1 or not text2:
            return 0.0

        text1 = [self.preprocess_text(t) for t in text1]
        text2 = [self.preprocess_text(t) for t in text2]
        logging.debug(f"Preprocessed text1: {text1}")
        logging.debug(f"Preprocessed text2: {text2}")

        embeddings1 = [await self.embedding_provider.get_embedding(t) for t in text1]
        embeddings2 = [await self.embedding_provider.get_embedding(t) for t in text2]
        similarities = np.zeros((len(text1), len(text2)))
        for i, emb1 in enumerate(embeddings1):
            norm1 = np.linalg.norm(emb1) + 1e-8
            for j, emb2 in enumerate(embeddings2):
                norm2 = np.linalg.norm(emb2) + 1e-8
                cosine = np.dot(emb1, emb2) / (norm1 * norm2)
                similarities[i, j] = cosine
                logging.debug(f"Cosine similarity between '{text1[i]}' and '{text2[j]}': {cosine}")
        avg_similarity = float(np.mean(np.max(similarities, axis=1)))
        if avg_similarity < Config.MATCHING.fallback_threshold:
            logging.warning(f"Low similarity score ({avg_similarity}), attempting fallback matching")
            fallback_score = self._calculate_fallback_similarity(text1, text2)
            logging.debug(f"Fallback similarity score: {fallback_score}")
            return max(avg_similarity, fallback_score)
        return avg_similarity

    def _calculate_fallback_similarity(self, text1: List[str], text2: List[str]) -> float:
        """Calcula similitud basada en coincidencia de texto simple"""
        # Convierte todos los textos a minúsculas para comparación
        text1_lower = [t.lower() for t in text1]
        text2_lower = [t.lower() for t in text2]
        
        # Cuenta coincidencias exactas o parciales
        matches = 0
        for t1 in text1_lower:
            for t2 in text2_lower:
                if t1 in t2 or t2 in t1:
                    matches += 1
                    break
        
        return matches / len(text1) if text1 else 0.0

class SemanticAnalyzer(TextAnalyzer):
    """Maneja el análisis semántico de texto usando LLM y procesamiento de texto estructurado"""
    def __init__(self, embedding_provider: IEmbeddingProvider):
        super().__init__(embedding_provider)
        self.client = AsyncOpenAI(api_key=embedding_provider.client.api_key)
        self.model = Config.MODEL.chat_model
        self.text_processor = TextProcessor()

    async def standardize_job_description(self, description: str, hiring_preferences: dict) -> JobProfile:
        """Standardize job description into structured JSON format"""
        # Pre-process and translate text
        processed_text = self.text_processor.process_text(description)
        
        prompt = f"""
        Extract key information in Spanish from this job description:
        - Skills should be specific technical skills and tools
        - Experience should include years and key technical responsibilities 
        - Education should use standard terms (doctorado, master, grado)
        
        Required skills from preferences: {', '.join(hiring_preferences.get('habilidades_preferidas', []))}
        
        Output JSON with:
        {{
            "nombre_vacante": "job title",
            "habilidades": ["skill1", "skill2"],
            "experiencia": ["X_years_experience in...", "other requirements"],
            "formacion": ["education level requirements"]
        }}
        
        Text: {processed_text}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Post-process LLM output
        profile_data = json.loads(response.choices[0].message.content)
        profile_data["habilidades"] = [
            self.text_processor.normalize_skill(skill) 
            for skill in profile_data["habilidades"]
        ]
        profile_data["formacion"] = [
            self.text_processor.standardize_education(edu)
            for edu in profile_data["formacion"]
        ]
        profile_data["experiencia"] = [
            self.text_processor.extract_years_experience(exp)
            for exp in profile_data["experiencia"]
        ]
        
        return JobProfile(**profile_data)

    async def standardize_preferences(self, preferences: str) -> PreferenciaReclutadorProfile:
        """Standardize recruiter preferences into structured skills list"""
        if not preferences.strip():
            return PreferenciaReclutadorProfile(habilidades_preferidas=[])
            
        processed_text = self.text_processor.process_text(preferences)
        
        prompt = f"""
        Extract specific technical skills in Spanish from these preferences.
        Focus on hard skills, tools and technologies only.
        
        Output JSON as:
        {{"habilidades_preferidas": ["skill1", "skill2"]}}
        
        Preferences: {processed_text}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        profile_data = json.loads(response.choices[0].message.content)
        profile_data["habilidades_preferidas"] = [
            self.text_processor.normalize_skill(skill)
            for skill in profile_data["habilidades_preferidas"]
        ]
        
        return PreferenciaReclutadorProfile(
            habilidades_preferidas=profile_data["habilidades_preferidas"],
            raw_data=profile_data
        )

    async def standardize_resume(self, resume_text: str) -> CandidateProfile:
        """Standardize resume into structured JSON format"""
        processed_text = self.text_processor.process_text(resume_text)
        
        prompt = f"""
        Extract key information in Spanish from this resume:
        - List specific technical skills and tools
        - Include quantifiable achievements and years of experience
        - Standardize education levels
        
        Output JSON with:
        {{
            "nombre_candidato": "full name",
            "habilidades": ["skill1", "skill2"],  
            "experiencia": ["X_years_experience in...", "achievements"],
            "formacion": ["education with levels"]
        }}
        
        Resume: {processed_text}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        profile_data = json.loads(response.choices[0].message.content)
        raw_data = profile_data.copy()
        
        # Post-process LLM output
        profile_data["habilidades"] = [
            self.text_processor.normalize_skill(skill) 
            for skill in profile_data["habilidades"]
        ]
        profile_data["formacion"] = [
            self.text_processor.standardize_education(edu)
            for edu in profile_data["formacion"]
        ]
        profile_data["experiencia"] = [
            self.text_processor.extract_years_experience(exp)
            for exp in profile_data["experiencia"]
        ]
        profile_data["raw_data"] = raw_data
        
        return CandidateProfile(**profile_data)

    async def standardize_killer_criteria(self, criteria: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Standardize killer criteria into structured format"""
        if not any(criteria.values()):
            return {"killer_habilidades": [], "killer_experiencia": []}
            
        # Pre-process both criteria types
        skills_text = "\n".join(criteria.get("killer_habilidades", []))
        exp_text = "\n".join(criteria.get("killer_experiencia", []))
        processed_text = self.text_processor.process_text(
            f"Skills:\n{skills_text}\n\nExperience:\n{exp_text}"
        )
        
        prompt = f"""
        Extract and normalize mandatory requirements in Spanish:
        - Skills should be specific technical skills
        - Experience should include years and key technical requirements
        
        Output JSON as:
        {{
            "killer_habilidades": ["required_skill1", "required_skill2"],
            "killer_experiencia": ["X_years_experience1", "X_years_experience2"]
        }}
        
        Requirements: {processed_text}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Post-process LLM output
        result["killer_habilidades"] = [
            self.text_processor.normalize_skill(skill)
            for skill in result["killer_habilidades"]
        ]
        result["killer_experiencia"] = [
            self.text_processor.extract_years_experience(exp)
            for exp in result["killer_experiencia"]
        ]
        
        return result

class MatchingEngine(TextAnalyzer):
    """Maneja la lógica de coincidencia entre requisitos del trabajo y perfiles de candidatos"""
    def __init__(self, embedding_provider: IEmbeddingProvider):
        super().__init__(embedding_provider)
        # Umbral mínimo de similitud para considerar que se cumple un criterio eliminatorio
        self.threshold = 0.7

    async def check_killer_criteria(
        self,
        candidate: CandidateProfile,
        killer_criteria: Optional[Dict[str, List[str]]]
    ) -> Tuple[bool, List[str]]:
        """Verifica si el candidato cumple con los criterios eliminatorios mediante análisis semántico extraído
        para habilidades y experiencia de forma paralela.
        Para killer_experiencia, se suma el total de años extraídos de todas las entradas del candidato
        y se compara con el mínimo requerido extraído de la cadena de criterios.
        """
        if not killer_criteria or not any(killer_criteria.values()):
            return True, []

        disqualification_reasons = []

        # Process killer_habilidades (skills)
        killer_skills = killer_criteria.get("killer_habilidades", [])
        if killer_skills:
            # Normalize candidate skills (assumed to be a list of strings)
            candidate_skills = [skill.lower().strip() for skill in candidate.habilidades]
            for req_skill in killer_skills:
                req_norm = req_skill.lower().strip()
                if req_norm not in candidate_skills:
                    disqualification_reasons.append("No cumple con la habilidad obligatoria: " + req_skill)

        # Process killer_experiencia (experience)
        killer_experiences = killer_criteria.get("killer_experiencia", [])
        if killer_experiences:
            # Sum candidate's experience years from every entry in candidate.experiencia (assumed list of strings)
            candidate_total_years = sum(extract_years_number(exp) for exp in candidate.experiencia)
            # For each required experience criterion, check candidate's total experience years
            for req_exp in killer_experiences:
                required_years = extract_years_number(req_exp)
                if candidate_total_years < required_years:
                    disqualification_reasons.append(
                        f"Experiencia insuficiente: requiere {required_years} años, tiene {candidate_total_years} años."
                    )
        # Log borderline cases as needed (keeping existing tolerance logic if needed)
        # ...existing code for borderline tolerance can be inserted here if required...

        # Candidate is qualified if no disqualification reasons were found
        return (len(disqualification_reasons) == 0, disqualification_reasons)

    async def calculate_match_score(
        self, 
        job: JobProfile,
        preferences: PreferenciaReclutadorProfile, 
        candidate: CandidateProfile,
        killer_criteria: Optional[Dict[str, List[str]]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> MatchScore:
        """Calcula la puntuación de coincidencia entre un trabajo y un candidato"""
        killer_met = True
        killer_reasons = []
        if killer_criteria:
            killer_met, killer_reasons = await self.check_killer_criteria(candidate, killer_criteria)

        # Pesos por defecto si no se especifican
        weights = weights or {
            "habilidades": 0.3,
            "experiencia": 0.3,
            "formacion": 0.3,
            "preferencias_reclutador": 0.1
        }
        
        # Compute component scores and capture debug info
        debug_data = {}
        comp_scores = {}
        for comp in ["habilidades", "experiencia", "formacion"]:
            sim = await self.calculate_semantic_similarity(getattr(job, comp), getattr(candidate, comp))
            comp_scores[comp] = sim
            debug_data[comp] = {
                "candidate": getattr(candidate, comp),
                "job": getattr(job, comp),
                "cosine_similarity": sim,
                "weight": weights.get(comp, 0),
                "weighted_score": sim * weights.get(comp, 0)
            }
        # For recruiter preferences, use 1.0 (100%) if preferences are empty
        if not preferences.habilidades_preferidas:
            pref_sim = 1.0  # Perfect score when no preferences specified
            logging.info("No recruiter preferences specified, using perfect score (1.0)")
        else:
            pref_sim = await self.calculate_semantic_similarity(preferences.habilidades_preferidas, candidate.habilidades)
        
        comp_scores["preferencias_reclutador"] = pref_sim
        debug_data["preferencias_reclutador"] = {
            "candidate": candidate.habilidades,
            "preferences": preferences.habilidades_preferidas,
            "cosine_similarity": pref_sim,
            "weight": weights.get("preferencias_reclutador", 0),
            "weighted_score": pref_sim * weights.get("preferencias_reclutador", 0)
        }
        
        final = sum(score * weights[comp] for comp, score in comp_scores.items())
        # Include killer criteria details in debug info and disqualify if necessary
        debug_data["killer"] = {
            "qualified": killer_met,
            "reasons": killer_reasons
        }
        return MatchScore(
            final_score=final,
            component_scores=comp_scores,
            disqualified=not killer_met,
            disqualification_reasons=killer_reasons,
            debug_info=debug_data
        )

class RankingSystem:
    """Maneja la clasificación de candidatos basada en puntuaciones de coincidencia"""
    def __init__(self, matching_engine: MatchingEngine):
        self.matching_engine = matching_engine
    
    async def rank_candidates(
        self, 
        job: JobProfile,
        preferences: PreferenciaReclutadorProfile, 
        candidates: List[CandidateProfile],
        killer_criteria: Optional[Dict[str, List[str]]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> List[Tuple[CandidateProfile, MatchScore]]:
        """Clasifica candidatos por su puntuación y estado de descalificación"""
        # Calcula puntuaciones para todos los candidatos
        rankings = []
        for candidate in candidates:
            score = await self.matching_engine.calculate_match_score(
                job,
                preferences, 
                candidate,
                killer_criteria,
                weights
            )
            rankings.append((candidate, score))
        
        # Ordena: primero los no descalificados por puntuación, luego los descalificados
        rankings.sort(
            key=lambda x: (not x[1].disqualified, x[1].final_score),
            reverse=True
        )
        
        return rankings