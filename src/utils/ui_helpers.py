import streamlit as st
from typing import Any, Dict, List, Optional
import pandas as pd
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns

def create_sidebar_nav() -> None:
    """
    Crea un menú de navegación en la barra lateral
    """
    with st.sidebar:
        st.markdown("## 📋 Navegación")
        st.markdown("---")
        
        st.markdown("""
        * 📄 **Cargar Archivos**
        * ⚙️ **Configurar Vacantes**
        * 📊 **Ver Resultados**
        """)
        
        st.markdown("---")
        st.markdown("### ℹ️ Acerca de")
        st.markdown("""
        Esta aplicación ayuda a identificar a los candidatos 
        más adecuados para vacantes específicas.
        """)

def show_candidate_card(name: str, score: float, skills: List[str], education: str) -> None:
    """
    Muestra un candidato en formato de tarjeta
    
    Args:
        name: Nombre del candidato
        score: Puntuación del candidato (0-1)
        skills: Lista de habilidades principales
        education: Información educativa
    """
    # Definir color según score
    if score >= 0.7:
        color = "#1e8449"  # verde
    elif score >= 0.4:
        color = "#f57c00"  # naranja
    else:
        color = "#c0392b"  # rojo
    
    # Construir HTML para la tarjeta
    card_html = f"""
    <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; color: #333;">{name}</h3>
            <div style="background-color: {color}; color: white; padding: 0.25rem 0.75rem; border-radius: 16px; font-weight: bold;">
                {score:.0%}
            </div>
        </div>
        <div style="margin: 0.75rem 0; border-bottom: 1px solid #eee; padding-bottom: 0.5rem;">
            <span style="font-weight: 500; color: #555;">{education}</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
    """
    
    # Añadir habilidades
    for skill in skills[:4]:  # Limitar a 4 habilidades para ahorrar espacio
        card_html += f'<span style="background-color: #f3f4f6; border-radius: 12px; padding: 0.25rem 0.5rem; font-size: 0.85rem;">{skill}</span>'
    
    if len(skills) > 4:
        card_html += f'<span style="background-color: #f3f4f6; border-radius: 12px; padding: 0.25rem 0.5rem; font-size: 0.85rem;">+{len(skills)-4} más</span>'
    
    card_html += """
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def create_score_chart(dataframe: pd.DataFrame, top_n: int = 10) -> BytesIO:
    """
    Crea un gráfico de barras para las puntuaciones de los candidatos
    
    Args:
        dataframe: DataFrame con los datos de los candidatos
        top_n: Número de candidatos para mostrar
    
    Returns:
        BytesIO: Buffer con la imagen del gráfico
    """
    plt.figure(figsize=(10, 6))
    
    # Preparar los datos
    df = dataframe.copy()
    df['Score Numérico'] = df['Score Final'].str.rstrip('%').astype(float) / 100
    df = df.nlargest(top_n, 'Score Numérico')
    
    # Crear el gráfico
    sns.set_style("whitegrid")
    ax = sns.barplot(x='Score Numérico', y='Nombre', data=df, palette="Blues_r")
    
    # Personalizar
    ax.set_title(f"Top {top_n} Candidatos por Puntuación", fontsize=15)
    ax.set_xlabel("Puntuación", fontsize=12)
    ax.set_ylabel("Candidato", fontsize=12)
    
    # Añadir etiquetas de porcentaje
    for i, v in enumerate(df['Score Numérico']):
        ax.text(v + 0.01, i, f"{v:.0%}", va='center')
    
    plt.tight_layout()
    
    # Guardar en un buffer
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    buf.seek(0)
    plt.close()
    
    return buf

def show_score_chart(dataframe: pd.DataFrame, top_n: int = 10) -> None:
    """
    Muestra un gráfico de barras para las puntuaciones de los candidatos
    
    Args:
        dataframe: DataFrame con los datos de los candidatos
        top_n: Número de candidatos para mostrar
    """
    buf = create_score_chart(dataframe, top_n)
    st.image(buf, use_column_width=True)
