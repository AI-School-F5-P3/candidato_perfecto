import logging
import numpy as np
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

# Configuración de estilos personalizados
def set_custom_style():
    st.set_page_config(
        page_title="HR Analysis Pro",
        page_icon="👔",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            background-color: #FF4B4B;
            color: white;
            font-weight: bold;
        }
        .stButton > button:hover {
            background-color: #FF6B6B;
            border-color: #FF4B4B;
        }
        .important-text {
            color: #FF4B4B;
            font-weight: bold;
        }
        .sidebar-text {
            font-size: 14px;
            color: #666;
        }
        .status-box {
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
        .success-box {
            background-color: #D4EDDA;
            color: #155724;
            border: 1px solid #C3E6CB;
        }
        .warning-box {
            background-color: #FFF3CD;
            color: #856404;
            border: 1px solid #FFEEBA;
        }
        .error-box {
            background-color: #F8D7DA;
            color: #721C24;
            border: 1px solid #F5C6CB;
        }
        .metric-card {
            background-color: #F8F9FA;
            padding: 1rem;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

class HRAnalysisApp:
    def __init__(self):
        try:
            self.api_url = "http://localhost:11434"
            self.analyzer = SemanticAnalyzer(self.api_url)
            self.matching_engine = MatchingEngine(self.analyzer)
            self.ranking_system = RankingSystem(self.matching_engine)
            self.initialize_session_state()
            logging.info("Analysis components initialized.")
        except Exception as e:
            logging.error(f"Error during HRAnalysisApp initialization: {str(e)}")
            raise e

    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'job_profile' not in st.session_state:
            st.session_state.job_profile = None
        if 'candidates' not in st.session_state:
            st.session_state.candidates = []
        if 'analysis_complete' not in st.session_state:
            st.session_state.analysis_complete = False
        if 'error' not in st.session_state:
            st.session_state.error = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.analyzer.close()

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

    def render_sidebar(self):
        """Render sidebar with information and settings"""
        with st.sidebar:
            st.image("https://via.placeholder.com/150x150.png?text=HR+Pro", width=150)
            st.markdown("### Sobre la aplicación")
            st.markdown("""
                <div class='sidebar-text'>
                Esta herramienta profesional de análisis de CV te ayuda a:
                - Evaluar candidatos objetivamente
                - Identificar las mejores coincidencias
                - Ahorrar tiempo en el proceso de selección
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### Configuración")
            
            # Ajustes de puntuación
            st.markdown("#### Pesos de evaluación")
            weights = {
                "killer_skills": st.slider("Killer Skills", 0.0, 1.0, 0.4, 0.1),
                "no_killer_skills": st.slider("No Killer Skills", 0.0, 1.0, 0.2, 0.1),
                "education": st.slider("Educación", 0.0, 1.0, 0.2, 0.1),
                "specific_requirements": st.slider("Requisitos Específicos", 0.0, 1.0, 0.2, 0.1)
            }
            
            # Normalizar pesos
            total = sum(weights.values())
            if total > 0:
                weights = {k: v/total for k, v in weights.items()}
            
            st.session_state.weights = weights

    def render_job_section(self):
        """Render job description and requirements section"""
        st.markdown("## 📋 Descripción del Puesto")
        
        # Container para la descripción del puesto
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                job_file = st.file_uploader(
                    "Descripción del puesto (TXT o PDF)", 
                    type=['txt', 'pdf'],
                    help="Sube un archivo con la descripción detallada del puesto"
                )
                
                education_level = st.selectbox(
                    "Nivel educativo requerido",
                    ["High School", "Bachelor", "Master", "PhD"],
                    help="Selecciona el nivel mínimo de educación requerido"
                )

            with col2:
                if job_file:
                    st.markdown("""
                        <div class="success-box status-box">
                            ✅ Archivo cargado: {filename}
                        </div>
                    """.format(filename=job_file.name), unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div class="warning-box status-box">
                            ⚠️ Pendiente: Sube el archivo de descripción del puesto
                        </div>
                    """, unsafe_allow_html=True)

        # Container para los requisitos
        st.markdown("### 📝 Requisitos del Puesto")
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                killer_skills = st.text_area(
                    "Killer Skills",
                    placeholder="Ejemplo:\nPython\nSQL\nDocker",
                    height=150,
                    help="Habilidades imprescindibles para el puesto (una por línea)"
                )

            with col2:
                no_killer_skills = st.text_area(
                    "No Killer Skills",
                    placeholder="Ejemplo:\nKubernetes\nAWS\nTerraform",
                    height=150,
                    help="Habilidades deseables pero no imprescindibles (una por línea)"
                )

        specific_requirements = st.text_area(
            "Requisitos Específicos",
            placeholder="Ejemplo:\nUbicación: Madrid\nDisponibilidad: Inmediata\nIdiomas: Inglés C1, Español nativo",
            height=100,
            help="Otros requisitos importantes como ubicación, disponibilidad, idiomas, etc."
        )

        return job_file, education_level, killer_skills, no_killer_skills, specific_requirements

    def render_candidates_section(self):
        """Render candidates upload section"""
        st.markdown("## 👥 Candidatos")
        
        resume_files = st.file_uploader(
            "CVs de los candidatos (TXT o PDF)", 
            type=['txt', 'pdf'],
            accept_multiple_files=True,
            help="Selecciona múltiples archivos de CV para analizar"
        )

        if resume_files:
            st.markdown(f"""
                <div class="success-box status-box">
                    ✅ {len(resume_files)} CV(s) cargados
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="warning-box status-box">
                    ⚠️ Pendiente: Sube los CVs de los candidatos
                </div>
            """, unsafe_allow_html=True)

        return resume_files

    def render_results_section(self, rankings=None):
        """Render analysis results section"""
        if rankings:
            st.markdown("## 📊 Resultados del Análisis")
            
            # Métricas principales
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                    <div class="metric-card">
                        <h3>Candidatos Analizados</h3>
                        <h2>{}</h2>
                    </div>
                """.format(len(rankings)), unsafe_allow_html=True)
            
            with col2:
                top_score = rankings[0][1]["final_score"] if rankings else 0
                st.markdown("""
                    <div class="metric-card">
                        <h3>Mejor Puntuación</h3>
                        <h2>{:.1%}</h2>
                    </div>
                """.format(top_score), unsafe_allow_html=True)
            
            with col3:
                avg_score = np.mean([r[1]["final_score"] for r in rankings]) if rankings else 0
                st.markdown("""
                    <div class="metric-card">
                        <h3>Puntuación Media</h3>
                        <h2>{:.1%}</h2>
                    </div>
                """.format(avg_score), unsafe_allow_html=True)

            # Tabla de resultados
            styled_df = self.create_ranking_dataframe(rankings)
            st.dataframe(
                styled_df,
                use_container_width=True,
                height=400
            )

            # Exportar resultados
            if st.button("📥 Exportar Resultados"):
                df = styled_df.data
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name="resultados_analisis.csv",
                    mime="text/csv"
                )

    def create_ranking_dataframe(self, rankings) -> pd.DataFrame:
        """Create and style rankings DataFrame"""
        try:
            data = []
            for candidate, scores in rankings:
                row = {
                    'Nombre Candidato': candidate.name,
                    'Puntuación Total': scores['final_score'],
                    'Killer Skills': scores['component_scores']['killer_skills'],
                    'No Killer Skills': scores['component_scores']['no_killer_skills'],
                    'Educación': scores['component_scores']['education'],
                    'Requisitos Específicos': scores['component_scores']['specific_requirements'],
                    'Habilidades': ', '.join(candidate.skills[:5]) + ('...' if len(candidate.skills) > 5 else ''),
                    'Educación (Descripcion)': candidate.education_level
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            
            # Aplicar estilos
            percentage_cols = ['Puntuación Total', 'Killer Skills', 'No Killer Skills', 'Educación', 'Requisitos Específicos']
            styled_df = df.style.background_gradient(
                subset=['Puntuación Total'],
                cmap='RdYlGn'
            ).format({
                col: '{:.1%}' for col in percentage_cols
            })
            
            return styled_df
        except Exception as e:
            logging.error(f"Error creating ranking DataFrame: {str(e)}")
            raise e

async def main():
    # Configurar estilo personalizado
    set_custom_style()
    
    app = HRAnalysisApp()
    
    # Renderizar sidebar
    app.render_sidebar()
    
    # Título principal
    st.title("🎯 HR Analysis Pro")
    st.markdown("""
        <div style='margin-bottom: 2rem;'>
            Sistema profesional de análisis y matching de candidatos
        </div>
    """, unsafe_allow_html=True)

    try:
        # Secciones principales
        job_file, education_level, killer_skills, no_killer_skills, specific_requirements = app.render_job_section()
        resume_files = app.render_candidates_section()

        # Botón de análisis
        analyze_button = st.button(
            "🔍 Analizar Candidatos",
            disabled=not (job_file and resume_files)
        )

        if analyze_button:
            with st.spinner("⏳ Analizando candidatos..."):
                async with app as analysis_app:
                    # Preparar preferencias
                    hiring_preferences = {
                        "education_level": education_level,
                        "killer_skills": [s.strip() for s in killer_skills.split('\n') if s.strip()],
                        "no_killer_skills": [s.strip() for s in no_killer_skills.split('\n') if s.strip()],
                        "specific_requirements": [s.strip() for s in specific_requirements.split('\n') if s.strip()]
                    }
                    
                    # Procesar datos
                    job_profile = await analysis_app.process_job_description(job_file, hiring_preferences)
                    candidate_profiles = await analysis_app.process_resumes(resume_files)
                    rankings = await analysis_app.ranking_system.rank_candidates(job_profile, candidate_profiles)
                    
                    # Guardar resultados en session_state
                    st.session_state.job_profile = job_profile
                    st.session_state.rankings = rankings
                    st.session_state.analysis_complete = True

            st.success("✅ Análisis completado con éxito!")
            
        # Mostrar resultados si están disponibles
        if st.session_state.analysis_complete:
            app.render_results_section(st.session_state.rankings)

    except Exception as e:
        st.error(f"""
            Ha ocurrido un error durante el análisis:
            ```
            {str(e)}
            ```
            Por favor, verifica los archivos e inténtalo de nuevo.
        """)
        logging.error(f"Error in main app: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())