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
                    st.markdown("Detalles del candidato:")
                    display_candidate_details(row['raw_data'])

            # =============================================
            # Nuevo: Gráfico radar para competencias clave
            # =============================================
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
            else:
                st.info("No hay candidatos calificados para mostrar el gráfico de competencias")

            # =============================================
            # Nuevo: Explicación de ponderaciones
            # =============================================
            with st.expander("🔍 Cómo se calculan los scores", expanded=False):
                st.markdown("""
                **Fórmula de puntuación final**:  
                `(Habilidades × Peso) + (Experiencia × Peso) + (Formación × Peso) + (Preferencias × Peso)`  

                - Los pesos son configurables por vacante y deben sumar 1.0  
                - Los criterios eliminatorios se verifican primero  
                - Scores se normalizan entre 0% y 100%  
                """)
                if hasattr(job_profile, 'weights'):
                    st.markdown("**Pesos actuales para esta vacante:**")
                    weights = job_profile.weights
                    st.write(f"- Habilidades: {weights.get('habilidades', 0):.0%}")
                    st.write(f"- Experiencia: {weights.get('experiencia', 0):.0%}")
                    st.write(f"- Formación: {weights.get('formacion', 0):.0%}")
                    st.write(f"- Preferencias: {weights.get('preferencias_reclutador', 0)::.0%}")

            # =============================================
            # ...resto del código existente (detalle de requisitos, etc.)...
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

# Reemplazar la función display_candidate_details existente por la siguiente:
def display_candidate_details(raw_data: any) -> None:
    """Muestra detalles ampliados del candidato"""
    import json, re
    try:
        # Convertir raw_data a dict de forma segura
        if isinstance(raw_data, str):
            data_dict = json.loads(raw_data)
        elif isinstance(raw_data, dict):
            data_dict = raw_data.copy()
        else:
            raise ValueError("Formato de datos no soportado")
        
        # Asegurar campos críticos
        data_dict.setdefault('job_skills', [])
        data_dict.setdefault('job_experience', 0)
        data_dict.setdefault('experiencia', [])
        data_dict.setdefault('formacion', [])

        # =============================================
        # Análisis Comparativo (mejorado)
        # =============================================
        st.markdown("### Análisis Comparativo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("✅ **Fortalezas Principales**")
            # Habilidades
            matched_skills = len(set(data_dict['habilidades']) & set(data_dict['job_skills']))
            st.write(f"- Coincidencia en {matched_skills}/{len(data_dict['job_skills'])} habilidades clave")
            
            # Experiencia
            exp_years = 0
            for exp in data_dict['experiencia']:
                if isinstance(exp, dict) and 'duracion' in exp:
                    match = re.search(r'\d+', str(exp['duracion']))
                    if match:
                        exp_years += int(match.group())
            st.write(f"- {exp_years} años de experiencia relevante")
            
            # Formación
            has_higher_education = any(edu in data_dict['formacion'] for edu in ['master', 'grado'])
            st.write("- Formación acorde al puesto" if has_higher_education else "- Formación básica")

        with col2:
            st.markdown("⚠️ **Áreas de Mejora**")
            # Habilidades faltantes
            missing_skills = set(data_dict['job_skills']) - set(data_dict['habilidades'])
            if missing_skills:
                st.write(f"- Faltan {len(missing_skills)} habilidades: {', '.join(list(missing_skills)[:3])}...")
            
            # Experiencia
            if exp_years < data_dict['job_experience']:
                st.write(f"- Experiencia insuficiente: requiere {data_dict['job_experience']} años")
    
            # Preferencias
            if data_dict.get('preferencias_score', 0) < 0.7:
                st.write(f"- Alineamiento con preferencias: {data_dict['preferencias_score']:.0%}")

        # =============================================
        # Timeline de Experiencia (robusto)
        # =============================================
        st.markdown("📅 **Historial Profesional**")
        valid_experience = [
            exp for exp in data_dict['experiencia']
            if isinstance(exp, dict) and 'puesto' in exp
        ][:3]  # Limitar a 3 entradas
        
        if valid_experience:
            timeline_data = {
                "Posición": [exp.get('puesto', 'Sin especificar') for exp in valid_experience],
                "Duración": [exp.get('duracion', 'No disponible') for exp in valid_experience],
                "Habilidades": [", ".join(exp.get('habilidades', [])) for exp in valid_experience]
            }
            st.dataframe(
                pd.DataFrame(timeline_data),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Posición": st.column_config.TextColumn(width="large"),
                    "Duración": st.column_config.TextColumn(width="medium"),
                    "Habilidades": st.column_config.ListColumn("Tecnologías usadas")
                }
            )
        else:
            st.warning("No se encontró experiencia estructurada en el CV")
            
    except Exception as e:
        st.error("Error mostrando detalles del candidato")
        logging.error(f"display_candidate_details error: {str(e)} | Data: {str(raw_data)[:200]}")
