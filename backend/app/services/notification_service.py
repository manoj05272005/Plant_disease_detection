"""
Notification Service
Handles notification creation and management
"""
from typing import Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.schemas import NotificationType
from app.utils.localization import Localizer
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing user notifications"""
    
    @staticmethod
    async def create_notification(
        db: AsyncIOMotorDatabase,
        user_id: str,
        notification_type: NotificationType,
        title: Dict[str, str],
        message: Dict[str, str],
        data: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> str:
        """
        Create a new notification
        
        Args:
            db: Database connection
            user_id: User ID
            notification_type: Type of notification
            title: Multi-language title
            message: Multi-language message
            data: Additional data
        
        Returns:
            Notification ID
        """
        try:
            notification = {
                "user_id": user_id,
                "type": notification_type,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "data": data or {},
                "priority": priority,
                "is_read": False,
                "created_at": datetime.utcnow()
            }
            
            result = await db.notifications.insert_one(notification)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            raise



        
    
    @staticmethod
    async def get_user_notifications(
        db: AsyncIOMotorDatabase,
        user_id: str,
        language: str = "en",
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get user notifications
        
        Args:
            db: Database connection
            user_id: User ID
            language: Preferred language
            limit: Maximum number of notifications
            unread_only: Return only unread notifications
        
        Returns:
            List of notifications
        """
        try:
            query = {"user_id": user_id}
            
            if unread_only:
                query["is_read"] = False
            
            cursor = db.notifications.find(query).sort("created_at", -1).limit(limit)
            notifications = await cursor.to_list(length=limit)
            
            # Localize notifications
            localized_notifications = []
            for notif in notifications:
                localized_notifications.append({
                    "_id": str(notif["_id"]),
                    "user_id": notif["user_id"],
                    "notification_type": notif.get("notification_type")
                    or notif.get("type"),
                    "priority": notif.get("priority", "normal"),
                    "type": notif.get("type"),
                    "title": Localizer.get_localized_dict(notif.get("title", {}), language),
                    "message": Localizer.get_localized_dict(notif.get("message", {}), language),
                    "data": notif.get("data", {}),
                    "is_read": notif.get("is_read", False),
                    "created_at": notif["created_at"]
                })
            
            return localized_notifications
            
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            raise
    
    @staticmethod
    async def mark_as_read(
        db: AsyncIOMotorDatabase,
        notification_id: str,
        user_id: str
    ) -> bool:
        """
        Mark notification as read
        
        Args:
            db: Database connection
            notification_id: Notification ID
            user_id: User ID
        
        Returns:
            Success status
        """
        try:
            result = await db.notifications.update_one(
                {
                    "_id": ObjectId(notification_id),
                    "user_id": user_id
                },
                {
                    "$set": {"is_read": True}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    @staticmethod
    async def mark_all_as_read(
        db: AsyncIOMotorDatabase,
        user_id: str
    ) -> int:
        """
        Mark all notifications as read for a user
        
        Args:
            db: Database connection
            user_id: User ID
        
        Returns:
            Number of notifications marked
        """
        try:
            result = await db.notifications.update_many(
                {
                    "user_id": user_id,
                    "is_read": False
                },
                {
                    "$set": {"is_read": True}
                }
            )
            
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return 0
    
    @staticmethod
    async def get_unread_count(
        db: AsyncIOMotorDatabase,
        user_id: str
    ) -> int:
        """
        Get count of unread notifications
        
        Args:
            db: Database connection
            user_id: User ID
        
        Returns:
            Unread count
        """
        try:
            count = await db.notifications.count_documents({
                "user_id": user_id,
                "is_read": False
            })
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    @staticmethod
    async def create_diagnosis_notification(
        db: AsyncIOMotorDatabase,
        user_id: str,
        diagnosis_id: str,
        disease_name: str
    ):
        """Create notification for completed diagnosis"""
        await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.DIAGNOSIS_COMPLETE,
            title={
                "en": "Diagnosis Complete",
                "hi": "निदान पूर्ण",
                "kn": "ರೋಗನಿರ್ಣಯ ಪೂರ್ಣಗೊಂಡಿದೆ",
                "ta": "நோய் கண்டறிதல் முடிந்தது",
                "te": "రోగ నిర్ధారణ పూర్తయింది"
            },
            message={
                "en": f"Your crop has been diagnosed with {disease_name}. View treatment recommendations.",
                "hi": f"आपकी फसल में {disease_name} का निदान किया गया है। उपचार की सिफारिशें देखें।",
                "kn": f"ನಿಮ್ಮ ಬೆಳೆಗೆ {disease_name} ರೋಗನಿರ್ಣಯ ಆಗಿದೆ. ಚಿಕಿತ್ಸಾ ಶಿಫಾರಸುಗಳನ್ನು ವೀಕ್ಷಿಸಿ.",
                "ta": f"உங்கள் பயிருக்கு {disease_name} நோய் கண்டறியப்பட்டுள்ளது. சிகிச்சை பரிந்துரைகளைப் பார்க்கவும்.",
                "te": f"మీ పంటకు {disease_name} నిర్ధారించబడింది. చికిత్స సిఫార్సులను చూడండి."
            },
            data={
                "diagnosis_id": diagnosis_id,
                "disease_name": disease_name
            }
        )


# Global service instance
notification_service = NotificationService()
