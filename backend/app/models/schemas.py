"""
Pydantic Schemas for Request/Response Models
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ============ ENUMS ============

class CropType(str, Enum):
    """Supported crop types"""
    TOMATO = "tomato"
    RICE = "rice"
    WHEAT = "wheat"
    CORN = "corn"
    POTATO = "potato"
    APPLE = "apple"
    PEPPER = "pepper"
    STRAWBERRY = "strawberry"


class SeverityLevel(str, Enum):
    """Disease severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TreatmentType(str, Enum):
    """Treatment types"""
    ORGANIC = "organic"
    CHEMICAL = "chemical"
    BOTH = "both"


class NotificationType(str, Enum):
    """Notification types"""
    DIAGNOSIS_COMPLETE = "diagnosis_complete"
    TREATMENT_UPDATE = "treatment_update"
    WEATHER_ALERT = "weather_alert"
    SYSTEM = "system"


# ============ USER SCHEMAS ============

class Location(BaseModel):
    """Location information"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None


class UserCreate(BaseModel):
    """Schema for user registration"""
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    password: str = Field(..., min_length=8)
    preferred_language: Optional[str] = "en"
    location: Optional[Union[str, Dict[str, Any]]] = None
    
    @field_validator('email', 'phone')
    @classmethod
    def at_least_one_contact(cls, v, info):
        """Ensure at least one contact method is provided"""
        # This will be validated in the endpoint logic
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str  # Can be email or phone
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: Optional[str] = Field(None, alias="_id")
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: str
    location: Optional[Union[str, Dict[str, Any]]] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserUpdate(BaseModel):
    """Schema for user profile update"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    preferred_language: Optional[str] = None
    location: Optional[Union[str, Dict[str, Any]]] = None


# ============ AUTH SCHEMAS ============

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


class PasswordReset(BaseModel):
    """Password reset request"""
    username: str  # Can be email or phone


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    otp: str
    new_password: str = Field(..., min_length=8)


class SessionInfo(BaseModel):
    """User session information"""
    id: str = Field(..., alias="_id")
    device_type: str
    user_agent: Optional[str] = None
    login_time: datetime
    last_activity: datetime
    is_active: bool

    class Config:
        populate_by_name = True


class PasskeyBeginRequest(BaseModel):
    """Request payload for beginning passkey registration/authentication."""
    username: str


class PasskeyFinishRequest(BaseModel):
    """Request payload for completing passkey registration/authentication."""
    username: str
    credential: Dict[str, Any]


class PasskeyRegistrationResult(BaseModel):
    """Response after a passkey is successfully registered."""
    message: str
    credential_id: str


class PasskeyLoginResult(Token):
    """Token response for successful passkey authentication."""
    passkey: bool = True


# ============ DIAGNOSIS SCHEMAS ============

class ImageQualityCheck(BaseModel):
    """Image quality check result"""
    is_acceptable: bool
    blur_score: float
    message: str
    recommendations: Optional[List[str]] = []


class BoundingBox(BaseModel):
    """Bounding box for detected disease region"""
    x: int
    y: int
    width: int
    height: int
    confidence: float


class DiseaseDetection(BaseModel):
    """Single disease detection result"""
    disease_id: str
    disease_name: str
    confidence: float
    severity: SeverityLevel
    affected_area_percentage: Optional[float] = None


class SecondaryDiagnosis(BaseModel):
    """A secondary (co-occurring) infection detected on the same plant."""
    disease_id: str
    disease_name: str
    confidence: float
    severity: Optional[str] = "unknown"
    infected_ratio: Optional[float] = 0.0
    bounding_boxes: Optional[List[BoundingBox]] = []


class DiagnosisCreate(BaseModel):
    """Schema for creating diagnosis"""
    crop_type: CropType
    image_path: str
    location: Optional[Union[str, Dict[str, Any]]] = None


