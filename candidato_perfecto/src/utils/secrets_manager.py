# File: /candidato_perfecto/candidato_perfecto/src/utils/secrets_manager.py

import streamlit as st
import logging

class SecretsManager:
    """Class to manage retrieval of sensitive information from Streamlit secrets."""
    
    @staticmethod
    def get_api_key() -> str:
        """Retrieve the OpenAI API key from Streamlit secrets."""
        try:
            api_key = st.secrets["openai"]["api_key"]
            logging.info("API key retrieved successfully.")
            return api_key
        except KeyError as e:
            logging.error(f"API key not found in secrets: {str(e)}")
            raise e
        except Exception as e:
            logging.error(f"Error retrieving API key: {str(e)}")
            raise e