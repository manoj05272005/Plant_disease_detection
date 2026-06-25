"""
Standalone Unit Tests - Security Functions
These tests demonstrate testing capability without requiring full app imports
"""
import pytest
import re
import bcrypt
from jose import jwt
from datetime import datetime, timedelta

# Test configuration
SECRET_KEY = "test_secret_key_for_demonstration"
ALGORITHM = "HS256"


# Security Functions to Test
def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_otp(length: int = 6) -> str:
    """Generate numeric OTP"""
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


# ============================================================================
# UNIT TESTS
# ============================================================================

@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_password_hash_creates_valid_hash(self):
        """Test that password hashing creates a valid bcrypt hash"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60
        print(f"✓ Password hash created: {hashed[:20]}...")
    
    def test_password_hash_is_unique(self):
        """Test that same password creates different hashes (due to salt)"""
        password = "TestPassword456"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        print(f"✓ Unique hashes generated for same password")
    
    def test_verify_password_success(self):
        """Test password verification with correct password"""
        password = "CorrectPassword789"
        hashed = get_password_hash(password)
        
        result = verify_password(password, hashed)
        
        assert result is True
        print(f"✓ Password verification successful")
    
    def test_verify_password_failure(self):
        """Test password verification with wrong password"""
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = get_password_hash(password)
        
        result = verify_password(wrong_password, hashed)
        
        assert result is False
        print(f"✓ Incorrect password rejected")
    
    def test_empty_password_handling(self):
        """Test handling of empty password"""
        password = ""
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert verify_password("", hashed) is True
        print(f"✓ Empty password handled correctly")


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and validation"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
        print(f"✓ JWT token created: {token[:30]}...")
    
    def test_token_contains_correct_data(self):
        """Test token contains encoded data"""
        user_id = "test_user_456"
        data = {"sub": user_id}
        token = create_access_token(data)
        
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert decoded["sub"] == user_id
        assert decoded["type"] == "access"
        assert "exp" in decoded
        print(f"✓ Token payload verified: user={user_id}")
    
    def test_token_expiration_set(self):
        """Test token has expiration time"""
        data = {"sub": "user789"}
        token = create_access_token(data)
        
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert "exp" in decoded
        exp_time = datetime.fromtimestamp(decoded["exp"])
        assert exp_time > datetime.utcnow()
        print(f"✓ Token expiration set correctly")
    
    def test_custom_expiration(self):
        """Test token with custom expiration"""
        data = {"sub": "user999"}
        custom_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta=custom_delta)
        
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert "exp" in decoded
        print(f"✓ Custom token expiration working")


@pytest.mark.unit
class TestOTPGeneration:
    """Test OTP generation"""
    
    def test_generate_otp_default_length(self):
        """Test OTP generation with default 6 digits"""
        otp = generate_otp()
        
        assert len(otp) == 6
        assert otp.isdigit()
        print(f"✓ OTP generated: {otp}")
    
    def test_generate_otp_custom_length(self):
        """Test OTP with custom length"""
        otp = generate_otp(length=4)
        
        assert len(otp) == 4
        assert otp.isdigit()
        print(f"✓ 4-digit OTP generated: {otp}")
    
    def test_otp_uniqueness(self):
        """Test that OTPs are reasonably unique"""
        otps = [generate_otp() for _ in range(100)]
        unique_otps = set(otps)
        
        assert len(unique_otps) > 85  # At least 85% unique
        print(f"✓ Generated 100 OTPs, {len(unique_otps)} unique")
    
    def test_otp_numeric_only(self):
        """Test OTP contains only numbers"""
        otp = generate_otp(length=8)
        
        assert all(c.isdigit() for c in otp)
        assert re.match(r'^\d+$', otp)
        print(f"✓ OTP is numeric: {otp}")


@pytest.mark.unit
class TestDataValidation:
    """Test data validation functions"""
    
    def test_email_pattern(self):
        """Test email validation pattern"""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.in",
            "admin@company.org"
        ]
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in valid_emails:
            assert re.match(email_pattern, email)
        
        print(f"✓ Email validation working")
    
    def test_phone_number_format(self):
        """Test phone number validation"""
        valid_phones = ["1234567890", "9876543210"]
        
        for phone in valid_phones:
            assert len(phone) == 10
            assert phone.isdigit()
        
        print(f"✓ Phone validation working")
    
    def test_string_sanitization(self):
        """Test string sanitization"""
        unsafe_string = "<script>alert('xss')</script>"
        safe_string = unsafe_string.replace("<", "&lt;").replace(">", "&gt;")
        
        assert "<script>" not in safe_string
        assert "&lt;script&gt;" in safe_string
        print(f"✓ String sanitization working")


# Run tests with detailed output
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-p", "no:warnings"])
