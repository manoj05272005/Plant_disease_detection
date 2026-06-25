"""
Chatbot Service
Handles multilingual conversational AI for crop and agriculture assistance
"""
import logging
from typing import Dict, Any, Optional, List
try:
    from transformers import pipeline
except ImportError:
    pipeline = None
from deep_translator import GoogleTranslator
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Chatbot service for multilingual agricultural assistance
    """
    
    def __init__(self):
        """Initialize the chatbot service with AI models"""
        try:
            # Initialize intent classifier for understanding user queries
            if pipeline is not None:
                self.classifier = pipeline(
                    "zero-shot-classification", 
                    model="facebook/bart-large-mnli"
                )
            else:
                logger.warning("Transformers is not installed. Zero-shot chatbot classifier will fall back to rule-based classification.")
                self.classifier = None
            
            # Define supported conversation intents
            self.supported_intents = [
                "crop disease diagnosis",
                "weather inquiry", 
                "farming advice",
                "fertilizer guidance",
                "irrigation tips",
                "pest control",
                "seasonal farming",
                "general greeting",
                "goodbye"
            ]
            
            # Intent descriptions for better classification
            self.intent_descriptions = {
                "crop disease diagnosis": "Asking about plant health, diseases, symptoms, or leaf problems",
                "weather inquiry": "Asking about weather, rain, temperature, or climate conditions",
                "farming advice": "Asking for general farming tips, cultivation methods, or best practices",
                "fertilizer guidance": "Asking about fertilizers, nutrients, or soil enhancement",
                "irrigation tips": "Asking about watering, irrigation systems, or water management",
                "pest control": "Asking about insects, pests, or pest management strategies",
                "seasonal farming": "Asking about planting seasons, harvest time, or seasonal activities",
                "general greeting": "Saying hello, hi, introducing oneself, or asking who the assistant is",
                "goodbye": "Saying goodbye, thanks, or ending the conversation"
            }
            
            # Supported languages (matching existing app languages)
            self.supported_languages = {
                'en': 'english',
                'hi': 'hindi',
                'ta': 'tamil',
                'te': 'telugu',
                'kn': 'kannada',
                'ml': 'malayalam'
            }
            
            logger.info("Chatbot service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize chatbot service: {e}")
            raise

    def detect_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Detect user intent from their message
        
        Args:
            user_message: User's input message
            
        Returns:
            Dict containing intent and confidence score
        """
        if self.classifier is None:
            # Simple keyword matching fallback
            msg = user_message.lower()
            intent = "general_greeting"
            if any(w in msg for w in ["disease", "sick", "spot", "leaf", "rot", "blight", "scab"]):
                intent = "crop disease diagnosis"
            elif any(w in msg for w in ["weather", "rain", "temp", "hot", "cold", "forecast"]):
                intent = "weather inquiry"
            elif any(w in msg for w in ["fertilizer", "manure", "urea", "potash"]):
                intent = "fertilizer guidance"
            elif any(w in msg for w in ["water", "irrigate", "drip", "sprinkler"]):
                intent = "irrigation tips"
            elif any(w in msg for w in ["pest", "bug", "insect", "spray"]):
                intent = "pest control"
            elif any(w in msg for w in ["plant", "season", "grow", "crop"]):
                intent = "seasonal farming"
            elif any(w in msg for w in ["bye", "thank"]):
                intent = "goodbye"
            
            return {
                "intent": intent,
                "confidence": 0.8,
                "description": self.intent_descriptions.get(intent, "Default intent")
            }

        try:
            # Use descriptions for better intent classification
            descriptions = list(self.intent_descriptions.values())
            
            result = self.classifier(user_message, candidate_labels=descriptions)
            
            # Map back from description to intent name
            best_description = result['labels'][0]
            best_intent = next(
                (intent for intent, desc in self.intent_descriptions.items() 
                 if desc == best_description), 
                "general_greeting"
            )
            
            return {
                "intent": best_intent,
                "confidence": result['scores'][0],
                "description": best_description
            }
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            return {
                "intent": "general_greeting",
                "confidence": 0.5,
                "description": "Default greeting"
            }

    def generate_response(self, intent: str, user_message: str, language: str = "en") -> str:
        """
        Generate appropriate response based on detected intent
        
        Args:
            intent: Detected user intent
            user_message: Original user message
            language: Target language for response
            
        Returns:
            Generated response in specified language
        """
        try:
            # Generate English response based on intent
            english_response = self._get_intent_response(intent, user_message)
            
            # Translate to target language if not English
            if language != "en":
                try:
                    translated_response = GoogleTranslator(
                        source='auto', 
                        target=language
                    ).translate(english_response)
                    return translated_response
                except Exception as e:
                    logger.warning(f"Translation failed for language {language}: {e}")
                    return english_response  # Fallback to English
            
            return english_response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._get_fallback_response(language)

    def _get_intent_response(self, intent: str, user_message: str) -> str:
        """
        Get appropriate response for detected intent
        
        Args:
            intent: User intent
            user_message: Original message for context
            
        Returns:
            English response string
        """
        responses = {
            "crop disease diagnosis": [
                "I can help you identify plant diseases! To provide accurate diagnosis, I'll need you to take a clear photo of the affected plant leaf using the camera feature. You can then get detailed information about the disease and treatment recommendations.",
                "For disease diagnosis, please use the camera feature to capture a clear image of the affected plant parts. I'll analyze the image and provide you with detailed diagnosis and treatment suggestions.",
                "I'd be happy to help diagnose plant diseases! Please use the scan feature to take a photo of the plant leaf or affected area. Make sure the image is clear and well-lit for best results."
            ],
            "weather inquiry": [
                "For current weather information, you can check the weather widget on your home screen. It provides real-time conditions near your farm location including temperature, humidity, and weather forecasts.",
                "Weather information is available on your dashboard! The weather card shows current conditions, temperature, and humidity data for your farm area.",
                "You can find live weather conditions on the home screen. The weather widget displays current temperature, humidity, and conditions specific to your farming location."
            ],
            "farming advice": [
                "I'm here to help with farming advice! What specific aspect of farming would you like guidance on? I can assist with crop selection, planting techniques, soil management, or general agricultural practices.",
                "I'd be happy to share farming tips! Are you looking for advice on a specific crop, soil preparation, planting seasons, or general farming practices? Let me know what you need help with.",
                "I can provide various farming guidance! Whether you need help with crop rotation, soil health, planting techniques, or seasonal farming activities, I'm here to assist you."
            ],
            "fertilizer guidance": [
                "For fertilizer recommendations, I suggest conducting a soil test first to understand your soil's nutrient needs. Based on your crop type and soil condition, you can choose organic fertilizers like compost and manure, or specific NPK fertilizers as needed.",
                "Fertilizer selection depends on your crop and soil type. Generally, organic options like compost, vermicompost, and green manure are excellent for soil health. For specific nutrients, NPK fertilizers can supplement based on soil testing results.",
                "Proper fertilization is key to healthy crops! Consider using organic fertilizers like cow dung, compost, or green manure. For specific deficiencies, targeted fertilizers can help. Always test your soil first for best results."
            ],
            "irrigation tips": [
                "Efficient watering is crucial for healthy crops! Use drip irrigation for water conservation, water early morning or evening to reduce evaporation, and monitor soil moisture to avoid over or under-watering.",
                "For optimal irrigation, consider the crop type and growth stage. Generally, deep but less frequent watering is better than shallow frequent watering. Mulching helps retain soil moisture and reduces water needs.",
                "Smart irrigation practices include checking soil moisture regularly, using water-efficient methods like drip systems, and timing irrigation based on weather conditions. Avoid watering during hot midday hours."
            ],
            "pest control": [
                "For effective pest management, try integrated pest management (IPM) approaches. Use neem oil, introduce beneficial insects, practice crop rotation, and maintain field hygiene. Monitor plants regularly for early pest detection.",
                "Natural pest control methods include neem oil sprays, companion planting, encouraging beneficial insects, and maintaining clean farming practices. For severe infestations, consult with agricultural experts for targeted solutions.",
                "Pest management is best done through prevention and natural methods. Regular monitoring, proper sanitation, biological controls like beneficial insects, and organic sprays can effectively manage most pest problems."
            ],
            "seasonal farming": [
                "Seasonal farming planning depends on your local climate and crop choices. Generally, prepare soil during off-seasons, plant according to monsoon patterns, and plan crop rotation for year-round productivity.",
                "For seasonal success, align your planting with local weather patterns, choose crop varieties suited to each season, and plan harvesting to avoid monsoon damage. Crop diversification helps spread risk across seasons.",
                "Successful seasonal farming involves timing your activities with weather patterns, selecting appropriate crop varieties for each season, and planning for seasonal challenges like droughts or excessive rains."
            ],
            "general_greeting": [
                "Hello! I'm your AI farming assistant. I'm here to help you with crop disease diagnosis, farming advice, weather information, and agricultural guidance. How can I assist you today?",
                "Hi there! Welcome to your agricultural AI assistant. I can help you identify plant diseases, provide farming tips, share weather updates, and offer agricultural guidance. What would you like to know?",
                "Greetings! I'm here to support your farming needs. Whether you need help with disease diagnosis, farming practices, weather information, or agricultural advice, I'm ready to assist you!"
            ],
            "goodbye": [
                "Thank you for using the agricultural assistant! Feel free to come back anytime you need farming advice or plant disease diagnosis. Have a great day with your farming activities!",
                "Goodbye! I hope I was able to help you today. Remember, I'm always here when you need agricultural guidance or disease diagnosis. Take care of your crops!",
                "It was great helping you today! Come back anytime you need farming assistance or plant health diagnosis. Wishing you success with your agricultural endeavors!"
            ]
        }
        
        # Get random response from available options for the intent
        intent_responses = responses.get(intent, responses["general_greeting"])
        import random
        return random.choice(intent_responses)

    def _get_fallback_response(self, language: str) -> str:
        """
        Provide fallback response when other methods fail
        
        Args:
            language: Target language code
            
        Returns:
            Fallback response string
        """
        fallback_responses = {
            "en": "I'm here to help with your farming needs! You can ask me about crop diseases, weather, or farming advice.",
            "hi": "मैं आपकी खेती की जरूरतों में मदद के लिए यहाँ हूँ! आप मुझसे फसल की बीमारियों, मौसम या खेती की सलाह के बारे में पूछ सकते हैं।",
            "ta": "உங்கள் விவசாய தேவைகளுக்கு உதவ நான் இங்கே இருக்கிறேன்! பயிர் நோய்கள், வானிலை அல்லது விவசாய ஆலோசனை பற்றி என்னிடம் கேட்கலாம்।",
            "te": "మీ వ్యవసాయ అవసరాలకు సహాయం చేయడానికి నేను ఇక్కడ ఉన్నాను! పంట వ్యాధులు, వాతావరణం లేదా వ్యవసాయ సలహా గురించి నన్ను అడగవచ్చు।",
            "kn": "ನಿಮ್ಮ ಕೃಷಿ ಅವಶ್ಯಕತೆಗಳಿಗೆ ಸಹಾಯ ಮಾಡಲು ನಾನು ಇಲ್ಲಿದ್ದೇನೆ! ಬೆಳೆ ರೋಗಗಳು, ಹವಾಮಾನ ಅಥವಾ ಕೃಷಿ ಸಲಹೆ ಬಗ್ಗೆ ನೀವು ನನ್ನನ್ನು ಕೇಳಬಹುದು।",
            "ml": "നിങ്ങളുടെ കൃഷി ആവശ്യങ്ങൾക്ക് സഹായിക്കാൻ ഞാൻ ഇവിടെയുണ്ട്! വിള രോഗങ്ങൾ, കാലാവസ്ഥ അല്ലെങ്കിൽ കൃഷി ഉപദേശം എന്നിവയെക്കുറിച്ച് നിങ്ങൾക്ക് എന്നോട് ചോദിക്കാം."
        }
        
        return fallback_responses.get(language, fallback_responses["en"])

    def process_message(self, user_message: str, language: str = "en") -> Dict[str, Any]:
        """
        Process user message and generate appropriate response
        
        Args:
            user_message: User's input message
            language: User's preferred language code
            
        Returns:
            Dict with response, intent, and metadata
        """
        try:
            # Detect intent from user message
            intent_info = self.detect_intent(user_message)
            
            # Generate appropriate response
            response = self.generate_response(
                intent_info["intent"], 
                user_message, 
                language
            )
            
            return {
                "response": response,
                "intent": intent_info["intent"],
                "confidence": intent_info["confidence"],
                "language": language,
                "message_processed": True
            }
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return {
                "response": self._get_fallback_response(language),
                "intent": "error",
                "confidence": 0.0,
                "language": language,
                "message_processed": False,
                "error": str(e)
            }