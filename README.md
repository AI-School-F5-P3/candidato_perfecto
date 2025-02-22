
#  CandidatoPerfecto 

<div align="center">
    <img src="logoNFQ.png" alt="Logo de IA Recruiter" />
</div>

## Índice  
- [Descripción de la Aplicación](#descripción-de-la-aplicación)  
- [🌟 Funcionalidades Clave](#-funcionalidades-clave)  
- [Beneficios de la Aplicación](#beneficios-de-la-aplicación)  
- [Público Objetivo](#público-objetivo)  
- [Tecnologías y Bibliotecas](#tecnologías-y-bibliotecas)  
- [Documentación](#documentación)  
- [Conclusión](#conclusión)
- [Prueba nuestra App](#prueba-nuestra-app!) 
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

- ⏳ **Ahorro de tiempo** en la selección de candidatos.
- 🎯 **Mayor precisión** en la identificación del talento adecuado.
- 🔍 **Transparencia y equidad** en el proceso de reclutamiento.
- ☁️ **Fácil integración** con herramientas de almacenamiento en la nube.

</details>

---

## Público Objetivo
<details>
  <summary>Ver más</summary>

- 🏢 Empresas y departamentos de Recursos Humanos.
- 🕵️‍♂️ Agencias de reclutamiento y selección de personal.
- 👩‍💼 Profesionales que buscan optimizar procesos de contratación con IA.

**IA Recruiter** es la solución definitiva para empresas que buscan optimizar su proceso de selección con tecnología avanzada. 🚀

</details>

---

## Tecnologías y Bibliotecas

<details>
  <summary>Ver más</summary>
  
--
Para desarrollar la aplicación **IA Recruiter**, se pueden utilizar diversas tecnologías y bibliotecas que faciliten la implementación de sus funcionalidades clave. A continuación, se presenta una lista de tecnologías y bibliotecas relevantes:

### 💻 Lenguajes de Programación
- **Python**: Ideal para el desarrollo de aplicaciones de IA y análisis de datos.
- **JavaScript**: Para el desarrollo del frontend y la interacción con el usuario.

### 🤖 Frameworks y Librerías de IA
- **TensorFlow**: Para construir y entrenar modelos de IA generativa.
- **PyTorch**: Otra opción popular para el desarrollo de modelos de aprendizaje profundo.
- **scikit-learn**: Para tareas de análisis de datos y clasificación.

### 🗣️ Procesamiento de Lenguaje Natural (NLP)
- **spaCy**: Para el procesamiento de texto y análisis semántico de los CVs.
- **NLTK**: Otra biblioteca para el procesamiento de lenguaje natural.
- **Transformers (Hugging Face)**: Para utilizar modelos preentrenados de NLP, como BERT o GPT, que pueden ayudar en la clasificación de textos.

### 📈 Visualización de Datos
- **Matplotlib**: Para crear gráficos y visualizaciones de datos.
- **Seaborn**: Para visualizaciones estadísticas más atractivas.
- **Plotly**: Para gráficos interactivos y dashboards.

### 🖥️ Backend y API
- **Flask**: Un microframework para crear aplicaciones web en Python.
- **Django**: Un framework más completo para aplicaciones web que puede ser útil si se requiere una estructura más robusta.

### 🌐 Frontend
- **React**: Para construir interfaces de usuario interactivas.
- **Vue.js**: Otra opción para el desarrollo de interfaces de usuario.

### 🗄️ Base de Datos
- **PostgreSQL**: Para almacenar datos de candidatos y vacantes.
- **MongoDB**: Una base de datos NoSQL que puede ser útil para almacenar datos no estructurados.

### ☁️ Integración con Google Drive
- **Google Drive API**: Para permitir la importación automática de CVs desde Google Drive.
-  Fácil integración con herramientas de almacenamiento en la nube.

### ⚖️ Librerías

### Contenedores y Despliegue
- **Docker**: Para crear contenedores que faciliten el despliegue de la aplicación.
- **Kubernetes**: Para la orquestación de contenedores en entornos de producción.


</details>


--- 

### Documentación
<details>
  <summary>Ver más</summary>

## 1. Diagrama de Flujo de Google Drive
Falta

## 2. Flujo Completo de la Aplicación

### 2.1 Inicio de la Aplicación

La aplicación se ejecuta mediante `app.py`.

- Se configuran los componentes de la interfaz de usuario y se carga el CSS personalizado.
- Se muestra la página principal con el título y la descripción de la aplicación.

### 2.2 Carga de CVs y Descripciones de Puestos

- Los usuarios pueden cargar CVs manualmente o importarlos desde Google Drive.
- Se pueden introducir descripciones de puestos y preferencias del reclutador.

### 2.3 Procesamiento de CVs y Descripciones de Puestos

- La clase `HRAnalysisApp` gestiona el procesamiento de los archivos.
- Se utilizan métodos asincrónicos para estandarizar y analizar los textos.

### 2.4 Análisis y Ranking

- Se realiza un análisis semántico comparando las habilidades y experiencia de los CVs con los requisitos del puesto.
- Se genera un ranking basado en criterios cuantitativos y semánticos.

### 2.5 Visualización del Ranking

- La interfaz de usuario en Streamlit muestra el ranking de los candidatos.
- Se incluyen gráficos interactivos y opción para exportar los resultados a Excel.

## 3. Análisis de la Descripción del Puesto

### 3.1 Modelo Utilizado

La aplicación utiliza un modelo de lenguaje grande (LLM) de OpenAI, que extrae y estandariza información clave de la descripción del puesto.

### 3.2 Proceso de Análisis

- **Preprocesamiento del Texto**: Se eliminan detalles innecesarios y se extrae la información clave.
- **Generación del Prompt**: Se construye un prompt con instrucciones detalladas para el modelo.
- **Llamada al Modelo**: El LLM analiza el texto y devuelve un JSON con la información estructurada.
- **Extracción de Palabras Clave**: Se identifican habilidades, experiencia y formación requeridas para el puesto.

### 3.3 Implementación en Código

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
## 4. Comparación con los CVs

### 4.1 Proceso de Comparación

- **Estandarización de los CVs**: Se analizan los CVs utilizando el mismo modelo LLM.
- **Extracción de Características**: Se identifican habilidades, experiencia y educación.
- **Cálculo de Puntuaciones**: Se comparan los CVs con la descripción del puesto.
- **Generación del Ranking**: Se asigna una puntuación a cada candidato en función de su idoneidad.

### 4.2 Código Relevante para Procesar CVs

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
## 5. Visualización del Ranking en Streamlit

### 5.1 Implementación en la Interfaz

- Se muestra un ranking con los mejores candidatos.
- Se utilizan gráficos interactivos para visualizar los datos.
- Se permite la exportación de resultados en formatos como CSV o Excel.

### 5.2 Código para la Visualización

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
</details>

---

### Conclusión
<details>
  <summary>Ver más</summary>
    
La combinación de estas tecnologías y bibliotecas permitirá desarrollar una aplicación robusta y eficiente que cumpla con los objetivos de **CandidatoPerfecto**, optimizando el proceso de selección de talento mediante el uso de inteligencia artificial y garantizando un enfoque ético y normativo.

</details>

