"""Módulo principal que coordina todos los componentes del sistema"""
import logging
import streamlit as st
import asyncio
import pandas as pd
from typing import List
import os
from datetime import datetime
import sys
import matplotlib.pyplot as plt
from src.frontend.state import session_state
import openai

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
    PreferenciaReclutadorProfile  # Added this import
)
from src.frontend.ui import UIComponents
from src.utils.utilities import setup_logging, create_score_row, sort_ranking_dataframe
from src.utils.file_handler import FileHandler
from src.utils.google_drive import GoogleDriveIntegration

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
        self.gdrive_folder_id = "1HiJatHPiHgtjMcQI34Amwjwlr5VQ535s"
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
                if isinstance(data, str):  # Handle string data (like killer criteria messages)
                    row = base.copy()
                    row["Comparison Type"] = comp
                    row["Debug Info"] = data
                    rows.append(row)
                    continue

                row = base.copy()
                row["Comparison Type"] = comp
                # Safely get values with defaults
                row["Candidate Text"] = str(data.get("candidate", ""))
                if comp == "preferencias_reclutador":
                    row["Job/Preference Text"] = str(data.get("preferences", ""))
                else:
                    row["Job/Preference Text"] = str(data.get("job", ""))
                row["Cosine Similarity"] = data.get("cosine_similarity", 0.0)
                row["Weight"] = data.get("weight", 0.0)
                row["Weighted Score"] = data.get("weighted_score", 0.0)
                rows.append(row)
                
        return pd.DataFrame(rows)

    async def generate_comparative_analysis(self, selected_cvs, job_profile):
        """Generates a comparative analysis report using OpenAI GPT-3.5-turbo."""
        try:
            cvs_data = [await self.analyzer.standardize_resume(cv) for cv in selected_cvs]
            prompt = self.create_comparison_prompt(cvs_data, job_profile)
            response = openai.Completion.create(
                engine="gpt-3.5-turbo",
                prompt=prompt,
                max_tokens=1500
            )
            report = response.choices[0].text
            visualizations = self.create_visualizations(cvs_data)
            return report, visualizations
        except Exception as e:
            logging.error(f"Error generating comparative analysis: {str(e)}")
            raise
        
    def create_comparison_prompt(self, cvs_data, job_profile):
        """Creates a detailed prompt for OpenAI GPT-3.5-turbo."""
        prompt = f'''
        Analyze these {len(cvs_data)} candidates for the following job position.
        Provide a detailed comparison report including:

        1. Individual Analysis for each candidate:
        - Key strengths aligned with the position
        - Potential gaps or areas for development
        - Experience relevance analysis
        - Skills match percentage explanation

        2. Comparative Analysis:
        - Relative strengths between candidates
        - Unique value propositions
        - Overall fit ranking explanation

        3. Final Recommendations:
        - Best fit justification
        - Development areas for each candidate
        - Hiring recommendations

        Use this data in your analysis:
        Job Description: {job_profile}
        Selected Candidates: {cvs_data}
        '''
        return prompt
    
    def create_visualizations(self, cvs_data):
        """Creates visualizations for the comparative analysis."""
        visualizations = []
        # Radar chart for skills comparison
        skills = list(set(skill for cv in cvs_data for skill in cv['habilidades']))
        skill_values = [[cv['habilidades'].count(skill) for skill in skills] for cv in cvs_data]
        fig, ax = plt.subplots()
        ax.plot(skills, skill_values)
        visualizations.append(fig)
        # Bar chart for experience comparison
        experience = list(set(exp for cv in cvs_data for exp in cv['experiencia']))
        exp_values = [[cv['experiencia'].count(exp) for exp in experience] for cv in cvs_data]
        fig, ax = plt.subplots()
        ax.bar(experience, exp_values)
        visualizations.append(fig)
        return visualizations   

# Inicialización de la aplicación y configuración de la UI
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
    os.environ['STREAMLIT_SECRETS_PATH'] = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
    api_key = st.secrets["openai"]["api_key"]
    app = HRAnalysisApp(api_key)
except Exception as e:
    logging.error(f"Error inicializando la aplicación: {str(e)}")
    st.error("Error inicializando la aplicación. Por favor revise su configuración.")
    app = None

# --- Opción 1: Carga manual de CVs
ui_inputs = UIComponents.create_main_sections()

# --- Opción 2: Carga desde Google Drive ---
st.markdown("---")
st.subheader("Cargar CVs desde Google Drive")

async def load_drive_cvs(app):
    """Función asíncrona para cargar CVs desde Google Drive"""
    try:
        drive_client = GoogleDriveIntegration(
            credentials_path=app.gdrive_credentials,
            folder_id=app.gdrive_folder_id
        )
        cv_texts = await drive_client.process_drive_cvs()
        st.session_state.drive_cvs = cv_texts
        st.success(f"✅ {len(cv_texts)} CVs cargados desde Google Drive")
    except Exception as e:
        st.error(f"❌ Error al cargar desde Google Drive: {str(e)}")
        logging.error(f"Google Drive Error: {str(e)}")

if st.button("🔄 Cargar CVs desde Google Drive", key="drive_button"):
    with st.spinner("Descargando CVs desde Google Drive..."):
        asyncio.run(load_drive_cvs(app))

