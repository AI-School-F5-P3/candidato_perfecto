"""Funciones de utilidad para el sistema de análisis de RRHH"""
import logging
from typing import List, Dict, Any, Union
import pandas as pd
import json
from io import BytesIO

def setup_logging(log_file: str = "app.log") -> None:
    """Configura el sistema de registro para la aplicación"""
    # Configura el registro tanto en archivo como en consola
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def format_list_preview(items: List[str], max_items: int = 5) -> str:
    """Formatea una lista para vista previa, mostrando solo los primeros elementos"""
    preview = items[:max_items]
    # Agrega "..." si hay más elementos que el máximo mostrado
    return ', '.join(preview) + ('...' if len(items) > max_items else '')

def create_score_row(candidate_data: Dict[str, Any], score_data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea una fila de datos para el DataFrame de resultados"""
    import json
    # Añadir campos esenciales
    candidate_data.setdefault('job_skills', [])
    candidate_data.setdefault('job_experience', 0)
    candidate_data.setdefault('preferencias_score', 0.0)

    # Convertir experiencia a strings para visualización
    exp_preview = []
    for exp in candidate_data.get('experiencia', []):
        if isinstance(exp, dict):
            exp_str = f"{exp.get('puesto', '')} ({exp.get('duracion', '')})"
            exp_preview.append(exp_str)
        else:
            exp_preview.append(str(exp))

    # Convert nested dicts to strings for safe DataFrame creation.
    if "raw_data" in candidate_data and isinstance(candidate_data["raw_data"], dict):
        candidate_data["raw_data"] = json.dumps(candidate_data["raw_data"])
    # Ensure candidate list fields contain only strings.
    for key in ['habilidades', 'experiencia', 'formacion']:
        if key in candidate_data and isinstance(candidate_data[key], list):
            candidate_data[key] = [json.dumps(item) if isinstance(item, dict) else str(item) for item in candidate_data[key]]
    # Construye un diccionario con los datos formateados para visualización
    return {
        'Nombre Candidato': candidate_data['nombre_candidato'],
        'Estado': 'Descalificado' if score_data['disqualified'] else 'Calificado',
        'Score Final': f"{score_data['final_score']:.1%}",
        'Score Habilidades': f"{score_data['component_scores']['habilidades']:.1%}",
        'Score Experiencia': f"{score_data['component_scores']['experiencia']:.1%}",
        'Score Formación': f"{score_data['component_scores']['formacion']:.1%}",
        'Score Preferencias': f"{score_data['component_scores']['preferencias_reclutador']:.1%}",
        'Habilidades': format_list_preview(candidate_data['habilidades']),
        'Experiencia': format_list_preview(exp_preview, 3),
        'Formación': format_list_preview(candidate_data['formacion'], 2),
        'Razones Descalificación': ', '.join(score_data.get('disqualification_reasons', [])) or 'N/A',
        'raw_data': json.dumps(candidate_data)  # Asegurar serialización
    }

def sort_ranking_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena el DataFrame de ranking por puntuación y estado de descalificación"""
    # Convierte las puntuaciones de porcentaje a números para ordenamiento
    df['Sort Score'] = df['Score Final'].str.rstrip('%').astype('float')
    
    # Ordena primero por estado (Calificado antes que Descalificado) y luego por puntuación
    df = df.sort_values(
        by=['Estado', 'Sort Score'], 
        ascending=[True, False],
        key=lambda x: x if x.name != 'Estado' else pd.Categorical(x, ['Calificado', 'Descalificado'])
    )
    return df.drop('Sort Score', axis=1)  # Elimina la columna temporal de ordenamiento

def export_rankings_to_excel(df_list: List[pd.DataFrame], sheet_names: List[str], file_output: Union[str, BytesIO]) -> bool:
    """
    Exporta múltiples DataFrames a un archivo Excel con múltiples hojas
    
    Args:
        df_list: Lista de DataFrames a exportar
        sheet_names: Lista de nombres para las hojas
        file_output: Ruta del archivo o BytesIO buffer donde guardar el Excel
        
    Returns:
        bool: True si la exportación fue exitosa, False en caso contrario
    """
    try:
        with pd.ExcelWriter(file_output, engine='openpyxl') if isinstance(file_output, str) else pd.ExcelWriter(file_output, engine='openpyxl') as writer:
            for df, sheet_name in zip(df_list, sheet_names):
                # Crear una copia del DataFrame para la exportación
                export_df = df.copy()
                
                # Eliminar la columna raw_data si existe
                if 'raw_data' in export_df.columns:
                    export_df = export_df.drop('raw_data', axis=1)
                
                # Exportar a Excel
                export_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                
                # Ajustar ancho de columnas
                worksheet = writer.sheets[sheet_name[:31]]
                for idx, col in enumerate(export_df.columns):
                    max_length = max(
                        export_df[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

        # Si es BytesIO, asegurarse de que el puntero esté al inicio
        if isinstance(file_output, BytesIO):
            file_output.seek(0)
        
        return True
    except Exception as e:
        logging.error(f"Error exportando a Excel: {str(e)}")
        return False