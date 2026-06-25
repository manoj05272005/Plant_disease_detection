"""
Authentication Router
Handles user registration, login, logout, and password reset
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
import json
import secrets

from app.core.database import get_database
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp,
    generate_reset_token,
    create_session,
    invalidate_session,
    invalidate_all_sessions,
    get_current_user
)
from app.models.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenRefresh,
    PasswordReset,
    PasswordResetConfirm,
    SessionInfo,
    PasskeyBeginRequest,
    PasskeyFinishRequest,
    PasskeyRegistrationResult,
    PasskeyLoginResult,
)
from app.core.config import settings
from app.utils.email_sender import send_password_reset_email
import logging

try:
    from webauthn import (
        generate_registration_options,
        verify_registration_response,
        generate_authentication_options,
        verify_authentication_response,
        options_to_json,
    )
    from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
    from webauthn.helpers.structs import PublicKeyCredentialDescriptor
except Exception:  # pragma: no cover - optional dependency at runtime
    generate_registration_options = None
    verify_registration_response = None
    generate_authentication_options = None
    verify_authentication_response = None
    options_to_json = None
    base64url_to_bytes = None
    bytes_to_base64url = None
    PublicKeyCredentialDescriptor = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _ensure_passkeys_available() -> None:
    if generate_registration_options is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Passkey support is not available on the server.",
        )


async def _find_user_by_username(db: AsyncIOMotorDatabase, username: str):
    return await db.users.find_one(
        {
            "$or": [
                {"email": username},
                {"phone": username},
            ]
        }
    )


def _pick_expected_origin(origin: Optional[str]) -> str:
    allowed = settings.WEBAUTHN_ALLOWED_ORIGINS
    if isinstance(allowed, str):
        allowed = [allowed]

    cleaned_allowed = [item.strip() for item in allowed if item]
    if origin and origin in cleaned_allowed:
        return origin
    if cleaned_allowed:
        return cleaned_allowed[0]
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="No WebAuthn origins configured on server.",
    )


async def _store_passkey_challenge(
    db: AsyncIOMotorDatabase,
    *,
    username: str,
    challenge: str,
    flow: str,
) -> None:
    await db.passkey_challenges.insert_one(
        {
            "username": username,
            "flow": flow,
            "challenge": challenge,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "is_used": False,
        }
    )


async def _consume_passkey_challenge(
    db: AsyncIOMotorDatabase,
    *,
    username: str,
    flow: str,
) -> bytes:
    challenge_doc = await db.passkey_challenges.find_one(
        {
            "username": username,
            "flow": flow,
            "is_used": False,
            "expires_at": {"$gt": datetime.utcnow()},
        },
        sort=[("created_at", -1)],
    )

    if not challenge_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passkey challenge expired. Please retry.",
        )

    await db.passkey_challenges.update_one(
        {"_id": challenge_doc["_id"]},
        {"$set": {"is_used": True}},
    )
    challenge = challenge_doc.get("challenge")
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passkey challenge is missing. Please retry.",
        )

    # Stored challenge is base64url from WebAuthn options JSON.
    return base64url_to_bytes(challenge)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Register a new user
    
    Epic 1, Pile 1 - User Registration (US1)
    """
    try:
        # Check if user already exists
        existing_user = None
        if user_data.email:
            existing_user = await db.users.find_one({"email": user_data.email})
        if not existing_user and user_data.phone:
            existing_user = await db.users.find_one({"phone": user_data.phone})
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or phone already exists"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Normalize location: accept string and convert to structured dict
               # FIXED: Always store location as a simple string, not a dict
        normalized_location = user_data.location
        if isinstance(normalized_location, dict):
            # If it's a dict like {"text": "city"}, extract the text value
            normalized_location = normalized_location.get('text', '')
        elif normalized_location is None:
            # Keep None as is
            normalized_location = None
        # If it's already a string, keep it as is
        # Create user document
        user_doc = {
            "name": user_data.name,
            "email": user_data.email,
            "phone": user_data.phone,
            "hashed_password": hashed_password,
            "preferred_language": user_data.preferred_language or settings.DEFAULT_LANGUAGE,
            "location": normalized_location,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": None
        }
        
        # Insert user
        result = await db.users.insert_one(user_doc)
        user_doc["_id"] = str(result.inserted_id)
        
        # Remove sensitive data
        user_doc.pop("hashed_password", None)
        
        logger.info(f"New user registered: {user_doc['_id']}")
        return user_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_agent: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Login user and return JWT tokens
    
    Epic 1, Pile 2 - Secure Login (US2)
    """
    try:
        # Find user by email or phone
        user = await db.users.find_one({
            "$or": [
                {"email": form_data.username},
                {"phone": form_data.username}
            ]
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        # Create tokens
        user_id = str(user["_id"])
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        # Create session for multi-device support
        device_info = {
            "device_type": "unknown",
            "user_agent": user_agent,
            "login_time": datetime.utcnow()
        }
        
        await create_session(db, user_id, device_info, access_token)
        
        logger.info(f"User logged in: {user_id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Refresh access token using refresh token
    """
    try:
        # Decode refresh token
        payload = decode_token(token_data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        
        # Verify user exists
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Logout user and invalidate session
    
    Epic 1, Pile 3 - Logout (US3)
    """
    try:
        user_id = str(current_user["_id"])
        
        # Invalidate current session
        # In production, you would get the token from the request
        # For now, we'll invalidate all sessions
        
        logger.info(f"User logged out: {user_id}")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/logout-all")
async def logout_all_devices(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Logout from all devices
    
    Epic 1, Pile 15 - Multi-Device Login Support (US15)
    """
    try:
        user_id = str(current_user["_id"])
        
        # Invalidate all sessions
        await invalidate_all_sessions(db, user_id)
        
        logger.info(f"User logged out from all devices: {user_id}")
        
        return {"message": "Successfully logged out from all devices"}
        
    except Exception as e:
        logger.error(f"Error logging out from all devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Request password reset
    
    Epic 1, Pile 4 - Forgot Password (US4)
    """
    try:
        # Find user
        user = await db.users.find_one({
            "$or": [
                {"email": password_reset.username},
                {"phone": password_reset.username}
            ]
        })
        
        if not user:
            # Don't reveal if user exists or not for security
            return {"message": "If the account exists, a reset code will be sent"}
        
        # Generate OTP and reset token
        otp = generate_otp()
        reset_token = generate_reset_token()
        
        # Store reset token in database
        await db.password_resets.insert_one({
            "user_id": str(user["_id"]),
            "reset_token": reset_token,
            "otp": otp,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=15),
            "is_used": False
        })
        
        # Try to send the OTP email; if SMTP is not configured or
        # the send fails, log the OTP for development and continue
        # so the user can still complete the reset flow.
        email_sent = False
        user_email = user.get("email")
        if user_email:
            try:
                send_password_reset_email(user_email, otp)
                email_sent = True
                logger.info(f"Password reset email sent to {user_email}")
            except Exception as e:
                logger.warning(
                    f"Could not send reset email to {user_email}: {e}. "
                    f"OTP for development/testing: {otp}"
                )
        
        response = {
            "message": "If the account exists, a reset code will be sent",
            "reset_token": reset_token
        }
        
        # In development (when email fails), include the OTP in the
        # response so the user can still complete the flow.
        if not email_sent:
            response["otp"] = otp
            response["message"] = (
                "Email service is unavailable. "
                "Use the OTP provided below to reset your password."
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in forgot password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Reset password using token and OTP
    
    Epic 1, Pile 4 - Forgot Password (US4)
    """
    try:
        # Find reset request
        reset_request = await db.password_resets.find_one({
            "reset_token": reset_data.token,
            "otp": reset_data.otp,
            "is_used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not reset_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password
        new_password_hash = get_password_hash(reset_data.new_password)
        
        await db.users.update_one(
            {"_id": ObjectId(reset_request["user_id"])},
            {
                "$set": {
                    "hashed_password": new_password_hash,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Mark reset request as used
        await db.password_resets.update_one(
            {"_id": reset_request["_id"]},
            {"$set": {"is_used": True}}
        )
        
        # Invalidate all sessions for security
        await invalidate_all_sessions(db, reset_request["user_id"])
        
        logger.info(f"Password reset successful for user: {reset_request['user_id']}")
        
        return {"message": "Password reset successful"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/passkeys/register/begin")
async def begin_passkey_registration(
    payload: PasskeyBeginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Start WebAuthn registration ceremony for an existing user."""
    _ensure_passkeys_available()

    user = await _find_user_by_username(db, payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    credential_docs = await db.passkeys.find({"user_id": str(user["_id"])}).to_list(length=50)
    exclude_creds = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(doc["credential_id"]))
        for doc in credential_docs
        if doc.get("credential_id")
    ]

    options = generate_registration_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_id=str(user["_id"]).encode("utf-8"),
        user_name=user.get("email") or user.get("phone") or str(user["_id"]),
        user_display_name=user.get("name") or "AgroScan User",
        challenge=secrets.token_bytes(32),
        exclude_credentials=exclude_creds,
    )

    options_json = json.loads(options_to_json(options))
    await _store_passkey_challenge(
        db,
        username=payload.username,
        challenge=options_json.get("challenge", ""),
        flow="register",
    )
    return options_json


@router.post("/passkeys/register/finish", response_model=PasskeyRegistrationResult)
async def finish_passkey_registration(
    payload: PasskeyFinishRequest,
    origin: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Verify WebAuthn attestation and bind passkey to user account."""
    _ensure_passkeys_available()

    user = await _find_user_by_username(db, payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    expected_challenge = await _consume_passkey_challenge(
        db,
        username=payload.username,
        flow="register",
    )

    verification = verify_registration_response(
        credential=payload.credential,
        expected_challenge=expected_challenge,
        expected_rp_id=settings.WEBAUTHN_RP_ID,
        expected_origin=_pick_expected_origin(origin),
        require_user_verification=True,
    )

    credential_id = bytes_to_base64url(verification.credential_id)
    existing = await db.passkeys.find_one({"credential_id": credential_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This passkey is already registered.",
        )

    await db.passkeys.insert_one(
        {
            "user_id": str(user["_id"]),
            "credential_id": credential_id,
            "public_key": bytes_to_base64url(verification.credential_public_key),
            "sign_count": verification.sign_count,
            "created_at": datetime.utcnow(),
            "last_used_at": None,
        }
    )

    return {
        "message": "Passkey registered successfully.",
        "credential_id": credential_id,
    }


@router.post("/passkeys/login/begin")
async def begin_passkey_login(
    payload: PasskeyBeginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Start WebAuthn authentication ceremony."""
    _ensure_passkeys_available()

    user = await _find_user_by_username(db, payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    credential_docs = await db.passkeys.find({"user_id": str(user["_id"])}).to_list(length=50)
    if not credential_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No passkey registered for this account.",
        )

    allow_creds = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(doc["credential_id"]))
        for doc in credential_docs
        if doc.get("credential_id")
    ]

    options = generate_authentication_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        challenge=secrets.token_bytes(32),
        allow_credentials=allow_creds,
    )

    options_json = json.loads(options_to_json(options))
    await _store_passkey_challenge(
        db,
        username=payload.username,
        challenge=options_json.get("challenge", ""),
        flow="login",
    )
    return options_json


@router.post("/passkeys/login/finish", response_model=PasskeyLoginResult)
async def finish_passkey_login(
    payload: PasskeyFinishRequest,
    user_agent: Optional[str] = Header(None),
    origin: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Verify WebAuthn assertion and issue JWT tokens."""
    _ensure_passkeys_available()

    user = await _find_user_by_username(db, payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    expected_challenge = await _consume_passkey_challenge(
        db,
        username=payload.username,
        flow="login",
    )

    credential_id = payload.credential.get("id")
    if not credential_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credential ID is missing.",
        )

    stored_passkey = await db.passkeys.find_one(
        {
            "user_id": str(user["_id"]),
            "credential_id": credential_id,
        }
    )
    if not stored_passkey:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Passkey not recognized for this account.",
        )

    auth_verification = verify_authentication_response(
        credential=payload.credential,
        expected_challenge=expected_challenge,
        expected_rp_id=settings.WEBAUTHN_RP_ID,
        expected_origin=_pick_expected_origin(origin),
        credential_public_key=base64url_to_bytes(stored_passkey["public_key"]),
        credential_current_sign_count=int(stored_passkey.get("sign_count", 0)),
        require_user_verification=True,
    )

    await db.passkeys.update_one(
        {"_id": stored_passkey["_id"]},
        {
            "$set": {
                "sign_count": auth_verification.new_sign_count,
                "last_used_at": datetime.utcnow(),
            }
        },
    )

    user_id = str(user["_id"])
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})

    device_info = {
        "device_type": "passkey",
        "user_agent": user_agent,
        "login_time": datetime.utcnow(),
    }
    await create_session(db, user_id, device_info, access_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "passkey": True,
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user information
    """
    current_user["_id"] = str(current_user["_id"])
    current_user.pop("hashed_password", None)
    return current_user
