class JobProcessor:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    async def process_job_description(self, job_file, hiring_preferences):
        """Process the job description file and hiring preferences"""
        try:
            job_content = await self.read_file_content(job_file)
            logging.info("Processing job description.")
            job_profile = await self.analyzer.standardize_job_description(job_content, hiring_preferences)
            logging.info("Job description processed successfully.")
            return job_profile
        except Exception as e:
            logging.error(f"Error processing job description: {str(e)}")
            raise e

    async def read_file_content(self, uploaded_file):
        """Read content from an uploaded file (TXT or PDF)"""
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
                logging.info(f"Extracted text from PDF: {uploaded_file.name}")
            else:
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                logging.info(f"Read text file: {uploaded_file.name}")

            return content
        except Exception as e:
            logging.error(f"Error reading file {uploaded_file.name}: {str(e)}")
            raise e