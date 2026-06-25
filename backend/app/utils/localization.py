"""
Localization and Translation Utilities
Handles multi-language support
"""
from typing import Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class Localizer:
    """Handles localization and translation"""
    
    # Translation dictionary (in production, load from database or JSON files)
    TRANSLATIONS = {
        "en": {
            "app_name": "Crop Disease Detection",
            "welcome": "Welcome",
            "diagnosis_complete": "Diagnosis Complete",
            "treatment_plan": "Treatment Plan",
            "prevention_tips": "Prevention Tips",
            "healthy_plant": "Your plant is healthy!",
            "no_treatment_needed": "No treatment is required at this time.",
            "consult_expert": "Please consult an agricultural expert",
            "low_confidence": "Low confidence in diagnosis. Please retake the image or consult an expert.",
        },
        "hi": {  # Hindi
            "app_name": "फसल रोग का पता लगाना",
            "welcome": "स्वागत है",
            "diagnosis_complete": "निदान पूर्ण",
            "treatment_plan": "उपचार योजना",
            "prevention_tips": "रोकथाम के सुझाव",
            "healthy_plant": "आपका पौधा स्वस्थ है!",
            "no_treatment_needed": "इस समय किसी उपचार की आवश्यकता नहीं है।",
            "consult_expert": "कृपया कृषि विशेषज्ञ से परामर्श करें",
            "low_confidence": "निदान में कम विश्वास। कृपया छवि को फिर से लें या किसी विशेषज्ञ से परामर्श करें।",
        },
        "kn": {  # Kannada
            "app_name": "ಬೆಳೆ ರೋಗ ಪತ್ತೆ",
            "welcome": "ಸ್ವಾಗತ",
            "diagnosis_complete": "ರೋಗನಿರ್ಣಯ ಪೂರ್ಣಗೊಂಡಿದೆ",
            "treatment_plan": "ಚಿಕಿತ್ಸಾ ಯೋಜನೆ",
            "prevention_tips": "ತಡೆಗಟ್ಟುವ ಸಲಹೆಗಳು",
            "healthy_plant": "ನಿಮ್ಮ ಸಸ್ಯ ಆರೋಗ್ಯಕರವಾಗಿದೆ!",
            "no_treatment_needed": "ಈ ಸಮಯದಲ್ಲಿ ಯಾವುದೇ ಚಿಕಿತ್ಸೆ ಅಗತ್ಯವಿಲ್ಲ.",
            "consult_expert": "ದಯವಿಟ್ಟು ಕೃಷಿ ತಜ್ಞರನ್ನು ಸಂಪರ್ಕಿಸಿ",
            "low_confidence": "ರೋಗನಿರ್ಣಯದಲ್ಲಿ ಕಡಿಮೆ ವಿಶ್ವಾಸ. ದಯವಿಟ್ಟು ಚಿತ್ರವನ್ನು ಮರುಪಡೆಯಿರಿ ಅಥವಾ ತಜ್ಞರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        },
        "ta": {  # Tamil
            "app_name": "பயிர் நோய் கண்டறிதல்",
            "welcome": "வரவேற்பு",
            "diagnosis_complete": "நோய் கண்டறிதல் முடிந்தது",
            "treatment_plan": "சிகிச்சை திட்டம்",
            "prevention_tips": "தடுப்பு குறிப்புகள்",
            "healthy_plant": "உங்கள் செடி ஆரோக்கியமாக உள்ளது!",
            "no_treatment_needed": "இந்த நேரத்தில் எந்த சிகிச்சையும் தேவையில்லை.",
            "consult_expert": "தயவுசெய்து விவசாய நிபுணரை அணுகவும்",
            "low_confidence": "நோய் கண்டறிதலில் குறைந்த நம்பிக்கை. படத்தை மீண்டும் எடுக்கவும் அல்லது நிபுணரை அணுகவும்.",
        },
        "te": {  # Telugu
            "app_name": "పంట వ్యాధి గుర్తింపు",
            "welcome": "స్వాగతం",
            "diagnosis_complete": "రోగ నిర్ధారణ పూర్తయింది",
            "treatment_plan": "చికిత్ sa పథకం",
            "prevention_tips": "నివారణ చిట్కాలు",
            "healthy_plant": "మీ మొక్క ఆరోగ్యంగా ఉంది!",
            "no_treatment_needed": "ఈ సమయంలో ఎటువంటి చికిత్స అవసరం లేదు.",
            "consult_expert": "దయచేసి వ్యవసాయ నిపుణుడిని సంప్రదించండి",
            "low_confidence": "రోగ నిర్ధారణలో తక్కువ నమ్మకం. చిత్రాన్ని మళ్లీ తీయండి లేదా నిపుణుడిని సంప్రదించండి.",
        },
    }
    
    @classmethod
    def translate(cls, key: str, language: str = "en", **kwargs) -> str:
        """
        Get translated string for a key
        
        Args:
            key: Translation key
            language: Target language code
            **kwargs: Format parameters
        
        Returns:
            Translated string
        """
        # Check if language is supported
        if language not in settings.SUPPORTED_LANGUAGES:
            logger.warning(f"Language {language} not supported, falling back to English")
            language = settings.DEFAULT_LANGUAGE
        
        # Get translation
        translations = cls.TRANSLATIONS.get(language, cls.TRANSLATIONS["en"])
        text = translations.get(key, cls.TRANSLATIONS["en"].get(key, key))
        
        # Format with parameters if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                logger.error(f"Missing format parameter: {e}")
        
        return text
    
    @classmethod
    def get_localized_dict(cls, data: Dict[str, str], language: str = "en") -> str:
        """
        Extract localized value from a multi-language dictionary
        
        Args:
            data: Dictionary with language codes as keys
            language: Preferred language
        
        Returns:
            Localized string
        """
        if not data:
            return ""
        
        # Try preferred language
        if language in data:
            return data[language]
        
        # Fall back to default language
        if settings.DEFAULT_LANGUAGE in data:
            return data[settings.DEFAULT_LANGUAGE]
        
        # Return first available
        return next(iter(data.values()), "")
    
    @classmethod
    def localize_remediation(cls, treatment_data: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        """
        Localize treatment/remediation data
        
        Args:
            treatment_data: Treatment data with multi-language fields
            language: Target language
        
        Returns:
            Localized treatment data
        """
        localized = {}
        
        for key, value in treatment_data.items():
            if isinstance(value, dict) and language in value:
                localized[key] = value[language]
            elif isinstance(value, dict) and settings.DEFAULT_LANGUAGE in value:
                localized[key] = value[settings.DEFAULT_LANGUAGE]
            elif isinstance(value, list):
                localized[key] = [cls.get_localized_dict(item, language) if isinstance(item, dict) else item for item in value]
            else:
                localized[key] = value
        
        return localized
    
    @classmethod
    def detect_language_from_header(cls, accept_language: Optional[str]) -> str:
        """
        Detect language from Accept-Language header
        
        Args:
            accept_language: Accept-Language header value
        
        Returns:
            Detected language code
        """
        if not accept_language:
            return settings.DEFAULT_LANGUAGE
        
        # Parse Accept-Language header (e.g., "en-US,en;q=0.9,hi;q=0.8")
        languages = []
        for lang in accept_language.split(','):
            if ';' in lang:
                code, quality = lang.split(';')
                try:
                    q = float(quality.split('=')[1])
                except:
                    q = 1.0
            else:
                code = lang
                q = 1.0
            
            # Extract base language code (e.g., "en" from "en-US")
            base_code = code.strip().split('-')[0].lower()
            languages.append((base_code, q))
        
        # Sort by quality
        languages.sort(key=lambda x: x[1], reverse=True)
        
        # Find first supported language
        for lang_code, _ in languages:
            if lang_code in settings.SUPPORTED_LANGUAGES:
                return lang_code
        
        return settings.DEFAULT_LANGUAGE
    
    @classmethod
    def get_simple_vocabulary(cls, text: str, language: str = "en") -> str:
        """
        Convert technical terms to simple farmer-friendly words
        
        Args:
            text: Technical text
            language: Target language
        
        Returns:
            Simplified text
        """
        # Technical to simple mappings (expandable)
        SIMPLIFICATIONS = {
            "en": {
                "pathogen": "disease-causing organism",
                "fungicide": "anti-fungal medicine",
                "pesticide": "pest killer",
                "chlorosis": "yellowing of leaves",
                "necrosis": "dead tissue",
                "lesion": "infected spot",
            }
        }
        
        simplifications = SIMPLIFICATIONS.get(language, {})
        
        for technical, simple in simplifications.items():
            text = text.replace(technical, simple)
        
        return text


# Helper functions for easy access
def t(key: str, language: str = "en", **kwargs) -> str:
    """Shorthand for translate"""
    return Localizer.translate(key, language, **kwargs)


def get_language_from_request(accept_language: Optional[str], user_preference: Optional[str] = None) -> str:
    """
    Get language from request, prioritizing user preference
    
    Args:
        accept_language: Accept-Language header
        user_preference: User's saved language preference
    
    Returns:
        Language code to use
    """
    if user_preference and user_preference in settings.SUPPORTED_LANGUAGES:
        return user_preference
    
    return Localizer.detect_language_from_header(accept_language)
