import streamlit as st
from pathlib import Path
from hr_analysis_system import JobProfile
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from frontend import comparative_analysis  # added import for comparative_analysis

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
    weights: Any = None  # Nuevo campo para pesos específicos (WeightSettings)

@dataclass
class UIInputs:
    """Almacena los inputs de la interfaz para la funcionalidad multivacante"""
    job_sections: List[JobSection]
    resume_files: List[Any]
    weights: WeightSettings
    # Se eliminan los campos de recruiter_skills y killer_criteria globales

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
        """Crea las secciones principales de la interfaz con soporte para múltiples vacantes"""
        job_sections = []
        with st.container():
            st.markdown('<div class="main-section">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Descripción(es) de la Vacante</div>', unsafe_allow_html=True)
            job_files = st.file_uploader(
                "Suba las descripciones del puesto (TXT o PDF)",
                type=['txt', 'pdf'],
                accept_multiple_files=True,
                key="job_upload_multi"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            if job_files:
                st.markdown("### Configurar cada vacante")
                for idx, job_file in enumerate(job_files):
                    with st.expander(f"Vacante {idx+1}: {job_file.name}"):
                        recruiter_skills = st.text_area(
                            "Preferencias del reclutador (una por línea)",
                            height=120,
                            key=f"skills_input_{idx}",
                            help="Ingrese las preferencias específicas para esta vacante."
                        )
                        killer_skills = st.text_area(
                            "Habilidades eliminatorias (una por línea)",
                            height=120,
                            key=f"killer_skills_input_{idx}",
                            help="Ingrese las habilidades obligatorias para esta vacante."
                        )
                        killer_experiencia = st.text_area(
                            "Experiencia eliminatoria (una por línea)",
                            height=120,
                            key=f"killer_exp_input_{idx}",
                            help="Ingrese la experiencia mínima requerida para esta vacante."
                        )
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
                        st.markdown("#### Configure los pesos para esta vacante (deben sumar 1.0)")
                        vac_hab = st.slider(
                            "Habilidades",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.3,
                            step=0.05,
                            key=f"vac_weight_habilidades_{idx}"
                        )
                        vac_exp = st.slider(
                            "Experiencia",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.3,
                            step=0.05,
                            key=f"vac_weight_experiencia_{idx}"
                        )
                        vac_for = st.slider(
                            "Formación",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.2,
                            step=0.05,
                            key=f"vac_weight_formacion_{idx}"
                        )
                        vac_pref = st.slider(
                            "Preferencias del Reclutador",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.2,
                            step=0.05,
                            key=f"vac_weight_preferencias_{idx}"
                        )
                        vac_total = round(vac_hab + vac_exp + vac_for + vac_pref, 2)
                        st.markdown(f"Total: **{vac_total}** (debe ser 1.0)")
                        if vac_total != 1.0:
                            st.error("⚠️ Los pesos no suman 1.0")
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
            
            # Sección de CVs
            with st.container():
                st.markdown('<div class="main-section">', unsafe_allow_html=True)
                st.markdown('<div class="section-header">CVs de Candidatos</div>', unsafe_allow_html=True)
                resume_files = st.file_uploader(
                    "Suba los CVs de los candidatos (TXT o PDF)",
                    type=['txt', 'pdf'],
                    accept_multiple_files=True,
                    key="cv_upload_multi"
                )
                st.markdown('</div>', unsafe_allow_html=True)
        
        weights = UIComponents.create_weight_sliders()
        return UIInputs(
            job_sections=job_sections,
            resume_files=resume_files,
            weights=weights
        )

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
            logging.error(f"Error in display_ranking: {str(e)})")