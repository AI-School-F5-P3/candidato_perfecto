"""Módulo principal que coordina todos los componentes del sistema"""
import logging
from openai import AsyncOpenAI
import streamlit as st
import asyncio
import pandas as pd
from typing import List, Optional
import os
from datetime import datetime
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
    PreferenciaReclutadorProfile  # Se añadió esta importación
)
import matplotlib.pyplot as plt
import seaborn as sns
from frontend.ui import UIComponents
from utils.utilities import setup_logging, create_score_row, sort_ranking_dataframe
from utils.file_handler import FileHandler
from utils.google_drive import GoogleDriveIntegration

# Configuración inicial de Streamlit y logging
st.set_page_config(page_title="El candidato perfecto", layout="wide")
setup_logging()
UIComponents.load_custom_css()

def initialize_session_state():
    """Inicializa el estado de la sesión si no existe"""
    for key, default_value in {
        'app': None,
        'analysis_results': None,
        'current_tab': "Ranking Principal",
        'drive_files': None,
        'selected_files': [],
        'drive_cvs': None,
        'is_processing': False
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

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
                model="gpt-3.5-turbo",
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
        self.gdrive_folder_id = "1HiJatHPiHgtjMcQI34Amwjwlr5VQ535s"
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

def render_drive_file_grid():
    """Renderiza los archivos de Drive en un grid con formato de tarjetas"""
    if not st.session_state.drive_files:
        return
    
    # Calcular número de columnas basado en el ancho de la pantalla
    num_columns = 4
    files = list(st.session_state.drive_files.items())
    
    # Crear filas de columnas para el grid
    for i in range(0, len(files), num_columns):
        cols = st.columns(num_columns)
        for col_idx, col in enumerate(cols):
            if i + col_idx < len(files):
                filename, file_id = files[i + col_idx]
                with col:
                    # Crear una tarjeta para cada archivo
                    st.markdown("""
                    <style>
                    .file-card {
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        padding: 10px;
                        margin: 5px;
                        background-color: white;
                    }
                    .file-card:hover {
                        border-color: #0066cc;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    with st.container():
                        st.markdown(f'<div class="file-card">', unsafe_allow_html=True)
                        is_selected = st.checkbox(
                            "Seleccionar",
                            key=f"check_{file_id}",
                            value=filename in st.session_state.selected_files
                        )
                        st.markdown(f"**{filename.split(' (Modificado')[0]}**")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        if is_selected and filename not in st.session_state.selected_files:
                            st.session_state.selected_files.append(filename)
                        elif not is_selected and filename in st.session_state.selected_files:
                            st.session_state.selected_files.remove(filename)

async def load_drive_cvs(app):
    """Función asíncrona para cargar CVs desde Google Drive"""
    try:
        # Crear un modal para la selección de archivos
        if st.session_state.drive_files is None:
            with st.spinner("Cargando lista de archivos de Drive..."):
                drive_client = GoogleDriveIntegration(
                    credentials_path=app.gdrive_credentials,
                    folder_id=app.gdrive_folder_id
                )
                files = await drive_client.list_cv_files()
                if not files:
                    st.warning("No se encontraron CVs en la carpeta de Google Drive")
                    return
                st.session_state.drive_files = {
                    f"{file['name']} (Modificado: {file['modifiedTime']})": file['id'] 
                    for file in files
                }

        # Mostrar el modal de selección
        with st.expander("📂 Selección de CVs", expanded=True):
            st.write("Seleccione los CVs que desea analizar:")
            render_drive_file_grid()
            
            # Mostrar botón de procesamiento solo si hay archivos seleccionados
            if st.session_state.selected_files:
                if st.button("Procesar CVs seleccionados", key="process_selected"):
                    with st.spinner("Procesando CVs seleccionados..."):
                        drive_client = GoogleDriveIntegration(
                            credentials_path=app.gdrive_credentials,
                            folder_id=app.gdrive_folder_id
                        )
                        selected_ids = [
                            st.session_state.drive_files[filename] 
                            for filename in st.session_state.selected_files
                        ]
                        cv_texts = await drive_client.process_selected_cvs(selected_ids)
                        st.session_state.drive_cvs = cv_texts
                        st.success(f"✅ {len(cv_texts)} CVs cargados desde Google Drive")
            else:
                st.info("Seleccione al menos un CV para procesar")
            
    except Exception as e:
        st.error(f"❌ Error al cargar desde Google Drive: {str(e)}")
        logging.error(f"Google Drive Error: {str(e)}")

def render_main_page():
    """Renderiza la página principal de la aplicación"""
    st.markdown('<h1 class="title">El candidato perfecto</h1>', unsafe_allow_html=True)
    st.write("""
    El sistema recopila información de una vacante junto con las preferencias del equipo reclutador 
    y las características obligatorias a cumplir por los candidatos. Con esta información, se analizan 
    los curriculum vitae de los candidatos y se obtiene un ranking de idoneidad basado en habilidades, 
    experiencia y formación. También se identifican los candidatos que no cumplen con los requisitos 
    obligatorios. Los pesos de ponderación pueden ser ajustados si así se requiere.
    """)
    
    ui_inputs = UIComponents.create_main_sections()
    
    # Sección de Google Drive
    st.markdown("---")
    st.subheader("Cargar CVs desde Google Drive")
    
    # Contenedor para la sección de Drive
    drive_section = st.container()
    
    with drive_section:
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Listar CVs disponibles", key="list_drive_button"):
                with st.spinner("Cargando archivos de Drive..."):
                    asyncio.run(load_drive_cvs(st.session_state.app))
        
        # Mostrar el grid de selección si hay archivos
        if st.session_state.drive_files:
            st.markdown("### CVs Disponibles")
            render_drive_file_grid()
            
            # Mostrar botón de procesamiento solo si hay archivos seleccionados
            if st.session_state.selected_files:
                if st.button("Procesar CVs seleccionados", key="process_selected"):
                    with st.spinner("Procesando CVs seleccionados..."):
                        drive_client = GoogleDriveIntegration(
                            credentials_path=st.session_state.app.gdrive_credentials,
                            folder_id=st.session_state.app.gdrive_folder_id
                        )
                        selected_ids = [
                            st.session_state.drive_files[filename] 
                            for filename in st.session_state.selected_files
                        ]
                        cv_texts = asyncio.run(drive_client.process_selected_cvs(selected_ids))
                        st.session_state.drive_cvs = cv_texts
                        st.success(f"✅ {len(cv_texts)} CVs cargados desde Google Drive")

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
    tab1, tab2, tab3 = st.tabs(["Ranking Principal", "Análisis Comparativo", "Excel"])
    
    with tab1:
        render_main_page()
        
    with tab2:
        if (
            'analysis_results' in st.session_state 
            and st.session_state.analysis_results 
            and 'df' in st.session_state.analysis_results
        ):
            logging.debug(f"analysis_results state: {st.session_state.analysis_results}")
            from frontend import comparative_analysis
            try:
                asyncio.run(comparative_analysis.render_comparative_analysis(
                    st.session_state.analysis_results['df']
                ))
            except Exception as e:
                logging.error(f"Error en análisis comparativo: {str(e)}")
                st.error("Error al mostrar el análisis comparativo. Por favor, intente de nuevo.")
        else:
            st.info("Primero debe realizar un análisis de candidatos para ver la comparación")

    with tab3:
        if (
            'analysis_results' in st.session_state 
            and st.session_state.analysis_results 
            and 'df' in st.session_state.analysis_results
        ):
            from frontend import excel_export
            try:
                excel_export.render_excel_export(
                    st.session_state.analysis_results['df']
                )
            except Exception as e:
                logging.error(f"Error en exportación Excel: {str(e)}")
                st.error("Error al generar la exportación Excel. Por favor, intente de nuevo.")
        else:
            st.info("Primero debe realizar un análisis de candidatos para exportar a Excel")

async def load_drive_cvs(app):
    """Función asíncrona para cargar CVs desde Google Drive"""
    try:
        drive_client = GoogleDriveIntegration(
            credentials_path=app.gdrive_credentials,
            folder_id=app.gdrive_folder_id
        )
        files = await drive_client.list_cv_files()
        
        if not files:
            st.warning("No se encontraron CVs en la carpeta de Google Drive")
            return
            
        st.session_state.drive_files = {
            f"{file['name']} (Modificado: {file['modifiedTime']})": file['id'] 
            for file in files
        }
        
    except Exception as e:
        st.error(f"❌ Error al cargar desde Google Drive: {str(e)}")
        logging.error(f"Google Drive Error: {str(e)}")

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
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "debug")
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
        else:
            st.warning("No se pudieron procesar los CVs. Por favor, verifique los archivos.")
                
    except Exception as e:
        logging.error(f"Error durante el análisis: {str(e)}")
        st.error(f"Error durante el análisis: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Error crítico en main: {str(e)}")
        st.error("Se produjo un error crítico en la aplicación.")

