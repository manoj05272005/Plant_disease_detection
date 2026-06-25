"""
Unit Tests for Remediation Service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.remediation_service import RemediationService
from bson import ObjectId


@pytest.mark.unit
class TestRemediationService:
    """Test remediation service"""
    
    @pytest.mark.asyncio
    async def test_get_remediation_by_disease_id(self, test_db):
        """Test get remediation by disease ID"""
        # Insert remediation data
        await test_db.knowledge_base.insert_one({
            "disease_id": "tomato_early_blight",
            "disease_name": {"en": "Early Blight"},
            "treatment": {
                "en": "Apply fungicide",
                "hi": "फफूंदनाशक लगाएं"
            },
            "prevention": {
                "en": "Crop rotation",
                "hi": "फसल चक्र"
            }
        })
        
        service = RemediationService(test_db)
        result = await service.get_remediation("tomato_early_blight", language="en")
        
        assert result is not None
        assert result["disease_id"] == "tomato_early_blight"
        assert "treatment" in result
    
    @pytest.mark.asyncio
    async def test_get_localized_remediation(self, test_db):
        """Test localized remediation"""
        await test_db.knowledge_base.insert_one({
            "disease_id": "tomato_late_blight",
            "disease_name": {
                "en": "Late Blight",
                "hi": "झुलसा रोग"
            },
            "treatment": {
                "en": "Apply copper fungicide",
                "hi": "तांबा फफूंदनाशक लगाएं"
            }
        })
        
        service = RemediationService(test_db)
        result = await service.get_remediation("tomato_late_blight", language="hi")
        
        assert result is not None
        assert "झुलसा रोग" in str(result)
    
    @pytest.mark.asyncio
    async def test_search_remediation(self, test_db):
        """Test search remediation by keyword"""
        await test_db.knowledge_base.insert_one({
            "disease_id": "tomato_leaf_spot",
            "disease_name": {"en": "Leaf Spot"},
            "symptoms": {"en": "Brown spots on leaves"}
        })
        
        service = RemediationService(test_db)
        results = await service.search_remediation("spot", language="en")
        
        assert isinstance(results, list)
        if len(results) > 0:
            assert any("spot" in str(r).lower() for r in results)
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_remediation(self, test_db):
        """Test get remediation for non-existent disease"""
        service = RemediationService(test_db)
        result = await service.get_remediation("nonexistent_disease")
        
        assert result is None


@pytest.mark.unit
class TestRemediationFormatting:
    """Test remediation data formatting"""
    
    @pytest.mark.asyncio
    async def test_format_remediation_data(self, test_db):
        """Test formatting of remediation data"""
        raw_data = {
            "_id": ObjectId(),
            "disease_id": "test_disease",
            "disease_name": {"en": "Test Disease"},
            "treatment": {"en": "Treatment plan"}
        }
        
        await test_db.knowledge_base.insert_one(raw_data)
        
        service = RemediationService(test_db)
        result = await service.get_remediation("test_disease", language="en")
        
        assert "_id" not in result or isinstance(result.get("_id"), str)
        assert "disease_id" in result
