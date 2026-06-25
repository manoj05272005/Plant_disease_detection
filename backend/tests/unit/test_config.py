"""
Unit Tests for Configuration Module
"""
import pytest
from app.core.config import settings


@pytest.mark.unit
class TestConfiguration:
    """Test configuration settings"""
    
    def test_app_name_exists(self):
        """Test app name is configured"""
        assert settings.APP_NAME is not None
        assert len(settings.APP_NAME) > 0
    
    def test_mongodb_url_exists(self):
        """Test MongoDB URL is configured"""
        assert settings.MONGODB_URL is not None
        assert "mongodb" in settings.MONGODB_URL.lower()
    
    def test_secret_key_exists(self):
        """Test secret key is configured"""
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 10
    
    def test_algorithm_is_valid(self):
        """Test JWT algorithm is valid"""
        assert settings.ALGORITHM in ["HS256", "HS384", "HS512"]
    
    def test_supported_languages(self):
        """Test supported languages configuration"""
        assert isinstance(settings.SUPPORTED_LANGUAGES, list)
        assert "en" in settings.SUPPORTED_LANGUAGES
        assert len(settings.SUPPORTED_LANGUAGES) >= 6
    
    def test_default_language(self):
        """Test default language is English"""
        assert settings.DEFAULT_LANGUAGE == "en"
    
    def test_token_expiration_settings(self):
        """Test token expiration settings"""
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0
    
    def test_upload_settings(self):
        """Test upload configuration"""
        assert settings.MAX_UPLOAD_SIZE > 0
        assert isinstance(settings.ALLOWED_IMAGE_EXTENSIONS, list)
        assert "jpg" in settings.ALLOWED_IMAGE_EXTENSIONS
    
    def test_confidence_threshold(self):
        """Test AI confidence threshold"""
        assert 0 < settings.CONFIDENCE_THRESHOLD < 1
        assert settings.CONFIDENCE_THRESHOLD == 0.85
