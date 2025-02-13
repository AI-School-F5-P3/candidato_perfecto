"""File handling operations module"""
import logging
import io
import PyPDF2
from typing import Union, BinaryIO

class FileHandler:
    """Handles file reading operations for different file types"""
    
    @staticmethod
    async def read_pdf_content(file_obj: BinaryIO) -> str:
        """Extract text content from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_obj.read()))
            content = "\n".join(
                page.extract_text() or ""
                for page in pdf_reader.pages
            )
            return content
        except Exception as e:
            logging.error(f"Error reading PDF file: {str(e)}")
            raise

    @staticmethod
    async def read_text_content(file_obj: BinaryIO) -> str:
        """Read content from text file"""
        try:
            content = file_obj.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            return content
        except Exception as e:
            logging.error(f"Error reading text file: {str(e)}")
            raise

    @staticmethod
    async def read_file_content(uploaded_file: Union[BinaryIO, None]) -> str:
        """Read content from an uploaded file (TXT or PDF)"""
        if not uploaded_file:
            raise ValueError("No file provided")
            
        try:
            file_extension = uploaded_file.name.lower().split('.')[-1]
            logging.info(f"Reading file: {uploaded_file.name} with extension {file_extension}")

            if file_extension == 'pdf':
                content = await FileHandler.read_pdf_content(uploaded_file)
                logging.info(f"Extracted text from PDF: {uploaded_file.name}")
            else:
                content = await FileHandler.read_text_content(uploaded_file)
                logging.info(f"Read text file: {uploaded_file.name}")

            return content
        except Exception as e:
            logging.error(f"Error reading file {uploaded_file.name}: {str(e)}")
            raise