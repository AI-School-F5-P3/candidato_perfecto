"""Common utilities and helper functions"""
import logging
from typing import List, Dict, Any
import pandas as pd

def setup_logging(log_file: str = "app.log") -> None:
    """Configure logging settings"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def format_list_preview(items: List[str], max_items: int = 5) -> str:
    """Format a list with ellipsis if it exceeds max_items"""
    preview = items[:max_items]
    return ', '.join(preview) + ('...' if len(items) > max_items else '')

def create_score_row(candidate_data: Dict[str, Any], score_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a standardized row for the ranking DataFrame"""
    return {
        'Nombre Candidato': candidate_data['nombre_candidato'],
        'Estado': 'Descalificado' if score_data['disqualified'] else 'Calificado',
        'Score Final': f"{score_data['final_score']:.1%}",
        'Score Habilidades': f"{score_data['component_scores']['habilidades']:.1%}",
        'Score Experiencia': f"{score_data['component_scores']['experiencia']:.1%}",
        'Score Formación': f"{score_data['component_scores']['formacion']:.1%}",
        'Score Preferencias': f"{score_data['component_scores']['preferencias_reclutador']:.1%}",
        'Habilidades': format_list_preview(candidate_data['habilidades']),
        'Experiencia': format_list_preview(candidate_data['experiencia'], 3),
        'Formación': format_list_preview(candidate_data['formacion'], 2),
        'Razones Descalificación': ', '.join(score_data.get('disqualification_reasons', [])) or 'N/A',
        'raw_data': candidate_data.get('raw_data')
    }

def sort_ranking_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sort DataFrame by qualification status and score"""
    df['Sort Score'] = df['Score Final'].str.rstrip('%').astype('float')
    df = df.sort_values(
        by=['Estado', 'Sort Score'], 
        ascending=[True, False],
        key=lambda x: x if x.name != 'Estado' else pd.Categorical(x, ['Calificado', 'Descalificado'])
    )
    return df.drop('Sort Score', axis=1)