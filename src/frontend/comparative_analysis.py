import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import logging
import asyncio
from typing import List, Dict

def render_comparative_analysis(df):
    """Render comparative analysis report for candidates"""
    try:
        st.markdown('<div class="section-header">Informe Comparativo de Candidatos</div>', unsafe_allow_html=True)
        
        if df.empty:
            st.warning("No hay datos para mostrar en el informe comparativo.")
            return
        
        st.dataframe(df, use_container_width=True)
        
        if 'Nombre Candidato' in df.columns and 'Score Final' in df.columns:
            fig, ax = plt.subplots(figsize=(5, 2))
            sns.barplot(x='Nombre Candidato', y='Score Final', data=df, ax=ax)
            ax.set_title('Comparación de Scores entre Candidatos')
            ax.set_xlabel('Nombre del Candidato')
            ax.set_ylabel('Score')
            plt.xticks(rotation=45)
            st.pyplot(fig)
        
        if 'analysis_result' in df.columns:
            for idx, row in df.iterrows():
                st.markdown(f"### Análisis para {row['Nombre Candidato']}")
                st.write(row['analysis_result'])
        else:
            st.info("No hay análisis detallado disponible para los candidatos.")
    except Exception as e:
        logging.error(f"Error in render_comparative_analysis: {str(e)}")
        st.error("Error al mostrar el informe comparativo. Verifique los datos y vuelva a intentar.")

def render_comparative_charts(comparative_df: pd.DataFrame) -> None:
    """Renderiza gráficos comparativos de los candidatos"""
    try:
        # Preparar datos para visualización
        score_cols = ['Score Habilidades', 'Score Experiencia', 'Score Formación']
        plot_data = comparative_df[['Nombre Candidato'] + score_cols].copy()
        
        for col in score_cols:
            plot_data[col] = plot_data[col].str.rstrip('%').astype(float) / 100

        # Crear gráfico de barras comparativo
        fig, ax = plt.subplots(figsize=(10, 6))
        x = range(len(plot_data['Nombre Candidato']))
        width = 0.25

        for i, col in enumerate(score_cols):
            ax.bar([xi + i*width for xi in x], plot_data[col], width, 
                  label=col.replace('Score ', ''))

        ax.set_ylabel('Puntuación')
        ax.set_title('Comparación de Scores por Categoría')
        ax.set_xticks([xi + width for xi in x])
        ax.set_xticklabels(plot_data['Nombre Candidato'], rotation=45)
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)

    except Exception as e:
        logging.error(f"Error en render_comparative_charts: {str(e)}")
        st.error("Error al generar los gráficos comparativos.")

def comparative_analysis_view(app):
    """Vista de análisis comparativo"""
    st.markdown('<h1 class="title">Análisis Comparativo de Candidatos</h1>', 
               unsafe_allow_html=True)
    
    if 'current_data' not in st.session_state:
        st.error("No hay datos disponibles. Por favor, realice primero el análisis de candidatos.")
        return

    df = st.session_state['current_data']['df']
    
    selected_candidates = st.multiselect(
        "Seleccione candidatos para comparar",
        options=df['Nombre Candidato'].tolist(),
        max_selections=5
    )

    if selected_candidates:
        with st.spinner("Generando análisis comparativo..."):
            # Obtener análisis detallado
            analysis_results = asyncio.run(
                app.analyze_text_comparatively(df, selected_candidates)
            )
            
            # Mostrar gráficos comparativos
            comparative_df = df[df['Nombre Candidato'].isin(selected_candidates)]
            render_comparative_charts(comparative_df)
            
            # Mostrar análisis detallado
            st.subheader("Análisis Detallado")
            for result in analysis_results:
                with st.expander(f"📋 Análisis de {result['nombre']}"):
                    st.write(result['analisis'])
                    st.markdown("**Puntuaciones:**")
                    st.json(result['scores'])

    if st.button("← Volver al Ranking Principal"):
        st.session_state['page'] = 'main'
        st.experimental_rerun()
