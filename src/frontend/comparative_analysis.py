import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import logging
import asyncio
from typing import List, Dict

async def render_comparative_analysis(df: pd.DataFrame) -> None:
    """Render comparative analysis report for candidates"""
    try:
        if df is None:
            st.error("No hay datos disponibles para el análisis comparativo")
            return
            
        if 'Estado' not in df.columns:
            st.error("Los datos no contienen la columna 'Estado' requerida")
            return
            
        st.markdown("## 📊 Análisis Comparativo de Candidatos")
        
        # Filtrar solo candidatos calificados
        qualified_df = df[df['Estado'] == 'Calificado']
        
        if qualified_df.empty:
            st.warning("No hay candidatos calificados para comparar.")
            return
            
        # Selector múltiple de candidatos
        selected_candidates = st.multiselect(
            "🔍 Seleccione los candidatos a comparar:",
            options=qualified_df['Nombre Candidato'].unique()
        )
        
        if selected_candidates:
            # Filtrar DataFrame para los candidatos seleccionados
            selected_df = qualified_df[qualified_df['Nombre Candidato'].isin(selected_candidates)]
            
            # 1. Mostrar tabla comparativa
            st.subheader("📋 Tabla Comparativa")
            st.dataframe(selected_df, use_container_width=True)
            
            # 2. Mostrar gráficos comparativos
            st.subheader("📈 Gráficos Comparativos")
            render_comparative_charts(selected_df)
            
            # 3. Generar y mostrar análisis GPT para cada candidato
            st.subheader("🤖 Análisis Detallado por GPT")
            
            for _, row in selected_df.iterrows():
                with st.expander(f"📝 Análisis de {row['Nombre Candidato']}"):
                    candidate_text = (
                        f"Experiencia: {row.get('Experiencia', 'No disponible')}\n"
                        f"Habilidades: {row.get('Habilidades', 'No disponible')}\n"
                        f"Formación: {row.get('Formación', 'No disponible')}\n"
                        f"Score Final: {row.get('Score Final', 'No disponible')}"
                    )
                    
                    prompt = (
                        "Como experto en recursos humanos, analiza el siguiente perfil "
                        "de candidato y genera un resumen conciso destacando fortalezas, "
                        f"áreas de mejora y fit con el puesto:\n\n{candidate_text}"
                    )
                    
                    with st.spinner(f"Analizando perfil de {row['Nombre Candidato']}..."):
                        analysis = await st.session_state.app.text_generation_provider.generate_text(prompt)
                        st.write(analysis)
                        
    except Exception as e:
        logging.error(f"Error in render_comparative_analysis: {str(e)}")
        st.error("Error al mostrar el informe comparativo. Verifique los datos y vuelva a intentar.")

def render_comparative_charts(comparative_df: pd.DataFrame) -> None:
    """Renderiza gráficos comparativos de los candidatos"""
    try:
        if comparative_df is None or comparative_df.empty:
            st.error("No hay datos disponibles para generar los gráficos")
            return
            
        required_cols = ['Nombre Candidato', 'Score Habilidades', 'Score Experiencia', 'Score Formación']
        if not all(col in comparative_df.columns for col in required_cols):
            st.error("Faltan columnas requeridas en los datos")
            return
            
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