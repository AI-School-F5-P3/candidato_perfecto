"""Lógica principal del sistema de análisis de candidatos usando NLP y embeddings"""
from openai import AsyncOpenAI
from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass
import json
from abc import ABC, abstractmethod
from src.utils.utilities import setup_logging
from src.utils.file_handler import FileHandler

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

    def __post_init__(self):
        if self.disqualification_reasons is None:
            self.disqualification_reasons = []

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

    async def calculate_semantic_similarity(self, text1: List[str], text2: List[str]) -> float:
        """Calcula la similitud semántica entre dos listas de texto usando embeddings"""
        # Obtiene embeddings para cada elemento de texto
        embeddings1 = [await self.embedding_provider.get_embedding(t) for t in text1]
        embeddings2 = [await self.embedding_provider.get_embedding(t) for t in text2]
        
        # Calcula matriz de similitud del coseno entre todos los pares de embeddings
        similarities = np.zeros((len(text1), len(text2)))
        for i, emb1 in enumerate(embeddings1):
            for j, emb2 in enumerate(embeddings2):
                similarities[i, j] = np.dot(emb1, emb2)
        
        # Retorna el promedio de las mejores coincidencias para cada texto en text1
        return float(np.mean(np.max(similarities, axis=1)))

class SemanticAnalyzer(TextAnalyzer):
    """Maneja el análisis semántico de texto usando LLM"""
    def __init__(self, embedding_provider: IEmbeddingProvider):
        super().__init__(embedding_provider)
        self.client = AsyncOpenAI(api_key=embedding_provider.client.api_key)
        self.model = "gpt-3.5-turbo"

    async def standardize_job_description(self, description: str) -> JobProfile:
        """Convierte la descripción del trabajo en formato estandarizado usando GPT"""
        prompt = f"""
        Analyze this job description. Extract and format 
        the output as JSON with the following structure:
        {{
            "nombre_vacante": "job title",
            "habilidades": ["skill1", "skill2"],
            "experiencia": [
                "years of experience required",
                "industry requirement 1",
                "domain knowledge 1",
                "responsibility 1"
            ],
            "formacion": [
                "required education level",
                "preferred education level",
                "certification 1",
                "certification 2"
            ]
        }}

        Job Description:
        {description}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        profile_data = json.loads(response.choices[0].message.content)
        return JobProfile(**profile_data)

    async def standardize_preferences(self, preferences: str) -> PreferenciaReclutadorProfile:
        """Convierte las preferencias del reclutador en formato estandarizado"""
        if not preferences.strip():
            return PreferenciaReclutadorProfile(habilidades_preferidas=[])
            
        skills = [skill.strip() for skill in preferences.split('\n') if skill.strip()]
        raw_data = {"habilidades_preferidas": skills}
        return PreferenciaReclutadorProfile(
            habilidades_preferidas=skills,
            raw_data=raw_data
        )

    async def standardize_resume(self, resume_text: str) -> CandidateProfile:
        """Convierte el texto del CV en formato estandarizado"""
        prompt = f"""
        Analyze this resume and extract key components.
        Format the output as JSON with the following structure:
        {{
            "nombre_candidato": "candidate name",
            "habilidades": ["skill1", "skill2"],
            "experiencia": [
                "total years of experience",
                "industry experience 1",
                "domain knowledge 1",
                "past role 1"
            ],
            "formacion": [
                "highest education level",
                "other education",
                "certification 1",
                "certification 2"
            ]
        }}

        Resume:
        {resume_text}
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

class MatchingEngine(TextAnalyzer):  # Fixed the syntax error here - added closing parenthesis
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
            
            # Si no alcanza el umbral mínimo, se considera que no cumple el criterio
            if score < self.threshold:
                reason = "No cumple con las habilidades obligatorias" if 'habilidades' in criteria_type else "No cumple con la experiencia obligatoria"
                disqualification_reasons.append(reason)
        
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
        # Primero verifica los criterios eliminatorios si existen
        if killer_criteria:
            meets_criteria, reasons = await self.check_killer_criteria(candidate, killer_criteria)
            if not meets_criteria:
                return MatchScore(
                    final_score=0.0,
                    component_scores={
                        "habilidades": 0.0,
                        "experiencia": 0.0,
                        "formacion": 0.0,
                        "preferencias_reclutador": 0.0
                    },
                    disqualified=True,
                    disqualification_reasons=reasons
                )

        # Pesos por defecto si no se especifican
        weights = weights or {
            "habilidades": 0.3,
            "experiencia": 0.3,
            "formacion": 0.3,
            "preferencias_reclutador": 0.1
        }
        
        # Calcula puntuaciones individuales para cada componente
        component_scores = {
            "habilidades": await self.calculate_semantic_similarity(job.habilidades, candidate.habilidades),
            "experiencia": await self.calculate_semantic_similarity(job.experiencia, candidate.experiencia),
            "formacion": await self.calculate_semantic_similarity(job.formacion, candidate.formacion),
            "preferencias_reclutador": await self.calculate_semantic_similarity(
                preferences.habilidades_preferidas,
                candidate.habilidades
            ) if preferences.habilidades_preferidas else 0.0
        }
        
        # Calcula puntuación final ponderada
        final_score = sum(
            score * weights[component]
            for component, score in component_scores.items()
        )
        
        return MatchScore(
            final_score=final_score,
            component_scores=component_scores
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