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
            skills_weight = st.slider(
                "Habilidades",
                min_value=0.0,
                max_value=1.0,
                value=0.4,
                step=0.05,
                key="skills_slider",
                label_visibility="visible"
            )
            experience_weight = st.slider(
                "Experiencia",
                min_value=0.0,
                max_value=1.0,
                value=0.25,
                step=0.05,
                key="exp_slider",
                label_visibility="visible"
            )
            education_weight = st.slider(
                "Educación",
                min_value=0.0,
                max_value=1.0,
                value=0.15,
                step=0.05,
                key="edu_slider",
                label_visibility="visible"
            )
            preferences_weight = st.slider(
                "Preferencias reclutador",
                min_value=0.0,
                max_value=1.0,
                value=0.2,
                step=0.05,
                key="pref_slider",
                label_visibility="visible"
            )
            
            total_weight = round(skills_weight + experience_weight + education_weight + preferences_weight, 2)
            
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
                "skills_weight": skills_weight,
                "experience_weight": experience_weight,
                "education_weight": education_weight,
                "preferences_weight": preferences_weight,
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
        
        # Recruiter Preferences Section
        st.markdown('<div class="main-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Preferencias del reclutador</div>', unsafe_allow_html=True)
        important_skills = st.text_area(
            "Aptitudes adicionales (una por línea)",
            height=120,
            key="skills_input"
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
    
    return job_file, important_skills, resume_files

def display_ranking(styled_df, job_profile):
    """Display ranking results and job requirements"""
    st.markdown('<div class="section-header">Ranking de Candidatos</div>', unsafe_allow_html=True)
    
    # Get the underlying DataFrame and remove raw_data for display
    df = styled_df.data
    display_df = df.copy()
    raw_data = display_df.pop('raw_data')  # Remove and store raw_data
    
    # Display the DataFrame without raw_data
    st.dataframe(
        display_df.style.background_gradient(
            subset=['Puntuación Total'],
            cmap='RdYlGn'
        ).format({
            'Puntuación Total': '{:.2%}',
            'Habilidades Requeridas': '{:.2%}',
            'Habilidades Preferentes': '{:.2%}',
            'Experiencia': '{:.2%}',
            'Educación': '{:.2%}'
        }),
        use_container_width=True
    )
    
    # Create expandable sections for each candidate's raw data
    for idx, (name, data) in enumerate(zip(df['Nombre Candidato'], raw_data)):
        with st.expander(f"Ver datos del candidato: {name}"):
            st.json(data)

    with st.expander("Ver Requisitos del Puesto"):
        st.json({
            "título": job_profile.title,
            "habilidades_requeridas": job_profile.required_skills,
            "habilidades_preferentes": job_profile.preferred_skills,
            "años_de_experiencia": job_profile.experience_years,
            "nivel_educativo": job_profile.education_level,
            "responsabilidades": job_profile.responsibilities,
            "conocimientos_industria": job_profile.industry_knowledge
        })