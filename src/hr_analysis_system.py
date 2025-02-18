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
        self.model = "text-embedding-3-small"

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
    """Maneja el análisis semántico de texto usando LLM"""
    def __init__(self, embedding_provider: IEmbeddingProvider):
        super().__init__(embedding_provider)
        self.client = AsyncOpenAI(api_key=embedding_provider.client.api_key)
        self.model = "gpt-3.5-turbo"

    async def standardize_job_description(self, description: str) -> JobProfile:
        """Standardize job description into a JSON with these keys: nombre_vacante, habilidades, experiencia, formacion."""
        processed_text = self.preprocess_text(description)
        prompt = f"""
        Extract and summarize key information from this job description.
        For experience requirements:
        - Condense long descriptions into concise points
        - Extract years of experience explicitly (e.g., specify at least X_years_experience)
        - Focus on key responsibilities and achievements
        - Standardize all durations as 'X_years_experience'
        
        For skills and education:
        - Use standard terms (e.g., 'masters_degree', 'bachelors_degree')
        - List only essential requirements
        
        Output a focused JSON with exactly these keys:
        {{
          "nombre_vacante": "clear job title",
          "habilidades": ["key technical skills only"],
          "experiencia": [
              "condensed experience points",
              "e.g., '5_years_experience in backend development'",
              "e.g., 'led_teams of 5-10 developers'"
          ],
          "formacion": ["required education levels only"]
        }}
        
        Text: {processed_text}
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        profile_data = json.loads(response.choices[0].message.content)
        return JobProfile(**profile_data)

    async def standardize_preferences(self, preferences: str) -> PreferenciaReclutadorProfile:
        """Standardize recruiter preferences into JSON with the key 'habilidades_preferidas'."""
        if not preferences.strip():
            return PreferenciaReclutadorProfile(habilidades_preferidas=[])
        processed_text = self.preprocess_text(preferences)
        prompt = f"""
        Extract and normalize skills from the following recruiter preferences.
        Output a JSON of the form:
        {{"habilidades_preferidas": [...]}} 
        Preferences: {processed_text}
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        profile_data = json.loads(response.choices[0].message.content)
        return PreferenciaReclutadorProfile(
            habilidades_preferidas=profile_data["habilidades_preferidas"],
            raw_data=profile_data
        )

    async def standardize_resume(self, resume_text: str) -> CandidateProfile:
        """Standardize resume text into JSON with keys: nombre_candidato, habilidades, experiencia, formacion."""
        processed_text = self.preprocess_text(resume_text)
        prompt = f"""
        Extract and summarize key information from this resume.
        For experience section:
        - Condense lengthy job descriptions into key achievements
        - Extract and standardize duration as 'X_years_experience'
        - Focus on quantifiable results and responsibilities
        - Limit to 2-3 key points per role
        - Remove unnecessary details while keeping core accomplishments
        
        For skills and education:
        - Extract technical skills and tools
        - Standardize education terms
        - Focus on relevant certifications
        
        Output a focused JSON with exactly these keys:
        {{
          "nombre_candidato": "candidate name",
          "habilidades": ["relevant technical skills only"],
          "experiencia": [
              "condensed experience points",
              "e.g., '3_years_experience leading backend teams'",
              "e.g., 'increased system performance by 40%'"
          ],
          "formacion": ["standardized education and certifications"]
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
        profile_data['raw_data'] = raw_data
        return CandidateProfile(**profile_data)

    async def standardize_killer_criteria(self, criteria: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Standardize killer criteria into a JSON with keys: killer_habilidades and killer_experiencia.
        IMPORTANT: If killer skills is empty then there are no killer skills required and the candidate must not be flagged as disqualified.
        Similarly, if killer experience is empty then there is no experience required and the candidate must not be flagged as disqualified.
        """
        if not any(criteria.values()):
            return {"killer_habilidades": [], "killer_experiencia": []}
        skills_text = "\n".join(criteria.get("killer_habilidades", []))
        exp_text = "\n".join(criteria.get("killer_experiencia", []))
        processed_text = self.preprocess_text(f"Skills:\n{skills_text}\n\nExperience:\n{exp_text}")
        prompt = f"""
        Normalize the following mandatory requirements.
        Convert durations to 'X_years_experience' and standardize technical terms.
        IMPORTANT: If killer skills is empty then no killer skills are required and no disqualification should occur.
        If killer experience is empty then no killer experience is required and no disqualification should occur.
        Output JSON as:
        {{
          "killer_habilidades": [...],
          "killer_experiencia": [...]
        }}
        Requirements: {processed_text}
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

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
        """Verifica si el candidato cumple con los criterios eliminatorios mediante análisis semántico"""
        if not killer_criteria or not any(killer_criteria.values()):
            return True, []
            
        disqualification_reasons = []

        # Verifica cada tipo de criterio eliminatorio (habilidades y experiencia)
        for criteria_type, criteria_list in killer_criteria.items():
            if not criteria_list:
                continue
                
            # Determina qué campo del perfil del candidato comparar basado en el tipo de criterio
            candidate_field = 'habilidades' if 'habilidades' in criteria_type else 'experiencia'
            score = await self.calculate_semantic_similarity(
                criteria_list,
                getattr(candidate, candidate_field)
            )
            
            # Allow a small tolerance margin of 0.05 before flagging disqualification
            if score < self.threshold:
                if score < self.threshold - 0.05:
                    reason = "No cumple con las habilidades obligatorias" if 'habilidades' in criteria_type else "No cumple con la experiencia obligatoria"
                    disqualification_reasons.append(reason)
                else:
                    logging.info("Borderline {0} match (score: {1}), not disqualifying".format(candidate_field, score))
        
        return len(disqualification_reasons) == 0, disqualification_reasons

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
        
        # Compile debug info and save CSV using FileHandler to relative folder (project root/docs/debug/)
        debug_rows = []
        for candidate, score in rankings:
            debug_rows.append({
                "nombre_candidato": candidate.nombre_candidato,
                "final_score": score.final_score,
                "disqualified": score.disqualified,
                "debug_info": json.dumps(score.debug_info)
            })
        import pandas as pd
        debug_df = pd.DataFrame(debug_rows)
        debug_path = "../docs/debug/debug.csv"  # Relative path from src folder
        FileHandler.save_dataframe(debug_df, debug_path)  # Using the new method
        
        return rankings