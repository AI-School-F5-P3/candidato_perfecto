import logging
import streamlit as st
import asyncio
from components.file_reader import FileReader
from components.job_processor import JobProcessor
from components.resume_processor import ResumeProcessor
from components.ranking_creator import RankingCreator
from frontend.ui import load_custom_css, setup_page_config, create_weight_sliders, create_main_sections
from hr_analysis_system import SemanticAnalyzer
from utils.logging_config import configure_logging
from utils.secrets_manager import get_api_key

# Configure logging
configure_logging()

class HRAnalysisApp:
    def __init__(self):
        try:
            # Initialize OpenAI API key from secure storage
            self.api_key = get_api_key("openai", "api_key")
            logging.info("API key obtained successfully.")

            # Initialize analysis components
            self.analyzer = SemanticAnalyzer(self.api_key)
            self.file_reader = FileReader()
            self.job_processor = JobProcessor(self.analyzer)
            self.resume_processor = ResumeProcessor(self.analyzer)
            self.ranking_creator = RankingCreator()
            logging.info("Analysis components initialized.")
        except Exception as e:
            logging.error(f"Error during HRAnalysisApp initialization: {str(e)}")
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
                
                job_profile = await app.job_processor.process_job_description(job_file, hiring_preferences)
                candidate_profiles = await app.resume_processor.process_resumes(resume_files)
                # Pass killer_criteria to rank_candidates
                rankings = await app.ranking_creator.rank_candidates(
                    job_profile, 
                    candidate_profiles,
                    killer_criteria if any(killer_criteria.values()) else None
                )
                logging.info("Candidate ranking completed.")

                styled_df = app.ranking_creator.create_ranking_dataframe(rankings)
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