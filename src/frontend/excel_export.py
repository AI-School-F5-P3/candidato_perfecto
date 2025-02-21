"""Módulo para la exportación de datos a Excel"""
import streamlit as st
import pandas as pd
from io import BytesIO
import logging
from datetime import datetime

def render_excel_export(df: pd.DataFrame) -> None:
    """Renderiza la pestaña de exportación Excel"""
    try:
        st.markdown("## 📊 Exportación a Excel")
        
        # Display the styled dataframe
        st.markdown("### Vista previa de datos")
        st.dataframe(df, use_container_width=True)
        
        # Create Excel export button
        st.markdown("### Exportar a Excel")
        
        # Generate Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Ranking', index=False)
            
            # Auto-adjust columns width
            worksheet = writer.sheets['Ranking']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_length
        
        # Generate download button
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Descargar Excel",
            data=excel_data,
            file_name=f'ranking_candidatos_{timestamp}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Add some usage notes
        st.markdown("""
        #### Notas:
        - El archivo Excel contiene todos los datos mostrados en la tabla superior
        - Las columnas se han ajustado automáticamente para mejor visualización
        - El nombre del archivo incluye la fecha y hora de exportación
        """)
        
    except Exception as e:
        logging.error(f"Error en render_excel_export: {str(e)}")
        st.error("Error al preparar la exportación Excel. Por favor, intente de nuevo.")
