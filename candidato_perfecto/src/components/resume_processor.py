class ResumeProcessor:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    async def process_resumes(self, resume_files):
        """Process multiple resume files and return candidate profiles."""
        candidate_profiles = []
        for resume_file in resume_files:
            try:
                resume_content = await self.read_file_content(resume_file)
                profile = await self.analyzer.standardize_resume(resume_content)
                candidate_profiles.append(profile)
            except Exception as e:
                logging.error(f"Error processing resume {resume_file.name}: {str(e)}")
        return candidate_profiles

    async def read_file_content(self, uploaded_file):
        """Read content from an uploaded file (TXT or PDF)."""
        try:
            file_extension = uploaded_file.name.lower().split('.')[-1]
            logging.info(f"Reading file: {uploaded_file.name} with extension {file_extension}")

            if file_extension == 'pdf':
                import PyPDF2
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                content = ""
                for page in pdf_reader.pages:
                    text = page.extract_text() or ""
                    content += text + "\n"
            else:
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')

            return content
        except Exception as e:
            logging.error(f"Error reading file {uploaded_file.name}: {str(e)}")
            raise e