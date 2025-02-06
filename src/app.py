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
                    'Educación (Descripcion)': candidate.education_level
                }
                data.append(row)
            df = pd.DataFrame(data)
            percentage_cols = ['Puntuación Total', 'Habilidades Requeridas', 'Habilidades Preferentes', 'Experiencia', 'Educación']
            styled_df = df.style.background_gradient(
                subset=['Puntuación Total'],
                cmap='RdYlGn'
            )
            for col in percentage_cols:
                styled_df = styled_df.format({col: '{:.2%}'})
            logging.info("Ranking DataFrame created successfully.")
            return styled_df
        except Exception as e:
            logging.error(f"Error creating ranking DataFrame: {str(e)}")
            raise e

# Modified main() function in Spanish
async def main():
    st.title("Sistema de Análisis de CVs")
    st.write("""
    Este sistema analiza descripciones de trabajo y CVs para encontrar las mejores coincidencias basadas en habilidades, 
    experiencia y educación. Por favor, suba los archivos requeridos y proporcione las preferencias de contratación.
    """)
    logging.info("Application started.")

    app = HRAnalysisApp()
    job_col, prefs_col = st.columns(2)

    with job_col:
        st.subheader("Descripción del Puesto")
        job_file = st.file_uploader(
            "Suba la descripción del puesto (TXT o PDF)", 
            type=['txt', 'pdf']
        )

    with prefs_col:
        st.subheader("Preferencias de Contratación")
        min_experience = st.number_input(
            "Años mínimos de experiencia", 
            min_value=0, 
            value=3
        )
        education_level = st.selectbox(
            "Nivel educativo requerido",
            ["High School", "Bachelor", "Master", "PhD"]
        )
        important_skills = st.text_area(
            "Habilidades importantes (una por línea, mínimo una)",
            height=100
        )

    st.subheader("CVs de Candidatos")
    resume_files = st.file_uploader(
        "Suba los CVs de los candidatos (TXT o PDF)", 
        type=['txt', 'pdf'],
        accept_multiple_files=True
    )

    if st.button("Analizar Candidatos") and job_file and resume_files:
        try:
            with st.spinner("Analizando candidatos..."):
                logging.info("Candidate analysis started.")
                hiring_preferences = {
                    "minimum_experience": min_experience,
                    "education_level": education_level,
                    "important_skills": [
                        skill.strip() 
                        for skill in important_skills.split('\n') 
                        if skill.strip()
                    ]
                }
                job_profile = await app.process_job_description(job_file, hiring_preferences)
                candidate_profiles = await app.process_resumes(resume_files)
                rankings = await app.ranking_system.rank_candidates(job_profile, candidate_profiles)
                logging.info("Candidate ranking completed.")

                st.subheader("Ranking de Candidatos")
                styled_df = app.create_ranking_dataframe(rankings)
                st.dataframe(styled_df, use_container_width=True)

                with st.expander("Ver Requisitos del Puesto"):
                    st.json({
                        "título": job_profile.title,
                        "habilidades_requeridas": job_profile.required_skills,
                        "habilidades_preferentes": job_profile.preferred_skills,
                        "años_de_experiencia": job_profile.experience_years,
                        "nivel_educativo": job_profile.education_level,
                        "responsabilidades": job_profile.responsibilities,
                        "conocimientos_industria": job_profile.industry_knowledge
                    })
        except Exception as e:
            logging.error(f"Error during candidate analysis: {str(e)}")
            st.error(f"Ocurrió un error: {str(e)}")
            raise e

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Fatal error in main: {str(e)}")