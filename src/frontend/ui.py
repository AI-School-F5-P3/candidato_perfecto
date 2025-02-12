import streamlit as st
from pathlib import Path
import logging

def load_custom_css():
    """Load custom CSS file from frontend directory"""
    try:
        css_path = Path(__file__).parent / 'style.css'
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        logging.warning(f"Could not load custom CSS: {str(e)}")

def setup_page_config():
    """Initialize page configuration"""
    st.set_page_config(layout="wide", page_title="Sistema de Análisis de CVs")

def create_weight_sliders():
    """Create and manage weight sliders in sidebar"""
    with st.sidebar:
        # Make the sidebar even more compact
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
                line-height: 1 !important;
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
            habilidades_weight = st.slider(
                "Habilidades",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.05,
                key="habilidades_slider",
                label_visibility="visible"
            )
            experiencia_weight = st.slider(
                "Experiencia",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.05,
                key="exp_slider",
                label_visibility="visible"
            )
            formacion_weight = st.slider(
                "Formación",
                min_value=0.0,
                max_value=1.0,
                value=0.2,
                step=0.05,
                key="formacion_slider",
                label_visibility="visible"
            )
            preferencias_reclutador_weight = st.slider(
                "Preferencias del Reclutador",
                min_value=0.0,
                max_value=1.0,
                value=0.2,
                step=0.05,
                key="preferencias_slider",
                label_visibility="visible"
            )
            
            total_weight = round(
                habilidades_weight + 
                experiencia_weight + 
                formacion_weight + 
                preferencias_reclutador_weight, 
                2
            )
            
            # Ultra compact total weight display
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

            return {
                "habilidades": habilidades_weight,
                "experiencia": experiencia_weight,
                "formacion": formacion_weight,
                "preferencias_reclutador": preferencias_reclutador_weight,
                "total_weight": total_weight
            }
            
def create_main_sections():
    """Create all main content sections in vertical layout"""
    # Container for better spacing
    with st.container():
        # Job Description Section
        st.markdown('<div class="main-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Descripción del Puesto</div>', unsafe_allow_html=True)
        job_file = st.file_uploader(
            "Suba la descripción del puesto (TXT o PDF)", 
            type=['txt', 'pdf'],
            key="job_upload"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Recruiter Preferences Section (Optional)
        st.markdown('<div class="main-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Preferencias del reclutador (Opcional)</div>', unsafe_allow_html=True)
        important_skills = st.text_area(
            "Preferencias del reclutador (una por línea)",
            height=120,
            key="skills_input",
            help="Campo opcional. Puede dejarlo vacío si no hay preferencias específicas."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Killer Criteria Section (Optional)
        st.markdown('<div class="main-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Criterios Eliminatorios (Opcional)</div>', unsafe_allow_html=True)
        
        # Create two columns for killer criteria
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
        
        # CV Upload Section
        st.markdown('<div class="main-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">CVs de Candidatos</div>', unsafe_allow_html=True)
        resume_files = st.file_uploader(
            "Suba los CVs de los candidatos (TXT o PDF)", 
            type=['txt', 'pdf'],
            accept_multiple_files=True,
            key="cv_upload"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Safely handle empty inputs by providing empty lists as defaults
    important_skills = important_skills or ""  # Convert None to empty string if needed
    killer_habilidades = killer_habilidades or ""
    killer_experiencia = killer_experiencia or ""
    
    # Create killer criteria dictionary with safe empty list defaults
    killer_criteria = {
        "killer_habilidades": [skill.strip() for skill in killer_habilidades.split('\n') if skill.strip()],
        "killer_experiencia": [exp.strip() for exp in killer_experiencia.split('\n') if exp.strip()]
    }
    
    return job_file, important_skills, resume_files, killer_criteria

def display_ranking(df, job_profile):
    """Display ranking results and job requirements"""
    try:
        st.markdown('<div class="section-header">Ranking de Candidatos</div>', unsafe_allow_html=True)
        
        # Create a clean display version without raw_data
        display_df = df.copy()
        raw_data = display_df.pop('raw_data')
        
        # Create the styled DataFrame with background colors
        def style_row(row):
            styles = []
            is_disqualified = row['Estado'] == 'Descalificado'
            for idx, _ in enumerate(row):
                if is_disqualified:
                    styles.append('background-color: #ffebee')  # Light red for disqualified
                elif row.index[idx] == 'Score Final':
                    score = float(row['Score Final'].rstrip('%')) / 100
                    if score >= 0.7:
                        styles.append('background-color: #e6ffe6')  # Green
                    elif score >= 0.4:
                        styles.append('background-color: #fff3e6')  # Orange
                    else:
                        styles.append('background-color: #ffe6e6')  # Red
                else:
                    styles.append('')
            return styles
        
        # Apply styling
        styled_df = display_df.style.apply(style_row, axis=1)
        
        # Display the DataFrame
        st.dataframe(styled_df, use_container_width=True)
        
        # Add legend for score colors and disqualification
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
        
        # Display expandable sections
        for idx, row in df.iterrows():
            expander_title = f"Ver datos del candidato: {row['Nombre Candidato']}"
            if row['Estado'] == 'Descalificado':
                expander_title += " (Descalificado)"
            
            with st.expander(expander_title):
                if row['Estado'] == 'Descalificado':
                    st.error(f"Razones de descalificación: {row['Razones Descalificación']}")
                st.json(row['raw_data'])

        with st.expander("Ver Requisitos del Puesto"):
            st.json({
                "nombre_vacante": job_profile.nombre_vacante,
                "habilidades": job_profile.habilidades,
                "experiencia": job_profile.experiencia,
                "formacion": job_profile.formacion,
                "habilidades_preferidas": job_profile.habilidades_preferidas
            })
            
    except Exception as e:
        logging.error(f"Error in display_ranking: {str(e)}")
        st.error("Error al mostrar los resultados. Verifique los datos y vuelva a intentar.")