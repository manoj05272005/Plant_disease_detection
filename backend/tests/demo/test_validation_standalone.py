"""
Standalone Unit Tests - Data Processing & Validation
Demonstrates testing without external dependencies
"""
import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, List


# ============================================================================
# UTILITY FUNCTIONS TO TEST
# ============================================================================

def validate_image_extension(filename: str) -> bool:
    """Validate image file extension"""
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)


def validate_file_size(size_bytes: int, max_mb: int = 10) -> bool:
    """Validate file size is within limits"""
    max_bytes = max_mb * 1024 * 1024
    return 0 < size_bytes <= max_bytes


def calculate_confidence_level(confidence: float) -> str:
    """Categorize confidence score"""
    if confidence >= 0.9:
        return "very_high"
    elif confidence >= 0.75:
        return "high"
    elif confidence >= 0.5:
        return "medium"
    else:
        return "low"


def format_diagnosis_response(data: Dict) -> Dict:
    """Format diagnosis data for API response"""
    return {
        "disease_name": data.get("disease_name", "Unknown"),
        "confidence": round(data.get("confidence", 0.0), 2),
        "severity": data.get("severity", "unknown"),
        "timestamp": datetime.utcnow().isoformat()
    }


def parse_language_code(lang_code: str) -> str:
    """Parse and validate language code"""
    supported_languages = ["en", "hi", "kn", "ta", "te", "ml"]
    cleaned = lang_code.lower().strip()[:2]
    return cleaned if cleaned in supported_languages else "en"


def calculate_pagination(total: int, page: int, per_page: int) -> Dict:
    """Calculate pagination metadata"""
    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        "total_items": total,
        "current_page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev
    }


# ============================================================================
# UNIT TESTS
# ============================================================================

@pytest.mark.unit
class TestFileValidation:
    """Test file validation functions"""
    
    def test_valid_image_extensions(self):
        """Test validation accepts valid image extensions"""
        valid_files = [
            "photo.jpg",
            "image.jpeg",
            "picture.png",
            "graphic.gif"
        ]
        
        for filename in valid_files:
            assert validate_image_extension(filename) is True
        
        print(f"✓ Valid image extensions accepted")
    
    def test_invalid_image_extensions(self):
        """Test validation rejects invalid extensions"""
        invalid_files = [
            "document.pdf",
            "text.txt",
            "script.js",
            "data.json"
        ]
        
        for filename in invalid_files:
            assert validate_image_extension(filename) is False
        
        print(f"✓ Invalid extensions rejected")
    
    def test_case_insensitive_validation(self):
        """Test extension validation is case-insensitive"""
        files = ["IMAGE.JPG", "Photo.PNG", "pic.JpEg"]
        
        for filename in files:
            assert validate_image_extension(filename) is True
        
        print(f"✓ Case-insensitive validation working")
    
    def test_file_size_validation(self):
        """Test file size validation"""
        valid_sizes = [
            1024,           # 1 KB
            1024 * 1024,    # 1 MB
            5 * 1024 * 1024 # 5 MB
        ]
        
        for size in valid_sizes:
            assert validate_file_size(size, max_mb=10) is True
        
        print(f"✓ Valid file sizes accepted")
    
    def test_file_size_exceeds_limit(self):
        """Test file size over limit is rejected"""
        large_size = 15 * 1024 * 1024  # 15 MB
        
        assert validate_file_size(large_size, max_mb=10) is False
        print(f"✓ Oversized files rejected")


