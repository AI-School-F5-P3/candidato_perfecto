"""Módulo inicial del sistema de análisis de RRHH
Este módulo exporta las clases principales del sistema para facilitar su importación"""

from .hr_analysis_system import (
    # Estructuras de datos básicas
    JobProfile,
    CandidateProfile,
    MatchScore,
    
    # Interfaces e implementaciones de embeddings
    IEmbeddingProvider,
    OpenAIEmbeddingProvider,
    
    # Componentes principales del sistema
    SemanticAnalyzer,     # Análisis y estructuración de texto
    MatchingEngine,       # Lógica de coincidencia
    RankingSystem        # Sistema de clasificación
)

__all__ = [
    'JobProfile',
    'CandidateProfile',
    'MatchScore',
    'IEmbeddingProvider',
    'OpenAIEmbeddingProvider',
    'SemanticAnalyzer',
    'MatchingEngine',
    'RankingSystem'
]