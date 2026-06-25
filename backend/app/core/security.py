"""
Security utilities for JWT tokens and password hashing
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from bson import ObjectId
import secrets
import logging

logger = logging.getLogger(__name__)

import bcrypt

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


# JWT Token utilities
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# OTP Generation
def generate_otp(length: int = 6) -> str:
    """Generate numeric OTP"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def generate_reset_token() -> str:
    """Generate secure reset token"""
    return secrets.token_urlsafe(32)


# Get current user from token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    # Users are stored with ObjectId primary keys; convert string token subject
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise credentials_exception

    user = await db.users.find_one({"_id": user_object_id})
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current active user (alias for compatibility)"""
    return current_user


# Session management for multi-device support
async def create_session(
    db: AsyncIOMotorDatabase,
    user_id: str,
    device_info: Dict[str, Any],
    token: str
) -> str:
    """Create a new user session"""
    session = {
        "user_id": user_id,
        "token": token,
        "device_info": device_info,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "is_active": True
    }
    
    result = await db.sessions.insert_one(session)
    return str(result.inserted_id)


async def invalidate_session(db: AsyncIOMotorDatabase, token: str):
    """Invalidate a specific session"""
    await db.sessions.update_one(
        {"token": token},
        {"$set": {"is_active": False}}
    )


async def invalidate_all_sessions(db: AsyncIOMotorDatabase, user_id: str):
    """Invalidate all sessions for a user (logout from all devices)"""
    await db.sessions.update_many(
        {"user_id": user_id},
        {"$set": {"is_active": False}}
    )


async def validate_session(db: AsyncIOMotorDatabase, token: str) -> bool:
    """Check if a session is valid"""
    session = await db.sessions.find_one({
        "token": token,
        "is_active": True,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    return session is not None
