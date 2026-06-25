"""
User Management Router
Handles user profile management and preferences
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database
from app.core.security import get_current_user
from app.models.schemas import UserUpdate, UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["User Management"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Get user profile
    
    Epic 1, Pile 5 - Profile Management (US5)
    """
    current_user["_id"] = str(current_user["_id"])
    current_user.pop("hashed_password", None)
    return current_user


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update user profile
    
    Epic 1, Pile 5 - Profile Management (US5)
    """
    try:
        user_object_id = current_user["_id"] if isinstance(current_user["_id"], ObjectId) else ObjectId(current_user["_id"])
        
        # Build update document
        update_data = {}
        if user_update.name is not None:
            update_data["name"] = user_update.name
        if user_update.preferred_language is not None:
            update_data["preferred_language"] = user_update.preferred_language
        if user_update.location is not None:
            update_data["location"] = user_update.location
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Update user
        result = await db.users.update_one(
            {"_id": user_object_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or no changes made"
            )
        
        # Get updated user
        updated_user = await db.users.find_one({"_id": user_object_id})
        updated_user["_id"] = str(updated_user["_id"])
        updated_user.pop("hashed_password", None)
        
        logger.info(f"Profile updated for user: {str(user_object_id)}")
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.get("/sessions")
async def get_active_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all active sessions for the user
    
    Epic 1, Pile 15 - Multi-Device Login Support (US15)
    """
    try:
        user_id = str(current_user["_id"])
        
        cursor = db.sessions.find({
            "user_id": user_id,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        }).sort("created_at", -1)
        
        sessions = await cursor.to_list(length=100)
        
        # Format sessions
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append({
                "session_id": str(session["_id"]),
                "device_info": session.get("device_info", {}),
                "created_at": session["created_at"],
                "expires_at": session["expires_at"]
            })
        
        return {
            "sessions": formatted_sessions,
            "total": len(formatted_sessions)
        }
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Revoke a specific session
    
    Epic 1, Pile 15 - Multi-Device Login Support (US15)
    """
    try:
        user_id = str(current_user["_id"])
        
        result = await db.sessions.update_one(
            {
                "_id": ObjectId(session_id),
                "user_id": user_id
            },
            {"$set": {"is_active": False}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )
