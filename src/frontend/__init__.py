"""Módulo de componentes de interfaz de usuario
Proporciona clases para la creación y gestión de la interfaz gráfica"""

from .ui import (
    # Componentes visuales y de interacción
    UIComponents,
    
    # Estructuras de datos para la interfaz
    WeightSettings,    # Configuración de pesos de puntuación
    UIInputs          # Contenedor de entradas del usuario
)

__all__ = [
    'UIComponents',
    'WeightSettings',
    'UIInputs'
]