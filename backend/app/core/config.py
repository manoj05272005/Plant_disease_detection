"""
Application Configuration
Manages all environment variables and app settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, List, Union
from functools import lru_cache
import json
from urllib.parse import urlparse




class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Crop Disease Detection API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    
    # MongoDB Configuration
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "crop_disease_db"
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_POOL_SIZE: int = 100
    
    # JWT Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Security
    PWD_HASH_ALGORITHM: str = "bcrypt"
    PWD_ROUNDS: int = 12
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = ["*"]
    
    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # If not JSON, split by comma
                if ',' in v:
                    return [origin.strip() for origin in v.split(',')]
                # Single origin
                return [v]
        return v
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "heic"]
    UPLOAD_DIR: str = "uploads"
    
    # AI Model Settings
    MODEL_PATH: str = "models"
    BLUR_THRESHOLD: int = 100  # Laplacian variance threshold
    CONFIDENCE_THRESHOLD: float = 0.85
    SEVERITY_LOW_THRESHOLD: float = 0.10
    SEVERITY_MEDIUM_THRESHOLD: float = 0.40
    
    # Language Support
    SUPPORTED_LANGUAGES: Union[str, List[str]] = ["en", "hi", "kn", "ta", "te", "mr", "bn"]
    DEFAULT_LANGUAGE: str = "en"
    
    @field_validator('SUPPORTED_LANGUAGES', mode='before')
    @classmethod
    def parse_supported_languages(cls, v):
        """Parse supported languages from string or list"""
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # If not JSON, split by comma
                if ',' in v:
                    return [lang.strip() for lang in v.split(',')]
                # Single language
                return [v]
        return v

    # WebAuthn / Passkey
    WEBAUTHN_RP_ID: str = "bond60-plant-disease-detection.hf.space"
    WEBAUTHN_RP_NAME: str = "AgroScan"
    WEBAUTHN_ALLOWED_ORIGINS: Union[str, List[str]] = [
        "https://bond60-plant-disease-detection.hf.space",
    ]

    @field_validator('WEBAUTHN_ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_webauthn_allowed_origins(cls, v):
        """Parse WebAuthn origins from string or list."""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                if ',' in v:
                    return [origin.strip() for origin in v.split(',')]
                return [v]
        return v

    @field_validator('WEBAUTHN_RP_ID', mode='before')
    @classmethod
    def normalize_webauthn_rp_id(cls, v):
        """Accept host or full URL and normalize to host-only RP ID."""
        if not isinstance(v, str):
            return v

        candidate = v.strip()
        if not candidate:
            return candidate

        if '://' in candidate:
            parsed = urlparse(candidate)
            if parsed.hostname:
                return parsed.hostname

        return candidate

    # Android Digital Asset Links (for passkey/Credential Manager association)
    ANDROID_APP_PACKAGE_NAME: Optional[str] = None
    ANDROID_APP_SHA256_CERT_FINGERPRINTS: Union[str, List[str]] = []

    @field_validator('ANDROID_APP_SHA256_CERT_FINGERPRINTS', mode='before')
    @classmethod
    def parse_android_fingerprints(cls, v):
        """Parse certificate fingerprints from JSON array or comma-separated string."""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [item.strip() for item in parsed if isinstance(item, str) and item.strip()]
            except json.JSONDecodeError:
                if ',' in v:
                    return [item.strip() for item in v.split(',') if item.strip()]
                return [v.strip()] if v.strip() else []
        return v
    
    # Email Configuration (for password reset)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    
    # SMS Configuration (for OTP)
    SMS_API_KEY: Optional[str] = None
    SMS_API_URL: Optional[str] = None
    
    # Redis (for caching and sessions)
    REDIS_URL: Optional[str] = None
    
    # Storage (AWS S3 or local)
    STORAGE_TYPE: str = "local"  # "local" or "s3"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    AWS_BUCKET_NAME: Optional[str] = None
    
    # Offline Sync Settings
    OFFLINE_DATA_RETENTION_DAYS: int = 30
    MAX_OFFLINE_RECORDS: int = 1000
    
    # Background Tasks
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Weather API (for offline weather data)
    WEATHER_API_KEY: Optional[str] = None
    WEATHER_API_URL: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
