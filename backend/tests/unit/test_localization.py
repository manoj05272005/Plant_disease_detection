"""
Unit Tests for Localization Module
"""
import pytest
from app.utils.localization import Localizer, get_language_from_request


@pytest.mark.unit
class TestLocalization:
    """Test localization utilities"""
    
    def test_translate_english(self):
        """Test translation to English"""
        text = Localizer.translate("app_name", "en")
        
        assert text == "Crop Disease Detection"
    
    def test_translate_hindi(self):
        """Test translation to Hindi"""
        text = Localizer.translate("welcome", "hi")
        
        assert text == "स्वागत है"
    
    def test_translate_kannada(self):
        """Test translation to Kannada"""
        text = Localizer.translate("welcome", "kn")
        
        assert text == "ಸ್ವಾಗತ"
    
    def test_translate_tamil(self):
        """Test translation to Tamil"""
        text = Localizer.translate("welcome", "ta")
        
        assert text == "வரவேற்பு"
    
    def test_translate_telugu(self):
        """Test translation to Telugu"""
        text = Localizer.translate("welcome", "te")
        
        assert text == "స్వాగతం"
    
    def test_translate_unsupported_language_fallback(self):
        """Test fallback to English for unsupported language"""
        text = Localizer.translate("app_name", "xyz")
        
        assert text == "Crop Disease Detection"  # Falls back to English
    
    def test_translate_missing_key(self):
        """Test translation with missing key"""
        text = Localizer.translate("nonexistent_key", "en")
        
        assert text == "nonexistent_key"  # Returns key itself
    
    def test_get_localized_dict_english(self):
        """Test getting localized value from dict"""
        data = {
            "en": "Hello",
            "hi": "नमस्ते",
            "kn": "ನಮಸ್ಕಾರ"
        }
        
        text = Localizer.get_localized_dict(data, "en")
        assert text == "Hello"
    
    def test_get_localized_dict_hindi(self):
        """Test localized dict for Hindi"""
        data = {
            "en": "Hello",
            "hi": "नमस्ते",
            "kn": "ನಮಸ್ಕಾರ"
        }
        
        text = Localizer.get_localized_dict(data, "hi")
        assert text == "नमस्ते"
    
    def test_get_localized_dict_fallback(self):
        """Test localized dict with fallback"""
        data = {
            "en": "Hello",
            "hi": "नमस्ते"
        }
        
        text = Localizer.get_localized_dict(data, "xyz")
        assert text == "Hello"  # Falls back to English


@pytest.mark.unit
class TestLanguageDetection:
    """Test language detection from request"""
    
    def test_language_from_header_hindi(self):
        """Test language detection from Accept-Language header"""
        lang = get_language_from_request("hi-IN,hi;q=0.9,en;q=0.8")
        
        assert lang == "hi"
    
    def test_language_from_header_english(self):
        """Test English from header"""
        lang = get_language_from_request("en-US,en;q=0.9")
        
        assert lang == "en"
    
    def test_language_from_user_preference(self):
        """Test language from user preference"""
        lang = get_language_from_request(None, user_preference="kn")
        
        assert lang == "kn"
    
    def test_language_default_fallback(self):
        """Test default language fallback"""
        lang = get_language_from_request(None, None)
        
        assert lang == "en"
    
    def test_user_preference_over_header(self):
        """Test user preference takes precedence"""
        lang = get_language_from_request("hi-IN", user_preference="ta")
        
        assert lang == "ta"
