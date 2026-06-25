"""
Unit Tests for Security Module
"""
import pytest
from datetime import timedelta
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp,
    generate_reset_token
)
from jose import jwt
from fastapi import HTTPException
from app.core.config import settings


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing utilities"""
    
    def test_password_hash_creates_different_hash(self):
        """Test that same password creates different hashes"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Due to salt
        assert hash1.startswith("$2b$")  # bcrypt format
    
    def test_verify_password_success(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_failure(self):
        """Test password verification with wrong password"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("wrongpassword", hashed) is False
    
    def test_password_hash_not_empty(self):
        """Test that password hash is not empty"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert len(hashed) > 0
        assert hashed != password
    
    def test_password_hash_length(self):
        """Test password hash has expected length"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert len(hashed) == 60  # bcrypt standard length


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and validation"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
    
    def test_decode_token_success(self):
        """Test token decoding with valid token"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "access"
    
    def test_decode_token_invalid(self):
        """Test token decoding with invalid token"""
        with pytest.raises(HTTPException) as exc:
            decode_token("invalid.token.here")
        
        assert exc.value.status_code == 401
        assert "Could not validate credentials" in exc.value.detail
    
    def test_token_custom_expiration(self):
        """Test token with custom expiration"""
        data = {"sub": "user123"}
        token = create_access_token(data, expires_delta=timedelta(hours=1))
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload


@pytest.mark.unit
class TestOTPGeneration:
    """Test OTP generation"""
    
    def test_generate_otp_default_length(self):
        """Test OTP generation with default length"""
        otp = generate_otp()
        
        assert len(otp) == 6
        assert otp.isdigit()
    
    def test_generate_otp_custom_length(self):
        """Test OTP generation with custom length"""
        otp = generate_otp(length=4)
        
        assert len(otp) == 4
        assert otp.isdigit()
    
    def test_generate_otp_uniqueness(self):
        """Test that OTPs are reasonably unique"""
        otps = [generate_otp() for _ in range(100)]
        unique_otps = set(otps)
        
        # Should have at least 90 unique OTPs out of 100
        assert len(unique_otps) > 90


@pytest.mark.unit
class TestResetToken:
    """Test reset token generation"""
    
    def test_generate_reset_token(self):
        """Test reset token generation"""
        token = generate_reset_token()
        
        assert token is not None
        assert len(token) > 20
        assert isinstance(token, str)
    
    def test_reset_token_uniqueness(self):
        """Test reset tokens are unique"""
        token1 = generate_reset_token()
        token2 = generate_reset_token()
        
        assert token1 != token2
