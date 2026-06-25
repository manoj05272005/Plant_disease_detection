"""
Unit Tests for Image Processing Module
"""
import pytest
import numpy as np
import cv2
from app.utils.image_processing import ImageProcessor


@pytest.mark.unit
class TestImageQualityCheck:
    """Test image quality checking"""
    
    def test_blur_detection_sharp_image(self):
        """Test blur detection on sharp image"""
        # Create sharp image with high frequency content
        image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        # Add some edges
        image[100:124, 100:124] = 255
        image[50:74, 50:74] = 0
        
        result = ImageProcessor.check_blur(image)
        
        assert "is_acceptable" in result
        assert "blur_score" in result
        assert isinstance(result["is_acceptable"], bool)
        assert isinstance(result["blur_score"], (int, float))
    
    def test_blur_detection_blurry_image(self):
        """Test blur detection on blurry image"""
        # Create uniform blurry image
        image = np.ones((224, 224, 3), dtype=np.uint8) * 128
        
        result = ImageProcessor.check_blur(image)
        
        assert result["is_acceptable"] is False
        assert result["blur_score"] < 100  # Below threshold
    
    def test_check_blur_with_valid_image(self, mock_image):
        """Test blur check with valid random image"""
        result = ImageProcessor.check_blur(mock_image)
        
        assert "is_acceptable" in result
        assert "message" in result


@pytest.mark.unit
class TestBoundingBoxDetection:
    """Test bounding box detection"""
    
    def test_detect_bounding_boxes(self, mock_image):
        """Test bounding box detection"""
        annotated, boxes = ImageProcessor.detect_bounding_boxes(mock_image)
        
        assert annotated is not None
        assert isinstance(boxes, list)
        assert annotated.shape == mock_image.shape
    
    def test_bounding_box_structure(self, mock_image):
        """Test bounding box data structure"""
        _, boxes = ImageProcessor.detect_bounding_boxes(mock_image)
        
        if len(boxes) > 0:
            box = boxes[0]
            assert "x" in box
            assert "y" in box
            assert "width" in box
            assert "height" in box
            assert isinstance(box["x"], (int, np.integer))
            assert isinstance(box["y"], (int, np.integer))


@pytest.mark.unit
class TestSeverityCalculation:
    """Test severity calculation"""
    
    def test_calculate_severity_with_boxes(self, mock_image):
        """Test severity calculation with bounding boxes"""
        boxes = [
            {"x": 50, "y": 50, "width": 100, "height": 100}
        ]
        
        severity = ImageProcessor.calculate_severity(mock_image, boxes)
        
        assert severity in ["low", "medium", "high", "critical"]
    
    def test_calculate_severity_no_boxes(self, mock_image):
        """Test severity calculation with no boxes"""
        severity = ImageProcessor.calculate_severity(mock_image, [])
        
        assert severity == "low"
    
    def test_calculate_severity_multiple_boxes(self, mock_image):
        """Test severity with multiple boxes"""
        boxes = [
            {"x": 10, "y": 10, "width": 50, "height": 50},
            {"x": 100, "y": 100, "width": 50, "height": 50}
        ]
        
        severity = ImageProcessor.calculate_severity(mock_image, boxes)
        assert severity in ["low", "medium", "high", "critical"]


@pytest.mark.unit
class TestImageEncoding:
    """Test image encoding utilities"""
    
    def test_encode_image_to_base64(self, mock_image):
        """Test image encoding to base64"""
        base64_str = ImageProcessor.encode_image_to_base64(mock_image)
        
        assert base64_str is not None
        assert isinstance(base64_str, str)
        assert base64_str.startswith("data:image/")
    
    def test_base64_string_format(self, mock_image):
        """Test base64 string format"""
        base64_str = ImageProcessor.encode_image_to_base64(mock_image)
        
        assert "base64," in base64_str
        parts = base64_str.split("base64,")
        assert len(parts) == 2
        assert len(parts[1]) > 0
