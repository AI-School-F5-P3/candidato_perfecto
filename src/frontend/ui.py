import streamlit as st
from hr_analysis_system import JobProfile
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import pandas as pd
from datetime import datetime
from utils.utilities import export_rankings_to_excel
from io import BytesIO

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
            
            # Validación de archivos duplicados en vacantes
            if job_files:
                duplicates, job_files = UIComponents._check_duplicate_files(job_files)
                if duplicates:
                    st.warning(f"⚠️ Se ignoraron los siguientes archivos duplicados de vacantes: {', '.join(duplicates)}")
            
            # Validación del límite de vacantes
            if job_files and len(job_files) > 5:
                st.warning("⚠️ Máximo 5 vacantes simultáneas para garantizar rendimiento")
                job_files = job_files[:5]  # Limitar a las primeras 5 vacantes
            
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

                # Validación de archivos duplicados en CVs
                if resume_files:
                    duplicates, resume_files = UIComponents._check_duplicate_files(resume_files)
                    if duplicates:
                        st.warning(f"⚠️ Se ignoraron los siguientes CVs duplicados: {', '.join(duplicates)}")
        
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
            st.markdown('<div class="section-header">Resultados por Vacante</div>', unsafe_allow_html=True)
            
            # Add Export to Excel button before the tabs
            if len(df_list) > 0:
                col1, col2 = st.columns([3, 1])
                with col2:
                    # Crear el buffer de Excel
                    buffer = BytesIO()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"resultados_ranking_{timestamp}.xlsx"
                    
                    # Preparar los datos para Excel
                    vacancy_names = [f"Vacante {i+1}" for i in range(len(df_list))]
                    success = export_rankings_to_excel(df_list, vacancy_names, buffer)
                    
                    if success:
                        st.download_button(
                            label="📥 Exportar a Excel",
                            data=buffer.getvalue(),
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_excel"
                        )

            # Crear pestañas para cada vacante
            if len(df_list) > 0:
                tabs = st.tabs([f"Vacante {i+1}: {job_profiles[i].nombre_vacante}" for i in range(len(df_list))])
                
                for idx, (tab, df, job_profile, recruiter_preferences, killer_criteria) in enumerate(
                    zip(tabs, df_list, job_profiles, recruiter_preferences_list, killer_criteria_list)):
                    
                    with tab:
                        st.markdown(f"### Resultados para: {job_profile.nombre_vacante}")
                        
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
                        
                        # Mostrar leyenda de colores
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
                                <div style="width: 20px; height: 20px; background-color: #ffe6e6; margin-right: 5px;"></div>
                                <span>Score < 40%</span>
                            </div>
                            <div style="display: flex; align-items: center;">
                                <div style="width: 20px; height: 20px; background-color: #ffebee; margin-right: 5px;"></div>
                                <span>Candidato descalificado por criterios eliminatorios</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            else:
                st.warning("No hay resultados para mostrar")

        except Exception as e:
            st.error("Error al mostrar los resultados. Verifique los datos y vuelva a intentar.")
            logging.error(f"Error in display_ranking: {str(e)}")