"""Tests for the MatchingEngine class"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import numpy as np
from src.hr_analysis_system import (
    MatchingEngine, 
    OpenAIEmbeddingProvider,
    JobProfile,
    CandidateProfile,
    MatchScore
)

@pytest.fixture
def mock_embedding_provider():
    """Fixture que proporciona un proveedor de embeddings simulado"""
    provider = MagicMock(spec=OpenAIEmbeddingProvider)
    provider.get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return provider

@pytest.fixture
def matching_engine(mock_embedding_provider):
    return MatchingEngine(mock_embedding_provider)

@pytest.fixture
def job_profile(sample_job_profile):
    return JobProfile(**sample_job_profile)

@pytest.fixture
def candidate_profile(sample_candidate_profile):
    return CandidateProfile(**sample_candidate_profile)

@pytest.mark.asyncio
async def test_calculate_semantic_similarity(matching_engine):
    """Prueba el cálculo de similitud semántica entre textos"""
    text1 = ["Python", "Machine Learning"]
    text2 = ["Python", "Deep Learning"]
    
    # Mock embeddings to return controlled values
    matching_engine.embedding_provider.get_embedding = AsyncMock(side_effect=[
        [1.0, 0.0],  # Python text1
        [0.0, 1.0],  # ML text1
        [1.0, 0.0],  # Python text2
        [0.5, 0.5],  # DL text2
    ])
    
    similarity = await matching_engine.calculate_semantic_similarity(text1, text2)
    assert isinstance(similarity, float)
    assert 0 <= similarity <= 1

@pytest.mark.asyncio
async def test_check_killer_criteria_pass(matching_engine, candidate_profile):
    """Prueba la verificación de criterios eliminatorios cuando el candidato los cumple"""
    # Mock similarity to return high score
    matching_engine.calculate_semantic_similarity = AsyncMock(return_value=0.8)
    
    killer_criteria = {
        "killer_habilidades": ["Python", "PyTorch"],
        "killer_experiencia": ["5+ years"]
    }
    
    meets_criteria, reasons = await matching_engine.check_killer_criteria(
        candidate_profile, 
        killer_criteria
    )
    
    assert meets_criteria is True
    assert len(reasons) == 0

@pytest.mark.asyncio
async def test_check_killer_criteria_fail(matching_engine, candidate_profile):
    """Prueba la verificación de criterios eliminatorios cuando el candidato no los cumple"""
    # Mock similarity to return low score
    matching_engine.calculate_semantic_similarity = AsyncMock(return_value=0.5)
    
    killer_criteria = {
        "killer_habilidades": ["Java", "Spring"],
        "killer_experiencia": ["10+ years"]
    }
    
    meets_criteria, reasons = await matching_engine.check_killer_criteria(
        candidate_profile, 
        killer_criteria
    )
    
    assert meets_criteria is False
    assert len(reasons) > 0
    assert any("habilidades" in reason.lower() for reason in reasons)
    assert any("experiencia" in reason.lower() for reason in reasons)

@pytest.mark.asyncio
async def test_calculate_match_score(matching_engine, job_profile, candidate_profile, matching_weights):
    """Prueba el cálculo de puntuación de coincidencia sin criterios eliminatorios"""
    # Mock similarity to return different scores for different components
    similarity_scores = {
        "habilidades": 0.8,
        "experiencia": 0.7,
        "formacion": 0.9,
        "preferencias_reclutador": 0.6
    }
    matching_engine.calculate_semantic_similarity = AsyncMock(side_effect=lambda *args: 
        similarity_scores[next(k for k, v in similarity_scores.items() if not v == -1)])
    
    match_score = await matching_engine.calculate_match_score(
        job_profile,
        candidate_profile,
        weights=matching_weights
    )
    
    assert isinstance(match_score, MatchScore)
    assert 0 <= match_score.final_score <= 1
    assert not match_score.disqualified
    assert all(0 <= score <= 1 for score in match_score.component_scores.values())

@pytest.mark.asyncio
async def test_calculate_match_score_with_killer_criteria(
    matching_engine,
    job_profile,
    candidate_profile,
    killer_criteria
):
    """Prueba el cálculo de puntuación de coincidencia con criterios eliminatorios"""
    # Mock similarity to fail killer criteria
    matching_engine.calculate_semantic_similarity = AsyncMock(return_value=0.5)
    
    match_score = await matching_engine.calculate_match_score(
        job_profile,
        candidate_profile,
        killer_criteria=killer_criteria
    )
    
    assert isinstance(match_score, MatchScore)
    assert match_score.final_score == 0.0
    assert match_score.disqualified
    assert len(match_score.disqualification_reasons) > 0

@pytest.mark.asyncio
async def test_empty_killer_criteria(matching_engine, candidate_profile):
    """Prueba el comportamiento con criterios eliminatorios vacíos"""
    empty_criteria = {"killer_habilidades": [], "killer_experiencia": []}
    meets_criteria, reasons = await matching_engine.check_killer_criteria(
        candidate_profile, 
        empty_criteria
    )
    
    assert meets_criteria is True
    assert len(reasons) == 0

@pytest.mark.asyncio
async def test_none_killer_criteria(matching_engine, candidate_profile):
    """Prueba el comportamiento con criterios eliminatorios nulos"""
    meets_criteria, reasons = await matching_engine.check_killer_criteria(
        candidate_profile, 
        None
    )
    
    assert meets_criteria is True
    assert len(reasons) == 0