"""Test configuration and shared fixtures"""
import pytest
import os
from pathlib import Path
import json
from typing import Dict

@pytest.fixture
def test_data_dir() -> Path:
    """Get the test data directory path"""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def mock_api_key() -> str:
    """Provide a mock API key for testing"""
    return "test-api-key-12345"

@pytest.fixture
def sample_job_description() -> str:
    """Provide a sample job description for testing"""
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
    """Provide a sample resume for testing"""
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
    """Provide a sample job profile for testing"""
    return {
        "nombre_vacante": "Senior ML Engineer",
        "habilidades": ["Python", "PyTorch", "TensorFlow", "NLP", "Deep Learning"],
        "experiencia": ["5+ years ML/AI experience", "NLP project experience"],
        "formacion": ["PhD or MS in Computer Science"],
        "habilidades_preferidas": ["PyTorch", "NLP"]
    }

@pytest.fixture
def sample_candidate_profile() -> Dict:
    """Provide a sample candidate profile for testing"""
    return {
        "nombre_candidato": "John Doe",
        "habilidades": ["Python", "PyTorch", "NLP", "Machine Learning"],
        "experiencia": ["6 years ML experience", "NLP project leadership"],
        "formacion": ["PhD in Computer Science"],
        "raw_data": None
    }

@pytest.fixture
def killer_criteria() -> Dict:
    """Provide sample killer criteria for testing"""
    return {
        "killer_habilidades": ["Python", "PyTorch"],
        "killer_experiencia": ["5+ years experience"]
    }

@pytest.fixture
def matching_weights() -> Dict:
    """Provide sample matching weights for testing"""
    return {
        "habilidades": 0.3,
        "experiencia": 0.3,
        "formacion": 0.3,
        "preferencias_reclutador": 0.1
    }