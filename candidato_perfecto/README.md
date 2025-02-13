# README.md

# Candidato Perfecto

Candidato Perfecto is a Streamlit application designed to analyze job descriptions and resumes to find the best matches based on skills, experience, knowledge, and education. This project leverages semantic analysis and machine learning techniques to streamline the hiring process.

## Project Structure

```
candidato_perfecto
├── src
│   ├── app.py                     # Main entry point for the application
│   ├── components
│   │   ├── __init__.py            # Package initialization for components
│   │   ├── file_reader.py          # Module for reading content from uploaded files
│   │   ├── job_processor.py         # Module for processing job descriptions
│   │   ├── resume_processor.py      # Module for processing resumes
│   │   └── ranking_creator.py       # Module for creating ranking DataFrames
│   ├── frontend
│   │   ├── __init__.py            # Package initialization for frontend
│   │   ├── ui.py                   # Module for Streamlit UI components
│   │   └── styles.css              # Custom styles for the application
│   ├── hr_analysis_system
│   │   ├── __init__.py            # Package initialization for HR analysis system
│   │   ├── semantic_analyzer.py    # Module for semantic analysis of job descriptions and resumes
│   │   ├── matching_engine.py       # Module for matching job profiles with candidate profiles
│   │   ├── ranking_system.py        # Module for ranking candidates
│   │   ├── job_profile.py           # Module defining the JobProfile class
│   │   └── candidate_profile.py     # Module defining the CandidateProfile class
│   └── utils
│       ├── __init__.py            # Package initialization for utilities
│       ├── logging_config.py       # Module for logging configuration
│       └── secrets_manager.py      # Module for managing sensitive information
├── requirements.txt                # List of dependencies required for the project
└── README.md                       # Documentation for the project
```

## Installation

To set up the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd candidato_perfecto
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key in the Streamlit secrets management. Create a `.streamlit/secrets.toml` file with the following content:
   ```
   [openai]
   api_key = "your_api_key_here"
   ```

## Usage

To run the application, execute the following command:
```
streamlit run src/app.py
```

Open your web browser and navigate to `http://localhost:8501` to access the application.

## Features

- Upload job descriptions and resumes in TXT or PDF format.
- Analyze candidates based on skills, experience, and education.
- Customize hiring preferences and weights for different criteria.
- View ranked candidates with detailed scoring breakdowns.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.