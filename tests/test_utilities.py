"""Tests for utility functions"""
import pytest
import pandas as pd
from src.utils.utilities import format_list_preview, create_score_row, sort_ranking_dataframe

def test_format_list_preview_under_max():
    """Test format_list_preview with list shorter than max_items"""
    items = ["A", "B", "C"]
    result = format_list_preview(items, max_items=5)
    assert result == "A, B, C"
    assert "..." not in result

def test_format_list_preview_over_max():
    """Test format_list_preview with list longer than max_items"""
    items = ["A", "B", "C", "D", "E", "F"]
    result = format_list_preview(items, max_items=3)
    assert result == "A, B, C..."
    assert result.endswith("...")

def test_format_list_preview_empty():
    """Test format_list_preview with empty list"""
    result = format_list_preview([], max_items=5)
    assert result == ""

def test_format_list_preview_exact():
    """Test format_list_preview with list equal to max_items"""
    items = ["A", "B", "C"]
    result = format_list_preview(items, max_items=3)
    assert result == "A, B, C"
    assert "..." not in result

def test_create_score_row():
    """Test create_score_row function"""
    candidate_data = {
        "nombre_candidato": "John Doe",
        "habilidades": ["Python", "ML", "NLP"],
        "experiencia": ["5 years ML", "Team Lead"],
        "formacion": ["PhD", "MS"],
        "raw_data": {"original": "data"}
    }
    
    score_data = {
        "final_score": 0.85,
        "component_scores": {
            "habilidades": 0.9,
            "experiencia": 0.8,
            "formacion": 0.85,
            "preferencias_reclutador": 0.7
        },
        "disqualified": False,
        "disqualification_reasons": []
    }
    
    row = create_score_row(candidate_data, score_data)
    
    assert row["Nombre Candidato"] == "John Doe"
    assert row["Estado"] == "Calificado"
    assert row["Score Final"] == "85.0%"
    assert row["Score Habilidades"] == "90.0%"
    assert row["Score Experiencia"] == "80.0%"
    assert row["Score Formación"] == "85.0%"
    assert row["Score Preferencias"] == "70.0%"
    assert isinstance(row["Habilidades"], str)
    assert isinstance(row["Experiencia"], str)
    assert isinstance(row["Formación"], str)
    assert row["raw_data"] == {"original": "data"}

def test_create_score_row_disqualified():
    """Test create_score_row with disqualified candidate"""
    candidate_data = {
        "nombre_candidato": "John Doe",
        "habilidades": ["Python"],
        "experiencia": ["2 years"],
        "formacion": ["BS"],
    }
    
    score_data = {
        "final_score": 0.0,
        "component_scores": {
            "habilidades": 0.0,
            "experiencia": 0.0,
            "formacion": 0.0,
            "preferencias_reclutador": 0.0
        },
        "disqualified": True,
        "disqualification_reasons": ["No cumple con la experiencia mínima"]
    }
    
    row = create_score_row(candidate_data, score_data)
    
    assert row["Estado"] == "Descalificado"
    assert "No cumple con la experiencia mínima" in row["Razones Descalificación"]
    assert row["Score Final"] == "0.0%"

def test_sort_ranking_dataframe():
    """Test sort_ranking_dataframe function"""
    data = {
        "Nombre Candidato": ["A", "B", "C", "D"],
        "Estado": ["Calificado", "Descalificado", "Calificado", "Descalificado"],
        "Score Final": ["90.0%", "0.0%", "85.0%", "0.0%"]
    }
    df = pd.DataFrame(data)
    
    sorted_df = sort_ranking_dataframe(df)
    
    # Check if calificados are first
    assert sorted_df.iloc[0]["Estado"] == "Calificado"
    assert sorted_df.iloc[1]["Estado"] == "Calificado"
    
    # Check if sorted by score within each group
    assert float(sorted_df.iloc[0]["Score Final"].rstrip("%")) > float(sorted_df.iloc[1]["Score Final"].rstrip("%"))
    
    # Check if temporary column was removed
    assert "Sort Score" not in sorted_df.columns

def test_sort_ranking_dataframe_empty():
    """Test sort_ranking_dataframe with empty DataFrame"""
    df = pd.DataFrame(columns=["Nombre Candidato", "Estado", "Score Final"])
    sorted_df = sort_ranking_dataframe(df)
    assert len(sorted_df) == 0
    assert list(sorted_df.columns) == ["Nombre Candidato", "Estado", "Score Final"]