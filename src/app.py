"""Módulo principal que coordina todos los componentes del sistema"""
import logging
from openai import AsyncOpenAI
import streamlit as st
import asyncio
import pandas as pd
from typing import List
import os
import matplotlib.pyplot as plt
import seaborn as sns
from src.hr_analysis_system import (
    SemanticAnalyzer, 
    MatchingEngine,
    RankingSystem,
    JobProfile,
    CandidateProfile,
    OpenAIEmbeddingProvider,
    MatchScore,
)
from src.frontend.ui import UIComponents
from src.utils.utilities import setup_logging, create_score_row, sort_ranking_dataframe
from src.utils.file_handler import FileHandler

class OpenAITextGenerationProvider:
    """Proveedor de generación de texto usando GPT-3.5 Turbo"""

    def __init__(self, api_key: str):
        """Inicializa el proveedor de generación de texto"""
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
        

class HRAnalysisApp:
    """Clase principal que orquesta el flujo completo del análisis"""
    def __init__(self, api_key: str):
        # Inicializa los componentes principales del sistema
        self.embedding_provider = OpenAIEmbeddingProvider(api_key)
        self.analyzer = SemanticAnalyzer(self.embedding_provider)
        self.matching_engine = MatchingEngine(self.embedding_provider)
        self.ranking_system = RankingSystem(self.matching_engine)
        self.file_handler = FileHandler()
        self.text_generation_provider = OpenAITextGenerationProvider(api_key)
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

    async def analyze_text_comparatively(self, df: pd.DataFrame, candidate_names: List[str]) -> List[str]:
        """Realiza un análisis de texto comparativo utilizando LLM y genera gráficos"""
        try:
            comparative_df = df[df['Nombre Candidato'].isin(candidate_names)].copy()
            analysis_results = []
            
            for idx, row in comparative_df.iterrows():
                candidate_text = f"Nombre: {row['Nombre Candidato']}\nExperiencia: {row['Experiencia']}\nHabilidades: {row['Habilidades']}\nFormación: {row['Formación']}"
                
                prompt = f"Analiza el siguiente perfil de candidato y genera un resumen conciso de sus fortalezas y áreas de mejora en español:\n{candidate_text}"
                
                try:
                    response = await self.text_generation_provider.client.chat.completions.create(
                        model=self.text_generation_provider.model,
                        messages=[
                            {"role": "system", "content": "Eres un experto en recursos humanos que analiza perfiles profesionales."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )    
                    
                    if response and response.choices:
                        analysis = response.choices[0].message.content.strip()
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
            
            st.session_state['analysis_results'] = analysis_results
            return analysis_results
            
        except Exception as e:
            logging.error(f"Error en el análisis comparativo: {str(e)}")
            st.error("Error al mostrar el informe comparativo. Verifique los datos y vuelva a intentar.")
            return []

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
                    
                    # Guardar el DataFrame en el estado de la sesión
                    st.session_state['styled_df'] = styled_df

                    # Navegar a la pantalla de análisis comparativo
                    st.session_state['page'] = 'comparative_analysis'
                    st.experimental_set_query_params(page='comparative_analysis')
                else:
                    st.warning("No se pudieron procesar los CVs. Por favor, verifique los archivos.")
                
        except Exception as e:
            logging.error(f"Error durante el análisis de candidatos: {str(e)}")
            st.error(f"Ocurrió un error durante el análisis: {str(e)}")
    elif ui_inputs.weights.total_weight != 1.0:
        st.error("Por favor, ajuste los pesos para que sumen exactamente 1.0 antes de continuar.")

def comparative_analysis(app: HRAnalysisApp):
    """Pantalla de análisis comparativo"""
    st.markdown('<h1 class="title">Análisis Comparativo</h1>', unsafe_allow_html=True)
    
    if 'styled_df' not in st.session_state:
        st.error("No se encontraron datos de ranking. Por favor, regrese a la pantalla principal y realice el análisis de candidatos.")
        return
    
    styled_df = st.session_state['styled_df']
    
    selected_candidate_names = st.multiselect(
        "Seleccione los nombres de los candidatos para el informe comparativo",
        options=styled_df['Nombre Candidato'].tolist()
    )
    
    if selected_candidate_names:
        with st.spinner("Generando análisis comparativo..."):
            analysis_results = asyncio.run(app.analyze_text_comparatively(styled_df, selected_candidate_names))
            
            if analysis_results:
                st.subheader("Análisis Individual de Candidatos")
                for result in analysis_results:
                    with st.expander(f"Análisis de {result['nombre']}"):
                        st.write(result['analisis'])
            
            comparative_df = styled_df[styled_df['Nombre Candidato'].isin(selected_candidate_names)]
            UIComponents.display_comparative_report(comparative_df)
    else:
        st.warning("Por favor, seleccione al menos un candidato para el informe comparativo.")

    if st.button("Regresar a la pantalla principal"):
        st.session_state['page'] = 'main'
        st.experimental_set_query_params(page='main')

def run_app():
    """Función principal que maneja la navegación entre pantallas"""
    if 'page' not in st.session_state:
        st.session_state['page'] = 'main'
    
    app = HRAnalysisApp(st.secrets["openai"]["api_key"])
    
    if st.session_state['page'] == 'main':
        asyncio.run(main())
    elif st.session_state['page'] == 'comparative_analysis':
        comparative_analysis(app)

if __name__ == "__main__":
    try:
        run_app()
    except Exception as e:
        logging.critical(f"Error crítico en main: {str(e)}")
        st.error("Se produjo un error crítico en la aplicación.")