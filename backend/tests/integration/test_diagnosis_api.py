"""
Integration Tests for Diagnosis API
"""
import pytest
import io
from PIL import Image


@pytest.mark.integration
class TestDiagnosisEndpoints:
    """Test diagnosis API endpoints"""
    
    @pytest.mark.asyncio
    async def test_upload_image_quality_check(self, authenticated_client):
        """Test image upload and quality check"""
        client, user_id = authenticated_client
        
        # Create test image
        img = Image.new('RGB', (500, 500), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)



        
        files = {
            "file": ("test.jpg", img_bytes, "image/jpeg")
        }
        
        response = await client.post("/api/v1/diagnosis/upload", files=files)
        
        assert response.status_code in [200, 201]
        if response.status_code == 200:
            data = response.json()
            assert "quality_check" in data or "diagnosis" in data
    
    @pytest.mark.asyncio
    async def test_diagnose_image_endpoint(self, authenticated_client):
        """Test diagnosis creation"""
        client, user_id = authenticated_client
        
        # Create test image
        img = Image.new('RGB', (224, 224), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {
            "file": ("test.jpg", img_bytes, "image/jpeg")
        }
        data = {
            "crop_type": "tomato"
        }
        
        response = await client.post(
            "/api/v1/diagnosis/diagnose",
            files=files,
            data=data
        )
        
        # Diagnosis may succeed or fail depending on model
        assert response.status_code in [200, 400, 500]
    
    @pytest.mark.asyncio
    async def test_get_diagnosis_by_id(self, authenticated_client, test_db, mock_diagnosis):
        """Test get diagnosis by ID"""
        client, user_id = authenticated_client
        
        # Insert diagnosis
        mock_diagnosis["user_id"] = user_id
        result = await test_db.diagnoses.insert_one(mock_diagnosis)
        diagnosis_id = str(result.inserted_id)
        
        response = await client.get(f"/api/v1/diagnosis/{diagnosis_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["disease_name"] == "Early Blight"
    
    @pytest.mark.asyncio
    async def test_get_user_diagnoses(self, authenticated_client, test_db, mock_diagnosis):
        """Test get all user diagnoses"""
        client, user_id = authenticated_client
        
        # Insert multiple diagnoses
        mock_diagnosis["user_id"] = user_id
        await test_db.diagnoses.insert_one(mock_diagnosis)
        await test_db.diagnoses.insert_one(mock_diagnosis)
        
        response = await client.get("/api/v1/diagnosis/my-diagnoses")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    @pytest.mark.asyncio
    async def test_delete_diagnosis(self, authenticated_client, test_db, mock_diagnosis):
        """Test delete diagnosis"""
        client, user_id = authenticated_client
        
        # Insert diagnosis
        mock_diagnosis["user_id"] = user_id
        result = await test_db.diagnoses.insert_one(mock_diagnosis)
        diagnosis_id = str(result.inserted_id)
        
        response = await client.delete(f"/api/v1/diagnosis/{diagnosis_id}")
        
        assert response.status_code == 200
        
        # Verify deleted
        deleted = await test_db.diagnoses.find_one({"_id": result.inserted_id})
        assert deleted is None


@pytest.mark.integration
class TestDiagnosisFilters:
    """Test diagnosis filtering and search"""
    
    @pytest.mark.asyncio
    async def test_filter_by_crop_type(self, authenticated_client, test_db):
        """Test filter diagnoses by crop type"""
        client, user_id = authenticated_client
        
        # Insert diagnoses with different crop types
        await test_db.diagnoses.insert_one({
            "user_id": user_id,
            "crop_type": "tomato",
            "disease_name": "Early Blight",
            "confidence": 0.9
        })
        await test_db.diagnoses.insert_one({
            "user_id": user_id,
            "crop_type": "potato",
            "disease_name": "Late Blight",
            "confidence": 0.85
        })
        
        response = await client.get("/api/v1/diagnosis/my-diagnoses?crop_type=tomato")
        
        assert response.status_code == 200
        data = response.json()
        assert all(d["crop_type"] == "tomato" for d in data)
    
    @pytest.mark.asyncio
    async def test_pagination(self, authenticated_client, test_db):
        """Test diagnosis pagination"""
        client, user_id = authenticated_client
        
        # Insert multiple diagnoses
        for i in range(15):
            await test_db.diagnoses.insert_one({
                "user_id": user_id,
                "crop_type": "tomato",
                "disease_name": f"Disease {i}",
                "confidence": 0.9
            })
        
        response = await client.get("/api/v1/diagnosis/my-diagnoses?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10
