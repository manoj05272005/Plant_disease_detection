"""
History Router
Handles diagnosis history, filtering, analytics, and reports
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from typing import Optional
from bson import ObjectId

from app.core.database import get_database
from app.core.security import get_current_user
from app.models.schemas import HistoryResponse, AnalyticsResponse, HistoryFilter, CropType, SeverityLevel, DiagnosisResponse, HistoryAnalytics
from app.utils.pdf_generator import PDFReportGenerator
from app.utils.localization import get_language_from_request
from app.services.remediation_service import remediation_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/", response_model=HistoryResponse)
async def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    crop_type: Optional[CropType] = None,
    severity: Optional[SeverityLevel] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    disease_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get diagnosis history with filtering
    
    Epic 1, Pile 9 - View History (US9)
    Epic 1, Pile 10 - Filter History (US10)
    """
    try:
        user_id = str(current_user["_id"])
        
        # Build query
        query = {"user_id": user_id, "is_deleted": {"$ne": True}}
        
        if crop_type:
            query["crop_type"] = crop_type.value
        if severity:
            query["severity"] = severity.value
        if disease_name:
            query["disease_name"] = {"$regex": disease_name, "$options": "i"}
        if start_date or end_date:
            query["created_at"] = {}
            if start_date:
                query["created_at"]["$gte"] = start_date
            if end_date:
                query["created_at"]["$lte"] = end_date
        
        # Get history
        total = await db.history.count_documents(query)
        cursor = db.history.find(query).sort("created_at", -1).skip(skip).limit(limit)
        history = await cursor.to_list(length=limit)

        # Format results
        for entry in history:
            entry["_id"] = str(entry["_id"])

        logger.info(f"History fetched for user: {user_id}, filters: {query}")

        return {
            "total": total,
            "items": history,
            "limit": limit,
            "offset": skip
        }
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history"
        )


@router.delete("/{history_id}")
async def delete_history_entry(
    history_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete a history entry
    
    Epic 1, Pile 13 - Delete History Entry (US13)
    """
    try:
        user_id = str(current_user["_id"])
        
        # Soft delete (mark as deleted rather than removing)
        result = await db.history.update_one(
            {
                "_id": ObjectId(history_id),
                "user_id": user_id
            },
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History entry not found"
            )
        
        logger.info(f"History entry deleted: {history_id} by user: {user_id}")
        
        return {"message": "History entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting history entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete history entry"
        )


@router.get("/analytics", response_model=HistoryAnalytics)
async def get_analytics(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get analytics and insights from diagnosis history
    
    Epic 1, Pile 14 - History Analytics (US14)
    """
    try:
        user_id = str(current_user["_id"])
        
        # Get all history for the user
        cursor = db.history.find({"user_id": user_id, "is_deleted": {"$ne": True}})
        history = await cursor.to_list(length=None)
        
        # Calculate statistics
        total_diagnoses = len(history)
        
        # Disease frequency
        disease_frequency = {}
        for entry in history:
            disease_name = entry.get("disease_name", "Unknown")
            disease_frequency[disease_name] = disease_frequency.get(disease_name, 0) + 1
        
        # Crop-wise trends
        crop_wise_trends = {}
        for entry in history:
            crop_type = entry.get("crop_type", "Unknown")
            crop_wise_trends[crop_type] = crop_wise_trends.get(crop_type, 0) + 1
        
        # Severity distribution
        severity_distribution = {}
        for entry in history:
            severity = entry.get("severity", "Unknown")
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # Monthly trends
        monthly_trends = {}
        for entry in history:
            created_at = entry.get("created_at")
            if created_at:
                month_key = created_at.strftime("%Y-%m")
                monthly_trends[month_key] = monthly_trends.get(month_key, 0) + 1
        
        monthly_trends_list = [
            {"month": month, "count": count}
            for month, count in sorted(monthly_trends.items())
        ]
        
        return {
            "total_diagnoses": total_diagnoses,
            "disease_frequency": disease_frequency,
            "crop_wise_trends": crop_wise_trends,
            "severity_distribution": severity_distribution,
            "monthly_trends": monthly_trends_list
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.get("/report/{diagnosis_id}")
async def download_report(
    diagnosis_id: str,
    include_treatment: bool = Query(True),
    include_prevention: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    accept_language: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate and download PDF report for a diagnosis
    
    Epic 1, Pile 12 - Download Report (US12)
    """
    try:
        user_id = str(current_user["_id"])
        language = get_language_from_request(accept_language, current_user.get("preferred_language"))
        
        # Get diagnosis
        diagnosis = await db.diagnoses.find_one({
            "_id": ObjectId(diagnosis_id),
            "user_id": user_id
        })
        
        if not diagnosis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnosis not found"
            )
        
        # Get treatment data if requested
        remediation_data = None
        if include_treatment:
            if diagnosis.get("is_healthy"):
                remediation_data = await remediation_service.get_healthy_plant_guidance(
                    disease_id=diagnosis["disease_id"],
                    language=language
                )
            else:
                remediation_data = await remediation_service.get_remediation(
                    db=db,
                    disease_id=diagnosis["disease_id"],
                    severity=diagnosis["severity"],
                    language=language
                )
                if not include_prevention and remediation_data:
                    remediation_data["prevention_tips"] = []
        
        # Get user data
        user_data = {
            "name": current_user.get("name"),
            "email": current_user.get("email"),
            "phone": current_user.get("phone")
        }
        
        # Generate PDF
        pdf_buffer = PDFReportGenerator.generate_diagnosis_report(
            diagnosis_data=diagnosis,
            remediation_data=remediation_data,
            user_data=user_data,
            language=language
        )
        
        logger.info(f"PDF report generated for diagnosis: {diagnosis_id}")
        
        # Return as streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=diagnosis_report_{diagnosis_id}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report"
        )
