"""Módulo de operaciones de manejo de archivos"""
import logging
import io
import os
import pandas as pd
from pathlib import Path
import PyPDF2
from typing import Union, BinaryIO

class FileHandler:
    """Maneja operaciones de lectura de archivos de diferentes tipos"""
    
    @staticmethod
    async def read_pdf_content(file_obj: BinaryIO) -> str:
        """Extrae contenido de texto de un archivo PDF"""
        try:
            # Maneja tanto objetos de archivo como contenido directo
            if hasattr(file_obj, 'read'):
                content = file_obj.read()
            else:
                content = file_obj
            
            # Convierte el contenido binario en un objeto PDF y extrae el texto
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logging.error(f"Error al leer archivo PDF: {str(e)}")
            return ""

    @staticmethod
    async def read_text_content(file_obj: BinaryIO) -> str:
        """Extrae contenido de texto de un archivo de texto"""
        try:
            # Soporta diferentes interfaces de archivo (streamlit, bytes, text)
            if hasattr(file_obj, 'getvalue'):
                content = file_obj.getvalue()
            else:
                content = file_obj.content if hasattr(file_obj, 'content') else file_obj.read()
            
            # Decodifica contenido binario a texto si es necesario
            if isinstance(content, bytes):
                return content.decode('utf-8', errors='replace')
            return str(content)
        except Exception as e:
            logging.error(f"Error al leer archivo de texto: {str(e)}")
            return ""

    @staticmethod
    async def read_file_content(uploaded_file: Union[BinaryIO, None]) -> str:
        """Lee contenido de un archivo subido (TXT o PDF)"""
        if not uploaded_file:
            raise ValueError("No se proporcionó ningún archivo")
            
        try:
            # Determina el tipo de archivo por su extensión
            file_extension = uploaded_file.name.lower().split('.')[-1]
            logging.info(f"Leyendo archivo: {uploaded_file.name} con extensión {file_extension}")

            # Procesa el archivo según su tipo
            if file_extension == 'pdf':
                content = await FileHandler.read_pdf_content(uploaded_file)
                logging.info(f"Texto extraído del PDF: {uploaded_file.name}")
            else:
                content = await FileHandler.read_text_content(uploaded_file)
                logging.info(f"Archivo de texto leído: {uploaded_file.name}")

            return content
        except Exception as e:
            logging.error(f"Error al leer archivo {uploaded_file.name}: {str(e)}")
            raise

    @staticmethod
    def save_dataframe(df: pd.DataFrame, filepath: str, create_dirs: bool = True) -> None:
        """Save a pandas DataFrame to CSV, optionally creating the directory structure.
        
        Args:
            df: DataFrame to save
            filepath: Path to save the CSV file
            create_dirs: If True, create directory structure if it doesn't exist
        """
        if create_dirs:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_csv(filepath, index=False)