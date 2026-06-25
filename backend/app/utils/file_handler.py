"""
File handling utilities
"""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """File upload and management utilities"""
    
    @staticmethod
    def ensure_upload_dir():
        """Ensure upload directory exists and return the path"""
        upload_path = Path(settings.UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for subdir in ['images', 'heatmaps', 'reports', 'videos']:
            (upload_path / subdir).mkdir(exist_ok=True)
        
        return str(upload_path)
    
    @staticmethod
    def generate_filename(original_filename: str, prefix: str = "") -> str:
        """Generate unique filename"""
        ext = Path(original_filename).suffix
        unique_name = f"{prefix}{uuid.uuid4().hex}{ext}"
        return unique_name
    
    @staticmethod
    async def save_upload_file(
        upload_file: UploadFile,
        subdir: str = "images"
    ) -> str:
        """
        Save uploaded file
        
        Args:
            upload_file: FastAPI UploadFile object
            subdir: Subdirectory to save in
        
        Returns:
            Relative file path
        """
        try:
            FileHandler.ensure_upload_dir()
            
            # Generate unique filename
            filename = FileHandler.generate_filename(upload_file.filename)
            file_path = Path(settings.UPLOAD_DIR) / subdir / filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await upload_file.read()
                await f.write(content)
            
            # Return relative path
            return f"{subdir}/{filename}"
            
        except Exception as e:
            logger.error(f"Error saving upload file: {e}")
            raise
    
    @staticmethod
    async def save_image_from_base64(
        base64_data: str,
        subdir: str = "images",
        prefix: str = ""
    ) -> str:
        """
        Save image from base64 string
        
        Args:
            base64_data: Base64 encoded image
            subdir: Subdirectory to save in
            prefix: Filename prefix
        
        Returns:
            Relative file path
        """
        try:
            import base64
            
            FileHandler.ensure_upload_dir()
            
            # Remove data URL prefix if present
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            
            # Decode
            img_bytes = base64.b64decode(base64_data)
            
            # Generate filename
            filename = FileHandler.generate_filename("image.jpg", prefix)
            file_path = Path(settings.UPLOAD_DIR) / subdir / filename
            
            # Save
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(img_bytes)
            
            return f"{subdir}/{filename}"
            
        except Exception as e:
            logger.error(f"Error saving base64 image: {e}")
            raise
    
    @staticmethod
    def get_file_url(file_path: str) -> str:
        """
        Get public URL for file
        
        Args:
            file_path: Relative file path
        
        Returns:
            Full URL
        """
        # In production, this would return S3 URL or CDN URL
        # For local development, return relative path
        return f"/uploads/{file_path}"
    
    @staticmethod
    async def delete_file(file_path: str):
        """Delete a file"""
        try:
            full_path = Path(settings.UPLOAD_DIR) / file_path
            if full_path.exists():
                os.remove(full_path)
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
