import streamlit as st
import asyncio
import pandas as pd
import json
from pathlib import Path
from typing import List
import aiofiles
from hr_analysis_system import (
    SemanticAnalyzer,
    MatchingEngine,
    RankingSystem,
    JobProfile,
    CandidateProfile
)

class HRAnalysisApp:
    def __init__(self):
        # Initialize OpenAI API key from Streamlit secrets
        self.api_key = st.secrets["openai"]["api_key"]
        
        # Initialize our analysis components
        self.analyzer = SemanticAnalyzer(self.api_key)
        self.matching_engine = MatchingEngine(self.analyzer)
        self.ranking_system = RankingSystem(self.matching_engine)

    async def read_file_content(self, uploaded_file) -> str:
        """Read content from an uploaded file (TXT or PDF)"""
        # Get file extension
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            import PyPDF2
            import io
            
            # Read PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            content = ""
            # Extract text from all pages
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
        else:
            # Handle as text file
            content = uploaded_file.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
                
        return content

    async def process_job_description(self, job_file, hiring_preferences: dict) -> JobProfile:
        """Process the job description file and hiring preferences"""
        job_content = await self.read_file_content(job_file)
        return await self.analyzer.standardize_job_description(job_content, hiring_preferences)

    async def process_resumes(self, resume_files) -> List[CandidateProfile]:
        """Process multiple resume files"""
        candidate_profiles = []
        for resume_file in resume_files:
            resume_content = await self.read_file_content(resume_file)
            profile = await self.analyzer.standardize_resume(resume_content)
            candidate_profiles.append(profile)
        return candidate_profiles

    def create_ranking_dataframe(self, rankings) -> pd.DataFrame:
        """Convert rankings to a pandas DataFrame for display"""
        data = []
        for candidate, scores in rankings:
            row = {
                'Candidate Name': candidate.name,
                'Total Score': scores['final_score'],  # Keep as float
                'Required Skills': scores['component_scores']['required_skills'],  # Keep as float
                'Preferred Skills': scores['component_scores']['preferred_skills'],  # Keep as float
                'Experience Match': scores['component_scores']['experience'],  # Keep as float
                'Education Match': scores['component_scores']['education'],  # Keep as float
                'Skills': ', '.join(candidate.skills[:5]) + ('...' if len(candidate.skills) > 5 else ''),
                'Experience (Years)': candidate.experience_years,
                'Education': candidate.education_level
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Format percentage columns after creating the style
        percentage_cols = ['Total Score', 'Required Skills', 'Preferred Skills', 'Experience Match', 'Education Match']
        
        # Create the styled dataframe
        styled_df = df.style.background_gradient(
            subset=['Total Score'],
            cmap='RdYlGn'
        )
        
        # Format percentage columns
        for col in percentage_cols:
            styled_df = styled_df.format({col: '{:.2%}'})
        
        return styled_df

async def main():
    st.title("HR Resume Analysis System")
    st.write("""
    This system analyzes job descriptions and resumes to find the best matches based on skills, 
    experience, and education. Please upload the required files and provide hiring preferences below.
    """)

    # Initialize the application
    app = HRAnalysisApp()

    # Create three main sections using columns
    job_col, prefs_col = st.columns(2)

    with job_col:
        st.subheader("Job Description")
        job_file = st.file_uploader(
            "Upload job description (TXT or PDF)", 
            type=['txt', 'pdf']
        )

    with prefs_col:
        st.subheader("Hiring Preferences")
        min_experience = st.number_input(
            "Minimum years of experience", 
            min_value=0, 
            value=3
        )
        education_level = st.selectbox(
            "Required education level",
            ["High School", "Bachelor", "Master", "PhD"]
        )
        important_skills = st.text_area(
            "Important skills (one per line)",
            height=100
        )

    st.subheader("Candidate Resumes")
    resume_files = st.file_uploader(
        "Upload candidate resumes (TXT or PDF)", 
        type=['txt', 'pdf'],
        accept_multiple_files=True
    )

    if st.button("Analyze Candidates") and job_file and resume_files:
        try:
            with st.spinner("Analyzing candidates..."):
                # Prepare hiring preferences
                hiring_preferences = {
                    "minimum_experience": min_experience,
                    "education_level": education_level,
                    "important_skills": [
                        skill.strip() 
                        for skill in important_skills.split('\n') 
                        if skill.strip()
                    ]
                }

                # Process job description
                job_profile = await app.process_job_description(
                    job_file, 
                    hiring_preferences
                )

                # Process resumes
                candidate_profiles = await app.process_resumes(resume_files)

                # Generate rankings
                rankings = await app.ranking_system.rank_candidates(
                    job_profile, 
                    candidate_profiles
                )

                # Display results
                st.subheader("Candidate Rankings")
                styled_df = app.create_ranking_dataframe(rankings)
                st.dataframe(styled_df, use_container_width=True)

                # Display detailed job requirements
                with st.expander("View Job Requirements"):
                    st.json({
                        "title": job_profile.title,
                        "required_skills": job_profile.required_skills,
                        "preferred_skills": job_profile.preferred_skills,
                        "experience_years": job_profile.experience_years,
                        "education_level": job_profile.education_level,
                        "responsibilities": job_profile.responsibilities,
                        "industry_knowledge": job_profile.industry_knowledge
                    })

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            raise e

if __name__ == "__main__":
    asyncio.run(main())