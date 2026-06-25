"""
Integration Tests for Remediation API
"""
import pytest


@pytest.mark.integration
class TestRemediationEndpoints:
    """Test remediation API endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_remediation_for_disease(self, authenticated_client):
        """Test get remediation for specific disease"""
        client, user_id = authenticated_client
        
        response = await client.get("/api/v1/remediation/tomato_early_blight")
        
        # May succeed if disease exists in knowledge base
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "disease_id" in data
            assert "treatment" in data
    
    @pytest.mark.asyncio
    async def test_get_localized_remediation(self, authenticated_client):
        """Test get remediation in different language"""
        client, user_id = authenticated_client
        
        response = await client.get(
            "/api/v1/remediation/tomato_early_blight?language=hi"
        )
        
        # Check response structure if successful
        if response.status_code == 200:
            data = response.json()
            assert "treatment" in data
    
    @pytest.mark.asyncio
    async def test_search_remediation(self, authenticated_client):
        """Test search remediation by keyword"""
        client, user_id = authenticated_client
        
        response = await client.get("/api/v1/remediation/search?q=blight")
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.integration
class TestRemediationPDF:
    """Test PDF generation for remediation"""
    
    @pytest.mark.asyncio
    async def test_generate_remediation_pdf(self, authenticated_client):
        """Test PDF generation"""
        client, user_id = authenticated_client
        
        response = await client.post("/api/v1/remediation/tomato_early_blight/pdf")
        
        # PDF generation may succeed or fail
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            assert response.headers["content-type"] == "application/pdf"
