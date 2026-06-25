"""
Script to update remediation_service.py with complete disease database from JSON
Run this once to migrate all disease data
"""
import json
import re

# Disease ID mapping from JSON format to Python naming
DISEASE_ID_MAP = {
    "Tomato___Early_blight": "tomato_early_blight",
    "Tomato___Late_blight": "tomato_late_blight",
    "Tomato___healthy": "tomato_healthy",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "tomato_tomato_yellow_leaf_curl_virus",
    "Potato___Early_blight": "potato_early_blight",
    "Potato___Late_blight": "potato_late_blight",
    "Potato___healthy": "potato_healthy",
    "Apple___Apple_scab": "apple_apple_scab",
    "Apple___Black_rot": "apple_black_rot",
    "Apple___Cedar_apple_rust": "apple_cedar_apple_rust",
    "Apple___healthy": "apple_healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": "corn_maize_cercospora_leaf_spot_gray_leaf_spot",
    "Corn_(maize)___Common_rust_": "corn_maize_common_rust",
    "Corn_(maize)___Northern_Leaf_Blight": "corn_maize_northern_leaf_blight",
    "Corn_(maize)___healthy": "corn_maize_healthy",
    "Pepper,_bell___Bacterial_spot": "pepper_bell_bacterial_spot",
    "Pepper,_bell___healthy": "pepper_bell_healthy",
    "Strawberry___Leaf_scorch": "strawberry_leaf_scorch",
    "Strawberry___healthy": "strawberry_healthy"
}


def convert_disease_data(json_data):
    """Convert JSON disease data to Python knowledge base format"""
    python_kb = {}
    
    for json_id, disease in json_data.items():
        # Convert disease ID
        python_id = DISEASE_ID_MAP.get(json_id, json_id.lower().replace("___", "_").replace("_(", "_").replace(")___", "_").replace(",_", "_").replace("_", "_"))
        
        # Create disease entry
        python_disease = {
            "disease_id": python_id,
            "name": disease.get("name", {}),
            "description": disease.get("description", {})
        }
        
        # Add treatments if present
        if disease.get("organic_treatment"):
            python_disease["organic_treatment"] = disease["organic_treatment"]
            
        if disease.get("chemical_treatment"):
            python_disease["chemical_treatment"] = disease["chemical_treatment"]
            
        # Add prevention steps
        if disease.get("prevention_steps"):
            python_disease["prevention_steps"] = disease["prevention_steps"]
            
        # Add severity guidance
        if disease.get("severity_guidance"):
            python_disease["severity_guidance"] = disease["severity_guidance"]
            
        # Add community tips if present
        if disease.get("community_tips"):
            python_disease["community_tips"] = disease["community_tips"]
            
        python_kb[python_id] = python_disease
    
    return python_kb


def generate_python_code(knowledge_base):
    """Generate Python code for knowledge base"""
    import pprint
    
    header = '''"""
Remediation Service
Handles treatment recommendations and remediation logic
"""
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.schemas import TreatmentType, SeverityLevel
from app.utils.localization import Localizer
import logging

logger = logging.getLogger(__name__)


class RemediationService:
    """Service for disease remediation and treatment recommendations"""
    
    KNOWLEDGE_BASE = '''
    
    # Generate the knowledge base dictionary
    kb_str = pprint.pformat(knowledge_base, width=120, compact=False)
    
    footer = '''
    
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
            
            # Fall back to in-memory data
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
            
            # Localize treatment steps
            localized_steps = []
            for step in treatment_data.get("steps", []):
                localized_step = {
                    "step_number": step["step_number"],
                    "description": Localizer.get_localized_dict(step.get("description", {}), language),
                    "icon": step.get("icon"),
                    "duration": Localizer.get_localized_dict(step.get("duration", {}), language) if step.get("duration") else None,
                    "safety_warning": Localizer.get_localized_dict(step.get("safety_warning", {}), language) if step.get("safety_warning") else None
                }
                localized_steps.append(localized_step)
            
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
            for step in localized_steps:
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
                "treatment": {
                    "type": treatment_type,
                    "steps": localized_steps,
                    "dosage": Localizer.get_localized_dict(treatment_data.get("dosage", {}), language),
                    "frequency": Localizer.get_localized_dict(treatment_data.get("frequency", {}), language),
                    "cost_estimate": treatment_data.get("cost_estimate"),
                },
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
        language: str = "en"
    ) -> Dict[str, Any]:
        """Get guidance for healthy plants"""
        knowledge = RemediationService.KNOWLEDGE_BASE.get("tomato_healthy", {})
        
        return {
            "disease_id": "healthy",
            "disease_name": Localizer.get_localized_dict(knowledge.get("name", {}), language),
            "message": Localizer.get_localized_dict(knowledge.get("description", {}), language),
            "prevention_tips": knowledge.get("prevention_steps", {}).get(language, []),
            "no_treatment_needed": True
        }


# Global service instance
remediation_service = RemediationService()
'''
    
    return header + kb_str + footer


def main():
    """Main function to convert and update the file"""
    # Load JSON data
    json_file = r"C:\Users\BhaviChasvi\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\sessions\288C3DCCE6FF88E294F95B169BF0F241531311D0\transfers\2026-06\3db9ff06-697c-452d-b736-fe0ae9be8cc7.json"
    
    print("Loading JSON data...")
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    print(f"Found {len(json_data)} diseases in JSON")
    
    # Convert to Python knowledge base
    print("Converting to Python format...")
    knowledge_base = convert_disease_data(json_data)
    
    # Generate Python code
    print("Generating Python code...")
    python_code = generate_python_code(knowledge_base)
    
    # Write to file
    output_file = r"c:\crop\Plant_disease_detection\backend\app\services\remediation_service.py"
    print(f"Writing to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(python_code)
    
    print("✓ Successfully updated remediation_service.py!")
    print(f"✓ Added {len(knowledge_base)} diseases")
    print("\nDiseases added:")
    for disease_id in sorted(knowledge_base.keys()):
        name_en = knowledge_base[disease_id].get("name", {}).get("en", disease_id)
        print(f"  - {disease_id}: {name_en}")


if __name__ == "__main__":
    main()
