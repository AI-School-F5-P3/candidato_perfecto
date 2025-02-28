import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import logging
import asyncio
from typing import List, Dict, Optional
import plotly.graph_objects as go  # Añadir esta importación

async def render_comparative_analysis(df_list: List[pd.DataFrame]) -> None:
    """Render comparative analysis report for candidates with vacancy selection"""
    try:
        if not df_list:
            st.error("No hay datos disponibles para el análisis comparativo")
            return

        st.markdown("## 📊 Análisis Comparativo de Candidatos")
        
        # Selector de vacante
        vacancy_names = [f"Vacante {i+1}" for i in range(len(df_list))]
        selected_vacancy = st.selectbox(
            "🎯 Seleccione la vacante a analizar:",
            range(len(vacancy_names)),
            format_func=lambda x: vacancy_names[x]
        )
        
        # Obtener DataFrame de la vacante seleccionada
        current_df = df_list[selected_vacancy]
        
        # Filtrar solo candidatos calificados
        qualified_df = current_df[current_df['Obligatorias'] == 'Cumple']
        
        if qualified_df.empty:
            st.warning(f"No hay candidatos calificados para comparar en la {vacancy_names[selected_vacancy]}.")
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
                    # Extraer datos técnicos del raw_data
                    technical_data = row.get('raw_data', {})
                    candidate_text = (
                        f"Candidato para {vacancy_names[selected_vacancy]}:\n"
                        f"Nombre: {row['Nombre Candidato']}\n"
                        f"Experiencia: {row.get('Experiencia', 'No disponible')}\n"
                        f"Habilidades: {row.get('Habilidades', 'No disponible')}\n"
                        f"Formación: {row.get('Formación', 'No disponible')}\n"
                        f"Score Final: {row.get('Score Final', 'No disponible')}\n"
                        f"Datos Técnicos Adicionales: {technical_data}"
                    )
                    
                    prompt = (
                        "Como experto en recursos humanos, analiza el siguiente perfil "
                        "considerando el puesto específico al que aplica. Genera un análisis "
                        "detallado que incluya:\n"
                        "1. Fortalezas principales\n"
                        "2. Áreas de mejora\n"
                        "3. Fit con el puesto específico\n"
                        "4. Recomendaciones para entrevista\n\n"
                        f"{candidate_text}"
                    )
                    
                    with st.spinner(f"Analizando perfil de {row['Nombre Candidato']}..."):
                        try:
                            provider = st.session_state.app.text_generation_provider
                            if provider and hasattr(provider, 'generate_text'):
                                analysis = await provider.generate_text(prompt)
                                if analysis:
                                    st.write(analysis)
                                else:
                                    st.warning("No se pudo generar el análisis.")
                            else:
                                st.warning("El servicio de análisis de texto no está disponible.")
                        except Exception as e:
                            st.error(f"Error al generar el análisis: {str(e)}")
                        
    except Exception as e:
        logging.error(f"Error in render_comparative_analysis: {str(e)}")
        st.error("Error al mostrar el informe comparativo. Verifique los datos y vuelva a intentar.")

def render_comparative_charts(comparative_df: pd.DataFrame) -> None:
    """Renderiza gráficos comparativos de los candidatos"""
    try:
        if comparative_df is None or comparative_df.empty:
            st.error("No hay datos disponibles para generar los gráficos")
            return
            
        required_cols = ['Nombre Candidato', 'Score Habilidades', 'Score Experiencia', 'Score Formación', 'Score Preferencias']
        if not all(col in comparative_df.columns for col in required_cols):
            st.error("Faltan columnas requeridas en los datos")
            return

        # Gráfico de radar
        st.markdown("### Distribución de Competencias Clave")
        categories = ['Habilidades', 'Experiencia', 'Formación', 'Preferencias']
        fig = go.Figure()
        
        for _, row in comparative_df.iterrows():
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

        # Gráfico de barras mejorado
        st.markdown("### Comparación de Scores por Categoría")
        score_cols = ['Score Habilidades', 'Score Experiencia', 'Score Formación']
        plot_data = comparative_df[['Nombre Candidato'] + score_cols].copy()
        
        for col in score_cols:
            plot_data[col] = plot_data[col].str.rstrip('%').astype(float) / 100

        # Crear gráfico de barras comparativo con Plotly
        fig = go.Figure()
        
        for col in score_cols:
            fig.add_trace(go.Bar(
            x=plot_data['Nombre Candidato'],
            y=plot_data[col],
            name=col.replace('Score ', ''),
            text=plot_data[col].apply(lambda x: f'{x*100:.1f}%'),
            textposition='auto'
            ))

        fig.update_layout(
            barmode='group',
            xaxis_tickangle=-45,
            yaxis=dict(title='Puntuación'),
            title='Comparación de Scores por Categoría',
            margin=dict(l=20, r=20, t=40, b=20),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logging.error(f"Error en render_comparative_charts: {str(e)}")
        st.error("Error al generar los gráficos comparativos.")