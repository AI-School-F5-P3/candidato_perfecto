"""Pruebas para funciones utilitarias"""
import pytest
import pandas as pd
from src.utils.utilities import format_list_preview, create_score_row, sort_ranking_dataframe

def test_format_list_preview_under_max():
    """Prueba format_list_preview con una lista más corta que max_items"""
    items = ["A", "B", "C"]
    result = format_list_preview(items, max_items=5)
    assert result == "A, B, C"
    assert "..." not in result

def test_format_list_preview_over_max():
    """Prueba format_list_preview con una lista más larga que max_items"""
    items = ["A", "B", "C", "D", "E", "F"]
    result = format_list_preview(items, max_items=3)
    assert result == "A, B, C..."
    assert result.endswith("...")

def test_format_list_preview_empty():
    """Prueba format_list_preview con una lista vacía"""
    result = format_list_preview([], max_items=5)
    assert result == ""

def test_format_list_preview_exact():
    """Prueba format_list_preview con una lista igual a max_items"""
    items = ["A", "B", "C"]
    result = format_list_preview(items, max_items=3)
    assert result == "A, B, C"
    assert "..." not in result

def test_create_score_row():
    """Prueba create_score_row"""
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
    """Prueba create_score_row con un candidato descalificado"""
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
    """Prueba sort_ranking_dataframe"""
    data = {
        "Nombre Candidato": ["A", "B", "C", "D"],
        "Estado": ["Calificado", "Descalificado", "Calificado", "Descalificado"],
        "Score Final": ["90.0%", "0.0%", "85.0%", "0.0%"]
    }
    df = pd.DataFrame(data)
    
    sorted_df = sort_ranking_dataframe(df)
    
    # Verifica si los calificados están primero
    assert sorted_df.iloc[0]["Estado"] == "Calificado"
    assert sorted_df.iloc[1]["Estado"] == "Calificado"
    
    # Verifica si están ordenados por puntuación dentro de cada grupo
    assert float(sorted_df.iloc[0]["Score Final"].rstrip("%")) > float(sorted_df.iloc[1]["Score Final"].rstrip("%"))
    
    # Verifica si la columna temporal fue eliminada
    assert "Sort Score" not in sorted_df.columns

def test_sort_ranking_dataframe_empty():
    """Prueba sort_ranking_dataframe con un DataFrame vacío"""
    df = pd.DataFrame(columns=["Nombre Candidato", "Estado", "Score Final"])
    sorted_df = sort_ranking_dataframe(df)
    assert len(sorted_df) == 0
    assert list(sorted_df.columns) == ["Nombre Candidato", "Estado", "Score Final"]