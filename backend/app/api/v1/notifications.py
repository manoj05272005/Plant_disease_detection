"""
Notifications Router
Handles user notifications
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from app.core.database import get_database
from app.core.security import get_current_user
from app.models.schemas import NotificationResponse
from app.services.notification_service import notification_service
from app.utils.localization import get_language_from_request
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[NotificationResponse])
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    accept_language: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get user notifications
    
    Epic 1, Pile 7 - Notification Panel (US7)
    """
    try:
        user_id = str(current_user["_id"])
        language = get_language_from_request(accept_language, current_user.get("preferred_language"))
        
        notifications = await notification_service.get_user_notifications(
            db=db,
            user_id=user_id,
            language=language,
            limit=limit,
            unread_only=unread_only
        )
        
        return notifications
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.get("/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get count of unread notifications
    
    Epic 1, Pile 7 - Notification Panel (US7)
    """
    try:
        user_id = str(current_user["_id"])
        
        count = await notification_service.get_unread_count(db=db, user_id=user_id)
        
        return {"unread_count": count}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )


@router.patch("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Mark a notification as read
    
    Epic 1, Pile 7 - Notification Panel (US7)
    """
    try:
        user_id = str(current_user["_id"])
        
        success = await notification_service.mark_as_read(
            db=db,
            notification_id=notification_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.post("/mark-all-read")
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Mark all notifications as read
    
    Epic 1, Pile 7 - Notification Panel (US7)
    """
    try:
        user_id = str(current_user["_id"])
        
        count = await notification_service.mark_all_as_read(db=db, user_id=user_id)
        
        return {
            "message": f"{count} notifications marked as read",
            "count": count
        }
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )
