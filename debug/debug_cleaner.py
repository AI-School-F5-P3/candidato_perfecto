"""
Module to clean up old debug files.
"""
import os
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


class DebugCleaner:
    """Class responsible for managing and cleaning up old debug files."""
    
    def __init__(self):
        """Initialize the DebugCleaner."""
        self.debug_dir = self._get_debug_directory()
        logging.info(f"DebugCleaner initialized for directory: {self.debug_dir}")
    
    @staticmethod
    def _get_debug_directory() -> str:
        """Get the path to the debug directory."""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")
    
    def clean_old_files(self, days: int = 7) -> List[str]:
        """
        Delete debug files that are older than the specified number of days.
        
        Args:
            days: Number of days before files are considered old (default: 7)
            
        Returns:
            List of deleted file paths
        """
        if not os.path.exists(self.debug_dir):
            logging.warning(f"Debug directory does not exist: {self.debug_dir}")
            return []
        
        # Calculate cutoff date
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_files = []
        
        # Check all files in the debug directory
        for filename in os.listdir(self.debug_dir):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(self.debug_dir, filename)
            file_mod_time = os.path.getmtime(file_path)
            
            if file_mod_time < cutoff_time:
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    logging.info(f"Deleted old debug file: {file_path}")
                except Exception as e:
                    logging.error(f"Error deleting {file_path}: {str(e)}")
        
        if deleted_files:
            logging.info(f"Cleaned {len(deleted_files)} old debug files")
        else:
            logging.info("No old debug files to clean")
            
        return deleted_files
    
    @staticmethod
    def get_file_age(file_path: str) -> int:
        """
        Get the age of a file in days.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Age in days
        """
        if not os.path.exists(file_path):
            return -1
            
        file_mod_time = os.path.getmtime(file_path)
        file_mod_date = datetime.fromtimestamp(file_mod_time)
        current_date = datetime.now()
        
        age_days = (current_date - file_mod_date).days
        return age_days
    
    def list_debug_files(self, max_days: Optional[int] = None) -> List[dict]:
        """
        List all debug files with their ages.
        
        Args:
            max_days: If specified, only list files younger than max_days
            
        Returns:
            List of dictionaries with file info
        """
        if not os.path.exists(self.debug_dir):
            return []
            
        files_info = []
        
        for filename in os.listdir(self.debug_dir):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(self.debug_dir, filename)
            age_days = self.get_file_age(file_path)
            
            # Skip if older than max_days (if specified)
            if max_days is not None and age_days > max_days:
                continue
                
            file_info = {
                "filename": filename,
                "path": file_path,
                "age_days": age_days,
                "size_bytes": os.path.getsize(file_path)
            }
            files_info.append(file_info)
            
        return files_info