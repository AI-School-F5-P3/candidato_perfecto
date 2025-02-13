import logging
import streamlit as st
import asyncio
import pandas as pd
import json
from pathlib import Path
from typing import List
import aiofiles
from hr_analysis_system import (
    SemanticAnalyzer,
    MatchingEngine,
    RankingSystem,
    JobProfile,
    CandidateProfile
)
from frontend.ui import (
    load_custom_css,
    setup_page_config,
    create_weight_sliders,
    create_main_sections,
    display_ranking
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

class HRAnalysisApp:
    def __init__(self):
        try:
            # Initialize OpenAI API key from Streamlit secrets
            self.api_key = st.secrets["openai"]["api_key"]
            logging.info("API key obtained successfully.")

            # Initialize analysis components
            self.analyzer = SemanticAnalyzer(self.api_key)
            self.matching_engine = MatchingEngine(self.analyzer)
            self.ranking_system = RankingSystem(self.matching_engine)
            logging.info("Analysis components initialized.")
        except Exception as e:
            logging.error(f"Error during HRAnalysisApp initialization: {str(e)}")
            raise e

    async def read_file_content(self, uploaded_file) -> str:
        """Read content from an uploaded file (TXT or PDF)"""
        try:
            file_extension = uploaded_file.name.lower().split('.')[-1]
            logging.info(f"Reading file: {uploaded_file.name} with extension {file_extension}")

            if file_extension == 'pdf':
                import PyPDF2
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                content = ""
                for page in pdf_reader.pages:
                    text = page.extract_text() or ""
                    content += text + "\n"
                logging.info(f"Extracted text from PDF: {uploaded_file.name}")
            else:
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                logging.info(f"Read text file: {uploaded_file.name}")

            return content
        except Exception as e:
            logging.error(f"Error reading file {uploaded_file.name}: {str(e)}")
            raise e

    async def process_job_description(self, job_file, hiring_preferences: dict) -> JobProfile:
        """Process the job description file and hiring preferences"""
        try:
            job_content = await self.read_file_content(job_file)
            logging.info("Processing job description.")
            job_profile = await self.analyzer.standardize_job_description(job_content, hiring_preferences)
            logging.info("Job description processed successfully.")
            return job_profile
        except Exception as e:
            logging.error(f"Error processing job description: {str(e)}")
            raise e

    async def process_resumes(self, resume_files) -> List[CandidateProfile]:
        """Process multiple resume files"""
        candidate_profiles = []
        for resume_file in resume_files:
            try:
                resume_content = await self.read_file_content(resume_file)
                logging.info(f"Processing resume: {resume_file.name}")
                profile = await self.analyzer.standardize_resume(resume_content)
                candidate_profiles.append(profile)
                logging.info(f"Resume processed: {resume_file.name}")
            except Exception as e:
                logging.error(f"Error processing resume {resume_file.name}: {str(e)}")
        return candidate_profiles

    def create_ranking_dataframe(self, rankings) -> pd.DataFrame:
        """Convertir el ranking a un DataFrame de pandas para su visualización"""
        try:
            data = []
            for candidate, scores in rankings:
                # Pre-format all score values at creation time
                row = {
                    'Nombre Candidato': candidate.nombre_candidato,
                    'Estado': 'Descalificado' if scores.get('disqualified', False) else 'Calificado',
                    'Score Final': f"{scores['final_score']:.1%}",
                    'Score Habilidades': f"{scores['component_scores']['habilidades']:.1%}",
                    'Score Experiencia': f"{scores['component_scores']['experiencia']:.1%}",
                    'Score Formación': f"{scores['component_scores']['formacion']:.1%}",
                    'Score Preferencias': f"{scores['component_scores']['preferencias_reclutador']:.1%}",
                    'Habilidades': ', '.join(candidate.habilidades[:5]) + ('...' if len(candidate.habilidades) > 5 else ''),
                    'Experiencia': ', '.join(candidate.experiencia[:3]) + ('...' if len(candidate.experiencia) > 3 else ''),
                    'Formación': ', '.join(candidate.formacion[:2]) + ('...' if len(candidate.formacion) > 2 else ''),
                    'Razones Descalificación': ', '.join(scores.get('disqualification_reasons', [])) or 'N/A',
                    'raw_data': candidate.raw_data
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            
            # Sort by Estado (qualified first) and then by Score Final
            df['Sort Score'] = df['Score Final'].str.rstrip('%').astype('float')
            df = df.sort_values(
                by=['Estado', 'Sort Score'], 
                ascending=[True, False],  # True for Estado to put 'Calificado' first
                key=lambda x: x if x.name != 'Estado' else pd.Categorical(x, ['Calificado', 'Descalificado'])
            )
            df = df.drop('Sort Score', axis=1)
            
            logging.info("Ranking DataFrame created successfully.")
            return df
        except Exception as e:
            logging.error(f"Error creating ranking DataFrame: {str(e)}")
            raise e

async def main():
    # Initialize page configuration and styling
    setup_page_config()
    load_custom_css()
    
    # Title with custom CSS class
    st.markdown('<h1 class="title">Sistema de Análisis de CVs</h1>', unsafe_allow_html=True)
    st.write("""
    Este sistema analiza descripciones de trabajo y CVs para encontrar las mejores coincidencias basadas en habilidades, 
    experiencia y conocimiento, y formación.
    """)
    logging.info("Application started.")

    app = HRAnalysisApp()
    
    # Create UI components using the new frontend functions
    weights = create_weight_sliders()
    
    # Create all main sections in vertical layout and get killer criteria
    job_file, important_skills, resume_files, killer_criteria = create_main_sections()

    if st.button("Analizar Candidatos") and job_file and resume_files and weights["total_weight"] == 1.0:
        try:
            with st.spinner("Analizando candidatos..."):
                logging.info("Candidate analysis started.")
                # Create a simplified hiring preferences structure with safe handling of empty inputs
                skills_list = [skill.strip() for skill in (important_skills or "").split('\n') if skill.strip()]
                hiring_preferences = {
                    "habilidades_preferidas": skills_list,
                    "weights": {
                        "habilidades": weights["habilidades"],
                        "experiencia": weights["experiencia"],
                        "formacion": weights["formacion"],
                        "preferencias_reclutador": weights["preferencias_reclutador"]
                    }
                }
                
                # Store killer criteria and log if any were provided
                if any(killer_criteria.values()):
                    logging.info(f"Killer criteria received: {json.dumps(killer_criteria, indent=2)}")
                else:
                    logging.info("No killer criteria provided")
                
                job_profile = await app.process_job_description(job_file, hiring_preferences)
                candidate_profiles = await app.process_resumes(resume_files)
                # Pass killer_criteria to rank_candidates
                rankings = await app.ranking_system.rank_candidates(
                    job_profile, 
                    candidate_profiles,
                    killer_criteria if any(killer_criteria.values()) else None
                )
                logging.info("Candidate ranking completed.")

                styled_df = app.create_ranking_dataframe(rankings)
                display_ranking(styled_df, job_profile)
                
        except Exception as e:
            logging.error(f"Error during candidate analysis: {str(e)}")
            st.error(f"Ocurrió un error durante el análisis: {str(e)}")
    elif weights["total_weight"] != 1.0:
        st.error("Por favor, ajuste los pesos para que sumen exactamente 1.0 antes de continuar.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Fatal error in main: {str(e)}")