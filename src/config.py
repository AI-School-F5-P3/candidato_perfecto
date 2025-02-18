"""Configuración del sistema de análisis de RRHH"""
from dataclasses import dataclass
from typing import Dict

@dataclass
class ModelConfig:
    """Configuración de modelos de IA"""
    # Modelos de OpenAI utilizados para el análisis
    chat_model: str = "gpt-3.5-turbo"      # Modelo para análisis de texto y extracción de información
    embedding_model: str = "text-embedding-3-small"  # Modelo para cálculo de similitud semántica

@dataclass
class MatchingConfig:
    """Configuración de parámetros de coincidencia"""
    # Umbral de similitud mínima para criterios eliminatorios (70%)
    killer_criteria_threshold: float = 0.7
    
    # Umbral mínimo de similitud para considerar una coincidencia válida
    min_similarity_threshold: float = 0.3
    
    # Umbral para activar mecanismo de fallback
    fallback_threshold: float = 0.2

    # Distribución por defecto de pesos para cada componente
    default_weights: Dict[str, float] = None

    def __post_init__(self):
        if self.default_weights is None:
            self.default_weights = {
                "habilidades": 0.3,
                "experiencia": 0.3,
                "formacion": 0.3,
                "preferencias_reclutador": 0.1
            }

@dataclass
class DisplayConfig:
    """Configuración de visualización"""
    # Límites de elementos a mostrar en las vistas previas
    max_skills_preview: int = 5
    max_experience_preview: int = 3
    max_education_preview: int = 2
    
    # Umbrales para categorización de puntuaciones
    score_thresholds = {
        "high": 0.7,    # Verde: >= 70%
        "medium": 0.4   # Amarillo: >= 40%, Rojo: < 40%
    }
    
    # Esquema de colores para la interfaz
    colors = {
        "success": "#e6ffe6",      # Verde claro para puntuaciones altas
        "warning": "#fff3e6",      # Amarillo claro para puntuaciones medias
        "danger": "#ffe6e6",       # Rojo claro para puntuaciones bajas
        "disqualified": "#ffebee"  # Rojo muy claro para candidatos descalificados
    }

class Config:
    """Contenedor de configuración global"""
    MODEL = ModelConfig()
    MATCHING = MatchingConfig()
    DISPLAY = DisplayConfig()