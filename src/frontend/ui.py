import streamlit as st
from pathlib import Path
from src.hr_analysis_system import JobProfile
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from src.frontend import comparative_analysis  # added import for comparative_analysis

@dataclass
class WeightSettings:
    """Configuración de pesos para diferentes componentes de puntuación"""
    habilidades: float
    experiencia: float
    formacion: float
    preferencias_reclutador: float
    total_weight: float

@dataclass
class UIInputs:
    """Almacena todos los inputs de usuario de la interfaz"""
    job_file: object
    recruiter_skills: str
    resume_files: List[object]
    killer_criteria: Dict[str, List[str]]
    weights: WeightSettings
    important_skills: str

class DriveFileSelector:
    """Componente para selección de archivos de Drive con búsqueda y desplegable"""
    @staticmethod
    def render_search_and_select(files: dict) -> List[str]:
        if not files:
            return []
            
        # Por defecto, todos los archivos están seleccionados
        if 'drive_search' not in st.session_state:
            st.session_state.drive_search = ""
        if 'selected_files' not in st.session_state:
            st.session_state.selected_files = list(files.keys())
        
        # Estilo personalizado para el contenedor
        st.markdown("""
            <style>
            .drive-selector {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
            }
            .file-count {
                background-color: #e7f3fe;
                border-radius: 20px;
                padding: 5px 15px;
                color: #0066cc;
                font-weight: bold;
                display: inline-block;
            }
            .search-box {
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 5px;
            }
            .button-container {
                display: flex;
                gap: 10px;
                margin: 10px 0;
            }
            </style>
        """, unsafe_allow_html=True)
            
        # Layout principal con diseño mejorado
        st.markdown('<div class="drive-selector">', unsafe_allow_html=True)
        
        # Cabecera con contador
        count_col, search_col = st.columns([1, 3])
        with count_col:
            st.markdown(
                f'<div class="file-count">📄 {len(st.session_state.selected_files)} / {len(files)} CVs</div>', 
                unsafe_allow_html=True
            )
        
        with search_col:
            search_term = st.text_input(
                "🔍 Filtrar CVs por nombre",
                value=st.session_state.drive_search,
                key="drive_search_input",
                placeholder="Escriba para filtrar..."
            ).lower()
        
        # Filtrar archivos según búsqueda
        filtered_files = {
            k: v for k, v in files.items() 
            if search_term in k.lower()
        }
        
        # Desplegable para lista de CVs con diseño mejorado
        with st.expander("📋 Gestionar selección de CVs", expanded=False):
            select_col1, select_col2 = st.columns(2)
            with select_col1:
                if st.button("✅ Seleccionar todos", 
                            use_container_width=True,
                            type="primary"):
                    st.session_state.selected_files = list(filtered_files.keys())
                    st.rerun()
            with select_col2:
                if st.button("❌ Deseleccionar todos", 
                            use_container_width=True):
                    st.session_state.selected_files = []
                    st.rerun()
            
            st.markdown("---")
            
            # Grid de checkboxes con 2 columnas
            col1, col2 = st.columns(2)
            files_list = list(filtered_files.keys())
            mid_point = len(files_list) // 2
            
            for i, column in enumerate([col1, col2]):
                with column:
                    start_idx = i * mid_point
                    end_idx = (i + 1) * mid_point if i == 0 else len(files_list)
                    
                    for filename in files_list[start_idx:end_idx]:
                        display_name = filename.split(" (Modificado")[0]
                        is_selected = st.checkbox(
                            f"📄 {display_name}",
                            value=True,  # Siempre marcado por defecto
                            key=f"file_{filename}"
                        )
                        if is_selected and filename not in st.session_state.selected_files:
                            st.session_state.selected_files.append(filename)
                        elif not is_selected and filename in st.session_state.selected_files:
                            st.session_state.selected_files.remove(filename)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return st.session_state.selected_files

