from openai import AsyncOpenAI  # Add this import at the top
import openai
from typing import Dict, List, Tuple
import numpy as np
from dataclasses import dataclass
import json

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
    experiencia: List[str]  # Renamed from experiencia_conocimiento
    formacion: List[str]
    habilidades_preferidas: List[str] = None  # Add this field to store recruiter preferences

@dataclass
class CandidateProfile:
    """Standardized resume structure"""
    nombre_candidato: str
    habilidades: List[str]
    experiencia: List[str]  # Renamed from experiencia_conocimiento
    formacion: List[str]
    raw_data: Dict = None  # Keep raw_data for debugging UI

class SemanticAnalyzer:
    def __init__(self, api_key: str):
        """Initialize the semantic analyzer with OpenAI API key"""
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
        #self.model = "gpt-4o"

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text using OpenAI's embedding model"""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    async def standardize_job_description(self, description: str, preferences: Dict) -> JobProfile:
        """Convert raw job description and preferences into standardized format"""
        prompt = f"""
        Analyze this job description and hiring preferences. Extract and format 
        the output as JSON with the following structure:
        {{
            "nombre_vacante": "job title",
            "habilidades": ["skill1", "skill2"],  # List of required and preferred skills combined
            "experiencia": [  # List of experience requirements and industry knowledge
                "years of experience required",
                "industry requirement 1",
                "domain knowledge 1",
                "responsibility 1"
            ],
            "formacion": [  # List starting with educational qualifications, followed by certifications
                "required education level",
                "preferred education level",
                "certification 1",
                "certification 2"
            ]
        }}

        Important: Include any skills listed in the hiring preferences in the habilidades section.
        For formacion, list educational qualifications first, followed by any required certifications.

        Job Description:
        {description}

        Hiring Preferences:
        {json.dumps(preferences or {}, indent=2)}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        profile_data = json.loads(response.choices[0].message.content)
        # Add recruiter's preferred skills to the job profile (safely handle empty preferences)
        profile_data['habilidades_preferidas'] = preferences.get('habilidades_preferidas', []) if preferences else []
        return JobProfile(**profile_data)

    async def standardize_resume(self, resume_text: str) -> CandidateProfile:
        """Convert raw resume text into standardized format"""
        prompt = f"""
        Analyze this resume and extract key components.
        Format the output as JSON with the following structure:
        {{
            "nombre_candidato": "candidate name",
            "habilidades": ["skill1", "skill2"],  # All technical and soft skills
            "experiencia": [  # List of experience and domain knowledge
                "total years of experience",
                "industry experience 1",
                "domain knowledge 1",
                "past role 1"
            ],
            "formacion": [  # Educational qualifications followed by certifications
                "highest education level",
                "other education",
                "certification 1",
                "certification 2"
            ]
        }}

        Important: For formacion, list educational qualifications first (e.g., PhD, Master's, Bachelor's), 
        followed by any technical certifications or courses.

        Resume:
        {resume_text}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        profile_data = json.loads(response.choices[0].message.content)
        # Store raw data for debugging in UI
        raw_data = profile_data.copy()
        profile_data['raw_data'] = raw_data
        return CandidateProfile(**profile_data)

