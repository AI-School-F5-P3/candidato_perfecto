Documentación Técnica V2
Esta documentación detalla de manera exhaustiva los archivos Python, clases, métodos y funciones, así como el flujo de datos completo que se inicia a partir del arranque del app.py.

1. Arquitectura y Estructura del Proyecto
El proyecto se encuentra organizado de la siguiente forma:

src/
Contiene la lógica principal.

app.py: Punto de entrada de la aplicación.
hr_analysis_system.py: Implementación de la lógica de análisis, perfiles, coincidencias y ranking.
frontend/
ui.py: Funciones y clases para la interfaz de usuario utilizando Streamlit.
utils/
file_handler.py, utilities.py, text_processor.py: Funciones auxiliares y operaciones comunes.
docs/
Contiene la documentación y reportes de debug (por ejemplo, debug CSV).

tests/
Incluye las pruebas unitarias y de integración.

Otros archivos
Configuración del proyecto, dependencias (requirements.txt, pyproject.toml, setup.py, etc.), y archivos de configuración de Streamlit y VS Code.

2. Componentes Principales y Sus Responsabilidades
2.1. Módulo de Entrada y Orquestación: app.py
La clase principal, HRAnalysisApp, orquesta el flujo completo de la aplicación. Entre sus responsabilidades están:

Inicialización de Componentes:
Crea instancias de proveedores de embeddings, analizadores semánticos, motores de coincidencia, sistemas de ranking y utilidades de manejo de archivos.
Por ejemplo, se instancian la clase OpenAIEmbeddingProvider y SemanticAnalyzer.

Procesamiento de Entrada:
Métodos asíncronos como process_job_description(), process_preferences() y process_resumes() reciben los archivos y textos subidos por el usuario, los pasan por procesos de normalización y estandarización (vía SemanticAnalyzer.standardize_job_description, SemanticAnalyzer.standardize_preferences y SemanticAnalyzer.standardize_resume) y generan estructuras de datos como JobProfile y CandidateProfile.

Generación de Reportes de Depuración:
El método create_debug_dataframe() de la clase crea un DataFrame con información de debug. Posteriormente, este DataFrame se guarda como un archivo CSV en la carpeta debug, lo que permite rastrear el flujo y las puntuaciones calculadas.

Interacción Con la Interfaz de Usuario:
Se integran los resultados procesados en la UI mediante las funciones de la clase UIComponents.

2.2. Módulo de Análisis y Coincidencia: hr_analysis_system.py
Este módulo contiene las clases y métodos dedicados al análisis semántico, evaluación y ranking.

Modelos de Datos:

PreferenciaReclutadorProfile: Representa las preferencias del reclutador.
KillerProfile: Almacena los criterios eliminatorios.
JobProfile: Estructura la descripción del puesto.
CandidateProfile: Estructura los datos estandarizados del CV.
MatchScore: Contiene la puntuación final, puntuaciones por componente, información de debug y razones de descalificación.
Procesamiento de Texto y Análisis Semántico:
La clase base TextAnalyzer maneja la normalización del texto y el cálculo de similitud semántica usando embeddings. Métodos importantes:

preprocess_text(): Estandariza el texto.
calculate_semantic_similarity(): Calcula la similitud utilizando el producto punto de vectores normalizados y, de ser necesario, un fallback a comparación básica.
La clase SemanticAnalyzer extiende TextAnalyzer y utiliza la API de OpenAI para transformar descripciones de trabajo, preferencias y CVs en perfiles estructurados mediante prompts y generación de JSON.

Coincidencia y Evaluación de Candidatos:
La clase MatchingEngine evalúa cada candidato, calculando:

Criterios Eliminatorios:
A través del método check_killer_criteria(), se verifica si el candidato cumple con requisitos obligatorios (habilidades y experiencia) con lógica detallada.

Cálculo de Puntuación de Coincidencia:
El método calculate_match_score() combina las similitudes de componentes (habilidades, experiencia, formación y preferencias del reclutador) usando pesos predefinidos o personalizados. Se genera un objeto MatchScore con información detallada, incluida la data de debug.

Ranking de Candidatos:
La clase RankingSystem ordena a los candidatos basándose en la puntuación calculada y el estado de descalificación. El método rank_candidates() procesa la lista de candidatos y devuelve una lista ordenada de tuplas (candidato, MatchScore).

2.3. Módulo de Interfaz de Usuario: ui.py
Este módulo utiliza Streamlit para construir la interfaz que:

Permite la carga de archivos de descripción del puesto y CVs.
Recibe preferencias del reclutador y criterios eliminatorios a través de campos de texto y sliders.
Muestra los resultados del análisis y ranking de forma interactiva y visual.
3. Flujo de Datos Detallado desde el Arranque en app.py
Inicio de la Aplicación
Configuración y Arranque:

Al iniciar la aplicación, se carga la configuración (por ejemplo, API keys y parámetros globales) y se establece la configuración de la UI mediante UIComponents.setup_page_config.
Se cargan los estilos personalizados con UIComponents.load_custom_css.
Extracción de Datos del Usuario:

El usuario sube la descripción del trabajo, CVs y especifica las preferencias y criterios eliminatorios. Estos datos son procesados en la UI y almacenados en ui_inputs.
Proceso Asíncrono en analyze_candidates:

Se invoca la función asíncrona analyze_candidates(ui_inputs, app) en app.py.
Se verifican las entradas (por ejemplo, existencia de job_file y resume_files).
Se crean diccionarios de preferencias que incluyen tanto las habilidades preferidas como los pesos de evaluación.
Procesamiento de la Descripción del Trabajo:

Se llama a process_job_description(ui_inputs.job_file, hiring_preferences) lo que utiliza SemanticAnalyzer.standardize_job_description para transformar el texto de la vacante en un JobProfile.
Procesamiento de Preferencias del Reclutador:

Se llama a process_preferences(ui_inputs.recruiter_skills) que utiliza SemanticAnalyzer.standardize_preferences para obtener un PreferenciaReclutadorProfile.
Procesamiento de CVs:

Dependiendo de la fuente, se procesan los CVs subidos manualmente o importados desde Google Drive utilizando process_resumes().
Cada CV es transformado en un CandidateProfile mediante SemanticAnalyzer.standardize_resume.
Evaluación y Ranking:

Si se han obtenido perfiles de candidatos, se procede a su evaluación.
Se invoca el método calculate_match_score() a través del MatchingEngine, el cual:
Calcula la similitud semántica para cada componente (habilidades, experiencia, formación) mediante calculate_semantic_similarity().
Evalúa los criterios eliminatorios a través de check_killer_criteria().
Combina los resultados usando un sistema de pesos para generar un MatchScore.
La lista de candidatos junto con sus puntuaciones se ordena utilizando el método rank_candidates() de RankingSystem.
Generación y Almacenamiento del Debug CSV:

Los resultados de debug, que incluyen detalles de puntuaciones por componente, información de killer criteria y datos de similitud, se agrupan en un DataFrame a través de create_debug_dataframe().
Este DataFrame se exporta a un archivo CSV con un nombre basado en la fecha y hora (por ejemplo, debug_YYYYMMDD_HHMMSS.csv) en la carpeta debug.
Actualización de la UI:

Los resultados finales, junto con el debug CSV, se almacenan en el estado de sesión de Streamlit.
Finalmente, se actualiza la interfaz visual con las puntuaciones y el ranking de candidatos utilizando métodos de UIComponents.