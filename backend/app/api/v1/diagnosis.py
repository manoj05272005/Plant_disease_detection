"""
Diagnosis Router
Handles image upload, AI diagnosis, and quality checks
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Header, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from typing import Optional
from bson import ObjectId
import cv2
import numpy as np

from app.core.database import get_database
from app.core.security import get_current_user
from app.models.schemas import DiagnosisCreate, DiagnosisResponse, CropType, ImageQualityCheck
from app.services.ai_service import ai_service
from app.utils.image_processing import ImageProcessor
from app.utils.file_handler import FileHandler
from app.utils.localization import get_language_from_request
from app.services.notification_service import notification_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnosis", tags=["Diagnosis"])


@router.post("/check-quality", response_model=ImageQualityCheck)
async def check_image_quality(
    image: UploadFile = File(...),
):
    """
    Check image quality before diagnosis
    
    Epic 3 - AI Detection (US5: Blur Detection)
    """
    try:
        # Read image
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
        
        # Check quality
        quality_result = ImageProcessor.check_blur(img)
        
        return quality_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking image quality: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image quality check failed"
        )


@router.post("/", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
async def create_diagnosis(
    background_tasks: BackgroundTasks,
    crop_type: CropType = Form(...),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    accept_language: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create new diagnosis from uploaded image
    
    Epic 3 - AI Detection (US2: Image Upload & Analysis)
    """
    try:
        user_id = str(current_user["_id"])
        language = get_language_from_request(accept_language, current_user.get("preferred_language"))
        
        # Read and validate image
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
        
        # Check image quality
        quality_check = ImageProcessor.check_blur(img)
        if not quality_check["is_acceptable"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=quality_check["message"]
            )
        
        # Save original image
        image_bytes = cv2.imencode('.jpg', img)[1].tobytes()
        import base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        image_path = await FileHandler.save_image_from_base64(
            f"data:image/jpeg;base64,{image_base64}",
            subdir="images",
            prefix=f"{crop_type.value}_"
        )
        
        # Run AI diagnosis
        diagnosis_result = await ai_service.predict_disease(img, crop_type.value)
        
        # Save heatmap
        heatmap_base64 = ImageProcessor.encode_image_to_base64(diagnosis_result["heatmap_image"])
        heatmap_path = await FileHandler.save_image_from_base64(
            heatmap_base64,
            subdir="heatmaps",
            prefix="heatmap_"
        )
        
        # Create diagnosis document
        diagnosis_doc = {
            "user_id": user_id,
            "crop_type": crop_type.value,
            "disease_id": diagnosis_result["disease_id"],
            "disease_name": diagnosis_result["disease_name"],
            "confidence": diagnosis_result["confidence"],
            "severity": diagnosis_result["severity"],
            "is_healthy": diagnosis_result["is_healthy"],
            "is_uncertain": diagnosis_result.get("is_uncertain", False),
            "image_url": FileHandler.get_file_url(image_path),
            "heatmap_url": FileHandler.get_file_url(heatmap_path),
            "bounding_boxes": diagnosis_result.get("bounding_boxes", []),
            "secondary_diagnoses": diagnosis_result.get("secondary_diagnoses", []),
            "multi_infection": diagnosis_result.get("multi_infection", False),
            "created_at": datetime.utcnow(),
            "metadata": {
                "image_quality": quality_check,
                "all_predictions": diagnosis_result.get("all_predictions", {}),
                "original_prediction": diagnosis_result.get("disease_id", "")
            }
        }
        
        # Save to database
        result = await db.diagnoses.insert_one(diagnosis_doc)
        diagnosis_id = str(result.inserted_id)
        diagnosis_doc["_id"] = diagnosis_id
        
        # Save to history
        history_doc = {
            "user_id": user_id,
            "diagnosis_id": diagnosis_id,
            "crop_type": crop_type.value,
            "disease_name": diagnosis_result["disease_name"],
            "confidence": diagnosis_result["confidence"],
            "severity": diagnosis_result["severity"],
            "image_url": FileHandler.get_file_url(image_path),
            "created_at": datetime.utcnow()
        }
        await db.history.insert_one(history_doc)
        
        # Create notification in background
        background_tasks.add_task(
            notification_service.create_diagnosis_notification,
            db,
            user_id,
            diagnosis_id,
            diagnosis_result["disease_name"]
        )
        
        logger.info(f"Diagnosis created: {diagnosis_id} for user: {user_id}")
        
        return diagnosis_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating diagnosis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Diagnosis creation failed"
        )