@pytest.mark.unit
class TestConfidenceCalculation:
    """Test confidence level categorization"""
    
    def test_very_high_confidence(self):
        """Test very high confidence classification"""
        result = calculate_confidence_level(0.95)
        
        assert result == "very_high"
        print(f"✓ Very high confidence: 0.95 → {result}")
    
    def test_high_confidence(self):
        """Test high confidence classification"""
        result = calculate_confidence_level(0.80)
        
        assert result == "high"
        print(f"✓ High confidence: 0.80 → {result}")
    
    def test_medium_confidence(self):
        """Test medium confidence classification"""
        result = calculate_confidence_level(0.65)
        
        assert result == "medium"
        print(f"✓ Medium confidence: 0.65 → {result}")
    
    def test_low_confidence(self):
        """Test low confidence classification"""
        result = calculate_confidence_level(0.30)
        
        assert result == "low"
        print(f"✓ Low confidence: 0.30 → {result}")
    
    def test_boundary_values(self):
        """Test boundary confidence values"""
        assert calculate_confidence_level(0.90) == "very_high"
        assert calculate_confidence_level(0.75) == "high"
        assert calculate_confidence_level(0.50) == "medium"
        print(f"✓ Boundary values handled correctly")


@pytest.mark.unit
class TestDataFormatting:
    """Test data formatting functions"""
    
    def test_format_diagnosis_response(self):
        """Test diagnosis response formatting"""
        input_data = {
            "disease_name": "Early Blight",
            "confidence": 0.9234567,
            "severity": "medium"
        }
        
        result = format_diagnosis_response(input_data)
        
        assert result["disease_name"] == "Early Blight"
        assert result["confidence"] == 0.92
        assert result["severity"] == "medium"
        assert "timestamp" in result
        print(f"✓ Diagnosis formatted correctly")
    
    def test_format_with_missing_data(self):
        """Test formatting with missing fields"""
        input_data = {}
        
        result = format_diagnosis_response(input_data)
        
        assert result["disease_name"] == "Unknown"
        assert result["confidence"] == 0.0
        assert result["severity"] == "unknown"
        print(f"✓ Missing data handled with defaults")


@pytest.mark.unit
class TestLanguageHandling:
    """Test language code parsing"""
    
    def test_valid_language_codes(self):
        """Test parsing valid language codes"""
        codes = ["en", "hi", "kn", "ta", "te"]
        
        for code in codes:
            result = parse_language_code(code)
            assert result == code
        
        print(f"✓ Valid language codes parsed")
    
    def test_uppercase_language_codes(self):
        """Test uppercase codes are normalized"""
        result = parse_language_code("EN")
        
        assert result == "en"
        print(f"✓ Uppercase normalized: EN → en")
    
    def test_invalid_language_fallback(self):
        """Test invalid codes fall back to English"""
        invalid_codes = ["xyz", "abc", "123"]
        
        for code in invalid_codes:
            result = parse_language_code(code)
            assert result == "en"
        
        print(f"✓ Invalid codes fallback to 'en'")
    
    def test_language_code_truncation(self):
        """Test long codes are truncated"""
        result = parse_language_code("en-US")
        
        assert result == "en"
        print(f"✓ Long codes truncated: en-US → en")


@pytest.mark.unit
class TestPagination:
    """Test pagination calculations"""
    
    def test_pagination_first_page(self):
        """Test pagination for first page"""
        result = calculate_pagination(total=100, page=1, per_page=10)
        
        assert result["current_page"] == 1
        assert result["total_pages"] == 10
        assert result["has_next"] is True
        assert result["has_prev"] is False
        print(f"✓ First page pagination correct")
    
    def test_pagination_middle_page(self):
        """Test pagination for middle page"""
        result = calculate_pagination(total=100, page=5, per_page=10)
        
        assert result["has_next"] is True
        assert result["has_prev"] is True
        print(f"✓ Middle page pagination correct")
    
    def test_pagination_last_page(self):
        """Test pagination for last page"""
        result = calculate_pagination(total=100, page=10, per_page=10)
        
        assert result["has_next"] is False
        assert result["has_prev"] is True
        print(f"✓ Last page pagination correct")
    
    def test_pagination_partial_page(self):
        """Test pagination with partial last page"""
        result = calculate_pagination(total=95, page=10, per_page=10)
        
        assert result["total_pages"] == 10
        assert result["has_next"] is False
        print(f"✓ Partial page handled correctly")


# Run tests with detailed output
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-p", "no:warnings"])
