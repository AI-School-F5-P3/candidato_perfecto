"""Configuración y fixtures compartidos para pruebas"""
import pytest
import os
from pathlib import Path
import json
from typing import Dict
from unittest.mock import MagicMock
from src.hr_analysis_system import OpenAIEmbeddingProvider

@pytest.fixture
def test_data_dir() -> Path:
    """Obtener la ruta del directorio de datos de prueba"""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def mock_api_key() -> str:
    """Proporcionar una clave API simulada para pruebas"""
    return "test-api-key-12345"

@pytest.fixture
def sample_job_description() -> str:
    """Proporcionar una descripción de trabajo de muestra para pruebas"""
    return """
    Senior Machine Learning Engineer
    
    Requirements:
    - 5+ years of experience in ML/AI
    - Python, PyTorch, TensorFlow
    - PhD or MS in Computer Science
    - Experience with NLP and deep learning
    """

@pytest.fixture
def sample_resume() -> str:
    """Proporcionar un currículum de muestra para pruebas"""
    return """
    John Doe
    ML Engineer
    
    Experience:
    - 6 years in machine learning
    - Expert in Python, PyTorch
    - Led NLP projects
    
    Education:
    PhD in Computer Science
    """

@pytest.fixture
def sample_job_profile() -> Dict:
    """Proporcionar un perfil de trabajo de muestra para pruebas"""
    return {
        "nombre_vacante": "Senior ML Engineer",
        "habilidades": ["Python", "PyTorch", "TensorFlow", "NLP", "Deep Learning"],
        "experiencia": ["5+ years ML/AI experience", "NLP project experience"],
        "formacion": ["PhD or MS in Computer Science"],
        "habilidades_preferidas": ["PyTorch", "NLP"]
    }

@pytest.fixture
def sample_candidate_profile() -> Dict:
    """Proporcionar un perfil de candidato de muestra para pruebas"""
    return {
        "nombre_candidato": "John Doe",
        "habilidades": ["Python", "PyTorch", "NLP", "Machine Learning"],
        "experiencia": ["6 years ML experience", "NLP project leadership"],
        "formacion": ["PhD in Computer Science"],
        "raw_data": None
    }

@pytest.fixture
def killer_criteria() -> Dict:
    """Proporcionar criterios eliminatorios de muestra para pruebas"""
    return {
        "killer_habilidades": ["Python", "PyTorch"],
        "killer_experiencia": ["5+ years experience"]
    }

@pytest.fixture
def matching_weights() -> Dict:
    """Proporcionar pesos de coincidencia de muestra para pruebas"""
    return {
        "habilidades": 0.3,
        "experiencia": 0.3,
        "formacion": 0.3,
        "preferencias_reclutador": 0.1
    }

@pytest.fixture
def mock_embedding_provider():
    """Fixture que proporciona un proveedor de embeddings simulado"""
    provider = MagicMock(spec=OpenAIEmbeddingProvider)
    provider.get_embedding = MagicMock(return_value=[0.1, 0.2, 0.3])
    return provider