from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import json
import httpx

@dataclass
class JobProfile:
    """Standardized job requirement structure"""
    title: str
    killer_skills: List[str]
    no_killer_skills: List[str]
    education_level: str
    specific_requirements: List[str]
    responsibilities: List[str]
    industry_knowledge: List[str]
    
@dataclass
class CandidateProfile:
    """Standardized resume structure"""
    name: str
    skills: List[str]
    education_level: str
    past_roles: List[str]
    industry_experience: List[str]
    location: str
    languages: List[str]
    availability: str

class SemanticAnalyzer:
    def __init__(self, api_url: str = "http://localhost:11434"):
        """Initialize the semantic analyzer with Ollama API URL"""
        self.api_url = api_url
        self.model = "llama2"
        self.client = httpx.AsyncClient()

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text using Ollama's embedding endpoint"""
        response = await self.client.post(
            f"{self.api_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text
            }
        )
        return response.json()["embedding"]

    async def _generate_json_response(self, prompt: str) -> dict:
        """Helper method to generate JSON responses from LLM"""
        response = await self.client.post(
            f"{self.api_url}/api/generate",
            json={
                "model": self.model,
                "prompt": f"{prompt}\nResponde SOLO en formato JSON válido.",
                "stream": False
            },
            timeout=120
        )
        try:
            response_text = response.json()["response"]
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
            raise ValueError("No valid JSON found in response")
        except Exception as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}")

    async def check_killer_skills(self, resume_text: str, killer_skills: List[str]) -> Dict:
        """Check if resume contains all required killer skills"""
        prompt = f"""
        Eres un asistente experto en análisis de recursos humanos. Tu tarea es analizar este CV y verificar si contiene todas las killer skills requeridas: {killer_skills}. 
        Si no tiene TODAS las killer_skills, el CV no es válido y no puede pasar al resto del proceso de selección.

        Ten en cuenta las variaciones comunes para cada skill. Por ejemplo:
        - "Python": "python programming", "python developer", "python development"
        - "SQL": "MySQL", "PostgreSQL", "SQL Server", "database management"
        - "Docker": "containerization", "docker containers", "docker-compose"

        Considera también las versiones y niveles:
        - "Python 3.x" es compatible con "Python"
        - "Advanced SQL" cumple con "SQL"
        - "Docker expert" cumple con "Docker"

        CV para analizar:
        {resume_text}

        Responde en el siguiente formato JSON:
        {{
            "has_all_killer_skills": true/false,
            "found_skills": ["skill1", "skill2", ...],
            "missing_skills": ["skill3", "skill4", ...],
        }}
        """
        response = await self._generate_json_response(prompt)
        return response["has_all_killer_skills"]

    async def standardize_job_description(self, description: str, preferences: Dict) -> JobProfile:
        """Convert raw job description and preferences into standardized format"""
        prompt = f"""
        Eres un asistente experto en análisis de recursos humanos. Tu tarea es analizar esta descripción de puesto y generar la información estructurada.

        Ten en cuenta las variaciones en educación, te pongo unos ejemplos:
        - "Grado universitario" = "Bachelor's degree"
        - "Licenciatura" = "Bachelor's degree"
        - "Máster" = "Master's degree"
        - "Postgrado" = "Master's degree"
        - "Doctorado" = "PhD"
        
        Asegúrate de normalizar la educación a uno de estos valores exactos:
        - "High School"
        - "Bachelor"
        - "Master"
        - "PhD"

        Descripción del trabajo:
        {description}

        Preferencias de contratación:
        {json.dumps(preferences, indent=2)}

        Responde EXACTAMENTE en este formato JSON:
        {{
            "title": "string",
            "killer_skills": ["skill1", "skill2"],
            "no_killer_skills": ["skill1", "skill2"],
            "education_level": "High School/Bachelor/Master/PhD",
            "specific_requirements": ["requirement1", "requirement2"],
            "responsibilities": ["resp1", "resp2"],
            "industry_knowledge": ["knowledge1", "knowledge2"]
        }}
        """
        
        profile_data = await self._generate_json_response(prompt)
        return JobProfile(**profile_data)

    async def standardize_resume(self, resume_text: str) -> CandidateProfile:
        """Convert raw resume text into standardized format"""
        prompt = f"""
        Eres un asistente experto en análisis de recursos humanos. Tu tarea es analizar este CV y extraer la información en un formato estandarizado.

        Considera las variaciones en la información, por ejemplo:

        Educación:
        - "Ingeniero en..." = "Bachelor"
        - "Graduado en..." = "Bachelor"
        - "MSc/MS/M.S." = "Master"
        - "MBA" = "Master"
        - "Doctorado/PhD" = "PhD"
        
        Asegúrate de normalizar la educación a uno de estos valores exactos:
        - "High School"
        - "Bachelor"
        - "Master"
        - "PhD"

        Experiencia:
        - "X años de experiencia" = incluir en past_roles
        - "Desde 20XX" = calcular años y añadir al rol correspondiente

        CV para analizar:
        {resume_text}

        Responde EXACTAMENTE en este formato JSON:
        {{
            "name": "string",
            "skills": ["skill1", "skill2"],
            "education_level": "High School/Bachelor/Master/PhD",
            "past_roles": ["role1", "role2"],
            "industry_experience": ["industry1", "industry2"],
            "location": "string",
            "languages": ["language1", "language2"],
            "availability": "string"
        }}
        """
        response = await self._generate_json_response(prompt)
        return CandidateProfile(**response)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class MatchingEngine:
    def __init__(self, analyzer: SemanticAnalyzer):
        self.analyzer = analyzer
        
    async def calculate_skill_match_score(
        self, 
        job_skills: List[str], 
        candidate_skills: List[str]
    ) -> float:
        """Calculate semantic similarity between job and candidate skills"""
        if not job_skills or not candidate_skills:
            return 0.0
            
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

    async def calculate_specific_requirements_score(
        self,
        job_requirements: List[str],
        candidate: CandidateProfile
    ) -> float:
        """Calculate match score for specific requirements"""
        if not job_requirements:
            return 1.0
            
        scores = []
        for req in job_requirements:
            req_lower = req.lower()
            if "ubicación" in req_lower or "localización" in req_lower:
                location_match = await self.analyzer.get_embedding(req)
                candidate_location = await self.analyzer.get_embedding(candidate.location)
                scores.append(float(np.dot(location_match, candidate_location)))
            elif "idioma" in req_lower:
                # Check language requirements
                required_langs = [lang.strip() for lang in req.split(":")[1].split(",")]
                lang_match = any(lang.lower() in [cl.lower() for cl in candidate.languages] 
                            for lang in required_langs)
                scores.append(1.0 if lang_match else 0.0)
            elif "disponibilidad" in req_lower:
                avail_match = await self.analyzer.get_embedding(req)
                candidate_avail = await self.analyzer.get_embedding(candidate.availability)
                scores.append(float(np.dot(avail_match, candidate_avail)))
                
        return np.mean(scores) if scores else 1.0

    async def calculate_match_score(
        self, 
        job: JobProfile, 
        candidate: CandidateProfile
    ) -> Dict[str, float]:
        """Calculate overall match score between job and candidate"""
        # Calculate different components of the match
        killer_skills_score = await self.calculate_skill_match_score(
            job.killer_skills, 
            candidate.skills
        )
        
        no_killer_skills_score = await self.calculate_skill_match_score(
            job.no_killer_skills, 
            candidate.skills
        )
        
        # Education match
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
        
        # Specific requirements match
        specific_requirements_score = await self.calculate_specific_requirements_score(
            job.specific_requirements,
            candidate
        )
        
        # Calculate weighted final score
        weights = {
            "no_killer_skills": 0.2,
            "education": 0.2,
            "specific_requirements": 0.2
        }
        
        final_score = (
            weights["no_killer_skills"] * no_killer_skills_score +
            weights["education"] * education_score +
            weights["specific_requirements"] * specific_requirements_score
        )
        
        return {
            "final_score": final_score,
            "component_scores": {
                "no_killer_skills": no_killer_skills_score,
                "education": education_score,
                "specific_requirements": specific_requirements_score
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
        # Calculate scores for all candidates
        rankings = []
        for candidate in candidates:
            score = await self.matching_engine.calculate_match_score(job, candidate)
            rankings.append((candidate, score))
        
        # Sort by final score in descending order
        rankings.sort(key=lambda x: x[1]["final_score"], reverse=True)
        return rankings