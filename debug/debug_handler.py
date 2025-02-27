"""
Module to handle the generation of debug files in JSON format.
"""
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path
import sys
import pandas as pd

# Add project root to path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hr_analysis_system import JobProfile, CandidateProfile, MatchScore


class DebugHandler:
    """Class responsible for creating and saving debug information in JSON format."""
    
    def __init__(self):
        """Initialize the DebugHandler."""
        self.debug_dir = self._get_debug_directory()
        os.makedirs(self.debug_dir, exist_ok=True)
        logging.info(f"Debug directory initialized at: {self.debug_dir}")
    
    @staticmethod
    def _get_debug_directory() -> str:
        """Get the path to the debug directory."""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")
    
    def create_debug_data(self, job: JobProfile, rankings: List[Tuple[CandidateProfile, MatchScore]], 
                          original_job_content: str = None, 
                          recruiter_preferences: Any = None, 
                          killer_criteria: Dict = None,
                          job_section_weights: Dict = None) -> Dict[str, Any]:
        """
        Create structured debug data from job profile and rankings according to specified format:
        - Vacant name
        - Content of original data before generating the job dictionaries
        - Three job standardization dictionaries
        - Recruiter skills dictionary
        - Two killer criteria dictionaries (killer skills and killer experience)
        - For each candidate:
          - Original candidate data before generating resume dictionaries
          - Three resume standardization dictionaries
          - Six comparison cosine distances
          - Weights applied
          - Scores with weights applied
          - Total score
        
        Args:
            job: The JobProfile object
            rankings: List of candidate and score tuples
            original_job_content: Original job description content
            recruiter_preferences: The recruiter_preferences from standardize_preferences
            killer_criteria: Killer criteria from standardize_killer_criteria
            job_section_weights: The weights from JobSection
            
        Returns:
            Dictionary with structured debug data
        """
        debug_data = {
            "vacante": {
                "nombre_vacante": job.nombre_vacante,
                "original_data": original_job_content,  # Directly use original_job_content
                "habilidades": job.habilidades,
                "experiencia": job.experiencia,
                "formacion": job.formacion,
                "habilidades_preferidas": recruiter_preferences.habilidades_preferidas if recruiter_preferences else None,
                "killer_criteria": killer_criteria or {},
                "weights": job_section_weights or {}
            },
            "candidates": []
        }
        
        for candidate, score in rankings:
            candidate_debug = {
                "nombre_candidato": candidate.nombre_candidato,
                "original_data": candidate.raw_data if hasattr(candidate, 'raw_data') else None,
                "dictionaries": {
                    "habilidades": candidate.habilidades,
                    "experiencia": candidate.experiencia,
                    "formacion": candidate.formacion
                },
                "debug_info": []
            }
                
            # Preserve the full debug_info for complete information
            candidate_debug["debug_info"] = score.debug_info
            
            debug_data["candidates"].append(candidate_debug)
        
        return debug_data
    
    def save_debug_json(self, job: JobProfile, rankings: List[Tuple[CandidateProfile, MatchScore]], 
                        vacancy_index: int = 0, 
                        original_job_content: str = None,
                        recruiter_preferences: Any = None,
                        killer_criteria: Dict = None,
                        job_section_weights: Dict = None) -> str:
        """
        Save debug data as JSON file.
        
        Args:
            job: The JobProfile object
            rankings: List of candidate and score tuples
            vacancy_index: Index of the vacancy for file naming
            original_job_content: Original job description content
            recruiter_preferences: The recruiter preferences object
            killer_criteria: The standardized killer criteria
            job_section_weights: The weights from job section
            
        Returns:
            Path to the saved JSON file
        """
        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        debug_data = self.create_debug_data(
            job, rankings, 
            original_job_content=original_job_content,
            recruiter_preferences=recruiter_preferences,
            killer_criteria=killer_criteria,
            job_section_weights=job_section_weights
        )
        
        # Create filename with timestamp and vacancy index
        #filename = os.path.join(self.debug_dir, f"debug_vacancy_{vacancy_index+1}_{timestamp}.json")
        filename = os.path.join(self.debug_dir, f"{timestamp}_{job.nombre_vacante[:19]}.json")

        
        # Write to JSON file with proper formatting and encoding
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(debug_data, json_file, ensure_ascii=False, indent=2, default=str)
        
        logging.info(f"Debug JSON saved at {filename}")
        return filename
    
    @staticmethod
    def create_debug_dataframe(job: JobProfile, rankings: List[Tuple[CandidateProfile, MatchScore]]) -> pd.DataFrame:
        """
        Generate a pandas DataFrame with debug data (for compatibility with existing code).
        This method preserves the same format as the original create_debug_dataframe.
        
        Args:
            job: The JobProfile object
            rankings: List of candidate and score tuples
            
        Returns:
            DataFrame with debug information
        """
        rows = []
        for candidate, score in rankings:
            base = {
                "Candidate": candidate.nombre_candidato,
                "Job Name": job.nombre_vacante
            }
            # For each component in debug_info, create a row
            for comp, data in score.debug_info.items():
                row = base.copy()
                row["Comparison Type"] = comp
                if isinstance(data, str):
                    row["Debug Info"] = data
                else:
                    row["Debug Info"] = json.dumps(data, default=str)  # Convert to JSON string
                rows.append(row)
        
        return pd.DataFrame(rows)