class DiagnosisResponse(BaseModel):
    """Schema for diagnosis response"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    crop_type: str
    disease_id: str
    disease_name: str
    confidence: float
    severity: str
    is_healthy: bool
    is_uncertain: bool = False
    image_url: str
    heatmap_url: Optional[str] = None
    bounding_boxes: Optional[List[BoundingBox]] = []
    secondary_diagnoses: List[Dict[str, Any]] = []
    multi_infection: bool = False
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


class VideoAnalysisRequest(BaseModel):
    """Video analysis request"""
    crop_type: CropType
    frame_interval: int = Field(default=30, ge=1, le=60)  # Extract frame every N frames


# ============ REMEDIATION SCHEMAS ============

class TreatmentStep(BaseModel):
    """Single treatment step"""
    step_number: int
    title: str
    description: str
    duration: Optional[str] = None
    precautions: List[str] = []


class Treatment(BaseModel):
    """Treatment plan"""
    treatment_type: TreatmentType
    name: str
    description: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    cost_estimate: Optional[str] = None
    steps: List[TreatmentStep] = []
    safety_warnings: List[str] = []


class RemediationResponse(BaseModel):
    """Remediation plan response"""
    disease_id: str
    disease_name: str
    severity: SeverityLevel
    treatments: List[Treatment]
    prevention_tips: List[str] = []
    expert_advice: Optional[str] = None
    reference_images: List[str] = []
    language: str = "en"


class HealthyGuidance(BaseModel):
    """Guidance for healthy plants"""
    crop_type: str
    maintenance_tips: List[str]
    prevention_tips: List[str]
    optimal_conditions: Dict[str, str]
    language: str = "en"


# ============ HISTORY SCHEMAS ============

class HistoryFilter(BaseModel):
    """Filters for diagnosis history"""
    crop_type: Optional[CropType] = None
    disease_id: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class HistoryItem(BaseModel):
    """History entry"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    diagnosis_id: str
    crop_type: str
    disease_name: str
    confidence: float
    severity: str
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True


class HistoryResponse(BaseModel):
    """History list response"""
    total: int
    items: List[HistoryItem]
    limit: int
    offset: int


class AnalyticsResponse(BaseModel):
    """Analytics response"""
    total_diagnoses: int
    by_crop_type: Dict[str, int]
    by_disease: Dict[str, int]
    by_severity: Dict[str, int]
    most_common_disease: Optional[str] = None
    average_confidence: float
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class MonthlyTrend(BaseModel):
    """Monthly trend data"""
    month: str
    count: int


class HistoryAnalytics(BaseModel):
    """History analytics response"""
    total_diagnoses: int
    disease_frequency: Dict[str, int]
    crop_wise_trends: Dict[str, int]
    severity_distribution: Dict[str, int]
    monthly_trends: List[MonthlyTrend]


# ============ NOTIFICATION SCHEMAS ============

class NotificationCreate(BaseModel):
    """Create notification"""
    user_id: str
    title: str
    message: str
    notification_type: NotificationType
    priority: str = "normal"  # low, normal, high
    data: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """Notification response"""
    id: str = Field(..., alias="_id")
    user_id: str
    title: str
    message: str
    notification_type: NotificationType
    priority: str
    is_read: bool = False
    data: Optional[Dict[str, Any]] = None
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class NotificationList(BaseModel):
    """List of notifications"""
    total: int
    unread_count: int
    notifications: List[NotificationResponse]


# ============ GENERAL SCHEMAS ============

class HealthCheck(BaseModel):
    """API health check response"""
    status: str
    version: str
    timestamp: datetime
    database: str
    message: str


# ============ CHATBOT SCHEMAS ============

class ChatMessage(BaseModel):
    """Chat message from user"""
    message: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="en", pattern=r'^(en|hi|ta|te|kn|ml)$')


class ChatResponse(BaseModel):
    """Chat response from AI assistant"""
    response: str
    intent: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    language: str
    message_processed: bool
    error: Optional[str] = None


class ConversationHistory(BaseModel):
    """User conversation history entry"""
    id: str = Field(..., alias="_id")
    user_id: str
    message: str
    response: str
    intent: str
    confidence: float
    language: str
    timestamp: datetime
    
    class Config:
        populate_by_name = True


class ConversationSummary(BaseModel):
    """Summary of user's conversation patterns"""
    user_id: str
    total_messages: int
    common_intents: List[Dict[str, Any]]
    preferred_language: str
    last_conversation: datetime


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
