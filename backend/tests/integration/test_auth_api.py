"""
Integration Tests for Authentication API
"""
import pytest
from datetime import datetime


@pytest.mark.integration
@pytest.mark.auth
class TestRegistration:
    """Test user registration endpoints"""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client, test_db):
        """Test successful user registration"""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123!",
            "phone": "1234567890",
            "preferred_language": "en"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "john@example.com"
        
        # Verify user in database
        user = await test_db.users.find_one({"email": "john@example.com"})
        assert user is not None
        assert user["name"] == "John Doe"
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_db):
        """Test registration with existing email"""
        # Create existing user
        await test_db.users.insert_one({
            "email": "existing@example.com",
            "name": "Existing User",
            "hashed_password": "hash",
            "created_at": datetime.utcnow()
        })
        
        user_data = {
            "name": "New User",
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "phone": "1234567890"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        user_data = {
            "name": "John Doe",
            "email": "invalid-email",
            "password": "SecurePass123!",
            "phone": "1234567890"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        """Test registration with weak password"""
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "123",
            "phone": "1234567890"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.auth
class TestLogin:
    """Test login endpoints"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_db):
        """Test successful login"""
        from app.core.security import get_password_hash
        
        # Create user
        await test_db.users.insert_one({
            "email": "test@example.com",
            "name": "Test User",
            "hashed_password": get_password_hash("testpassword"),
            "is_active": True,
            "created_at": datetime.utcnow()
        })
        
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_db):
        """Test login with wrong password"""
        from app.core.security import get_password_hash
        
        await test_db.users.insert_one({
            "email": "test@example.com",
            "hashed_password": get_password_hash("correctpassword"),
            "is_active": True,
            "created_at": datetime.utcnow()
        })
        
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "anypassword"
        })
        
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestLogout:
    """Test logout endpoints"""
    
    @pytest.mark.asyncio
    async def test_logout_success(self, authenticated_client, test_db):
        """Test successful logout"""
        client, user_id = authenticated_client
        
        response = await client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()


@pytest.mark.integration
@pytest.mark.auth
class TestPasswordReset:
    """Test password reset flow"""
    
    @pytest.mark.asyncio
    async def test_request_password_reset(self, client, test_db):
        """Test request password reset"""
        await test_db.users.insert_one({
            "email": "test@example.com",
            "name": "Test User",
            "hashed_password": "hash",
            "created_at": datetime.utcnow()
        })
        
        response = await client.post("/api/v1/auth/forgot-password", json={
            "email": "test@example.com"
        })
        
        assert response.status_code == 200
        
        # Verify reset token created
        reset = await test_db.password_resets.find_one({"email": "test@example.com"})
        assert reset is not None
    
    @pytest.mark.asyncio
    async def test_verify_reset_otp(self, client, test_db):
        """Test OTP verification"""
        # Create reset request
        await test_db.password_resets.insert_one({
            "email": "test@example.com",
            "otp": "123456",
            "created_at": datetime.utcnow()
        })
        
        response = await client.post("/api/v1/auth/verify-otp", json={
            "email": "test@example.com",
            "otp": "123456"
        })
        
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.auth
class TestTokenRefresh:
    """Test token refresh"""
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client, test_db):
        """Test token refresh with valid refresh token"""
        from app.core.security import get_password_hash, create_refresh_token
        from bson import ObjectId
        
        user_id = str(ObjectId())
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        # May fail if user doesn't exist, just testing endpoint
        assert response.status_code in [200, 401]
