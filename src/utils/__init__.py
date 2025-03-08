"""Módulo de utilidades y funciones auxiliares
Proporciona funciones compartidas para el manejo de archivos y formateo de datos"""

from .utilities import (
    # Funciones de configuración y registro
    setup_logging,
    
    # Funciones de formateo y presentación
    format_list_preview,
    create_score_row,
    sort_ranking_dataframe
)

# Manejador de archivos para PDF y texto
from .file_handler import FileHandler

__all__ = [
    'setup_logging',
    'format_list_preview',
    'create_score_row',
    'sort_ranking_dataframe',
    'FileHandler'
]