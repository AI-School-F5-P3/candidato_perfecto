

#  CandidatoPerfecto 

<div align="center">
    <img src="logoNFQ.png" alt="Logo de IA Recruiter" />
</div>

## Índice  
- [Descripción de la Aplicación](#descripcion-de-la-aplicacion)  
- [🌟 Funcionalidades Clave](#funcionalidades-clave)  
- [Beneficios de la Aplicación](#beneficios-de-la-aplicacion)  
- [Público Objetivo](#publico-objetivo)  
- [Tecnologías y Bibliotecas](#tecnologias-y-bibliotecas)  
- [Documentación](#documentacion)  
- [Conclusión](#conclusion)  
- [Prueba nuestra App](#prueba-nuestra-app)  
--- 

## Descripción de la Aplicación
**IA Recruiter** es una innovadora aplicación basada en Inteligencia Artificial que revoluciona el proceso de selección de talento. Diseñada para ayudar a empresas y reclutadores a encontrar al candidato ideal, la aplicación analiza y clasifica automáticamente un conjunto de perfiles profesionales para determinar cuáles se ajustan mejor a una vacante específica.


---



## 🌟 Funcionalidades Clave
<details>
  <summary>Ver más</summary>

### 🔍 Análisis y Clasificación de Candidatos
- Evaluación de **20 CVs** proporcionados, utilizando algoritmos de IA Generativa para identificar el grado de adecuación de cada perfil a una vacante.
- Generación de un **ranking** basado en criterios semánticos y cuantitativos.

### 📄 Procesamiento de Vacantes
- Recepción de la descripción detallada del puesto y las preferencias del hiring manager.
- Análisis profundo de los requisitos del puesto para una mejor correspondencia con los candidatos.

### ⚖️ Cumplimiento Normativo y Ético ---> COMPLETAR
- Implementación de filtros y principios éticos para garantizar una selección justa y transparente.
- Consideración de regulaciones vigentes en el uso de IA para la contratación.

### 📊 Generación de Reportes y Visualización de Datos
- Representación visual de los resultados del ranking para facilitar la toma de decisiones.
- Análisis detallado del por qué cada candidato ha sido clasificado en determinada posición.

### ☁️ Desafío Extra: Integración con Google Drive
- Automatización del proceso de importación de CVs directamente desde Google Drive.
- Optimización del flujo de trabajo y reducción de errores manuales en la gestión de datos.

</details>
---

## Beneficios de la Aplicación

<details>
  <summary>Ver más</summary>

- ⏳ **Optimización de tiempo** en la selección de candidatos.
- 🎯 **Mayor precisión** en la identificación del talento adecuado.
- 🔍 **Transparencia y equidad** en el proceso de reclutamiento.
- ☁️ **Fácil integración** con herramientas de almacenamiento en la nube.


</details>
---

## Público Objetivo


- 🏢 Empresas y departamentos de Recursos Humanos.
- 🕵️‍♂️ Agencias de reclutamiento y selección de personal.
- 👩‍💼 Profesionales que buscan optimizar procesos de contratación con IA.

**IA Recruiter** es la solución definitiva para empresas que buscan optimizar su proceso de selección con tecnología avanzada. 🚀



---

## Tecnologías y Bibliotecas
<details>
  <summary>Ver más</summary>

Para desarrollar la aplicación **IA Recruiter**, se pueden utilizar diversas tecnologías y bibliotecas que faciliten la implementación de sus funcionalidades clave. A continuación, se presenta una lista de tecnologías y bibliotecas relevantes:

### 💻 Lenguajes de Programación
- **Python**: Ideal para el desarrollo de aplicaciones de IA y análisis de datos.


### 🗣️ Procesamiento de Lenguaje Natural (NLP)
- **spaCy**: Para el procesamiento de texto y análisis semántico de los CVs.
- **NLTK**: Otra biblioteca para el procesamiento de lenguaje natural.

### 📈 Visualización de Datos
- **Bibliotecas integradas en Streamlit**: Para crear gráficos y visualizaciones de datos.

### 🌐 Frontend
- **Streamlit**: Para construir interfaces de usuario interactivas.


### 🗄️ Base de Datos
- **PostgreSQL**: Para almacenar datos de candidatos y vacantes.
- **MongoDB**: Una base de datos NoSQL que puede ser útil para almacenar datos no estructurados.

### ☁️ Integración con Google Drive
- **Google Drive API**: Para permitir la importación automática de CVs desde Google Drive.
-  Fácil integración con herramientas de almacenamiento en la nube.


### Contenedores y Despliegue
- **Docker**: Para crear contenedores que faciliten el despliegue de la aplicación.

</details>
--- 

### Documentación
<details>
  <summary>Ver más</summary>

- [1.Diagrama de Flujo](#1.-diagrama-de-flujo) 
- [2. Funcionamiento](#funcionamiento) 
- [3.Componentes Principales](#componentes-principales) 
- [4.Flujo desglosado](#flujo-desglosado) 
- [5.Condiguración](#configuracion) 
- [6.Estructura de Pruebas](#estructurad-de-pruebas) 
- [7.Dependencias Principales](#dependencias-principales) 
- [8.Manejo de Errores](#manejor-de-errores) 
- [9.Implicaciones de Rendimiento](#implicaciones-de-rendimiento)

</details>
---
## 1.Diagrama de Flujo
<details>
  <summary>Ver más</summary>
    
<div align="center">
    <img src="diagrama/hr-system-drawio V2.drawio.png" alt="Logo de IA Recruiter" />
</div>


    
## 2.Funcionamiento
<details>
  <summary>Ver más</summary>
    
### 1. Proceso
### 1.1 Inicio de la Aplicación

La aplicación se ejecuta mediante `app.py`.

- Se configuran los componentes de la interfaz de usuario y se carga el CSS personalizado.
- Se muestra la página principal con el título y la descripción de la aplicación.

### 1.2 Carga de CVs y Descripciones de Puestos

- Los usuarios pueden cargar CVs manualmente o importarlos desde Google Drive.
- Se pueden introducir descripciones de puestos y preferencias del reclutador.

### 1.3 Procesamiento de CVs y Descripciones de Puestos

- La clase `HRAnalysisApp` gestiona el procesamiento de los archivos.
- Se utilizan métodos asincrónicos para estandarizar y analizar los textos.

### 1.4 Análisis y Ranking

- Se realiza un análisis semántico comparando las habilidades y experiencia de los CVs con los requisitos del puesto.
- Se genera un ranking basado en criterios cuantitativos y semánticos.

### 1.5 Visualización del Ranking

- La interfaz de usuario en Streamlit muestra el ranking de los candidatos.
- Se incluyen gráficos interactivos y opción para exportar los resultados a Excel.


### 2. Análisis de la Descripción del Puesto
### 2.1 Modelo Utilizado

La aplicación utiliza un modelo de lenguaje grande (LLM) de OpenAI, que extrae y estandariza información clave de la descripción del puesto.

### 2.2 Proceso de Análisis

- **Preprocesamiento del Texto**: Se eliminan detalles innecesarios y se extrae la información clave.
- **Generación del Prompt**: Se construye un prompt con instrucciones detalladas para el modelo.
- **Llamada al Modelo**: El LLM analiza el texto y devuelve un JSON con la información estructurada.
- **Extracción de Palabras Clave**: Se identifican habilidades, experiencia y formación requeridas para el puesto.

### 2.3 Implementación en Código

El siguiente fragmento de código muestra cómo se analiza la descripción del puesto:

```python
class SemanticAnalyzer(TextAnalyzer):
    async def standardize_job_description(self, description: str, hiring_preferences: dict) -> JobProfile:
        processed_text = self.preprocess_text(description)
        prompt = f"""
        Extract key information from this job description:
        - Standardize skills, experience, and education
        - Output as JSON format
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        profile_data = json.loads(response.choices[0].message.content)
        return JobProfile(
            nombre_vacante=profile_data["nombre_vacante"],
            habilidades=profile_data["habilidades"],
            experiencia=profile_data["experiencia"],
            formacion=profile_data["formacion"]
        )
```


### 3. Comparación con los CVs
### 3.1 Proceso de Comparación

- **Estandarización de los CVs**: Se analizan los CVs utilizando el mismo modelo LLM.
- **Extracción de Características**: Se identifican habilidades, experiencia y educación.
- **Cálculo de Puntuaciones**: Se comparan los CVs con la descripción del puesto.
- **Generación del Ranking**: Se asigna una puntuación a cada candidato en función de su idoneidad.

### 3.2 Código Relevante para Procesar CVs

```python
class SemanticAnalyzer(TextAnalyzer):
    async def standardize_resume(self, resume_text: str) -> CandidateProfile:
        processed_text = self.preprocess_text(resume_text)
        prompt = """
        Extract key information from this resume:
        - Standardize skills, experience, and education
        - Output as JSON format
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        profile_data = json.loads(response.choices[0].message.content)
        return CandidateProfile(
            nombre_candidato=profile_data["nombre_candidato"],
            habilidades=profile_data["habilidades"],
            experiencia=profile_data["experiencia"],
            formacion=profile_data["formacion"]
        )
```

### 4. Visualización del Ranking en Streamlit
### 4.1 Implementación en la Interfaz

- Se muestra un ranking con los mejores candidatos.
- Se utilizan gráficos interactivos para visualizar los datos.
- Se permite la exportación de resultados en formatos como CSV o Excel.

### 4.2 Código para la Visualización

```python
async def analyze_candidates(ui_inputs, app):
    if 'drive_cvs' in st.session_state:
        candidate_profiles = await app.process_resumes(st.session_state.drive_cvs)
    else:
        candidate_profiles = await app.process_resumes(ui_inputs.resume_files)
    
    rankings = await app.ranking_system.rank_candidates(
        job_profile, recruiter_preferences, candidate_profiles,
        standardized_killer_criteria, hiring_preferences["weights"]
    )
    styled_df = app.create_ranking_dataframe(rankings)
    UIComponents.display_ranking(
        df=styled_df, job_profile=job_profile,
        recruiter_preferences=recruiter_preferences,
        killer_criteria=standardized_killer_criteria
    )
```



## 3.Componentes Principales

1. **hr_analysis_system.py**
   - Contiene la lógica de negocio principal y las estructuras de datos
   - Componentes clave:
     - Modelos de datos (`JobProfile`, `CandidateProfile`, `MatchScore`)
     - Interfaz `IEmbeddingProvider` e implementación `OpenAIEmbeddingProvider`
     - Clase base `TextAnalyzer` con cálculo de similitud semántica
     - `SemanticAnalyzer` para procesamiento de texto usando OpenAI
     - `MatchingEngine` para la lógica de coincidencia candidato-trabajo
     - `RankingSystem` para clasificación de candidatos

2. **app.py**
   - Punto de entrada principal de la aplicación
   - Integra todos los componentes
   - Maneja el flujo de la aplicación y la interacción del usuario
   - Componentes:
     - Clase `HRAnalysisApp` coordinando todas las operaciones
     - Función principal asíncrona gestionando el ciclo de vida de la aplicación

3. **frontend/**
   - Componentes de UI y estilos
   - Componentes:
     - Clase `UIComponents` gestionando todos los elementos de UI
     - Estilizado CSS personalizado
     - Estructuras de datos de entrada/salida (`WeightSettings`, `UIInputs`)

4. **utils/**
   - Funciones de utilidad y ayudantes
   - Componentes:
     - `FileHandler` para operaciones con archivos
     - Utilidades comunes para formateo y procesamiento de datos
     - Configuración de registro


## 4. Flujo desglosado
<details>
  <summary>Ver más</summary>

1. **Procesamiento de Entrada**
   ```
   Entrada Usuario -> FileHandler -> SemanticAnalyzer -> Perfiles Estandarizados
   ```
   - Se cargan la descripción del trabajo y los CVs
   - Los archivos son procesados por FileHandler
   - El texto es analizado y estructurado por SemanticAnalyzer 
   - Produce objetos estandarizados JobProfile y CandidateProfile

2. **Proceso de Coincidencia**
   ```
   Perfiles -> MatchingEngine -> MatchScore
   ```
   - Los perfiles se comparan usando similitud semántica
   - Se verifican los criterios eliminatorios si se proporcionan
   - Se calculan las puntuaciones por componente (habilidades, experiencia, educación)
   - Se generan las puntuaciones finales de coincidencia

3. **Proceso de Clasificación**
   ```
   MatchScores -> RankingSystem -> Resultados Clasificados
   ```
   - Los candidatos se ordenan según puntuaciones de coincidencia
   - Se identifican los candidatos descalificados
   - Los resultados se formatean para visualización

4. **Visualización**
   ```
   Resultados Clasificados -> UIComponents -> Interfaz de Usuario
   ```
   - Los resultados se convierten a DataFrame
   - Se aplican estilos basados en puntuaciones
   - Se crean elementos interactivos
   - La visualización final se presenta al usuario


---
    
## 5. Configuración
<details>
  <summary>Ver más</summary>

El sistema utiliza un módulo de configuración central (`config.py`) con los siguientes componentes:

1. **ModelConfig**
   - Configuración del modelo LLM
   - Configuración del modelo de embeddings

2. **MatchingConfig**
   - Umbrales de coincidencia
   - Distribuciones de peso por defecto

3. **DisplayConfig**
   - Configuración de visualización UI
   - Esquemas de color
   - Límites de vista previa



    
## 6. Estructura de Pruebas
<details>
  <summary>Ver más</summary>

El conjunto de pruebas está organizado en los siguientes componentes:

1. **Pruebas Unitarias**
   - `test_semantic_analyzer.py`: Pruebas para análisis de texto
   - `test_matching_engine.py`: Pruebas para lógica de coincidencia
   - `test_ranking_system.py`: Pruebas para funcionalidad de clasificación
   - `test_file_handler.py`: Pruebas para operaciones con archivos
   - `test_utilities.py`: Pruebas para funciones de utilidad

2. **Configuración de Pruebas**
   - `conftest.py`: Fixtures compartidos de prueba
   - `pyproject.toml`: Configuración de pruebas y cobertura
  


## 7. Dependencias
<details>
  <summary>Ver más</summary>

 Las dependencias clave están organizadas por funcionalidad:

1. **Procesamiento Principal**
   - streamlit: Framework de UI
   - pandas: Manipulación de datos
   - numpy: Operaciones numéricas

2. **IA/ML**
   - openai: LLM y embeddings

3. **Manejo de Archivos**
   - PyPDF2: Procesamiento de PDF
   - aiofiles: Operaciones de archivo asíncronas

4. **Pruebas**
   - pytest: Framework de pruebas
   - pytest-asyncio: Soporte de pruebas asíncronas
   - pytest-cov: Informes de cobertura




## 8. Manejo de Errores
<details>
  <summary>Ver más</summary>

El sistema implementa un manejo integral de errores:

1. **Operaciones de Archivo**
   - Tipos de archivo inválidos
   - Problemas de codificación
   - Errores de extracción PDF

2. **Operaciones de API**
   - Errores de API de OpenAI
   - Limitación de tasa
   - Problemas de conexión

3. **Errores de Procesamiento**
   - Datos de entrada inválidos
   - Fallos de análisis
   - Errores de puntuación

4. **Errores de UI**
   - Validación de entrada
   - Formateo de visualización
   - Gestión de estado


## 9. Implicaciones de Rendimiento
<details>
  <summary>Ver más</summary>

1. **Operaciones Asíncronas**
   - Lectura de archivos asíncrona
   - Llamadas API no bloqueantes
   - UI permanece responsiva

2. **Gestión de Recursos**
   - Uso eficiente de memoria
   - Manejo apropiado de archivos
   - Agrupación de conexiones

3. **Optimización**
   - Caché de embeddings
   - Procesamiento por lotes donde sea posible
   - Operaciones eficientes con DataFrame


### Prueba nuestra App
<details>
  <summary>Ver más</summary>

## 🚀 Instrucciones de Uso
Sigue estos pasos para instalar y ejecutar la aplicación correctamente.

## 1. Clonar el Repositorio  
```bash
git clone https://github.com/tu_usuario/tu_repositorio.git
cd tu_repositorio
```
## 2. Crear un Entorno Virtual (Opcional pero Recomendado)
```
python -m venv venv
source venv/bin/activate  # En macOS/Linux
venv\Scripts\activate      # En Windows
```
## 3. Instala dependencias
```
pip install -r requirements.txt

```
## 4. Ejecutar la Aplicación
```
streamlit run src/app.py

```

## 5. Detener la applicación
```
Detener la Aplicación
```

## 6. Listo! Ahora puedes acceder a la aplicación desde tu navegador en
- http://localhost:8501/`

## 7. Explicación
🔹 **Explicación:**  
- Se clona el repositorio y se accede a la carpeta del proyecto.  
- Se recomienda crear un entorno virtual para aislar las dependencias.  
- Se instalan los paquetes necesarios desde `requirements.txt`.  
- Se ejecuta la aplicación con **Streamlit**.  
- Se indica cómo detener la aplicación cuando sea necesario.  

### Conclusión
    
La combinación de estas tecnologías y bibliotecas permitirá desarrollar una aplicación robusta y eficiente que cumpla con los objetivos de **CandidatoPerfecto**, optimizando el proceso de selección de talento mediante el uso de inteligencia artificial y garantizando un enfoque ético y normativo.
