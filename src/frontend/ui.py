import streamlit as st
from pathlib import Path
from src.hr_analysis_system import JobProfile
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

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
    important_skills: str
    resume_files: List[object]
    killer_criteria: Dict[str, List[str]]
    weights: WeightSettings

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
            st.markdown(
                """
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
                
                # Mostrar el peso total
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
            important_skills = st.text_area(
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
            important_skills=important_skills,
            resume_files=resume_files,
            killer_criteria=killer_criteria,
            weights=weights
        )

    @staticmethod
    def display_ranking(df: pd.DataFrame, job_profile: JobProfile) -> None:
        """Muestra el ranking de candidatos"""
        st.markdown('<div class="section-header">Ranking de Candidatos</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        
        # Botón para ir al análisis comparativo
        if st.button("Ir al análisis comparativo"):
            st.session_state['page'] = 'comparative_analysis'
            st.experimental_set_query_params(page='comparative_analysis')

    @staticmethod
    def display_comparative_report(df: pd.DataFrame) -> None:
        """Muestra el informe comparativo de candidatos"""
        try:
            st.markdown('<div class="section-header">Informe Comparativo de Candidatos</div>', unsafe_allow_html=True)
            
            # Mostrar el DataFrame comparativo
            st.dataframe(df, use_container_width=True)
            
            # Generar gráficos comparativos
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Nombre Candidato', y='Score Final', data=df, ax=ax)  # Cambia a 'Nombre Candidato'
            ax.set_title('Comparación de Scores entre Candidatos')
            ax.set_xlabel('Nombre del Candidato')
            ax.set_ylabel('Score')
            st.pyplot(fig)
            
            # Mostrar el texto generado por el LLM
            for idx, row in df.iterrows():
                st.markdown(f"### Análisis para {row['Nombre Candidato']}")
                st.write(row['analysis_result'])
            
        except Exception as e:
            logging.error(f"Error in display_comparative_report: {str(e)}")
            st.error("Error al mostrar el informe comparativo. Verifique los datos y vuelva a intentar.")