# --- Procesamiento Unificado ---
async def analyze_candidates(ui_inputs, app):
    if not ui_inputs.job_file:
        st.warning("⚠️ Por favor, suba un archivo de descripción del puesto")
        return
        
    if not ('drive_cvs' in st.session_state or ui_inputs.resume_files):
        st.warning("⚠️ Por favor, cargue CVs desde Google Drive o suba archivos manualmente")
        return
        
    if ui_inputs.weights.total_weight != 1.0:
        st.error("Por favor, ajuste los pesos para que sumen exactamente 1.0")
        return
    
    # Prepara las preferencias y pesos
    hiring_preferences = {
        "habilidades_preferidas": [
            skill.strip() 
            for skill in (ui_inputs.recruiter_skills or "").split('\n')  # Cambiar important_skills por recruiter_skills
            if skill.strip()
        ],
        "weights": {
            "habilidades": ui_inputs.weights.habilidades,
            "experiencia": ui_inputs.weights.experiencia,
            "formacion": ui_inputs.weights.formacion,
            "preferencias_reclutador": ui_inputs.weights.preferencias_reclutador
        }
    }
    
    try:
        # Procesa la descripción del trabajo y preferencias
        job_profile = await app.process_job_description(ui_inputs.job_file, hiring_preferences)
        recruiter_preferences = await app.process_preferences(ui_inputs.recruiter_skills)
        standardized_killer_criteria = await app.analyzer.standardize_killer_criteria(ui_inputs.killer_criteria)
        
        # Procesa los CVs según la fuente
        if 'drive_cvs' in st.session_state:
            candidate_profiles = await app.process_resumes(st.session_state.drive_cvs)
        else:
            candidate_profiles = await app.process_resumes(ui_inputs.resume_files)
        
        if candidate_profiles:
            # Store candidate profiles in session state
            st.session_state['candidate_profiles'] = candidate_profiles

            # Realiza el ranking
            rankings = await app.ranking_system.rank_candidates(
                job_profile,
                recruiter_preferences,
                candidate_profiles,
                standardized_killer_criteria if any(standardized_killer_criteria.values()) else None,
                hiring_preferences["weights"]
            )
            
            logging.info("Ranking de candidatos completado.")
            styled_df = app.create_ranking_dataframe(rankings)
            
            # Create and save debug information
            debug_df = app.create_debug_dataframe(job_profile, rankings)
            debug_dir = os.path.join(os.path.dirname(__file__), "docs", "debug")
            os.makedirs(debug_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_filename = os.path.join(debug_dir, f"debug_{timestamp}.csv")
            debug_df.to_csv(debug_filename, index=False)
            logging.info(f"Debug CSV guardado en {debug_filename}")
            
            # Store results in session state
            st.session_state['analysis_results'] = {
                'df': styled_df,
                'job_profile': job_profile,
                'recruiter_preferences': recruiter_preferences,
                'killer_criteria': standardized_killer_criteria,
                'debug_csv': debug_filename
            }
            
            UIComponents.display_ranking(
                df=styled_df,
                job_profile=job_profile,
                recruiter_preferences=recruiter_preferences,
                killer_criteria=standardized_killer_criteria
            )
            # Añadir botón para generar informe avanzado
            if st.button("Generar Informe Avanzado", key="advanced_report_button"):
                st.session_state.selected_cvs = candidate_profiles
                st.session_state.page = 'advanced_report'
                st.experimental_rerun()
        else:
            st.warning("No se pudieron procesar los CVs. Por favor, verifique los archivos.")
                
    except Exception as e:
        logging.error(f"Error durante el análisis: {str(e)}")
        st.error(f"Error durante el análisis: {str(e)}")

# Configuración inicial del estado de la aplicación
def initialize_session_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'ranking'
    if 'selected_cvs' not in st.session_state:
        st.session_state.selected_cvs = None
    if 'job_profile' not in st.session_state:
        st.session_state.job_profile = None

# Ejecutar una función asíncrona dentro de Streamlit
def run_async(func, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(func(*args))
    loop.close()
    return result

# Función principal de la aplicación
def main():
    initialize_session_state()  # Inicializar session_state si no existe

    if st.session_state.page == 'ranking':
        st.title("Ranking de Candidatos")
        
        # Mostrar advertencia si aún no hay candidatos procesados
        if not st.session_state.selected_cvs:
            st.warning("Aún no se han procesado los candidatos.")

        # Botón para analizar candidatos
        if st.button("Analizar Candidatos", key="analyze_button"):
            run_async(analyze_candidates, ui_inputs, app)  # Ejecuta el análisis de candidatos
            
            # Verificar si los candidatos fueron procesados correctamente
            if st.session_state.selected_cvs:
                st.session_state.page = 'advanced_report'
                st.experimental_rerun()
            else:
                st.warning("No se encontraron candidatos para el informe avanzado.")

    elif st.session_state.page == 'advanced_report':
        st.title("Informe Avanzado de Candidatos")

        # Verificar si hay candidatos seleccionados antes de mostrar la página
        if st.session_state.selected_cvs:
            UIComponents.create_advanced_report_page(st.session_state.selected_cvs)
        else:
            st.warning("No hay candidatos disponibles para el informe avanzado.")
            st.button("Volver al Ranking", on_click=lambda: setattr(st.session_state, 'page', 'ranking'))

    elif st.session_state.page == 'report_results':
        st.title("Resultados del Informe Comparativo")

        # Generar el análisis comparativo de los CVs con el perfil de la vacante
        if st.session_state.selected_cvs:
            report, visualizations = asyncio.run(app.generate_comparative_analysis(
                st.session_state.selected_cvs, 
                st.session_state.job_profile
            ))
            UIComponents.create_report_results_page(report, visualizations)
        else:
            st.warning("No hay candidatos seleccionados para generar el informe.")

        # Botón para volver al ranking
        if st.button("Volver al Ranking"):
            st.session_state.page = 'ranking'
            st.experimental_rerun()

if __name__ == "__main__":
    main()