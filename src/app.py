"""Módulo principal que coordina todos los componentes del sistema"""
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
    """Clase principal que orquesta el flujo completo del análisis"""
    def __init__(self, api_key: str):
        # Inicializa los componentes principales del sistema
        self.embedding_provider = OpenAIEmbeddingProvider(api_key)
        self.analyzer = SemanticAnalyzer(self.embedding_provider)
        self.matching_engine = MatchingEngine(self.embedding_provider)
        self.ranking_system = RankingSystem(self.matching_engine)
        self.file_handler = FileHandler()
        logging.info("Componentes de análisis inicializados.")

    async def process_job_description(
        self, 
        job_file, 
        hiring_preferences: dict
    ) -> JobProfile:
        """Procesa la descripción del puesto y las preferencias del reclutador"""
        try:
            # Extrae el texto del archivo y lo convierte a formato estructurado
            job_content = await self.file_handler.read_file_content(job_file)
            logging.info("Procesando descripción del trabajo.")
            return await self.analyzer.standardize_job_description(job_content, hiring_preferences)
        except Exception as e:
            logging.error(f"Error procesando descripción del trabajo: {str(e)}")
            raise

    async def process_resumes(
        self, 
        resume_files
    ) -> List[CandidateProfile]:
        """Procesa múltiples CVs y los convierte a perfiles estructurados"""
        candidate_profiles = []
        for resume_file in resume_files:
            try:
                resume_content = await self.file_handler.read_file_content(resume_file)
                logging.info(f"Procesando CV: {resume_file.name}")
                profile = await self.analyzer.standardize_resume(resume_content)
                candidate_profiles.append(profile)
            except Exception as e:
                logging.error(f"Error procesando CV {resume_file.name}: {str(e)}")
        return candidate_profiles

    @staticmethod
    def create_ranking_dataframe(
        rankings: List[tuple[CandidateProfile, MatchScore]]
    ) -> pd.DataFrame:
        """Convierte los resultados del ranking en un DataFrame formateado para visualización"""
        try:
            # Crea filas de datos para cada candidato con sus puntuaciones
            data = []
            for candidate, scores in rankings:
                row = create_score_row(
                    candidate_data=vars(candidate),
                    score_data=vars(scores)
                )
                data.append(row)
            
            # Ordena el DataFrame por puntuación y estado de descalificación
            df = pd.DataFrame(data)
            df = sort_ranking_dataframe(df)
            
            logging.info("DataFrame de ranking creado exitosamente.")
            return df
        except Exception as e:
            logging.error(f"Error creando DataFrame de ranking: {str(e)}")
            raise

async def main():
    """Punto de entrada principal que maneja el flujo de la aplicación"""
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
    logging.info("Aplicación iniciada.")

    try:
        # Configura la API key de OpenAI desde los secrets
        os.environ['STREAMLIT_SECRETS_PATH'] = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
        api_key = st.secrets["openai"]["api_key"]
        app = HRAnalysisApp(api_key)
    except Exception as e:
        logging.error(f"Error inicializando la aplicación: {str(e)}")
        st.error("Error inicializando la aplicación. Por favor revise su configuración.")
        return
    
    # Obtiene los inputs del usuario desde la interfaz
    ui_inputs = UIComponents.create_main_sections()
    
    # Procesa los datos cuando se presiona el botón y los inputs son válidos
    if st.button("Analizar Candidatos") and ui_inputs.job_file and ui_inputs.resume_files and ui_inputs.weights.total_weight == 1.0:
        try:
            with st.spinner("Analizando candidatos..."):
                logging.info("Análisis de candidatos iniciado.")
                
                # Prepara las preferencias y pesos para el análisis
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
                
                # Procesa la descripción del trabajo y los CVs
                job_profile = await app.process_job_description(ui_inputs.job_file, hiring_preferences)
                candidate_profiles = await app.process_resumes(ui_inputs.resume_files)
                
                if candidate_profiles:
                    # Realiza el ranking de candidatos
                    rankings = await app.ranking_system.rank_candidates(
                        job_profile, 
                        candidate_profiles,
                        ui_inputs.killer_criteria if any(ui_inputs.killer_criteria.values()) else None,
                        hiring_preferences["weights"]
                    )
                    
                    logging.info("Ranking de candidatos completado.")
                    styled_df = app.create_ranking_dataframe(rankings)
                    UIComponents.display_ranking(styled_df, job_profile)
                else:
                    st.warning("No se pudieron procesar los CVs. Por favor, verifique los archivos.")
                
        except Exception as e:
            logging.error(f"Error durante el análisis de candidatos: {str(e)}")
            st.error(f"Ocurrió un error durante el análisis: {str(e)}")
    elif ui_inputs.weights.total_weight != 1.0:
        st.error("Por favor, ajuste los pesos para que sumen exactamente 1.0 antes de continuar.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Error crítico en main: {str(e)}")
        st.error("Se produjo un error crítico en la aplicación.")