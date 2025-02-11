from openai import AsyncOpenAI  # Add this import at the top
import openai
from typing import Dict, List, Tuple
import numpy as np
from dataclasses import dataclass
import json

@dataclass
class JobProfile:
    """Standardized job requirement structure"""
    title: str
    required_skills: List[str]
    preferred_skills: List[str]
    experience_years: int
    education_level: str
    responsibilities: List[str]
    industry_knowledge: List[str]
    preferences: Dict = None  # Added to store weights and other preferences
    
@dataclass
class CandidateProfile:
    """Standardized resume structure"""
    name: str
    skills: List[str]
    experience_years: int
    education_level: str
    past_roles: List[str]
    industry_experience: List[str]
    raw_data: Dict = None  # Store the original JSON data for debugging

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
        Analyze this job description and hiring preferences. The hiring preferences take precedence 
        over the job description requirements. If there is any conflict or ambiguity, the preferences 
        should be considered the primary source of truth.

        Please extract and merge the requirements, giving priority to the preferences, and format 
        the output as JSON with the following structure:
        {{
            "title": "job title",
            "required_skills": ["skill1", "skill2"],
            "preferred_skills": ["skill1", "skill2"],
            "experience_years": number,
            "education_level": "level",
            "responsibilities": ["resp1", "resp2"],
            "industry_knowledge": ["domain1", "domain2"]
        }}

        Important: Any skills listed in the hiring preferences must be included in the required_skills 
        section, even if they were not mentioned in the original job description.

        Job Description:
        {description}

        Hiring Preferences:
        {json.dumps(preferences, indent=2)}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        profile_data = json.loads(response.choices[0].message.content)
        # Add preferences to the profile data
        profile_data['preferences'] = preferences
        return JobProfile(**profile_data)

    async def standardize_resume(self, resume_text: str) -> CandidateProfile:
        """Convert raw resume text into standardized format"""
        prompt = f"""
        Analyze this resume and extract key components.
        Format the output as JSON with the following structure:
        {{
            "name": "candidate name",
            "skills": ["skill1", "skill2"],
            "experience_years": number,
            "education_level": "level",
            "past_roles": ["role1", "role2"],
            "industry_experience": ["industry1", "industry2"]
        }}

        Resume:
        {resume_text}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        profile_data = json.loads(response.choices[0].message.content)
        # Store raw data in the profile
        raw_data = profile_data.copy()
        profile_data['raw_data'] = raw_data
        return CandidateProfile(**profile_data)

class MatchingEngine:
    def __init__(self, analyzer: SemanticAnalyzer):
        self.analyzer = analyzer
        
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
        candidate: CandidateProfile
    ) -> Dict[str, float]:
        """Calculate overall match score between job and candidate"""
        # Calculate different components of the match
        required_skills_score = await self.calculate_skill_match_score(
            job.required_skills, 
            candidate.skills
        )
        
        preferred_skills_score = await self.calculate_skill_match_score(
            job.preferred_skills, 
            candidate.skills
        )
        
        # Experience score (simplified)
        experience_score = min(1.0, candidate.experience_years / job.experience_years)
        
        # Education match (simplified)
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
        
        # Get weights from preferences or use defaults
        weights = getattr(job, 'preferences', {}).get('weights', {
            "required_skills": 0.4,
            "preferred_skills": 0.2,
            "experience": 0.25,
            "education": 0.15
        })
        
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
        # Calculate scores for all candidates
        rankings = []
        for candidate in candidates:
            score = await self.matching_engine.calculate_match_score(job, candidate)
            rankings.append((candidate, score))
        
        # Sort by final score in descending order
        rankings.sort(key=lambda x: x[1]["final_score"], reverse=True)
        return rankings