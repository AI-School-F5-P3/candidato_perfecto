"""Pruebas para el módulo ranking_system"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.hr_analysis_system import (
    RankingSystem,
    MatchingEngine,
    JobProfile,
    CandidateProfile,
    MatchScore
)

@pytest.fixture
def mock_matching_engine():
    """Fixture que proporciona un motor de coincidencia simulado"""
    engine = MagicMock(spec=MatchingEngine)
    engine.calculate_match_score = AsyncMock()
    return engine

@pytest.fixture
def ranking_system(mock_matching_engine):
    return RankingSystem(mock_matching_engine)

@pytest.fixture
def job_profile(sample_job_profile):
    return JobProfile(**sample_job_profile)

@pytest.fixture
def candidate_profiles(sample_candidate_profile):
    # Crear múltiples candidatos con diferentes perfiles
    profiles = []
    names = ["John Doe", "Jane Smith", "Bob Wilson"]
    scores = [0.9, 0.7, 0.5]
    
    for name, score in zip(names, scores):
        profile = sample_candidate_profile.copy()
        profile["nombre_candidato"] = name
        profiles.append(CandidateProfile(**profile))
    
    return profiles

@pytest.mark.asyncio
async def test_rank_candidates_no_killer_criteria(
    ranking_system,
    mock_matching_engine,
    job_profile,
    candidate_profiles,
    matching_weights
):
    """Prueba la clasificación de candidatos sin criterios eliminatorios"""
    # Simular puntuaciones de coincidencia para diferentes candidatos
    scores = [
        MatchScore(final_score=0.9, component_scores={"habilidades": 0.9, "experiencia": 0.9, "formacion": 0.9, "preferencias_reclutador": 0.9}),
        MatchScore(final_score=0.7, component_scores={"habilidades": 0.7, "experiencia": 0.7, "formacion": 0.7, "preferencias_reclutador": 0.7}),
        MatchScore(final_score=0.5, component_scores={"habilidades": 0.5, "experiencia": 0.5, "formacion": 0.5, "preferencias_reclutador": 0.5})
    ]
    mock_matching_engine.calculate_match_score.side_effect = scores
    
    rankings = await ranking_system.rank_candidates(
        job_profile,
        candidate_profiles,
        weights=matching_weights
    )
    
    assert len(rankings) == len(candidate_profiles)
    # Verificar si están ordenados en orden descendente por puntuación
    assert all(r1[1].final_score >= r2[1].final_score 
              for r1, r2 in zip(rankings, rankings[1:]))

@pytest.mark.asyncio
async def test_rank_candidates_with_killer_criteria(
    ranking_system,
    mock_matching_engine,
    job_profile,
    candidate_profiles,
    killer_criteria
):
    """Prueba la clasificación de candidatos con criterios eliminatorios"""
    # Simular puntuaciones incluyendo un candidato descalificado
    scores = [
        MatchScore(final_score=0.9, component_scores={"habilidades": 0.9, "experiencia": 0.9, "formacion": 0.9, "preferencias_reclutador": 0.9}),
        MatchScore(final_score=0.0, component_scores={"habilidades": 0.0, "experiencia": 0.0, "formacion": 0.0, "preferencias_reclutador": 0.0}, disqualified=True, disqualification_reasons=["No cumple con las habilidades obligatorias"]),
        MatchScore(final_score=0.7, component_scores={"habilidades": 0.7, "experiencia": 0.7, "formacion": 0.7, "preferencias_reclutador": 0.7})
    ]
    mock_matching_engine.calculate_match_score.side_effect = scores
    
    rankings = await ranking_system.rank_candidates(
        job_profile,
        candidate_profiles,
        killer_criteria=killer_criteria
    )
    
    assert len(rankings) == len(candidate_profiles)
    # Verificar si los candidatos calificados están clasificados antes que los descalificados
    qualified = [r for r in rankings if not r[1].disqualified]
    disqualified = [r for r in rankings if r[1].disqualified]
    assert all(q[1].final_score > d[1].final_score for q in qualified for d in disqualified)

@pytest.mark.asyncio
async def test_rank_candidates_empty_list(ranking_system, job_profile):
    """Prueba la clasificación con una lista vacía de candidatos"""
    rankings = await ranking_system.rank_candidates(job_profile, [])
    assert len(rankings) == 0

@pytest.mark.asyncio
async def test_rank_candidates_equal_scores(
    ranking_system,
    mock_matching_engine,
    job_profile,
    candidate_profiles
):
    """Prueba la clasificación cuando hay puntuaciones iguales"""
    # Simular que todos los candidatos tienen la misma puntuación
    same_score = MatchScore(
        final_score=0.8,
        component_scores={
            "habilidades": 0.8,
            "experiencia": 0.8,
            "formacion": 0.8,
            "preferencias_reclutador": 0.8
        }
    )
    mock_matching_engine.calculate_match_score.return_value = same_score
    
    rankings = await ranking_system.rank_candidates(job_profile, candidate_profiles)
    
    assert len(rankings) == len(candidate_profiles)
    # Verificar si todas las puntuaciones son iguales
    assert all(r[1].final_score == 0.8 for r in rankings)