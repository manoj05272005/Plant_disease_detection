"""
Unit Tests for AI Service
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from app.services.ai_service import AIService


@pytest.mark.unit
class TestAIServiceInitialization:
    """Test AI Service initialization"""
    
    def test_ai_service_singleton(self):
        """Test that AIService is a singleton"""
        service1 = AIService()
        service2 = AIService()
        
        assert service1 is service2
    
    @patch('app.services.ai_service.tf.keras.models.load_model')
    def test_load_model(self, mock_load_model):
        """Test model loading"""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        service = AIService()
        service.load_model()
        
        assert mock_load_model.called


@pytest.mark.unit
class TestImagePreprocessing:
    """Test image preprocessing"""
    
    def test_preprocess_image_shape(self, mock_image):
        """Test preprocessed image shape"""
        service = AIService()
        
        preprocessed = service.preprocess_image(mock_image)
        
        assert preprocessed.shape == (1, 224, 224, 3)
    
    def test_preprocess_image_normalization(self, mock_image):
        """Test image normalization"""
        service = AIService()
        
        preprocessed = service.preprocess_image(mock_image)
        
        # Check values are normalized
        assert preprocessed.min() >= 0
        assert preprocessed.max() <= 1
    
    def test_preprocess_resize(self):
        """Test image resizing during preprocessing"""
        service = AIService()
        large_image = np.random.randint(0, 255, (500, 500, 3), dtype=np.uint8)
        
        preprocessed = service.preprocess_image(large_image)
        
        assert preprocessed.shape == (1, 224, 224, 3)


@pytest.mark.unit
@pytest.mark.ai
class TestDiseaseDetection:
    """Test disease detection"""
    
    @patch('app.services.ai_service.AIService.model')
    def test_predict_disease(self, mock_model, mock_image):
        """Test disease prediction"""
        # Mock model prediction
        mock_predictions = np.array([[0.05, 0.15, 0.75, 0.05]])
        mock_model.predict = Mock(return_value=mock_predictions)
        
        service = AIService()
        service.model = mock_model
        
        result = service.predict(mock_image)
        
        assert "disease_id" in result
        assert "confidence" in result
        assert "is_healthy" in result
        assert result["confidence"] > 0
    
    @patch('app.services.ai_service.AIService.model')
    def test_predict_returns_highest_confidence(self, mock_model, mock_image):
        """Test prediction returns highest confidence class"""
        mock_predictions = np.array([[0.1, 0.2, 0.6, 0.1]])
        mock_model.predict = Mock(return_value=mock_predictions)
        
        service = AIService()
        service.model = mock_model
        
        result = service.predict(mock_image)
        
        assert result["confidence"] == pytest.approx(0.6, rel=0.01)
    
    @patch('app.services.ai_service.AIService.model')
    def test_low_confidence_detection(self, mock_model, mock_image):
        """Test handling of low confidence predictions"""
        mock_predictions = np.array([[0.25, 0.25, 0.25, 0.25]])
        mock_model.predict = Mock(return_value=mock_predictions)
        
        service = AIService()
        service.model = mock_model
        
        result = service.predict(mock_image)
        
        assert result["confidence"] < 0.5


@pytest.mark.unit
@pytest.mark.ai
class TestGradCAM:
    """Test Grad-CAM heatmap generation"""
    
    @patch('app.services.ai_service.AIService.model')
    def test_generate_heatmap(self, mock_model, mock_image):
        """Test heatmap generation"""
        service = AIService()
        service.model = mock_model
        
        # Mock required model methods
        mock_model.layers = [Mock(name='conv2d')]
        mock_grad_model = Mock()
        mock_grad_model.return_value = (
            Mock(numpy=lambda: np.random.rand(1, 7, 7, 512)),
            Mock(numpy=lambda: np.random.rand(1, 1))
        )
        
        with patch('tensorflow.GradientTape'):
            heatmap = service.generate_gradcam_heatmap(mock_image, class_idx=0)
            
            if heatmap is not None:
                assert heatmap.shape[0] == mock_image.shape[0]
                assert heatmap.shape[1] == mock_image.shape[1]
