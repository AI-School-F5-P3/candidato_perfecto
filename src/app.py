"""Módulo principal que coordina todos los componentes del sistema"""
import logging
from openai import AsyncOpenAI
import streamlit as st
import asyncio
import pandas as pd
from typing import List, Optional
import os
from datetime import datetime
from pathlib import Path
import sys

# Añade la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hr_analysis_system import (
    SemanticAnalyzer,
    MatchingEngine,
    RankingSystem,
    JobProfile,
    CandidateProfile,
    OpenAIEmbeddingProvider,
    MatchScore,
    PreferenciaReclutadorProfile
)

import matplotlib.pyplot as plt
import seaborn as sns
from frontend.ui import UIComponents
from utils.utilities import setup_logging, create_score_row, sort_ranking_dataframe, export_rankings_to_excel
from utils.file_handler import FileHandler
from utils.google_drive import GoogleDriveIntegration
from src.config import Config

# Configuración inicial de Streamlit y logging
st.set_page_config(page_title="El candidato perfecto", layout="wide")
setup_logging()
UIComponents.load_custom_css()

def initialize_session_state():
    """Inicializa el estado de la sesión si no existe"""
    if 'app' not in st.session_state:
        st.session_state.app = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "Ranking Principal"

class OpenAITextGenerationProvider:
    """Proveedor de generación de texto usando OpenAI API"""

    def __init__(self, api_key: str):
        """Inicializa el proveedor de generación de texto"""
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_text(self, prompt: str) -> str:
        """
        Genera texto usando OpenAI API
        
        Args:
            prompt (str): El prompt para generar el texto
            
        Returns:
            str: El texto generado
        """
        try:
            response = await self.client.chat.completions.create(
                model=Config.MODEL.chat_model,
                messages=[
                    {"role": "system", "content": "Eres un experto en recursos humanos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error en generate_text: {str(e)}")
            return f"Error al generar análisis: {str(e)}"
        

class HRAnalysisApp:
    """Clase principal que orquesta el flujo completo del análisis"""
    def __init__(self, api_key: str):
        # Inicializa los componentes principales del sistema
        self.embedding_provider = OpenAIEmbeddingProvider(api_key)
        self.analyzer = SemanticAnalyzer(self.embedding_provider)
        self.matching_engine = MatchingEngine(self.embedding_provider)
        self.ranking_system = RankingSystem(self.matching_engine)
        self.file_handler = FileHandler()
        
        # Configuración de Google Drive
        self.gdrive_credentials = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            ".streamlit", 
            "google_credentials",
            "service-account-key.json"
        )
        self.gdrive_folder_id = Config.GDRIVE.folder_id
        self.text_generation_provider = OpenAITextGenerationProvider(api_key)
        self.comparative_analysis = ComparativeAnalysis(self.text_generation_provider)
        logging.info("Componentes de análisis inicializados.")

    async def process_drive_cvs(self) -> List[CandidateProfile]:
        """Procesa CVs desde Google Drive"""
        drive_client = GoogleDriveIntegration(self.gdrive_credentials, self.gdrive_folder_id)
        cv_texts = await drive_client.process_drive_cvs()
        return await self.process_resumes(cv_texts)

    async def process_job_description(self, job_file, hiring_preferences: dict) -> JobProfile:
        """Procesa la descripción del puesto y las preferencias del reclutador"""
        try:
            job_content = await self.file_handler.read_file_content(job_file)
            logging.info("Procesando descripción del trabajo.")
            return await self.analyzer.standardize_job_description(job_content, hiring_preferences)
        except Exception as e:
            logging.error(f"Error procesando descripción del trabajo: {str(e)}")
            raise

    async def process_preferences(self, preferences_text: str) -> PreferenciaReclutadorProfile:
        """Procesa las preferencias del reclutador"""
        try:
            logging.info("Procesando preferencias del reclutador.")
            return await self.analyzer.standardize_preferences(preferences_text)
        except Exception as e:
            logging.error(f"Error procesando preferencias: {str(e)}")
            raise

    async def process_resumes(self, resume_files) -> List[CandidateProfile]:
        """Procesa múltiples CVs y los convierte a perfiles estructurados"""
        candidate_profiles = []
        
        # Si resume_files es una lista de strings (de Google Drive)
        if all(isinstance(x, str) for x in resume_files):
            for idx, content in enumerate(resume_files):
                try:
                    logging.info(f"Procesando CV #{idx+1} desde Google Drive")
                    profile = await self.analyzer.standardize_resume(content)
                    candidate_profiles.append(profile)
                except Exception as e:
                    logging.error(f"Error procesando CV #{idx+1}: {str(e)}")
        # Si son archivos subidos manualmente
        else:
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
    def create_ranking_dataframe(rankings: List[tuple[CandidateProfile, MatchScore]]) -> pd.DataFrame:
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

    def create_debug_dataframe(self, job: JobProfile, rankings: List[tuple[CandidateProfile, MatchScore]]) -> pd.DataFrame:
        """Genera un DataFrame debug utilizando debug_info almacenado en MatchScore sin llamadas adicionales."""
        rows = []
        for candidate, score in rankings:
            base = {
                "Candidate": candidate.nombre_candidato,
                "Job Name": job.nombre_vacante
            }
            # Para cada componente en debug_info, crear una fila
            for comp, data in score.debug_info.items():
                row = base.copy()
                row["Comparison Type"] = comp
                if isinstance(data, str):
                    row["Debug Info"] = data
                else:
                    row["Debug Info"] = str(data)  # Convert non-string data to string
                rows.append(row)
        
        return pd.DataFrame(rows)

    async def analyze_text_comparatively(self, df: pd.DataFrame, candidate_names: List[str]) -> List[dict]:
        """Wrapper para el análisis comparativo de candidatos"""
        return await self.comparative_analysis.analyze_text_comparatively(df, candidate_names)

class ComparativeAnalysis:
    def __init__(self, text_generation_provider):
        self.text_generation_provider = text_generation_provider

    async def analyze_text_comparatively(self, df: pd.DataFrame, candidate_names: List[str]) -> List[dict]:
        """Realiza un análisis de texto comparativo utilizando LLM y genera gráficos"""
        try:
            comparative_df = df[df['Nombre Candidato'].isin(candidate_names)].copy()
            analysis_results = []

            for _, row in comparative_df.iterrows():
                candidate_text = (
                    f"Nombre: {row['Nombre Candidato']}\n"
                    f"Experiencia: {row.get('Experiencia', 'No disponible')}\n"
                    f"Habilidades: {row.get('Habilidades', 'No disponible')}\n"
                    f"Formación: {row.get('Formación', 'No disponible')}"
                )

                prompt = (
                    "Analiza el siguiente perfil de candidato y genera un resumen conciso de sus fortalezas y áreas de mejora en español:\n"
                    f"{candidate_text}"
                )

                try:
                    response = await self.text_generation_provider.generate_text(prompt)    
                    
                    if response:
                        analysis = response.strip()
                        analysis_results.append({
                            'nombre': row['Nombre Candidato'],
                            'analisis': analysis
                        })
                    else:
                        raise ValueError("No se recibió respuesta del modelo")
                
                except Exception as e:
                    logging.error(f"Error al analizar el candidato {row['Nombre Candidato']}: {str(e)}")
                    analysis_results.append({
                        'nombre': row['Nombre Candidato'],
                        'analisis': f"Error al analizar el perfil: {str(e)}"
                    })
            
            # Guardar en una clave diferente
            st.session_state['comparative_analysis_results'] = analysis_results
            return analysis_results
            
        except Exception as e:
            logging.error(f"Error en el análisis comparativo: {str(e)}")
            st.error("Error al mostrar el informe comparativo. Verifique los datos y vuelva a intentar.")
            return []

def render_main_page():
    """Renderiza la página principal de la aplicación"""
    
    ui_inputs = UIComponents.create_main_sections()
            
    if st.button("Analizar Candidatos", key="analyze_button"):
        asyncio.run(analyze_candidates(ui_inputs, st.session_state.app))

def main():
    """Función principal que maneja el flujo de la aplicación"""
    initialize_session_state()
    
    if not st.session_state.app:
        try:
            api_key = st.secrets["openai"]["api_key"]
            st.session_state.app = HRAnalysisApp(api_key)
        except Exception as e:
            logging.error(f"Error inicializando la aplicación: {str(e)}")
            st.error("Error inicializando la aplicación. Por favor revise su configuración.")
            return

    # Crear pestañas
    tab1, tab2 = st.tabs(["Ranking Principal", "Análisis Comparativo"])
    
    with tab1:
        render_main_page()
        
    with tab2:
        if (
            'analysis_results' in st.session_state 
            and st.session_state.analysis_results 
            and 'df_list' in st.session_state.analysis_results
        ):
            logging.debug("Loading comparative analysis with multiple vacancies")
            from frontend import comparative_analysis
            try:
                asyncio.run(comparative_analysis.render_comparative_analysis(
                    st.session_state.analysis_results['df_list']
                ))
            except Exception as e:
                logging.error(f"Error en análisis comparativo: {str(e)}")
                st.error("Error al mostrar el análisis comparativo. Por favor, intente de nuevo.")
        else:
            st.info("Primero debe realizar un análisis de candidatos para ver la comparación")

async def analyze_candidates(ui_inputs, app):
    if not ui_inputs.job_sections:
        st.warning("⚠️ Por favor, suba al menos una descripción de puesto")
        return
        
    if not ('drive_cvs' in st.session_state or ui_inputs.resume_files):
        st.warning("⚠️ Por favor, cargue CVs desde Google Drive o suba archivos manualmente")
        return

    # Procesa los CVs (se mantiene igual)
    if 'drive_cvs' in st.session_state:
        candidate_profiles = await app.process_resumes(st.session_state.drive_cvs)
    else:
        candidate_profiles = await app.process_resumes(ui_inputs.resume_files)
    
    if not candidate_profiles:
        st.warning("No se pudieron procesar los CVs. Por favor, verifique los archivos.")
        return

    # Crear directorio para archivos de depuración
    debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "debug")
    os.makedirs(debug_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Para cada vacante se procesa la descripción, preferencias y criterios, y se analiza el ranking
    try:
        for idx, job_section in enumerate(ui_inputs.job_sections):
            # Prepara preferencias propias para la vacante usando los pesos del job_section
            hiring_preferences = {
                "habilidades_preferidas": [
                    skill.strip() 
                    for skill in (job_section.recruiter_skills or "").split('\n')
                    if skill.strip()
                ],
                "weights": job_section.weights
            }
            
            job_profile = await app.process_job_description(job_section.job_file, hiring_preferences)
            recruiter_preferences = await app.process_preferences(job_section.recruiter_skills)
            standardized_killer_criteria = await app.analyzer.standardize_killer_criteria(job_section.killer_criteria)
            
            rankings = await app.ranking_system.rank_candidates(
                job_profile,
                recruiter_preferences,
                candidate_profiles,
                standardized_killer_criteria if any(standardized_killer_criteria.values()) else None,
                hiring_preferences["weights"]
            )
            
            ranking_df = app.create_ranking_dataframe(rankings)
            
            # Create and save debug information for this vacancy
            debug_df = app.create_debug_dataframe(job_profile, rankings)
            debug_filename = os.path.join(debug_dir, f"debug_vacancy_{idx+1}_{timestamp}.csv")
            debug_df.to_csv(debug_filename, index=False)
            logging.info(f"Debug CSV para vacante {idx+1} guardado en {debug_filename}")
            
            # Crear listas para acumular resultados si no existen
            if 'df_list' not in locals():
                df_list = []
                job_profiles = []
                recruiter_preferences_list = []
                killer_criteria_list = []
                debug_files = []  # Nueva lista para archivos de debug

            # Añadir resultados a las listas
            df_list.append(ranking_df)
            job_profiles.append(job_profile)
            recruiter_preferences_list.append(recruiter_preferences)
            killer_criteria_list.append(job_section.killer_criteria)
            debug_files.append(debug_filename)  # Añadir ruta del archivo de debug

            # Create output directory if it doesn't exist
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
        # Store results in session state
        st.session_state['analysis_results'] = {
            'df_list': df_list,
            'job_profiles': job_profiles,
            'recruiter_preferences_list': recruiter_preferences_list,
            'killer_criteria_list': killer_criteria_list,
            'debug_files': debug_files  # Añadir lista de archivos de debug
        }

        # Realizar una única llamada al display_ranking con todas las listas
        if len(df_list) > 0:
            await UIComponents.display_ranking(
                df_list,
                job_profiles,
                recruiter_preferences_list,
                killer_criteria_list
            )

    except Exception as e:
        logging.error(f"Error durante el análisis: {str(e)}")
        st.error(f"Error en el análisis: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Error crítico en main: {str(e)}")
        st.error("Se produjo un error crítico en la aplicación.")
