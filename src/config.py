"""Configuration settings and constants for the HR Analysis System"""
from dataclasses import dataclass
from typing import Dict

@dataclass
class ModelConfig:
    """LLM model configuration"""
    chat_model: str = "gpt-3.5-turbo"
    embedding_model: str = "text-embedding-3-small"

@dataclass
class MatchingConfig:
    """Matching engine configuration"""
    killer_criteria_threshold: float = 0.7
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
    """UI display configuration"""
    max_skills_preview: int = 5
    max_experience_preview: int = 3
    max_education_preview: int = 2
    score_thresholds = {
        "high": 0.7,
        "medium": 0.4
    }
    colors = {
        "success": "#e6ffe6",
        "warning": "#fff3e6",
        "danger": "#ffe6e6",
        "disqualified": "#ffebee"
    }

class Config:
    """Global configuration container"""
    MODEL = ModelConfig()
    MATCHING = MatchingConfig()
    DISPLAY = DisplayConfig()