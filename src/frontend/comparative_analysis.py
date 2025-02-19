import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import asyncio

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

def comparative_analysis_view(app):
    """Pantalla de análisis comparativo, integra selección de candidatos, análisis y reporte gráfico"""
    st.markdown('<h1 class="title">Análisis Comparativo</h1>', unsafe_allow_html=True)
    
    if 'current_data' not in st.session_state:
        st.error("No se encontraron datos de ranking. Por favor, regrese a la pantalla principal y realice el análisis de candidatos.")
        return
    
    df = st.session_state['current_data']['df']
    
    selected_candidate_names = st.multiselect(
        "Seleccione los nombres de los candidatos para el informe comparativo",
        options=df['Nombre Candidato'].tolist()
    )
    
    if selected_candidate_names:
        with st.spinner("Generando análisis comparativo..."):
            analysis_results = asyncio.run(app.analyze_text_comparatively(df, selected_candidate_names))
            if analysis_results:
                st.subheader("Análisis Individual de Candidatos")
                for result in analysis_results:
                    with st.expander(f"Análisis de {result['nombre']}"):
                        st.write(result['analisis'])
        
        comparative_df = df[df['Nombre Candidato'].isin(selected_candidate_names)]
        render_comparative_analysis(comparative_df)
    else:
        st.warning("Por favor, seleccione al menos un candidato para el informe comparativo.")
    
    if st.button("Regresar a la pantalla principal"):
        st.session_state['page'] = 'main'
        st.experimental_set_query_params(page='main')
