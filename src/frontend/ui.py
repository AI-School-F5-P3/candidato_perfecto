import streamlit as st
from pathlib import Path
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from hr_analysis_system import generar_informe_comparativo, CandidateProfile

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

class UIComponents:
    """Maneja todos los componentes de la interfaz de usuario"""
    @staticmethod
    def load_custom_css() -> None:
        """Carga estilos CSS personalizados"""
        try:
            css_path = Path(__file__).parent / 'style.css'
            with open(css_path) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except Exception as e:
            logging.warning(f"Could not load custom CSS: {str(e)}")

    @staticmethod
    def setup_page_config() -> None:
        """Configura las opciones generales de la página"""
        st.set_page_config(layout="wide", page_title="Sistema de Análisis de CVs")

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
            
            selected_candidates = []  # Lista para almacenar los candidatos seleccionados

            for idx, row in df.iterrows():
                expander_title = f"Ver datos del candidato: {row['Nombre Candidato']}"
                if row['Estado'] == 'Descalificado':
                    expander_title += " (Descalificado)"
                
                with st.expander(expander_title):
                    # Mostrar el estado de descalificación si corresponde
                    if row['Estado'] == 'Descalificado':
                        st.error(f"Razones de descalificación: {row['Razones Descalificación']}")
                    
                    # Mostrar los datos crudos del candidato
                    st.json(row['raw_data'])
                    
                    # Añadir checkbox para seleccionar el candidato
                    if row['Estado'] != 'Descalificado':  # Solo permitir seleccionar candidatos no descalificados
                        if st.checkbox(f"Seleccionar para informe comparativo: {row['Nombre Candidato']}", key=f"select_{idx}"):
                            # Añadir el candidato seleccionado a la lista
                            selected_candidates.append(
                                CandidateProfile(
                                    nombre_candidato=row['Nombre Candidato'],
                                    habilidades=row['Habilidades'],
                                    experiencia=row['Experiencia']
                                )
                            )

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
                
            # Aquí es donde agregamos el botón para generar el informe comparativo
            st.markdown('<div class="section-header">Generar Informe Comparativo</div>', unsafe_allow_html=True)
            
            # Botón para generar el informe comparativo
            if st.button('Generar Informe Comparativo'):
                if selected_candidates:
                    # Llamar a la función de generación de informe con los candidatos seleccionados
                    informe = generar_informe_comparativo(selected_candidates, job_profile)

                    # Mostrar el informe generado
                    st.text_area("Informe Comparativo Generado", value=informe, height=400)
                else:
                    st.warning("Por favor, seleccione al menos un candidato para generar el informe.")
            
        except Exception as e:
            st.error("Error al mostrar los resultados. Verifique los datos y vuelva a intentar.")
            logging.error(f"Error in display_ranking: {str(e)}")