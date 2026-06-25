"""
Unit Tests for File Handler Module
"""
import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch
from app.utils.file_handler import FileHandler


@pytest.mark.unit
class TestFileUpload:
    """Test file upload utilities"""
    
    def test_validate_image_extension(self):
        """Test image extension validation"""
        handler = FileHandler()
        
        assert handler.validate_extension("test.jpg") is True
        assert handler.validate_extension("test.jpeg") is True
        assert handler.validate_extension("test.png") is True
        assert handler.validate_extension("test.txt") is False
        assert handler.validate_extension("test.pdf") is False
    
    def test_validate_file_size(self):
        """Test file size validation"""
        handler = FileHandler()
        
        # Mock file with size
        mock_file = Mock()
        mock_file.size = 5 * 1024 * 1024  # 5MB
        
        assert handler.validate_size(mock_file, max_size=10 * 1024 * 1024) is True
        assert handler.validate_size(mock_file, max_size=2 * 1024 * 1024) is False
    
    def test_generate_unique_filename(self):
        """Test unique filename generation"""
        handler = FileHandler()
        
        filename1 = handler.generate_unique_filename("test.jpg")
        filename2 = handler.generate_unique_filename("test.jpg")
        
        assert filename1 != filename2
        assert filename1.endswith(".jpg")
        assert filename2.endswith(".jpg")
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        handler = FileHandler()
        
        sanitized = handler.sanitize_filename("test file@#$.jpg")
        
        assert "@" not in sanitized
        assert "#" not in sanitized
        assert "$" not in sanitized
        assert sanitized.endswith(".jpg")


@pytest.mark.unit
class TestFileOperations:
    """Test file operations"""
    
    @pytest.mark.asyncio
    async def test_save_upload_file(self, tmp_path):
        """Test saving uploaded file"""
        handler = FileHandler()
        
        # Mock uploaded file
        mock_file = Mock()
        mock_file.filename = "test.jpg"
        mock_file.read = Mock(return_value=b"fake image data")
        
        save_path = tmp_path / "test.jpg"
        
        with patch.object(handler, 'get_upload_path', return_value=str(save_path)):
            result = await handler.save_file(mock_file)
            
            assert result is not None
    
    def test_delete_file(self, tmp_path):
        """Test file deletion"""
        handler = FileHandler()
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        assert test_file.exists()
        
        handler.delete_file(str(test_file))
        
        assert not test_file.exists()
    
    def test_file_exists(self, tmp_path):
        """Test file existence check"""
        handler = FileHandler()
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        assert handler.file_exists(str(test_file)) is True
        assert handler.file_exists(str(tmp_path / "nonexistent.txt")) is False


@pytest.mark.unit
class TestPathGeneration:
    """Test path generation"""
    
    def test_get_upload_path(self):
        """Test upload path generation"""
        handler = FileHandler()
        
        path = handler.get_upload_path("test.jpg", subfolder="images")
        
        assert "uploads" in path
        assert "images" in path
        assert path.endswith(".jpg")
    
    def test_create_upload_directories(self, tmp_path):
        """Test upload directory creation"""
        handler = FileHandler()
        
        upload_dir = tmp_path / "uploads" / "images"
        
        handler.ensure_directory_exists(str(upload_dir))
        
        assert upload_dir.exists()
        assert upload_dir.is_dir()
