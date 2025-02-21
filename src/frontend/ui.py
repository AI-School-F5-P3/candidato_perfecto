import streamlit as st
from pathlib import Path
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass

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

            # Sección principal de ranking
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
            
            # Leyenda del ranking
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

            # Tabs para mostrar detalles
            tab1, tab2, tab3, tab4 = st.tabs([
                "Detalles de Candidatos", 
                "Requisitos del Puesto", 
                "Preferencias del Reclutador",
                "Criterios Eliminatorios"
            ])

            # Tab 1: Detalles de Candidatos
            with tab1:
                for idx, row in df.iterrows():
                    st.markdown(f"### {row['Nombre Candidato']}")
                    if row['Estado'] == 'Descalificado':
                        st.error(f"Razones de descalificación: {row['Razones Descalificación']}")
                    st.json(row['raw_data'])
                    st.markdown("---")

            # Tab 2: Requisitos del Puesto
            with tab2:
                st.json({
                    "nombre_vacante": job_profile.nombre_vacante,
                    "habilidades": job_profile.habilidades,
                    "experiencia": job_profile.experiencia,
                    "formacion": job_profile.formacion
                })

            # Tab 3: Preferencias del Reclutador
            with tab3:
                st.json({
                    "habilidades_preferidas": recruiter_preferences.habilidades_preferidas
                })

            # Tab 4: Criterios Eliminatorios
            with tab4:
                st.json({
                    "habilidades_obligatorias": killer_criteria.get("killer_habilidades", []),
                    "experiencia_obligatoria": killer_criteria.get("killer_experiencia", [])
                })
                
        except Exception as e:
            st.error("Error al mostrar los resultados. Verifique los datos y vuelva a intentar.")
            logging.error(f"Error in display_ranking: {str(e)}")

# Añadir nueva clase para manejar múltiples vacantes
class VacancySection:
    """Maneja la interfaz para múltiples descripciones de puestos"""
    @staticmethod
    def create_vacancy_section():
        """Maneja la interfaz para múltiples descripciones de puestos"""
        st.markdown('<div class="section-header">Descripciones de Puestos</div>', unsafe_allow_html=True)
        
        
        # Inicializar el estado de las vacantes si no existe
        if 'vacancies' not in st.session_state:
            st.session_state.vacancies = [{
                'id': 0,
                'weights': {
                    'habilidades': 0.3,
                    'experiencia': 0.3,
                    'formacion': 0.2,
                    'preferencias_reclutador': 0.2
                }
            }]
            
        # Contenedor para vacantes
        for i, vacancy in enumerate(st.session_state.vacancies):
            with st.expander(f"📋 Vacante {i + 1}", expanded=True):
                # Sección de archivo
                vacancy['job_file'] = st.file_uploader(
                    "Descripción del puesto (TXT o PDF)",
                    type=['txt', 'pdf'],
                    key=f"job_upload_{i}"
                )
                
                # Sección de pesos con colores
                st.markdown("### 🎚️ Pesos de Evaluación")
                
                # Columnas para los pesos
                col1, col2 = st.columns(2)
                
                with col1:
                    vacancy['weights']['habilidades'] = st.slider(
                        "Habilidades 💡",
                        0.0, 1.0, 
                        vacancy['weights'].get('habilidades', 0.3),
                        0.05,
                        key=f"w_hab_{i}"
                    )
                    
                    vacancy['weights']['formacion'] = st.slider(
                        "Formación 📚",
                        0.0, 1.0, 
                        vacancy['weights'].get('formacion', 0.2),
                        0.05,
                        key=f"w_form_{i}"
                    )
                
                with col2:
                    vacancy['weights']['experiencia'] = st.slider(
                        "Experiencia 💼",
                        0.0, 1.0, 
                        vacancy['weights'].get('experiencia', 0.3),
                        0.05,
                        key=f"w_exp_{i}"
                    )
                    
                    vacancy['weights']['preferencias_reclutador'] = st.slider(
                        "Preferencias 👥",
                        0.0, 1.0, 
                        vacancy['weights'].get('preferencias_reclutador', 0.2),
                        0.05,
                        key=f"w_pref_{i}"
                    )
                
                # Cálculo y visualización del total
                total = sum(vacancy['weights'].values())
                if total == 1.0:
                    st.success(f"✅ Total: {total:.2f}")
                else:
                    st.error(f"⚠️ Total: {total:.2f} (debe ser 1.0)")
                
                # Sección de criterios
                st.markdown("### 📋 Criterios de Evaluación")
                
                # Preferencias del reclutador
                vacancy['recruiter_skills'] = st.text_area(
                    "Preferencias del reclutador 👥",
                    value=vacancy.get('recruiter_skills', ''),
                    height=100,
                    placeholder="Escribe una preferencia por línea",
                    key=f"skills_{i}"
                )
                
                # Criterios obligatorios en columnas
                col1, col2 = st.columns(2)
                with col1:
                    vacancy['killer_habilidades'] = st.text_area(
                        "Habilidades obligatorias ⭐",
                        value=vacancy.get('killer_habilidades', ''),
                        height=100,
                        placeholder="Una habilidad por línea",
                        key=f"killer_skills_{i}"
                    )
                
                with col2:
                    vacancy['killer_experiencia'] = st.text_area(
                        "Experiencia obligatoria ⭐",
                        value=vacancy.get('killer_experiencia', ''),
                        height=100,
                        placeholder="Una experiencia por línea",
                        key=f"killer_exp_{i}"
                    )
                
                # Botón para eliminar vacante
                if len(st.session_state.vacancies) > 1:
                    if st.button("🗑️ Eliminar esta vacante", key=f"delete_{i}"):
                        st.session_state.vacancies.pop(i)
                        st.rerun()
        
        # Botón para añadir nueva vacante
        if st.button("➕ Añadir Nueva Vacante"):
            st.session_state.vacancies.append({
                'id': len(st.session_state.vacancies),
                'weights': {
                    'habilidades': 0.3,
                    'experiencia': 0.3,
                    'formacion': 0.2,
                    'preferencias_reclutador': 0.2
                }
            })
            st.rerun()