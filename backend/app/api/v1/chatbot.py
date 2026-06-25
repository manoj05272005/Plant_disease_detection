"""
Chatbot Router
Handles multilingual conversational AI for agricultural assistance
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime

from app.core.database import get_database
from app.core.security import get_current_user
from app.models.schemas import ChatMessage, ChatResponse, ConversationHistory
from app.services.chatbot_service import ChatbotService
from app.utils.localization import get_language_from_request
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Initialize chatbot service (singleton)
chatbot_service = None

def get_chatbot_service() -> ChatbotService:
    """Get or create chatbot service instance"""
    global chatbot_service
    if chatbot_service is None:
        chatbot_service = ChatbotService()
    return chatbot_service


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    current_user: dict = Depends(get_current_user),
    accept_language: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Send message to agricultural AI chatbot and get multilingual response
    
    Features:
    - Intent recognition (disease diagnosis, weather, farming advice, etc.)
    - Multilingual response generation
    - Conversation history tracking
    - Support for 6 languages (en, hi, ta, te, kn, ml)
    """
    try:
        user_id = str(current_user["_id"])
        
        # Get language preference (header > user profile > message > default)
        language = get_language_from_request(
            accept_language, 
            current_user.get("preferred_language")
        )
        if not language:
            language = chat_message.language
        
        # Get chatbot service and process message
        service = get_chatbot_service()
        result = service.process_message(
            user_message=chat_message.message,
            language=language
        )
        
        # Save conversation history to database
        await _save_conversation_history(
            db=db,
            user_id=user_id,
            message=chat_message.message,
            response=result["response"],
            intent=result["intent"],
            confidence=result["confidence"],
            language=language
        )
        
        # Return formatted response
        return ChatResponse(
            response=result["response"],
            intent=result["intent"],
            confidence=result["confidence"],
            language=language,
            message_processed=result["message_processed"],
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error processing chatbot message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process your message. Please try again."
        )


@router.get("/history", response_model=list[ConversationHistory])
async def get_conversation_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get user's conversation history with the chatbot
    
    Args:
        limit: Maximum number of conversations to return (default: 20)
    
    Returns:
        List of conversation history entries
    """
    try:
        user_id = str(current_user["_id"])
        
        # Query conversation history from database
        cursor = db.conversation_history.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)
        
        conversations = []
        async for doc in cursor:
            conversations.append(ConversationHistory(**doc))
        
        return conversations
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history."
        )


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_conversation_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Clear user's conversation history with the chatbot
    """
    try:
        user_id = str(current_user["_id"])
        
        # Delete all conversation history for the user
        await db.conversation_history.delete_many({"user_id": user_id})
        
        logger.info(f"Cleared conversation history for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear conversation history."
        )


@router.get("/intents")
async def get_supported_intents():
    """
    Get list of supported conversation intents
    
    Returns:
        List of supported intents with descriptions
    """
    try:
        service = get_chatbot_service()
        return {
            "intents": service.intent_descriptions,
            "supported_languages": list(service.supported_languages.keys())
        }
    except Exception as e:
        logger.error(f"Error getting supported intents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supported intents."
        )


async def _save_conversation_history(
    db: AsyncIOMotorDatabase,
    user_id: str,
    message: str,
    response: str,
    intent: str,
    confidence: float,
    language: str
) -> None:
    """
    Save conversation to database for history tracking
    
    Args:
        db: Database connection
        user_id: User identifier
        message: User's input message
        response: AI assistant's response
        intent: Detected intent
        confidence: Confidence score for intent detection
        language: Language used for conversation
    """
    try:
        conversation_doc = {
            "user_id": user_id,
            "message": message,
            "response": response,
            "intent": intent,
            "confidence": confidence,
            "language": language,
            "timestamp": datetime.utcnow()
        }
        
        await db.conversation_history.insert_one(conversation_doc)
        
    except Exception as e:
        logger.error(f"Failed to save conversation history: {e}")
        # Don't raise exception here as it's not critical to the main flow