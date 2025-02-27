import streamlit as st
from hr_analysis_system import JobProfile
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import pandas as pd
from datetime import datetime
from utils.utilities import export_rankings_to_excel
from io import BytesIO
from utils.drive_utils import load_drive_cvs
import asyncio

@dataclass
class WeightSettings:
    """Configuración de pesos para diferentes componentes de puntuación"""
    habilidades: float
    experiencia: float
    formacion: float
    preferencias_reclutador: float
    total_weight: float

@dataclass
class JobSection:
    """Contiene los datos de cada vacante"""
    job_file: Any
    recruiter_skills: str
    killer_criteria: Dict[str, List[str]]
    weights: Any = None

@dataclass
class UIInputs:
    """Almacena los inputs de la interfaz para la funcionalidad multivacante"""
    job_sections: List[JobSection]
    resume_files: List[Any]

class UIComponents:
    """Maneja todos los componentes de la interfaz de usuario"""
    @staticmethod
    def load_custom_css() -> None:
        """Carga estilos CSS personalizados"""
        st.markdown(
            """
            <style>
            /* Color scheme - Red, Blue, Orange */
            :root {
                --primary-blue: #1e6091;
                --secondary-blue: #4a89aa;
                --primary-red: #d32f2f;
                --light-red: #ffebee;
                --primary-orange: #f57c00;
                --light-orange: #fff3e0;
                --bg-color: #f8f9fa;
                --text-color: #333333;
                --border-radius: 8px;
                --card-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            /* General styling */
            .stApp {
                background-color: var(--bg-color);
            }
            
            /* Layout containers */
            .card-container {
                background-color: white;
                border-radius: var(--border-radius);
                padding: 1.5rem;
                box-shadow: var(--card-shadow);
                margin-bottom: 1rem;
                border-top: 4px solid var(--primary-blue);
            }
            
            .section-container {
                padding: 0.5rem;
                margin-bottom: 0.75rem;
                border-radius: var(--border-radius);
            }
            
            /* Typography */
            .main-title {
                color: var(--primary-blue);
                font-size: 2.2rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                text-align: center;
            }
            
            .section-title {
                color: var(--primary-blue);
                font-size: 1.4rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
                padding-bottom: 0.25rem;
                border-bottom: 2px solid var(--secondary-blue);
            }
            
            .section-header {
                color: var(--primary-blue);
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
            }
            
            /* Custom elements */
            .badge {
                display: inline-block;
                padding: 0.2rem 0.6rem;
                border-radius: 16px;
                font-size: 0.8rem;
                font-weight: 600;
                margin-right: 0.5rem;
            }
            
            .badge-blue {
                background-color: var(--secondary-blue);
                color: white;
            }
            
            .badge-red {
                background-color: var(--primary-red);
                color: white;
            }
            
            .badge-orange {
                background-color: var(--primary-orange);
                color: white;
            }
            
            /* Results styling */
            .score-high {
                background-color: #e6ffe6;
            }
            
            .score-medium {
                background-color: var(--light-orange);
            }
            
            .score-low {
                background-color: var(--light-red);
            }
            
            .disqualified {
                background-color: var(--light-red);
            }
            
            /* Button styling */
            .custom-button {
                background-color: var(--primary-blue);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: var(--border-radius);
                text-align: center;
                font-weight: 600;
                text-decoration: none;
                display: inline-block;
                border: none;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            
            .custom-button:hover {
                background-color: var(--secondary-blue);
            }
            
            /* Hide Streamlit default footer */
            footer {
                visibility: hidden;
            }
            
            /* Compact file uploader */
            .stFileUploader {
                padding-bottom: 0.5rem !important;
            }
            
            /* Custom expander styling */
            .streamlit-expanderHeader {
                background-color: var(--secondary-blue);
                color: white !important;
                border-radius: var(--border-radius);
                padding: 0.5rem !important;
            }
            
            .streamlit-expanderContent {
                border: 1px solid #e0e0e0;
                border-radius: 0 0 var(--border-radius) var(--border-radius);
                padding: 0.75rem !important;
            }
            
            /* Legend styling */
            .legend-container {
                margin: 10px 0;
                font-size: 0.8rem;
                background-color: white;
                padding: 0.75rem;
                border-radius: var(--border-radius);
                border: 1px solid #e0e0e0;
            }
            
            .legend-item {
                display: flex;
                align-items: center;
                margin-bottom: 0.25rem;
            }
            
            .legend-color {
                width: 16px;
                height: 16px;
                margin-right: 0.5rem;
                border-radius: 2px;
            }
            
            /* Table styling */
            .dataframe {
                border-collapse: collapse;
                width: 100%;
            }
            
            .dataframe th {
                background-color: var(--secondary-blue);
                color: white;
                padding: 0.5rem;
                text-align: left;
            }
            
            /* Adjusting streamlit specific elements */
            div.stSlider > div {
                padding-top: 0.5rem !important;
                padding-bottom: 0.5rem !important;
            }
            
            .stTextArea > div > div {
                padding-top: 0.25rem !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    @staticmethod
    def _check_duplicate_files(files: List[Any]) -> Tuple[List[str], List[Any]]:
        """
        Verifica archivos duplicados y retorna los nombres duplicados y lista limpia
        """
        seen = {}
        duplicates = []
        unique_files = []
        
        for file in files:
            if file.name in seen:
                duplicates.append(file.name)
            else:
                seen[file.name] = True
                unique_files.append(file)
                
        return duplicates, unique_files

    @staticmethod
    def create_main_sections() -> UIInputs:
        """Crea las secciones principales de la interfaz con soporte para múltiples vacantes"""
        # Aplicar el estilo personalizado
        UIComponents.load_custom_css()
        
        # Header con título principal
        st.markdown('<div class="main-title">El Candidato Perfecto - Sistema de Análisis de Candidatos</div>', unsafe_allow_html=True)
        # Header con título principal y expander de información
        with st.expander("ℹ️ Información del Sistema", expanded=False):
            st.markdown("""
            ### 🔍 Acerca del Sistema
            El Candidato Perfecto es una herramienta avanzada de análisis que utiliza IA para evaluar candidatos y ayudar en la toma de decisiones de contratación.
            
            ### ✨ Capacidades
            - **Análisis múltiple**: Procesa varias vacantes simultáneamente
            - **IA semántica**: Evalúa similitud contextual entre requisitos y perfiles
            - **Criterios eliminatorios**: Descalifica automáticamente candidatos que no cumplen requisitos obligatorios
            - **Ponderación personalizada**: Ajuste de pesos para habilidades, experiencia, formación y preferencias
            - **Exportación de resultados**: Genera reportes en Excel para análisis posterior
            - **Integración con Google Drive**: Importa CVs directamente desde la nube
            
            ### 📋 Guía de uso
            1. **Cargue archivos**: Suba descripciones de vacantes y CVs de candidatos (local o Drive)
            
            2. **Configure cada vacante**:
               - Defina preferencias específicas del reclutador
               - Establezca criterios eliminatorios (habilidades y experiencia obligatorias)
               - Ajuste los pesos de evaluación (deben sumar 1.0)
               
            3. **Ejecute el análisis**: Haga clic en el botón de analizar candidatos
            
            4. **Revise resultados**:
               - Explore el ranking de candidatos por vacante
               - Verifique estadísticas de candidatos calificados vs descalificados
               - Exporte los resultados completos a Excel
            """, unsafe_allow_html=True)
        
        
        # Crear contenedor para seleccionar archivos
        st.markdown('<div class="section-title">Cargar Archivos</div>', unsafe_allow_html=True)
        
        job_sections = []
        
        # Layout de dos columnas para ambos uploaders
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">📄 Descripciones de Vacantes</div>', unsafe_allow_html=True)
            job_files = st.file_uploader(
                "Suba las descripciones del puesto (TXT o PDF)",
                type=['txt', 'pdf'],
                accept_multiple_files=True,
                key="job_upload_multi"
            )
            
            if job_files:
                st.markdown(f'<div class="badge badge-blue">{len(job_files)} archivos cargados</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">👨‍💼 CVs de Candidatos</div>', unsafe_allow_html=True)
            
            # Crear dos columnas para los métodos de carga
            upload_col1, upload_col2 = st.columns(2)
            
            with upload_col1:
                resume_files = st.file_uploader(
                    "Suba los CVs de los candidatos (TXT o PDF)",
                    type=['txt', 'pdf'],
                    accept_multiple_files=True,
                    key="cv_upload_multi"
                )
            
            with upload_col2:
                st.markdown('<div style="text-align: center; padding: 1rem 0;">', unsafe_allow_html=True)
                if st.button("🔄 Cargar CVs desde Google Drive", key="drive_button", use_container_width=True):
                    with st.spinner("Descargando CVs desde Google Drive..."):
                        asyncio.run(load_drive_cvs(st.session_state.app))
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Mostrar contadores de archivos cargados
            col_local, col_drive = st.columns(2)
            with col_local:
                if resume_files:
                    st.markdown(f'<div class="badge badge-blue">{len(resume_files)} archivos locales</div>', unsafe_allow_html=True)
            
            with col_drive:
                if 'drive_cvs' in st.session_state and st.session_state.drive_cvs:
                    st.markdown(f'<div class="badge badge-green">{len(st.session_state.drive_cvs)} archivos de Drive</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Validación de archivos duplicados en vacantes
        if job_files:
            duplicates, job_files = UIComponents._check_duplicate_files(job_files)
            if duplicates:
                st.warning(f"⚠️ Se ignoraron los siguientes archivos duplicados de vacantes: {', '.join(duplicates)}")
        
        # Validación del límite de vacantes
        if job_files and len(job_files) > 5:
            st.warning("⚠️ Máximo 5 vacantes simultáneas para garantizar rendimiento")
            job_files = job_files[:5]  # Limitar a las primeras 5 vacantes
            
        # Validación de archivos duplicados en CVs
        if resume_files:
            duplicates, resume_files = UIComponents._check_duplicate_files(resume_files)
            if duplicates:
                st.warning(f"⚠️ Se ignoraron los siguientes CVs duplicados: {', '.join(duplicates)}")
        
        if job_files:
            st.markdown('<div class="section-title">Configuración Opcional de Vacantes</div>', unsafe_allow_html=True)
            
            for idx, job_file in enumerate(job_files):
                with st.expander(f"Vacante {idx+1}: {job_file.name}", expanded=(idx == 0)):
                    # Organizar la configuración en columnas
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Preferencias del reclutador
                        st.markdown('<div class="section-header">💼 Preferencias del Reclutador</div>', unsafe_allow_html=True)
                        recruiter_skills = st.text_area(
                            "Preferencias del reclutador (una por línea)",
                            height=100,
                            key=f"skills_input_{idx}",
                            help="Ingrese las preferencias específicas para esta vacante."
                        )
                        
                        # Criterios eliminatorios
                        st.markdown('<div class="section-header">⛔ Criterios Eliminatorios</div>', unsafe_allow_html=True)
                        criterion1, criterion2 = st.columns(2)
                        
                        with criterion1:
                            killer_skills = st.text_area(
                                "Habilidades eliminatorias",
                                height=100,
                                key=f"killer_skills_input_{idx}",
                                help="Una habilidad por línea"
                            )
                            
                        with criterion2:
                            killer_experiencia = st.text_area(
                                "Experiencia eliminatoria",
                                height=100,
                                key=f"killer_exp_input_{idx}",
                                help="Una experiencia por línea"
                            )
                            
                    with col2:
                        # Configuración de pesos
                        st.markdown('<div class="section-header">⚖️ Distribución de Pesos</div>', unsafe_allow_html=True)
                        st.markdown("<small>Ajuste los pesos para cada categoría (deben sumar 1.0)</small>", unsafe_allow_html=True)
                        
                        vac_hab = st.slider(
                            "Habilidades",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.3,
                            step=0.05,
                            key=f"vac_weight_habilidades_{idx}",
                            format="%.2f"
                        )
                        vac_exp = st.slider(
                            "Experiencia",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.3,
                            step=0.05,
                            key=f"vac_weight_experiencia_{idx}",
                            format="%.2f"
                        )
                        vac_for = st.slider(
                            "Formación",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.2,
                            step=0.05,
                            key=f"vac_weight_formacion_{idx}",
                            format="%.2f"
                        )
                        vac_pref = st.slider(
                            "Preferencias del Reclutador",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.2,
                            step=0.05,
                            key=f"vac_weight_preferencias_{idx}",
                            format="%.2f"
                        )
                        vac_total = round(vac_hab + vac_exp + vac_for + vac_pref, 2)
                        
                        # Mostrar el total con color según sea correcto o no
                        if vac_total == 1.0:
                            st.markdown(f'<div style="background-color: #e6ffe6; padding: 0.5rem; border-radius: 4px; text-align: center; margin-top: 0.5rem;">Total: <b>{vac_total}</b> ✓</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="background-color: #ffebee; padding: 0.5rem; border-radius: 4px; text-align: center; margin-top: 0.5rem;">Total: <b>{vac_total}</b> ⚠️ Debe ser 1.0</div>', unsafe_allow_html=True)
                    
                    # Crear estructura de la JobSection
                    killer_criteria = {
                        "killer_habilidades": [
                            skill.strip()
                            for skill in (killer_skills or "").split('\n')
                            if skill.strip()
                        ],
                        "killer_experiencia": [
                            exp.strip()
                            for exp in (killer_experiencia or "").split('\n')
                            if exp.strip()
                        ]
                    }
                    
                    job_sections.append(JobSection(
                        job_file=job_file,
                        recruiter_skills=recruiter_skills,
                        killer_criteria=killer_criteria,
                        weights={
                            "habilidades": vac_hab,
                            "experiencia": vac_exp,
                            "formacion": vac_for,
                            "preferencias_reclutador": vac_pref
                        }
                    ))
        
        return UIInputs(
            job_sections=job_sections,
            resume_files=resume_files
        )

    @staticmethod
    async def display_ranking(df_list: List[pd.DataFrame], 
                            job_profiles: List[JobProfile], 
                            recruiter_preferences_list: List[Any], 
                            killer_criteria_list: List[Dict]) -> None:
        """
        Muestra el ranking de candidatos y detalles de la búsqueda para múltiples vacantes
        
        Args:
            df_list: Lista de DataFrames con los resultados de cada vacante
            job_profiles: Lista de perfiles de trabajo
            recruiter_preferences_list: Lista de preferencias del reclutador
            killer_criteria_list: Lista de criterios eliminatorios
        """
        try:
            st.markdown('<div class="section-title">Resultados por Vacante</div>', unsafe_allow_html=True)
            
            # Add Export to Excel button before the tabs
            if len(df_list) > 0:
                st.markdown('<div class="card-container">', unsafe_allow_html=True)
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown('<div class="section-header">🏆 Ranking de Candidatos</div>', unsafe_allow_html=True)
                    st.markdown(f"<p>Se evaluaron <b>{len(df_list[0]) if len(df_list) > 0 else 0}</b> candidatos para <b>{len(df_list)}</b> vacantes.</p>", unsafe_allow_html=True)
                
                with col2:
                    # Crear el buffer de Excel
                    buffer = BytesIO()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"resultados_ranking_{timestamp}.xlsx"
                    
                    # Preparar los datos para Excel
                    vacancy_names = [job_profile.nombre_vacante for job_profile in job_profiles]
                    success = export_rankings_to_excel(df_list, vacancy_names, buffer)
                    
                    if success:
                        st.download_button(
                            label="📥 Exportar a Excel",
                            data=buffer.getvalue(),
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_excel",
                            use_container_width=True
                        )
                st.markdown('</div>', unsafe_allow_html=True)

            # Crear pestañas para cada vacante
            if len(df_list) > 0:
                tabs = st.tabs([f"Vacante {i+1}: {job_profiles[i].nombre_vacante}" for i in range(len(df_list))])
                
                for idx, (tab, df, job_profile, recruiter_preferences, killer_criteria) in enumerate(
                    zip(tabs, df_list, job_profiles, recruiter_preferences_list, killer_criteria_list)):
                    
                    with tab:
                        st.markdown(f'<div class="section-header">📊 Resultados: {job_profile.nombre_vacante}</div>', unsafe_allow_html=True)
                        
                        display_df = df.copy()
                        raw_data = display_df.pop('raw_data')

                        def style_row(row):
                            styles = []
                            is_disqualified = row['Estado'] == 'Descalificado'
                            for idx, _ in enumerate(row):
                                if is_disqualified:
                                    styles.append('background-color: var(--light-red)')
                                elif row.index[idx] == 'Score Final':
                                    score = float(row['Score Final'].rstrip('%')) / 100
                                    if score >= 0.7:
                                        styles.append('background-color: #e6ffe6')
                                    elif score >= 0.4:
                                        styles.append('background-color: var(--light-orange)')
                                    else:
                                        styles.append('background-color: var(--light-red)')
                                else:
                                    styles.append('')
                            return styles

                        styled_df = display_df.style.apply(style_row, axis=1)
                        st.dataframe(styled_df, use_container_width=True)
                        
                        # Mostrar leyenda de colores con el nuevo estilo
                        st.markdown("""
                        <div class="legend-container">
                            <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 10px;">
                                <div class="legend-item">
                                    <div class="legend-color" style="background-color: #e6ffe6;"></div>
                                    <span>Score ≥ 70%</span>
                                </div>
                                <div class="legend-item">
                                    <div class="legend-color" style="background-color: #fff3e0;"></div>
                                    <span>40% ≤ Score < 70%</span>
                                </div>
                                <div class="legend-item">
                                    <div class="legend-color" style="background-color: #ffebee;"></div>
                                    <span>Score < 40%</span>
                                </div>
                                <div class="legend-item">
                                    <div class="legend-color" style="background-color: #ffebee;"></div>
                                    <span>Descalificado por criterios eliminatorios</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Estadísticas rápidas
                        qualified = len(df[df['Estado'] != 'Descalificado'])
                        disqualified = len(df[df['Estado'] == 'Descalificado'])
                        high_scores = len(df[df['Score Final'].str.rstrip('%').astype(float) >= 70])
                        
                        stat1, stat2, stat3 = st.columns(3)
                        with stat1:
                            st.metric("Candidatos calificados", qualified)
                        with stat2:
                            st.metric("Candidatos descalificados", disqualified)
                        with stat3:
                            st.metric("Candidatos con score alto (≥70%)", high_scores)

            else:
                st.warning("No hay resultados para mostrar")

        except Exception as e:
            st.error("Error al mostrar los resultados. Verifique los datos y vuelva a intentar.")
            logging.error(f"Error in display_ranking: {str(e)}")