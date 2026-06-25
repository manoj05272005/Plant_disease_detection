"""
Remediation Router
Handles treatment recommendations and remediation guidance
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from app.core.database import get_database
from app.core.security import get_current_user
from app.models.schemas import RemediationResponse, TreatmentType
from app.services.remediation_service import remediation_service
from app.utils.localization import get_language_from_request
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/remediation", tags=["Remediation"])


@router.get("/{disease_id}", response_model=RemediationResponse)
async def get_remediation(
    disease_id: str,
    severity: str = Query(..., description="Disease severity: low, medium, high"),
    treatment_type: TreatmentType = Query(TreatmentType.ORGANIC, description="Treatment type"),
    current_user: dict = Depends(get_current_user),
    accept_language: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get treatment recommendations for a disease
    
    Epic 2 - Remediation & Guidance
    US1: Step-by-step remediation instructions
    US2: Chemical and organic treatment options
    US3: Dosage and application frequency
    US4: Safety warnings
    US8: Severity-based guidance
    """
    try:
        language = get_language_from_request(accept_language, current_user.get("preferred_language"))
        
        # Get remediation data
        remediation_data = await remediation_service.get_remediation(
            db=db,
            disease_id=disease_id,
            severity=severity,
            treatment_type=treatment_type.value,
            language=language
        )
        
        logger.info(f"Remediation fetched for disease: {disease_id}, type: {treatment_type}, language: {language}")
        
        return remediation_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting remediation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve remediation guidance"
        )


@router.get("/healthy/guidance")
async def get_healthy_guidance(
    disease_id: str = Query("Tomato___healthy", description="Healthy disease id"),
    current_user: dict = Depends(get_current_user),
    accept_language: Optional[str] = Header(None)
):
    """
    Get guidance for healthy plants
    
    Epic 2 - Remediation & Guidance
    US9: No treatment needed for healthy plants
    """
    try:
        language = get_language_from_request(accept_language, current_user.get("preferred_language"))
        
        guidance = await remediation_service.get_healthy_plant_guidance(
            disease_id=disease_id,
            language=language
        )
        
        return guidance
        
    except Exception as e:
        logger.error(f"Error getting healthy guidance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve guidance"
        )