@router.get("/{diagnosis_id}", response_model=DiagnosisResponse)
async def get_diagnosis(
    diagnosis_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get diagnosis by ID
    
    Epic 1, Pile 11 - Detailed Report View (US11)
    """
    try:
        user_id = str(current_user["_id"])
        
        diagnosis = await db.diagnoses.find_one({
            "_id": ObjectId(diagnosis_id),
            "user_id": user_id
        })
        
        if not diagnosis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnosis not found"
            )
        
        diagnosis["_id"] = str(diagnosis["_id"])
        return diagnosis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diagnosis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve diagnosis"
        )


@router.post("/video", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
async def diagnose_from_video(
    background_tasks: BackgroundTasks,
    crop_type: CropType = Form(...),
    video: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    accept_language: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create diagnosis from video (extracts keyframes)
    
    Epic 3 - AI Detection (US3: Video Recording)
    """
    try:
        user_id = str(current_user["_id"])
        
        # Save video temporarily
        video_path = await FileHandler.save_upload_file(video, subdir="videos")
        full_video_path = f"{FileHandler.ensure_upload_dir()}/{video_path}"
        
        # Extract frames
        frames = ImageProcessor.extract_frames_from_video(full_video_path, num_frames=3)
        
        if not frames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract frames from video"
            )
        
        # Run diagnosis on frames (majority voting)
        diagnosis_result = await ai_service.predict_from_video_frames(frames, crop_type.value)
        
        # Use the best frame as the main image
        best_frame = frames[0]  # In production, select the frame with highest confidence
        
        # Save image
        image_bytes = cv2.imencode('.jpg', best_frame)[1].tobytes()
        import base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        image_path = await FileHandler.save_image_from_base64(
            f"data:image/jpeg;base64,{image_base64}",
            subdir="images",
            prefix=f"{crop_type.value}_video_"
        )
        
        # Save heatmap
        heatmap_base64 = ImageProcessor.encode_image_to_base64(diagnosis_result["heatmap_image"])
        heatmap_path = await FileHandler.save_image_from_base64(
            heatmap_base64,
            subdir="heatmaps",
            prefix="heatmap_"
        )
        
        # Create diagnosis document
        diagnosis_doc = {
            "user_id": user_id,
            "crop_type": crop_type.value,
            "disease_id": diagnosis_result["disease_id"],
            "disease_name": diagnosis_result["disease_name"],
            "confidence": diagnosis_result["confidence"],
            "severity": diagnosis_result["severity"],
            "is_healthy": diagnosis_result["is_healthy"],
            "is_uncertain": diagnosis_result.get("is_uncertain", False),
            "image_url": FileHandler.get_file_url(image_path),
            "heatmap_url": FileHandler.get_file_url(heatmap_path),
            "bounding_boxes": diagnosis_result.get("bounding_boxes", []),
            "secondary_diagnoses": diagnosis_result.get("secondary_diagnoses", []),
            "created_at": datetime.utcnow(),
            "metadata": {
                "source": "video",
                "frames_analyzed": len(frames),
                "original_prediction": diagnosis_result.get("disease_id", "")
            }
        }
        
        # Save to database
        result = await db.diagnoses.insert_one(diagnosis_doc)
        diagnosis_id = str(result.inserted_id)
        diagnosis_doc["_id"] = diagnosis_id
        
        # Save to history
        history_doc = {
            "user_id": user_id,
            "diagnosis_id": diagnosis_id,
            "crop_type": crop_type.value,
            "disease_name": diagnosis_result["disease_name"],
            "confidence": diagnosis_result["confidence"],
            "severity": diagnosis_result["severity"],
            "image_url": FileHandler.get_file_url(image_path),
            "created_at": datetime.utcnow()
        }
        await db.history.insert_one(history_doc)
        
        # Create notification
        background_tasks.add_task(
            notification_service.create_diagnosis_notification,
            db,
            user_id,
            diagnosis_id,
            diagnosis_result["disease_name"]
        )
        
        # Clean up video file
        background_tasks.add_task(FileHandler.delete_file, video_path)
        
        logger.info(f"Video diagnosis created: {diagnosis_id} for user: {user_id}")
        
        return diagnosis_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in video diagnosis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Video diagnosis failed"
        )


@router.get("/", response_model=list[DiagnosisResponse])
async def list_diagnoses(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List all diagnoses for current user
    """
    try:
        user_id = str(current_user["_id"])
        
        cursor = db.diagnoses.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
        diagnoses = await cursor.to_list(length=limit)
        
        for diagnosis in diagnoses:
            diagnosis["_id"] = str(diagnosis["_id"])
        
        return diagnoses
        
    except Exception as e:
        logger.error(f"Error listing diagnoses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list diagnoses"
        )
