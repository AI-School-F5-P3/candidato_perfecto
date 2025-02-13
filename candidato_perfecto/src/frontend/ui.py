# File: /candidato_perfecto/candidato_perfecto/src/frontend/ui.py

import streamlit as st

def load_custom_css():
    """Load custom CSS for the Streamlit application."""
    with open("src/frontend/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def setup_page_config():
    """Set up the Streamlit page configuration."""
    st.set_page_config(
        page_title="Sistema de Análisis de CVs",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def create_weight_sliders():
    """Create sliders for setting weights for different criteria."""
    st.sidebar.header("Ajuste de Pesos")
    habilidades = st.sidebar.slider("Peso para Habilidades", 0.0, 1.0, 0.25)
    experiencia = st.sidebar.slider("Peso para Experiencia", 0.0, 1.0, 0.25)
    formacion = st.sidebar.slider("Peso para Formación", 0.0, 1.0, 0.25)
    preferencias_reclutador = st.sidebar.slider("Peso para Preferencias del Reclutador", 0.0, 1.0, 0.25)

    total_weight = habilidades + experiencia + formacion + preferencias_reclutador
    return {
        "habilidades": habilidades,
        "experiencia": experiencia,
        "formacion": formacion,
        "preferencias_reclutador": preferencias_reclutador,
        "total_weight": total_weight
    }

def create_main_sections():
    """Create main sections for user input."""
    st.header("Análisis de Candidatos")
    
    job_file = st.file_uploader("Sube la descripción del trabajo (PDF o TXT)", type=["pdf", "txt"])
    important_skills = st.text_area("Habilidades Importantes (una por línea)")
    resume_files = st.file_uploader("Sube los CVs de los candidatos", type=["pdf", "txt"], accept_multiple_files=True)
    
    killer_criteria = {
        "min_experience": st.number_input("Experiencia mínima (años)", min_value=0),
        "max_experience": st.number_input("Experiencia máxima (años)", min_value=0),
        "required_skills": st.text_input("Habilidades requeridas (separadas por comas)")
    }
    
    return job_file, important_skills, resume_files, killer_criteria

def display_ranking(dataframe, job_profile):
    """Display the ranking DataFrame in the Streamlit app."""
    st.subheader("Ranking de Candidatos")
    st.dataframe(dataframe)
    st.write("Descripción del trabajo:")
    st.write(job_profile)