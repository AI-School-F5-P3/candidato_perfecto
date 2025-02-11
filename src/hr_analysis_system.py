from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass
import json
import httpx
import logging

@dataclass
class JobProfile:
    """Standardized job requirement structure"""
    title: str
    killer_skills: List[str]  # Nueva lista para skills obligatorias
    required_skills: List[str]
    preferred_skills: List[str]
    experience_years: int
    education_level: str
    responsibilities: List[str]
    industry_knowledge: List[str]
    
@dataclass
class CandidateProfile:
    """Standardized resume structure"""
    name: str
    skills: List[str]
    experience_years: int
    education_level: str
    past_roles: List[str]
    industry_experience: List[str]

class SemanticAnalyzer:
    def __init__(self, api_url: str = "http://localhost:11434"):
        """Initialize the semantic analyzer with Ollama API URL"""
        self.api_url = api_url
        self.model = "llama2"
        self.client = httpx.AsyncClient()

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text using Ollama's embedding endpoint"""
        try:
            response = await self.client.post(
                f"{self.api_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred: {str(e)}")
            raise e
        except Exception as e:
            logging.error(f"Error getting embedding for text '{text}': {str(e)}")
            raise e

    async def _generate_json_response(self, prompt: str) -> dict:
        """Helper method to generate JSON responses from Mistral"""
        try:
            response = await self.client.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{prompt}\nResponde SOLO en formato JSON válido.",
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            response_text = response.json()["response"]
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
            raise ValueError("No valid JSON found in response")
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred: {str(e)}")
            raise e
        except Exception as e:
            logging.error(f"Failed to parse JSON response: {str(e)}")
            raise e

    async def standardize_job_description(self, description: str, preferences: Dict) -> JobProfile:
        """Convert raw job description and preferences into standardized format"""
        prompt = f"""
        Analiza esta descripción de trabajo y preferencias de contratación y extrae los componentes clave.
        Debes responder en formato JSON con exactamente esta estructura:
        {{
            "title": "job title",
            "killer_skills": ["skill1", "skill2"],
            "required_skills": ["skill1", "skill2"],
            "preferred_skills": ["skill1", "skill2"],
            "experience_years": number,
            "education_level": "level",
            "responsibilities": ["resp1", "resp2"],
            "industry_knowledge": ["domain1", "domain2"]
        }}

        Descripción del trabajo:
        {description}

        Preferencias de contratación:
        {json.dumps(preferences, indent=2)}
        """
        
        profile_data = await self._generate_json_response(prompt)
        return JobProfile(**profile_data)

    async def standardize_resume(self, resume_text: str) -> CandidateProfile:
        """Convert raw resume text into standardized format"""
        prompt = f"""
        Analiza este CV y extrae los componentes clave. Asegúrate de identificar todas las habilidades 
        técnicas y competencias mencionadas en la sección de skills.
        Debes responder en formato JSON con exactamente esta estructura:
        {{
            "name": "candidate name",
            "skills": ["skill1", "skill2"],
            "experience_years": number,
            "education_level": "level",
            "past_roles": ["role1", "role2"],
            "industry_experience": ["industry1", "industry2"]
        }}

        CV:
        {resume_text}
        """
        
        profile_data = await self._generate_json_response(prompt)
        return CandidateProfile(**profile_data)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class MatchingEngine:
    def __init__(self, analyzer: SemanticAnalyzer):
        self.analyzer = analyzer
        
    async def has_killer_skills(
        self,
        killer_skills: List[str],
        candidate_skills: List[str]
    ) -> bool:
        """Verifica si el candidato tiene todas las killer skills requeridas"""
        try:
            for skill in killer_skills:
                skill_embeddings = await self.analyzer.get_embedding(skill)
                has_skill = False
                
                # Comparar con cada skill del candidato
                for candidate_skill in candidate_skills:
                    candidate_embedding = await self.analyzer.get_embedding(candidate_skill)
                    similarity = np.dot(skill_embeddings, candidate_embedding)
                    
                    # Umbral de similitud más estricto para killer skills
                    if similarity > 0.85:  # Umbral alto para asegurar matches precisos
                        has_skill = True
                        break
                
                if not has_skill:
                    return False
                    
            return True
        except Exception as e:
            logging.error(f"Error checking killer skills: {str(e)}")
            raise e

    async def calculate_skill_match_score(
        self, 
        job_skills: List[str], 
        candidate_skills: List[str]
    ) -> float:
        """Calculate semantic similarity between job and candidate skills"""
        try:
            job_embeddings = [await self.analyzer.get_embedding(skill) for skill in job_skills]
            candidate_embeddings = [await self.analyzer.get_embedding(skill) for skill in candidate_skills]
            
            similarities = np.zeros((len(job_skills), len(candidate_skills)))
            for i, job_emb in enumerate(job_embeddings):
                for j, cand_emb in enumerate(candidate_embeddings):
                    similarities[i, j] = np.dot(job_emb, cand_emb)
            
            return float(np.mean(np.max(similarities, axis=1)))
        except Exception as e:
            logging.error(f"Error calculating skill match score: {str(e)}")
            raise e

    async def calculate_match_score(
        self, 
        job: JobProfile, 
        candidate: CandidateProfile
    ) -> Optional[Dict[str, float]]:
        """Calculate overall match score between job and candidate"""
        # Primero verificar killer skills
        has_required = await self.has_killer_skills(job.killer_skills, candidate.skills)
        if not has_required:
            return None
            
        # Si pasa las killer skills, calcular el resto del matching
        required_skills_score = await self.calculate_skill_match_score(
            job.required_skills, 
            candidate.skills
        )
        
        preferred_skills_score = await self.calculate_skill_match_score(
            job.preferred_skills, 
            candidate.skills
        )
        
        experience_score = min(1.0, candidate.experience_years / job.experience_years) if job.experience_years > 0 else 1.0
        
        education_levels = {
            "high school": 1,
            "bachelor": 2,
            "master": 3,
            "phd": 4
        }
        education_score = min(
            1.0, 
            education_levels.get(candidate.education_level.lower(), 0) /
            education_levels.get(job.education_level.lower(), 1)
        )
        
        # Nuevos pesos sin killer skills
        weights = {
            "required_skills": 0.5,
            "preferred_skills": 0.2,
            "experience": 0.2,
            "education": 0.1
        }
        
        final_score = (
            weights["required_skills"] * required_skills_score +
            weights["preferred_skills"] * preferred_skills_score +
            weights["experience"] * experience_score +
            weights["education"] * education_score
        )
        
        return {
            "final_score": final_score,
            "component_scores": {
                "required_skills": required_skills_score,
                "preferred_skills": preferred_skills_score,
                "experience": experience_score,
                "education": education_score
            }
        }

class RankingSystem:
    def __init__(self, matching_engine: MatchingEngine):
        self.matching_engine = matching_engine
    
    async def rank_candidates(
        self, 
        job: JobProfile, 
        candidates: List[CandidateProfile]
    ) -> List[Tuple[CandidateProfile, Dict[str, float]]]:
        """Rank candidates based on their match scores"""
        try:
            rankings = []
            for candidate in candidates:
                score = await self.matching_engine.calculate_match_score(job, candidate)
                if score is not None:  # Solo incluir candidatos que pasen las killer skills
                    rankings.append((candidate, score))
            
            # Sort by final score in descending order
            rankings.sort(key=lambda x: x[1]["final_score"], reverse=True)
            return rankings
        except Exception as e:
            logging.error(f"Error ranking candidates: {str(e)}")
            raise e