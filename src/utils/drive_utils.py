import streamlit as st
import asyncio
from utils.google_drive import GoogleDriveIntegration

async def load_drive_cvs(app_instance):
    """Función asíncrona para cargar CVs desde Google Drive"""
    try:
        drive_client = GoogleDriveIntegration(
            credentials_path=app_instance.gdrive_credentials,
            folder_id=app_instance.gdrive_folder_id
        )
        cv_texts = await drive_client.process_drive_cvs()
        st.session_state.drive_cvs = cv_texts
        st.success(f"✅ {len(cv_texts)} CVs cargados desde Google Drive")
    except Exception as e:
        st.error(f"❌ Error al cargar desde Google Drive: {str(e)}")
        logging.error(f"Google Drive Error: {str(e)}")