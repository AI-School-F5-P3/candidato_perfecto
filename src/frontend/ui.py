import streamlit as st
from pathlib import Path
from hr_analysis_system import JobProfile
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from frontend import comparative_analysis  # added import for comparative_analysis
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
    weights: Any = None  # Nuevo campo para pesos específicos (WeightSettings)

@dataclass
class UIInputs:
    """Almacena los inputs de la interfaz para la funcionalidad multivacante"""
    job_sections: List[JobSection]
    resume_files: List[Any]
    # Se eliminó el campo global weights

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
        
        # Se elimina la asignación de pesos globales ya que se usan los de cada vacante
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

                        # Gráfico de radar para esta vacante
                        st.markdown("### Distribución de Competencias Clave")
                        top_candidates = df[df['Estado'] == 'Calificado'].head(3)
                        if not top_candidates.empty:
                            categories = ['Habilidades', 'Experiencia', 'Formación', 'Preferencias']
                            fig = go.Figure()
                            for _, row in top_candidates.iterrows():
                                scores = [
                                    float(row['Score Habilidades'].rstrip('%'))/100,
                                    float(row['Score Experiencia'].rstrip('%'))/100,
                                    float(row['Score Formación'].rstrip('%'))/100,
                                    float(row['Score Preferencias'].rstrip('%'))/100
                                ]
                                fig.add_trace(go.Scatterpolar(
                                    r=scores,
                                    theta=categories,
                                    fill='toself',
                                    name=row['Nombre Candidato']
                                ))
                            fig.update_layout(
                                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                                showlegend=True,
                                margin=dict(l=20, r=20, t=40, b=20)
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        # Detalles de los candidatos para esta vacante
                        st.markdown("### Detalles de Candidatos")
                        for idx, row in df.iterrows():
                            expander_title = f"Ver datos del candidato: {row['Nombre Candidato']}"
                            if row['Estado'] == 'Descalificado':
                                expander_title += " (Descalificado)"
                            
                            with st.expander(expander_title):
                                if row['Estado'] == 'Descalificado':
                                    st.error(f"Razones de descalificación: {row['Razones Descalificación']}")
                                await display_candidate_details(row['raw_data'], job_profile)

                        # Expandibles de información adicional
                        with st.expander("🔍 Cómo se calculan los scores"):
                            # ... (mantener el código existente del expander de scores)
                            pass

                        with st.expander("Ver Requisitos del Puesto"):
                            # ... (mantener el código existente del expander de requisitos)
                            pass

                        with st.expander("Ver Preferencias del Reclutador"):
                            # ... (mantener el código existente del expander de preferencias)
                            pass

                        with st.expander("Ver Criterios Eliminatorios"):
                            # ... (mantener el código existente del expander de criterios)
                            pass

            else:
                st.warning("No hay resultados para mostrar")

        except Exception as e:
            st.error("Error al mostrar los resultados. Verifique los datos y vuelva a intentar.")
            logging.error(f"Error in display_ranking: {str(e)}")

# Reemplazar la función display_candidate_details existente por la siguiente:
import uuid  # Importar uuid para generar identificadores únicos

import hashlib

import ast  # Nuevo importe

import json

async def display_candidate_details(raw_data: any, job_profile: JobProfile) -> None:
    """Muestra detalles del candidato sin análisis GPT"""
    import json
    import hashlib
    
    def safe_deserialize(data):
        if isinstance(data, dict):
            return data
        
        if isinstance(data, str):
            cleaned_data = data.strip()
            try:
                return json.loads(cleaned_data)
            except json.JSONDecodeError:
                try:
                    import ast
                    return ast.literal_eval(cleaned_data)
                except:
                    import re
                    nombre_match = re.search(r'nombre["\']?\s*:\s*["\']([^"\']+)["\']', cleaned_data, re.I)
                    habilidades_match = re.findall(r'habilidades["\']?\s*:\s*\[(.*?)\]', cleaned_data, re.I | re.S)
                    experiencia_match = re.findall(r'experiencia["\']?\s*:\s*\[(.*?)\]', cleaned_data, re.I | re.S)
                    formacion_match = re.findall(r'formacion["\']?\s*:\s*\[(.*?)\]', cleaned_data, re.I | re.S)
                    
                    return {
                        'nombre_candidato': nombre_match.group(1) if nombre_match else 'Nombre no disponible',
                        'habilidades': [h.strip() for h in habilidades_match[0].split(',')] if habilidades_match else [],
                        'experiencia': [e.strip() for e in experiencia_match[0].split(',')] if experiencia_match else [],
                        'formacion': [f.strip() for f in formacion_match[0].split(',')] if formacion_match else [],
                        'raw_text': cleaned_data
                    }
        return {'error': 'No se pudieron procesar los datos', 'raw_data': str(data)}

    def normalize_list(data):
        if isinstance(data, list):
            return [str(item).strip() for item in data if item]
        elif isinstance(data, str):
            return [data.strip()]
        return []

    try:
        # Procesar datos del candidato
        data_dict = safe_deserialize(raw_data)
        
        if not data_dict or (isinstance(data_dict, dict) and 'error' in data_dict):
            st.error("No se pudieron procesar los datos del candidato correctamente")
            st.write("Datos originales:", raw_data)
            return

        # Normalizar datos
        nombre = str(data_dict.get('nombre_candidato', 'Nombre no disponible'))
        habilidades = normalize_list(data_dict.get('habilidades', []))
        experiencia = normalize_list(data_dict.get('experiencia', []))
        formacion = normalize_list(data_dict.get('formacion', []))

        # Mostrar datos técnicos
        st.markdown("### 📌 Datos Técnicos")
        cols = st.columns(3)
        
        with cols[0]:
            st.markdown("**Habilidades**")
            for hab in habilidades:
                st.write(f"- {hab}")
            
        with cols[1]:
            st.markdown("**Experiencia**")
            for exp in experiencia:
                st.write(f"- {exp}")
                
        with cols[2]:
            st.markdown("**Formación**")
            for form in formacion:
                st.write(f"- {form}")

    except Exception as e:
        st.error(f"Error procesando datos del candidato: {str(e)}")
        logging.error(f"Error en display_candidate_details: {str(e)}")
        if raw_data:
            st.write("Datos originales:", raw_data)