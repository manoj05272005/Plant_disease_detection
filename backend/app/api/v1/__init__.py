"""
API v1 Router Configuration
"""
from fastapi import APIRouter
from app.api.v1 import auth, user, diagnosis, remediation, history, notifications, chatbot

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(diagnosis.router)
api_router.include_router(remediation.router)
api_router.include_router(history.router)
api_router.include_router(notifications.router)
api_router.include_router(chatbot.router)
