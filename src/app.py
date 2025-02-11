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
                row = {
                    'Nombre Candidato': candidate.name,
                    'Puntuación Total': scores['final_score'],
                    'Habilidades Requeridas': scores['component_scores']['required_skills'],
                    'Habilidades Preferentes': scores['component_scores']['preferred_skills'],
                    'Experiencia': scores['component_scores']['experience'],
                    'Educación': scores['component_scores']['education'],
                    'Habilidades': ', '.join(candidate.skills[:5]) + ('...' if len(candidate.skills) > 5 else ''),
                    'Experiencia (Años)': candidate.experience_years,
                    'Educación (Descripcion)': candidate.education_level,
                    'raw_data': candidate.raw_data  # Add raw data to DataFrame
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            
            # Create a copy without raw_data for styling
            display_cols = [col for col in df.columns if col != 'raw_data']
            styled_df = df[display_cols].style.background_gradient(
                subset=['Puntuación Total'],
                cmap='RdYlGn'
            )
            
            # Format percentage columns
            percentage_cols = ['Puntuación Total', 'Habilidades Requeridas', 'Habilidades Preferentes', 'Experiencia', 'Educación']
            for col in percentage_cols:
                styled_df = styled_df.format({col: '{:.2%}'})
            
            # Attach the original DataFrame with raw_data to the styled DataFrame
            styled_df.data = df
            
            logging.info("Ranking DataFrame created successfully.")
            return styled_df
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
    experiencia, educación y preferencias del reclutador.
    """)
    logging.info("Application started.")

    app = HRAnalysisApp()
    
    # Create UI components using the new frontend functions
    weights = create_weight_sliders()
    
    # Create all main sections in vertical layout
    job_file, important_skills, resume_files = create_main_sections()

    if st.button("Analizar Candidatos") and job_file and resume_files and weights["total_weight"] == 1.0:
        try:
            with st.spinner("Analizando candidatos..."):
                logging.info("Candidate analysis started.")
                # Create a more detailed hiring preferences structure
                skills_list = [skill.strip() for skill in important_skills.split('\n') if skill.strip()]
                hiring_preferences = {
                    "important_skills": skills_list,
                    "preferences_priority": """
                        Las habilidades especificadas en estas preferencias de contratación tienen 
                        prioridad sobre las mencionadas en la descripción del puesto. En caso de 
                        ambigüedad o conflicto entre los requisitos del puesto y estas preferencias, 
                        las preferencias prevalecerán. Estas habilidades se consideran críticas 
                        para el éxito en el puesto y deben tener un peso significativo en la 
                        evaluación de los candidatos.
                    """,
                    "skills_importance": "critical",
                    "override_job_description": True,
                    "weights": {
                        "required_skills": weights["skills_weight"],
                        "preferred_skills": weights["preferences_weight"],
                        "experience": weights["experience_weight"],
                        "education": weights["education_weight"]
                    }
                }
                job_profile = await app.process_job_description(job_file, hiring_preferences)
                candidate_profiles = await app.process_resumes(resume_files)
                rankings = await app.ranking_system.rank_candidates(job_profile, candidate_profiles)
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