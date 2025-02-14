"""Tests for the SemanticAnalyzer class"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from src.hr_analysis_system import SemanticAnalyzer, OpenAIEmbeddingProvider, JobProfile, CandidateProfile

@pytest.fixture
def mock_embedding_provider():
    provider = MagicMock(spec=OpenAIEmbeddingProvider)
    provider.get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    provider.client = MagicMock()
    provider.client.api_key = "test-key"
    return provider

@pytest.fixture
def analyzer(mock_embedding_provider):
    return SemanticAnalyzer(mock_embedding_provider)

@pytest.mark.asyncio
async def test_standardize_job_description(analyzer, sample_job_description, sample_job_profile):
    """Test job description standardization"""
    # Mock the OpenAI API response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps(sample_job_profile)))
    ]
    analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Test with preferences
    preferences = {"habilidades_preferidas": ["PyTorch", "NLP"]}
    result = await analyzer.standardize_job_description(sample_job_description, preferences)
    
    assert isinstance(result, JobProfile)
    assert result.nombre_vacante == sample_job_profile["nombre_vacante"]
    assert result.habilidades == sample_job_profile["habilidades"]
    assert result.experiencia == sample_job_profile["experiencia"]
    assert result.formacion == sample_job_profile["formacion"]
    assert result.habilidades_preferidas == preferences["habilidades_preferidas"]

@pytest.mark.asyncio
async def test_standardize_resume(analyzer, sample_resume, sample_candidate_profile):
    """Test resume standardization"""
    # Mock the OpenAI API response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps(sample_candidate_profile)))
    ]
    analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    result = await analyzer.standardize_resume(sample_resume)
    
    assert isinstance(result, CandidateProfile)
    assert result.nombre_candidato == sample_candidate_profile["nombre_candidato"]
    assert result.habilidades == sample_candidate_profile["habilidades"]
    assert result.experiencia == sample_candidate_profile["experiencia"]
    assert result.formacion == sample_candidate_profile["formacion"]
    assert result.raw_data == sample_candidate_profile

@pytest.mark.asyncio
async def test_standardize_job_description_error_handling(analyzer, sample_job_description):
    """Test error handling in job description standardization"""
    # Mock API error
    analyzer.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
    
    with pytest.raises(Exception) as exc_info:
        await analyzer.standardize_job_description(sample_job_description)
    assert "API Error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_standardize_resume_error_handling(analyzer, sample_resume):
    """Test error handling in resume standardization"""
    # Mock API error
    analyzer.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
    
    with pytest.raises(Exception) as exc_info:
        await analyzer.standardize_resume(sample_resume)
    assert "API Error" in str(exc_info.value)