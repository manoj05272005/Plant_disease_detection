"""
Remediation Service
Handles treatment recommendations and remediation logic
"""
from typing import Dict, Any, Optional
from pathlib import Path
import json
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase
from app.utils.localization import Localizer

logger = logging.getLogger(__name__)


def _load_remediation_json() -> Dict[str, Any]:
    """Load the comprehensive remediation knowledge base from JSON file."""
    json_path = Path(__file__).parent.parent / "data" / "remediation.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded remediation knowledge base with {len(data)} diseases from {json_path}")
        return data
    except Exception as e:
        logger.warning(f"Could not load remediation.json: {e}. Using empty fallback.")
        return {}


class RemediationService:
    """Service for disease remediation and treatment recommendations"""

    # Load comprehensive knowledge base from remediation.json
    KNOWLEDGE_BASE = _load_remediation_json()

    @staticmethod
    def _localize_treatment(treatment_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Localize treatment data by extracting the correct language from multi-lang dicts."""
        if not treatment_data:
            return {}
        
        localized = {}
        for key, value in treatment_data.items():
            if key == "steps" and isinstance(value, list):
                localized_steps = []
                for step in value:
                    localized_step = {}
                    for sk, sv in step.items():
                        if isinstance(sv, dict) and (language in sv or "en" in sv):
                            localized_step[sk] = sv.get(language, sv.get("en", str(sv)))
                        else:
                            localized_step[sk] = sv
                    localized_steps.append(localized_step)
                localized["steps"] = localized_steps
            elif isinstance(value, dict) and (language in value or "en" in value):
                localized[key] = value.get(language, value.get("en", str(value)))
            else:
                localized[key] = value
        
        return localized

    @staticmethod
    async def get_remediation(
        db: AsyncIOMotorDatabase,
        disease_id: str,
        severity: str,
        treatment_type: str = "organic",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get remediation recommendations
        
        Args:
            db: Database connection
            disease_id: Disease identifier
            severity: Disease severity level
            treatment_type: Type of treatment (organic/chemical)
            language: Language for recommendations
        
        Returns:
            Localized remediation data
        """
        try:
            # First try to get from database
            knowledge = await db.knowledge_base.find_one({"disease_id": disease_id})
            
            # Fall back to local knowledge base (remediation.json)
            if not knowledge:
                knowledge = RemediationService.KNOWLEDGE_BASE.get(disease_id, {})
            
            if not knowledge:
                raise ValueError(f"No knowledge base found for disease: {disease_id}")
            
            # Get localized disease name
            disease_name = Localizer.get_localized_dict(knowledge.get("name", {}), language)
            
            # Get treatment based on type
            if treatment_type == "chemical":
                treatment_data = knowledge.get("chemical_treatment", {})
            else:
                treatment_data = knowledge.get("organic_treatment", {})

            localized_treatment = RemediationService._localize_treatment(treatment_data, language)
            
            # Get prevention tips
            prevention_tips = knowledge.get("prevention_steps", {}).get(language, [])
            
            # Get severity-specific guidance
            severity_guidance = knowledge.get("severity_guidance", {}).get(severity, {})
            guidance_text = Localizer.get_localized_dict(severity_guidance, language) if severity_guidance else None
            
            # Get community tips if available
            community_tips_data = knowledge.get("community_tips", {})
            community_tips = community_tips_data.get(language, []) if isinstance(community_tips_data, dict) else []
            
            # Safety warnings
            safety_warnings = []
            for step in localized_treatment.get("steps", []):
                if step.get("safety_warning"):
                    safety_warnings.append(step["safety_warning"])
            
            # Check if expert consultation needed
            expert_consultation_required = (
                severity in ["high", "critical"] or
                treatment_type == "chemical"
            )
            
            return {
                "disease_id": disease_id,
                "disease_name": disease_name,
                "severity": severity,
                "treatment": localized_treatment,
                "prevention_tips": prevention_tips,
                "safety_warnings": safety_warnings,
                "severity_guidance": guidance_text,
                "community_tips": community_tips,
                "expert_consultation_required": expert_consultation_required
            }
            
        except Exception as e:
            logger.error(f"Error getting remediation: {e}")
            raise
    
    @staticmethod
    async def get_healthy_plant_guidance(
        disease_id: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Get guidance for healthy plants"""
        # Try to find crop-specific healthy guidance (e.g., "Tomato___healthy", "Apple___healthy")
        knowledge = RemediationService.KNOWLEDGE_BASE.get(disease_id, {})
        
        # Fallback: try generic healthy keys
        if not knowledge:
            for key in RemediationService.KNOWLEDGE_BASE:
                if "healthy" in key.lower():
                    knowledge = RemediationService.KNOWLEDGE_BASE[key]
                    break
        
        if not knowledge:
            knowledge = {
                "name": {"en": "Healthy Plant"},
                "description": {"en": "Your plant appears healthy with no signs of disease"},
                "prevention_steps": {"en": ["Continue regular care and monitoring"]}
            }
        
        return {
            "disease_id": "healthy",
            "disease_name": Localizer.get_localized_dict(knowledge.get("name", {}), language),
            "message": Localizer.get_localized_dict(knowledge.get("description", {}), language),
            "prevention_tips": knowledge.get("prevention_steps", {}).get(language, []),
            "no_treatment_needed": True
        }


# Global service instance
remediation_service = RemediationService()