class MatchingEngine:
    def __init__(self, analyzer: SemanticAnalyzer):
        self.analyzer = analyzer
        
    async def check_killer_criteria(
        self,
        candidate: CandidateProfile,
        killer_criteria: Dict[str, List[str]]
    ) -> Tuple[bool, List[str]]:
        """Check if candidate meets all killer criteria"""
        disqualification_reasons = []
        
        # Only check if there are any killer criteria
        if not any(killer_criteria.values()):
            return True, []
            
        # Check killer habilidades
        if killer_criteria.get("killer_habilidades"):
            habilidades_score = await self.calculate_skill_match_score(
                killer_criteria["killer_habilidades"],
                candidate.habilidades
            )
            if habilidades_score < 0.7:  # threshold for mandatory skills
                disqualification_reasons.append("No cumple con las habilidades obligatorias")
        
        # Check killer experiencia
        if killer_criteria.get("killer_experiencia"):
            experiencia_score = await self.calculate_skill_match_score(
                killer_criteria["killer_experiencia"],
                candidate.experiencia
            )
            if experiencia_score < 0.7:  # threshold for mandatory experience
                disqualification_reasons.append("No cumple con la experiencia obligatoria")
        
        return len(disqualification_reasons) == 0, disqualification_reasons
        
    async def calculate_skill_match_score(
        self, 
        job_skills: List[str], 
        candidate_skills: List[str]
    ) -> float:
        """Calculate semantic similarity between job and candidate skills"""
        # Get embeddings for all skills
        job_embeddings = [await self.analyzer.get_embedding(skill) for skill in job_skills]
        candidate_embeddings = [await self.analyzer.get_embedding(skill) for skill in candidate_skills]
        
        # Calculate similarity matrix
        similarities = np.zeros((len(job_skills), len(candidate_skills)))
        for i, job_emb in enumerate(job_embeddings):
            for j, cand_emb in enumerate(candidate_embeddings):
                similarities[i, j] = np.dot(job_emb, cand_emb)
        
        # Take the maximum similarity for each required skill
        return float(np.mean(np.max(similarities, axis=1)))

    async def calculate_match_score(
        self, 
        job: JobProfile, 
        candidate: CandidateProfile,
        killer_criteria: Dict[str, List[str]] = None
    ) -> Dict[str, float]:
        """Calculate overall match score between job and candidate"""
        # First check killer criteria if provided
        if killer_criteria:
            meets_criteria, reasons = await self.check_killer_criteria(candidate, killer_criteria)
            if not meets_criteria:
                return {
                    "final_score": 0.0,
                    "component_scores": {
                        "habilidades": 0.0,
                        "experiencia": 0.0,
                        "formacion": 0.0,
                        "preferencias_reclutador": 0.0
                    },
                    "disqualified": True,
                    "disqualification_reasons": reasons
                }
        
        # Continue with normal scoring if not disqualified
        # Calculate skills match
        habilidades_score = await self.calculate_skill_match_score(
            job.habilidades, 
            candidate.habilidades
        )
        
        # Calculate experience and knowledge match
        experiencia_score = await self.calculate_skill_match_score(
            job.experiencia,  # Updated field name
            candidate.experiencia  # Updated field name
        )
        
        # Calculate education and certification match
        formacion_score = await self.calculate_skill_match_score(
            job.formacion,
            candidate.formacion
        )

        # Calculate recruiter preferences match if available
        preferencias_score = 0.0
        if hasattr(job, 'habilidades_preferidas') and job.habilidades_preferidas:
            preferencias_score = await self.calculate_skill_match_score(
                job.habilidades_preferidas,
                candidate.habilidades
            )
        
        # Get weights from preferences
        weights = {
            "habilidades": 0.3,
            "experiencia": 0.3,  # Updated field name
            "formacion": 0.3,
            "preferencias_reclutador": 0.1
        }
        
        final_score = (
            weights["habilidades"] * habilidades_score +
            weights["experiencia"] * experiencia_score +  # Updated field name
            weights["formacion"] * formacion_score +
            weights["preferencias_reclutador"] * preferencias_score
        )
        
        return {
            "final_score": final_score,
            "component_scores": {
                "habilidades": habilidades_score,
                "experiencia": experiencia_score,  # Updated field name
                "formacion": formacion_score,
                "preferencias_reclutador": preferencias_score
            },
            "disqualified": False,
            "disqualification_reasons": []
        }

class RankingSystem:
    def __init__(self, matching_engine: MatchingEngine):
        self.matching_engine = matching_engine
    
    async def rank_candidates(
        self, 
        job: JobProfile, 
        candidates: List[CandidateProfile],
        killer_criteria: Dict[str, List[str]] = None
    ) -> List[Tuple[CandidateProfile, Dict[str, float]]]:
        """Rank candidates based on their match scores"""
        # Calculate scores for all candidates
        rankings = []
        for candidate in candidates:
            score = await self.matching_engine.calculate_match_score(
                job, 
                candidate, 
                killer_criteria
            )
            rankings.append((candidate, score))
        
        # Sort by final score in descending order, putting disqualified candidates at the end
        rankings.sort(
            key=lambda x: (
                not x[1].get("disqualified", False),  # Qualified candidates first
                x[1]["final_score"]  # Then by score
            ), 
            reverse=True
        )
        return rankings