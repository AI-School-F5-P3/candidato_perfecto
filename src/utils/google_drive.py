"""Módulo para integrar Google Drive y obtener CVs automáticamente"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import logging
from typing import List, Dict
from src.utils.file_handler import FileHandler

class GoogleDriveIntegration:
    """Clase para interactuar con Google Drive y descargar CVs"""
    def __init__(self, credentials_path: str, folder_id: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        self.service = build('drive', 'v3', credentials=self.credentials)
        self.folder_id = folder_id
        self.file_handler = FileHandler()
        logging.info("Conexión a Google Drive establecida.")

    async def list_cv_files(self) -> List[Dict]:
        """Lista todos los archivos PDF/DOCX en la carpeta especificada de Drive"""
        query = f"'{self.folder_id}' in parents and (mimeType='application/pdf' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')"
        results = self.service.files().list(
            q=query,
            fields="files(id, name, modifiedTime)"  # Añadido modifiedTime para mejor información
        ).execute()
        return results.get('files', [])

    async def download_file(self, file_id: str) -> bytes:
        """Descarga un archivo desde Google Drive"""
        request = self.service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return file_stream.getvalue()

    async def process_cv(self, file_id: str) -> str:
        """Procesa un único CV desde Drive"""
        try:
            content = await self.download_file(file_id)
            file_info = self.service.files().get(fileId=file_id, fields="name").execute()
            fake_file = io.BytesIO(content)
            fake_file.name = file_info['name']
            text = await self.file_handler.read_file_content(fake_file)
            logging.info(f"CV procesado: {file_info['name']}")
            return text
        except Exception as e:
            logging.error(f"Error procesando archivo {file_id}: {str(e)}")
            return ""

    async def process_cvs(self, file_ids: List[str] = None) -> List[str]:
        """
        Procesa CVs de Drive. Si no se proporcionan IDs, procesa todos los CVs de la carpeta.
        """
        if file_ids is None:
            files = await self.list_cv_files()
            file_ids = [file['id'] for file in files]

        cv_contents = []
        for file_id in file_ids:
            text = await self.process_cv(file_id)
            if text:
                cv_contents.append(text)
        
        return cv_contents