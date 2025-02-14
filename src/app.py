import logging
import streamlit as st
import asyncio
import pandas as pd
from typing import List
import os
from src.hr_analysis_system import (
    SemanticAnalyzer, 
    MatchingEngine,
    RankingSystem,
    JobProfile,
    CandidateProfile,
    OpenAIEmbeddingProvider,
    MatchScore
)
from src.frontend.ui import UIComponents
from src.utils.utilities import setup_logging, create_score_row, sort_ranking_dataframe
from src.utils.file_handler import FileHandler

class HRAnalysisApp:
    """Main application class implementing HR analysis functionality"""
    def __init__(self, api_key: str):
        self.embedding_provider = OpenAIEmbeddingProvider(api_key)
        self.analyzer = SemanticAnalyzer(self.embedding_provider)
        self.matching_engine = MatchingEngine(self.embedding_provider)
        self.ranking_system = RankingSystem(self.matching_engine)
        self.file_handler = FileHandler()
        logging.info("Analysis components initialized.")

    async def process_job_description(
        self, 
        job_file, 
        hiring_preferences: dict
    ) -> JobProfile:
        """Process the job description file and hiring preferences"""
        try:
            job_content = await self.file_handler.read_file_content(job_file)
            logging.info("Processing job description.")
            return await self.analyzer.standardize_job_description(job_content, hiring_preferences)
        except Exception as e:
            logging.error(f"Error processing job description: {str(e)}")
            raise

    async def process_resumes(
        self, 
        resume_files
    ) -> List[CandidateProfile]:
        """Process multiple resume files"""
        candidate_profiles = []
        for resume_file in resume_files:
            try:
                resume_content = await self.file_handler.read_file_content(resume_file)
                logging.info(f"Processing resume: {resume_file.name}")
                profile = await self.analyzer.standardize_resume(resume_content)
                candidate_profiles.append(profile)
            except Exception as e:
                logging.error(f"Error processing resume {resume_file.name}: {str(e)}")
        return candidate_profiles

    @staticmethod
    def create_ranking_dataframe(
        rankings: List[tuple[CandidateProfile, MatchScore]]
    ) -> pd.DataFrame:
        """Convert ranking results to a pandas DataFrame for visualization"""
        try:
            data = []
            for candidate, scores in rankings:
                row = create_score_row(
                    candidate_data=vars(candidate),
                    score_data=vars(scores)
                )
                data.append(row)
            
            df = pd.DataFrame(data)
            df = sort_ranking_dataframe(df)
            
            logging.info("Ranking DataFrame created successfully.")
            return df
        except Exception as e:
            logging.error(f"Error creating ranking DataFrame: {str(e)}")
            raise

async def main():
    """Main application entry point"""
    setup_logging()
    UIComponents.setup_page_config()
    UIComponents.load_custom_css()
    
    st.markdown('<h1 class="title">El candidato perfecto</h1>', unsafe_allow_html=True)
    st.write("""
    El sistema recopila información de una vacante junto con las preferencias del equipo reclutador 
    y las características obligatorias a cumplir por los candidatos. Con esta información, se analizan 
    los curriculum vitae de los candidatos y se obtiene un ranking de idoneidad basado en habilidades, 
    experiencia y formación. También se identifican los candidatos que no cumplen con los requisitos 
    obligatorios. Los pesos de ponderación pueden ser ajustados si así se requiere.
    """)
    logging.info("Application started.")

    try:
        # Override Streamlit's secrets path to look in src/.streamlit
        os.environ['STREAMLIT_SECRETS_PATH'] = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
        api_key = st.secrets["openai"]["api_key"]
        app = HRAnalysisApp(api_key)
    except Exception as e:
        logging.error(f"Error initializing application: {str(e)}")
        st.error("Error initializing the application. Please check your configuration.")
        return
    
    ui_inputs = UIComponents.create_main_sections()
    
    if st.button("Analizar Candidatos") and ui_inputs.job_file and ui_inputs.resume_files and ui_inputs.weights.total_weight == 1.0:
        try:
            with st.spinner("Analizando candidatos..."):
                logging.info("Candidate analysis started.")
                
                hiring_preferences = {
                    "habilidades_preferidas": [
                        skill.strip() 
                        for skill in (ui_inputs.important_skills or "").split('\n') 
                        if skill.strip()
                    ],
                    "weights": {
                        "habilidades": ui_inputs.weights.habilidades,
                        "experiencia": ui_inputs.weights.experiencia,
                        "formacion": ui_inputs.weights.formacion,
                        "preferencias_reclutador": ui_inputs.weights.preferencias_reclutador
                    }
                }
                
                job_profile = await app.process_job_description(ui_inputs.job_file, hiring_preferences)
                candidate_profiles = await app.process_resumes(ui_inputs.resume_files)
                
                if candidate_profiles:
                    rankings = await app.ranking_system.rank_candidates(
                        job_profile, 
                        candidate_profiles,
                        ui_inputs.killer_criteria if any(ui_inputs.killer_criteria.values()) else None,
                        hiring_preferences["weights"]
                    )
                    
                    logging.info("Candidate ranking completed.")
                    styled_df = app.create_ranking_dataframe(rankings)
                    UIComponents.display_ranking(styled_df, job_profile)
                else:
                    st.warning("No se pudieron procesar los CVs. Por favor, verifique los archivos.")
                
        except Exception as e:
            logging.error(f"Error during candidate analysis: {str(e)}")
            st.error(f"Ocurrió un error durante el análisis: {str(e)}")
    elif ui_inputs.weights.total_weight != 1.0:
        st.error("Por favor, ajuste los pesos para que sumen exactamente 1.0 antes de continuar.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Fatal error in main: {str(e)}")
        st.error("Se produjo un error crítico en la aplicación.")