class UIComponents:
    """Maneja todos los componentes de la interfaz de usuario"""
    @staticmethod
    def load_custom_css() -> None:
        """Carga estilos CSS personalizados"""
        st.markdown(
            """
            <style>
            .title {
                font-size: 2rem;
                font-weight: bold;
                margin-bottom: 1rem;
            }
            .section-header {
                font-size: 1.5rem;
                font-weight: bold;
                margin-top: 2rem;
                margin-bottom: 1rem;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    @staticmethod
    def setup_page_config() -> None:
        """Configura la página de Streamlit"""
        st.set_page_config(page_title="El candidato perfecto", layout="wide")

    @staticmethod
    def create_weight_sliders() -> WeightSettings:
        """Crea y gestiona los deslizadores de peso en la barra lateral"""
        with st.sidebar:
            # Aplicar estilo compacto a la barra lateral
            st.markdown("""
                <style>
                [data-testid="stSidebar"] {
                    min-width: 180px !important;
                    max-width: 250px !important;
                }
                div[data-testid="stVerticalBlock"] > div {
                    padding: 0 !important;
                    margin: 0 !important;
                }
                .stSlider [data-baseweb="slider"] {
                    margin: 0 !important;
                    padding: 0.25rem 0 !important;
                }
                label[data-testid="stWidgetLabel"] {
                    font-size: 0.8em !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                [data-testid="stText"] {
                    font-size: 0.8em !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                .section-header {
                    margin: 0 0 0.25rem 0 !important;
                    padding: 0 0 0.25rem 0 !important;
                }
                </style>
                """, 
                unsafe_allow_html=True
            )
            
            st.markdown('<div class="section-header">Pesos por sección</div>', unsafe_allow_html=True)
            
            with st.container():
                st.markdown('<div class="weights-container">', unsafe_allow_html=True)
                habilidades = st.slider(
                    "Habilidades",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.05,
                    key="habilidades_slider"
                )
                experiencia = st.slider(
                    "Experiencia",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.05,
                    key="exp_slider"
                )
                formacion = st.slider(
                    "Formación",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.2,
                    step=0.05,
                    key="formacion_slider"
                )
                preferencias = st.slider(
                    "Preferencias del Reclutador",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.2,
                    step=0.05,
                    key="preferencias_slider"
                )
                
                total_weight = round(habilidades + experiencia + formacion + preferencias, 2)
                
                st.markdown(
                    f"""
                    <div style='
                        background-color: #f0f2f6;
                        padding: 0.25rem;
                        border-radius: 4px;
                        margin: 0.25rem 0;
                        font-size: 0.8em;
                        text-align: center;
                        line-height: 1.2;
                    '>
                        Suma: <b>{total_weight}</b>
                        <div style='font-size: 0.75em; color: #666;'>
                            (debe ser 1.0)
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                if total_weight != 1.0:
                    st.error("⚠️", icon="⚠️")

                return WeightSettings(
                    habilidades=habilidades,
                    experiencia=experiencia,
                    formacion=formacion,
                    preferencias_reclutador=preferencias,
                    total_weight=total_weight
                )

    @staticmethod
    def create_main_sections() -> UIInputs:
        """Crea las secciones principales de la interfaz"""
        with st.container():
            # Sección de Descripción del Puesto
            st.markdown('<div class="main-section">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Descripción del Puesto</div>', unsafe_allow_html=True)
            job_file = st.file_uploader(
                "Suba la descripción del puesto (TXT o PDF)", 
                type=['txt', 'pdf'],
                key="job_upload"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Sección de Preferencias del Reclutador
            st.markdown('<div class="main-section">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Preferencias del reclutador (Opcional)</div>', unsafe_allow_html=True)
            recruiter_skills = st.text_area(
                "Preferencias del reclutador (una por línea)",
                height=120,
                key="skills_input",
                help="Campo opcional. Puede dejarlo vacío si no hay preferencias específicas."
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Sección de Criterios Eliminatorios
            st.markdown('<div class="main-section">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Criterios Eliminatorios (Opcional)</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                killer_habilidades = st.text_area(
                    "Habilidades obligatorias (una por línea)",
                    height=120,
                    key="killer_skills_input",
                    help="Campo opcional. Puede dejarlo vacío si no hay habilidades obligatorias."
                )
                
            with col2:
                killer_experiencia = st.text_area(
                    "Experiencia obligatoria (una por línea)",
                    height=120,
                    key="killer_exp_input",
                    help="Campo opcional. Puede dejarlo vacío si no hay experiencia obligatoria."
                )
                
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Sección de Subida de CVs
            st.markdown('<div class="main-section">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">CVs de Candidatos</div>', unsafe_allow_html=True)
            resume_files = st.file_uploader(
                "Suba los CVs de los candidatos (TXT o PDF)", 
                type=['txt', 'pdf'],
                accept_multiple_files=True,
                key="cv_upload"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Procesar criterios eliminatorios
        killer_criteria = {
            "killer_habilidades": [
                skill.strip() 
                for skill in (killer_habilidades or "").split('\n') 
                if skill.strip()
            ],
            "killer_experiencia": [
                exp.strip() 
                for exp in (killer_experiencia or "").split('\n') 
                if exp.strip()
            ]
        }

        weights = UIComponents.create_weight_sliders()
        
        return UIInputs(
            job_file=job_file,
            recruiter_skills=recruiter_skills,
            resume_files=resume_files,
            killer_criteria=killer_criteria,
            weights=weights,
            important_skills=recruiter_skills  # Asegurarse de incluir este campo
        )

    @staticmethod
    def render_drive_section():
        """Renderiza la sección de selección de archivos de Drive"""
        st.markdown("---")
        st.subheader("Cargar CVs desde Google Drive")
        
        if 'drive_files' in st.session_state and st.session_state.drive_files:
            selected_files = DriveFileSelector.render_search_and_select(st.session_state.drive_files)
            return selected_files
        return []

    @staticmethod
    def display_ranking(df, job_profile, recruiter_preferences, killer_criteria) -> None:
        """Muestra el ranking de candidatos y detalles de la búsqueda"""
        try:
            if 'current_data' not in st.session_state:
                st.session_state.current_data = {
                    'df': df,
                    'job_profile': job_profile,
                    'recruiter_preferences': recruiter_preferences,
                    'killer_criteria': killer_criteria
                }

            st.markdown('<div class="section-header">Ranking de Candidatos</div>', unsafe_allow_html=True)
            display_df = df.copy()
            raw_data = display_df.pop('raw_data')

            def style_row(row):
                styles = []
                is_disqualified = row['Estado'] == 'Descalificado'
                for idx, _ in enumerate(row):
                    if is_disqualified:
                        styles.append('background-color: #ffebee')
                    elif row.index[idx] == 'Score Final':
                        score = float(row['Score Final'].rstrip('%')) / 100
                        if score >= 0.7:
                            styles.append('background-color: #e6ffe6')
                        elif score >= 0.4:
                            styles.append('background-color: #fff3e6')
                        else:
                            styles.append('background-color: #ffe6e6')
                    else:
                        styles.append('')
                return styles

            styled_df = display_df.style.apply(style_row, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            st.markdown("""
            <div style="margin: 10px 0; font-size: 0.8em;">
                <div style="display: flex; gap: 20px; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center;">
                        <div style="width: 20px; height: 20px; background-color: #e6ffe6; margin-right: 5px;"></div>
                        <span>Score ≥ 70%</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 20px; height: 20px; background-color: #fff3e6; margin-right: 5px;"></div>
                        <span>40% ≤ Score < 70%</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 20px; height: 20px; background-color: #ffe6e6; margin-right: 5px;"></div>
                        <span>Score < 40%</span>
                    </div>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: #ffebee; margin-right: 5px;"></div>
                    <span>Candidato descalificado por criterios eliminatorios</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Always show candidate details
            for idx, row in df.iterrows():
                expander_title = f"Ver datos del candidato: {row['Nombre Candidato']}"
                if row['Estado'] == 'Descalificado':
                    expander_title += " (Descalificado)"
                
                with st.expander(expander_title):
                    if row['Estado'] == 'Descalificado':
                        st.error(f"Razones de descalificación: {row['Razones Descalificación']}")
                    st.json(row['raw_data'])

            # Show requirement details in expandable sections
            with st.expander("Ver Requisitos del Puesto"):
                st.json({
                    "nombre_vacante": job_profile.nombre_vacante,
                    "habilidades": job_profile.habilidades,
                    "experiencia": job_profile.experiencia,
                    "formacion": job_profile.formacion
                })

            with st.expander("Ver Preferencias del Reclutador"):
                st.json({
                    "habilidades_preferidas": recruiter_preferences.habilidades_preferidas
                })

            with st.expander("Ver Criterios Eliminatorios"):
                st.json({
                    "habilidades_obligatorias": killer_criteria.get("killer_habilidades", []),
                    "experiencia_obligatoria": killer_criteria.get("killer_experiencia", [])
                })
            
        except Exception as e:
            st.error("Error al mostrar los resultados. Verifique los datos y vuelva a intentar.")
            logging.error(f"Error in display_ranking: {str(e)}")
