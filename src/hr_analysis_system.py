from openai import AsyncOpenAI
from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass
import json
from abc import ABC, abstractmethod
from utils.utilities import setup_logging
from utils.file_handler import FileHandler

@dataclass
class PreferenciaReclutadorProfile:
    """Store recruiter preferences"""
    habilidades_preferidas: List[str]

@dataclass
class KillerProfile:
    """Store killer criteria"""
    killer_habilidades: List[str]
    killer_experiencia: List[str]

@dataclass
class JobProfile:
    """Standardized job requirement structure"""
    nombre_vacante: str
    habilidades: List[str]
    experiencia: List[str]
    formacion: List[str]
    habilidades_preferidas: Optional[List[str]] = None

@dataclass
class CandidateProfile:
    """Standardized resume structure"""
    nombre_candidato: str
    habilidades: List[str]
    experiencia: List[str]
    formacion: List[str]
    raw_data: Optional[Dict] = None

@dataclass
class MatchScore:
    """Represents the match scoring results"""
    final_score: float
    component_scores: Dict[str, float]
    disqualified: bool = False
    disqualification_reasons: List[str] = None

    def __post_init__(self):
        if self.disqualification_reasons is None:
            self.disqualification_reasons = []

class IEmbeddingProvider(ABC):
    """Abstract interface for embedding providers"""
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text"""
        pass

class OpenAIEmbeddingProvider(IEmbeddingProvider):
    """OpenAI implementation of embedding provider"""
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
    """Base class for text analysis operations"""
    def __init__(self, embedding_provider: IEmbeddingProvider):
        self.embedding_provider = embedding_provider

    async def calculate_semantic_similarity(self, text1: List[str], text2: List[str]) -> float:
        """Calculate semantic similarity between two lists of text"""
        embeddings1 = [await self.embedding_provider.get_embedding(t) for t in text1]
        embeddings2 = [await self.embedding_provider.get_embedding(t) for t in text2]
        
        similarities = np.zeros((len(text1), len(text2)))
        for i, emb1 in enumerate(embeddings1):
            for j, emb2 in enumerate(embeddings2):
                similarities[i, j] = np.dot(emb1, emb2)
        
        return float(np.mean(np.max(similarities, axis=1)))

class SemanticAnalyzer(TextAnalyzer):
    """Handles semantic analysis of text using LLM"""
    def __init__(self, embedding_provider: IEmbeddingProvider):
        super().__init__(embedding_provider)
        self.client = AsyncOpenAI(api_key=embedding_provider.client.api_key)
        self.model = "gpt-3.5-turbo"

    async def standardize_job_description(self, description: str, preferences: Optional[Dict] = None) -> JobProfile:
        """Convert raw job description and preferences into standardized format"""
        prompt = f"""
        Analyze this job description and hiring preferences. Extract and format 
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

        Hiring Preferences:
        {json.dumps(preferences or {}, indent=2)}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        profile_data = json.loads(response.choices[0].message.content)
        profile_data['habilidades_preferidas'] = preferences.get('habilidades_preferidas', []) if preferences else []
        return JobProfile(**profile_data)

    async def standardize_resume(self, resume_text: str) -> CandidateProfile:
        """Convert raw resume text into standardized format"""
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

class MatchingEngine(TextAnalyzer):
    """Handles matching logic between job requirements and candidate profiles"""
    def __init__(self, embedding_provider: IEmbeddingProvider):
        super().__init__(embedding_provider)
        self.threshold = 0.7

    async def check_killer_criteria(
        self,
        candidate: CandidateProfile,
        killer_criteria: Optional[Dict[str, List[str]]]
    ) -> Tuple[bool, List[str]]:
        """Check if candidate meets all killer criteria"""
        if not killer_criteria or not any(killer_criteria.values()):
            return True, []
            
        disqualification_reasons = []

        for criteria_type, criteria_list in killer_criteria.items():
            if not criteria_list:
                continue
                
            candidate_field = 'habilidades' if 'habilidades' in criteria_type else 'experiencia'
            score = await self.calculate_semantic_similarity(
                criteria_list,
                getattr(candidate, candidate_field)
            )
            
            if score < self.threshold:
                reason = "No cumple con las habilidades obligatorias" if 'habilidades' in criteria_type else "No cumple con la experiencia obligatoria"
                disqualification_reasons.append(reason)
        
        return len(disqualification_reasons) == 0, disqualification_reasons

    async def calculate_match_score(
        self, 
        job: JobProfile, 
        candidate: CandidateProfile,
        killer_criteria: Optional[Dict[str, List[str]]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> MatchScore:
        """Calculate overall match score between job and candidate"""
        # Check killer criteria first if provided
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

        weights = weights or {
            "habilidades": 0.3,
            "experiencia": 0.3,
            "formacion": 0.3,
            "preferencias_reclutador": 0.1
        }
        
        component_scores = {
            "habilidades": await self.calculate_semantic_similarity(job.habilidades, candidate.habilidades),
            "experiencia": await self.calculate_semantic_similarity(job.experiencia, candidate.experiencia),
            "formacion": await self.calculate_semantic_similarity(job.formacion, candidate.formacion),
            "preferencias_reclutador": await self.calculate_semantic_similarity(
                job.habilidades_preferidas or [],
                candidate.habilidades
            ) if job.habilidades_preferidas else 0.0
        }
        
        final_score = sum(
            score * weights[component]
            for component, score in component_scores.items()
        )
        
        return MatchScore(
            final_score=final_score,
            component_scores=component_scores
        )

class RankingSystem:
    """Handles candidate ranking based on match scores"""
    def __init__(self, matching_engine: MatchingEngine):
        self.matching_engine = matching_engine
    
    async def rank_candidates(
        self, 
        job: JobProfile, 
        candidates: List[CandidateProfile],
        killer_criteria: Optional[Dict[str, List[str]]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> List[Tuple[CandidateProfile, MatchScore]]:
        """Rank candidates based on their match scores"""
        rankings = []
        for candidate in candidates:
            score = await self.matching_engine.calculate_match_score(
                job, 
                candidate, 
                killer_criteria,
                weights
            )
            rankings.append((candidate, score))
        
        rankings.sort(
            key=lambda x: (not x[1].disqualified, x[1].final_score),
            reverse=True
        )
        return rankings