import numpy as np              # Provides efficient numerical operations and array handling
import tensorflow as tf         # Used for building and running machine learning models
import cv2                      # OpenCV library for image processing and computer vision tasks
import os
import tensorflow as tf
from gtts import gTTS
from IPython.display import Audio, display
from transformers import pipeline
import whisper
from deep_translator import GoogleTranslator
from langdetect import detect 
from gtts.lang import tts_langs
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LABEL_MAP_PATH = BASE_DIR / "data" / "new_label_map.txt"
# EPIC-4: USER STORY 5
FARMER_ADVICE = {
    "advice": {
        # Apple
        "Apple___Apple_scab": "Your apple leaves have spots. Spray neem oil and remove fallen leaves to stop the spread.",
        "Apple___Black_rot": "Black rot detected. Prune the dead wood and remove any 'mummified' fruit from the tree.",
        "Apple___Cedar_apple_rust": "Orange rusty spots found. Avoid planting cedar trees nearby and use a sulfur spray.",
        "Apple___healthy": "Your apple tree looks strong and healthy! Keep up the good work.",
        
        # Corn
        "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": "Gray spots found on corn. Rotate your crops next season and use a fungicide if it spreads.",
        "Corn_(maize)___Common_rust_": "Common rust found. These orange spots like moisture; avoid watering the leaves directly.",
        "Corn_(maize)___Northern_Leaf_Blight": "Long gray stripes seen on leaves. Pick resistant seeds next time and manage irrigation.",
        "Corn_(maize)___healthy": "Your corn is growing beautifully and looks very healthy!",
        
        # Pepper
        "Pepper,_bell___Bacterial_spot": "Bacterial spots on peppers. Avoid working in the field when plants are wet to prevent spreading.",
        "Pepper,_bell___healthy": "Your bell peppers are healthy and looking great!",
        
        # Potato
        "Potato___Early_blight": "Early blight found. Improve air circulation and keep the potato leaves dry.",
        "Potato___Late_blight": "Warning: Late blight can spread fast. Remove infected plants immediately and destroy them.",
        "Potato___healthy": "Your potato crop is healthy and free of blight!",
        
        # Strawberry
        "Strawberry___Leaf_scorch": "Strawberry leaves look 'scorched.' Water the base of the plant and remove old, dry leaves.",
        "Strawberry___healthy": "Your strawberry plants are in excellent health.",
        
        # Tomato
        "Tomato___Early_blight": "Tomato blight detected. Remove lower leaves to prevent soil fungus from jumping onto the plant.",
        "Tomato___Late_blight": "Late blight is serious for tomatoes. Use a copper-based spray and avoid damp conditions.",
        "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "Virus detected. This is spread by small whiteflies. Use yellow sticky traps to catch them.",
        "Tomato___healthy": "Your tomato plant is perfectly healthy!",
        
        # Fallback
        "default": "I see a problem with the leaf. Please take a clearer photo or show it to a local expert."
    },

    # EPIC-4: USER STORY 11
    "errors": {
        "blurry": "The photo is a bit shaky and blurry. Please hold the phone steady and try again.",
        "unclear": "I cannot see the leaf clearly. Please take a photo in brighter light or a different angle."
    }
}

# EPIC-4: USER STORY 11
def is_blurry(img_path, threshold: float = 100.0):
    img_path = str(img_path)
    img = cv2.imread(img_path)

    if img is None:
        # Image not found or not readable
        raise FileNotFoundError(
            f"OpenCV could not read the image at: {img_path}\n"
            f"Tip: use an absolute path or check the notebook working directory."
        )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold

def generate_gradcam(model, img_path, layer_name=None):
    """Generate a Grad-CAM heatmap overlay for the predicted class.

    Fixes Keras graph issues by building the Grad-CAM model using the
    MobileNetV2 base model's input graph (not Sequential's symbolic tensors).
    """
    base_model = model.layers[0]  # MobileNetV2 (Functional)

    # Pick a sensible conv layer if not provided
    if layer_name is None:
        for layer in reversed(base_model.layers):
            if isinstance(layer, tf.keras.layers.Conv2D):
                layer_name = layer.name
                break
        if layer_name is None:
            # Fallback: any layer with 'conv' in its name
            for layer in reversed(base_model.layers):
                if "conv" in layer.name.lower():
                    layer_name = layer.name
                    break

    if layer_name is None:
        raise ValueError("No convolutional layer found in base model.")

    conv_layer = base_model.get_layer(layer_name)

    # Build a Grad-CAM graph rooted at base_model.input to avoid tensor mismatch
    x = base_model.output
    for head_layer in model.layers[1:]:
        x = head_layer(x)
    preds = x

    grad_model = tf.keras.models.Model(
        inputs=base_model.input,
        outputs=[conv_layer.output, preds],
    )

    # Load and preprocess image
    img = tf.keras.preprocessing.image.load_img(img_path, target_size=(224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0).astype(np.float32)

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        pred_index = tf.argmax(predictions[0])
        loss = predictions[:, pred_index]

    grads = tape.gradient(loss, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    conv_outputs = conv_outputs[0]
    heatmap = tf.reduce_sum(pooled_grads * conv_outputs, axis=-1)

    # Convert to numpy once, then use numpy/cv2 safely
    heatmap = heatmap.numpy()
    heatmap = np.maximum(heatmap, 0)
    heatmap /= (np.max(heatmap) + 1e-8)

    heatmap = cv2.resize(heatmap, (224, 224))
    heatmap = np.uint8(255 * heatmap)

    original = cv2.imread(img_path)
    if original is None:
        raise FileNotFoundError(f"Could not read image from path: {img_path}")
    original = cv2.resize(original, (224, 224))

    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(original, 0.6, heatmap, 0.4, 0)

    output_path = "heatmap_output.jpg"
    cv2.imwrite(output_path, overlay)
    return output_path

# EPIC-3: USER STORY 8

def estimate_severity_from_heatmap(heatmap_path):
    heatmap = cv2.imread(heatmap_path)
    heatmap_gray = cv2.cvtColor(heatmap, cv2.COLOR_BGR2GRAY)

    # Threshold to isolate "hot" infected zones
    _, binary_map = cv2.threshold(heatmap_gray, 200, 255, cv2.THRESH_BINARY)

    infected_area = np.sum(binary_map == 255)
    total_area = binary_map.shape[0] * binary_map.shape[1]

    ratio = infected_area / total_area

    if ratio < 0.10:
        severity = "Low"
    elif ratio < 0.40:
        severity = "Medium"
    else:
        severity = "High"

    return {
        "severity": severity,
        "infected_ratio": round(ratio * 100, 2)
    }


import requests

def get_real_weather(location="Ettimadai, Tamil Nadu"):
    
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    if not API_KEY:
        return "Weather service is not configured."
    
    # Constructing the API URL
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={location}&appid={API_KEY}&units=metric"
    )
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status() # error for bad status codes
        data = response.json()
        
        # Extracting weather details
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        humidity = data['main']['humidity']
        
        # Creating a farmer-friendly actionable message
        if "rain" in desc.lower():
            advice = "Rain is expected. Avoid spraying pesticides."
        elif temp > 35:
            advice = "High temperature. Water crops well."
        else:
            advice = "Weather is stable. Good time for field work."

        return f"In {location}, it is {temp}°C with {desc}. {advice}"

    except requests.exceptions.RequestException:
        return "Unable to fetch weather right now."
    

class IntegratedFarmerAgent:
    def __init__(self, crop_model_path, whisper_size="base"):
        print("Initializing AI Engines...")
        p = Path(crop_model_path)
        if not p.is_absolute():
            p = (Path(__file__).resolve().parent / p).resolve()

        if not p.exists():
            raise FileNotFoundError(f".keras model not found at: {p}")
        
        self.crop_model = tf.keras.models.load_model(crop_model_path)
        self.speech_model = whisper.load_model(whisper_size)
        # Intent Classifier (Zero-Shot)
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        self.current_lang = "en" 
        self.skills = ["crop disease diagnosis", "weather inquiry", "general greeting"]

        self._tts_counter = 0

    def predict_disease(self, img_path, confidence_threshold=0.45):
        if is_blurry(img_path):
            return {
                "status": "error",
                "message": "Image is too blurry. Please retake photo.",
                "confidence": 0.0
            }
        
        img = tf.keras.preprocessing.image.load_img(img_path, target_size=(224, 224))
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
        img_array = np.expand_dims(img_array, axis=0)

        preds = self.crop_model.predict(img_array, verbose=0)[0]
        top_idx = int(np.argmax(preds))
        confidence = float(preds[top_idx])

        # Resolve label map robustly:
        # - uses `new_label_map` if it exists
        # - else uses existing notebook variable `label_map`
        # - else loads from LABEL_MAP_PATH/new_label_map.txt
        _map = globals().get("new_label_map") or globals().get("label_map")

        if _map is None:
            # ✅ always resolve label map relative to this script
            _map_path = Path(globals().get("LABEL_MAP_PATH", LABEL_MAP_PATH))
            if not _map_path.is_absolute():
                _map_path = (BASE_DIR / _map_path).resolve()

            if not _map_path.exists():
                raise FileNotFoundError(f"Label map file not found: {_map_path}")
            _map = {}
            with open(_map_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or ":" not in line:
                        continue
                    k, v = line.split(":", 1)
                    _map[int(k)] = v
            globals()["label_map"] = _map  # cache for future calls

        if isinstance(_map, dict):
            disease_name = _map.get(top_idx, f"Unknown_{top_idx}")
        else:
            # supports list/tuple style maps too
            disease_name = _map[top_idx]

        # Epic 3: Unknown/Unclear Result Story
        if confidence < confidence_threshold:
            return {
                "status": "unknown",
                "disease": "Unknown/Unclear",
                "message": "Please consult a human expert or retake the photo.",
                "confidence": round(confidence * 100, 2)   # EPIC-3: USER STORY 7
            }
        
            # Epic 3: USER STORY 9
        # Check if the predicted label contains the word "healthy"
        is_healthy = "healthy" in disease_name.lower()

        return {
            "status": "success",
            "disease": disease_name,
            "is_healthy": is_healthy,
            "confidence": round(confidence * 100, 2)
        }

    def _translator_lang_name(self, lang_code: str) -> str:
        """Map lang code -> deep_translator language name."""
        code = (lang_code or "en").lower()
        return {
            "en": "english",
            "hi": "hindi",
            "te": "telugu",}.get(code, "english")
    def _tts_lang_code(self, lang_code: str) -> str:
        """Ensure gTTS gets a supported lang code; fallback to English."""
        code = (lang_code or "en").lower()
        return code if code in tts_langs() else "en"

    # EPIC-4: USER STORY 1
    def auto_detect_language(self, audio_path):
        """User Story 1 & 3: Detects language and transcribes voice."""
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(self.speech_model.device)

        # 1. Detecting language
        _, probs = self.speech_model.detect_language(mel)
        detected_lang = max(probs, key=probs.get)
        
        # 2. Decode with the detected language
        options = whisper.DecodingOptions(fp16=False, language=detected_lang)
        result = whisper.decode(self.speech_model, mel, options)
        
        self.current_lang = detected_lang
        return self.current_lang, result.text

    def get_localized_advice(self, diagnosis_report):
        """User Story 5 & 11: Dynamic translation of diagnosis/errors."""
        disease_code = diagnosis_report["disease"]
        if diagnosis_report.get("status") == "error" or diagnosis_report["status"] == "unknown":
            # Map technical error status to simple farmer-friendly error words
            error_key = "blurry" if "blurry" in diagnosis_report["message"].lower() else "unclear"
            msg = FARMER_ADVICE.get("errors", {}).get(error_key, diagnosis_report["message"])
        elif diagnosis_report["is_healthy"]:
            msg = FARMER_ADVICE.get("advice", {}).get("healthy", "Your plant looks healthy.")
        else:
            default_msg = FARMER_ADVICE.get("default") or FARMER_ADVICE.get("advice", {}).get(
                "default",
                "I found a possible plant issue. Please take a clearer photo or consult an expert.",
            )
            parts = diagnosis_report["disease"].split("___")
            disease_only = parts[1].replace("_", " ") if len(parts) > 1 else parts[0].replace("_", " ")
            msg = FARMER_ADVICE.get("advice", {}).get(disease_code, default_msg)

        try:
            return GoogleTranslator(source='auto', target=self.current_lang).translate(msg)
        except:
            return msg

    def speak(self, text):
        """User Story 4: The missing 'Speak' method."""
        text = "" if text is None else str(text)
        lang = self._tts_lang_code(self.current_lang)

        self._tts_counter += 1
        out_path = Path(__file__).resolve().parent / f"response_{self._tts_counter:03d}.mp3"

        print(f"AI Output ({self.current_lang}): {text}")
        gTTS(text=text, lang=lang).save(str(out_path))

        # ✅ terminal: open in default player
        os.startfile(str(out_path))
        print("Opened audio:", str(out_path))

    # EPIC-4: USER STORY 3
    def process_full_request(self, image_path, audio_path):
        """The Responsive Master Pipeline."""
        # 1. Language & Transcription
        lang, user_text = self.auto_detect_language(audio_path)
        print(f"User said: {user_text}")
        skill_descriptions = {
            "crop disease diagnosis": "Checking a plant leaf for sickness or disease",
            "weather inquiry": "Asking about the weather, rain, or temperature",
            "general greeting": "Saying hello, hi, or asking who the assistant is"
        }
        # 2. Semantic Intent
        intent_result = self.classifier(user_text, candidate_labels=list(skill_descriptions.values()))
        best_description = intent_result['labels'][0]
        best_intent = [k for k, v in skill_descriptions.items() if v == best_description][0]
        print(f"Detected Intent: {best_intent}")

        if any(word in user_text.lower() for word in ["leaf", "disease", "plant", "बीमारी", "पत्ता"]):
            best_intent = "crop disease diagnosis"

        print(f"Refined Intent: {best_intent}")

        # 3. Decision Logic
        if best_intent == "weather inquiry":
            # Getting weather of the Ettimadai
            response_en = get_real_weather("Ettimadai, Tamil Nadu")
        elif best_intent == "crop disease diagnosis":
            report = self.predict_disease(image_path) 
            if report["status"] == "success":
                heatmap_path = generate_gradcam(self.crop_model, image_path)
                severity_info = estimate_severity_from_heatmap(heatmap_path)
                print(f"📸 Visual evidence saved to: {severity_info}")
            response_en = self.get_localized_advice(report)
        else:
            response_en = "Hello! I am your AI farming assistant. How can I help you today?"

        # 4. Final Translation & Speech
        if lang == 'en':
            final_msg = response_en
        else:
            final_msg = GoogleTranslator(source='auto', target=lang).translate(response_en)
            
        self.speak(final_msg)
        return final_msg
    
    # EPIC-4: USER STORY 2
    def process_text_input(self, typed_text,image_path = None):
        """
        User Story 2: Handles native language text input.
        1. Correctly detects the language code (e.g., 'hi')
        2. Understands intent
        3. Returns localized response
        """
        # A. Detect the actual language code
        try:
            # langdetect returns ISO codes like 'hi', 'te', 'en'
            detected_iso_code = detect(typed_text) 
        except:
            detected_iso_code = "en" 
            
        self.current_lang = detected_iso_code
        
        # B. Translate to English for the AI Brain
        translator = GoogleTranslator(source='auto', target='en')
        english_query = translator.translate(typed_text)
        
        print(f"Typed Text: {typed_text}")
        print(f"Detected Language Code: {self.current_lang}")
        print(f"Translated for AI: {english_query}")

        # C. Semantic Intent Analysis
        intent_result = self.classifier(english_query, candidate_labels=self.skills)
        best_intent = intent_result['labels'][0]
        print(f"Detected Intent: {best_intent}")

        # D. Decision Logic
        if best_intent == "weather inquiry":
            response_en = "The weather in Ettimadai is clear today. Great for your crops!"
        elif best_intent == "crop disease diagnosis":
            # Check if an image path was provided to the function
            if image_path: 
                report = self.predict_disease(image_path)
                if report["status"] == "success":
                    heatmap_path = generate_gradcam(self.crop_model, image_path)
                    severity_info = estimate_severity_from_heatmap(heatmap_path)
                    print(f"📸 Visual evidence saved to: {severity_info}")
                response_en = self.get_localized_advice(report)
            else:
                response_en = "I see you want a diagnosis. Please upload a photo of the leaf."
        else:
            response_en = "Hello! I am your AI assistant. I can help with disease diagnosis or weather."

        # E. Translate back to user's language
        # We use the ISO code (hi, te, etc.) which GoogleTranslator understands
        final_msg = GoogleTranslator(source='auto', target=self.current_lang).translate(response_en)
        self.speak(final_msg)
        return final_msg
    
# --- EXECUTION ---
MODEL_PATH = BASE_DIR / "model" / "crop_disease_master_model.keras"
SAMPLES_DIR = BASE_DIR / "test_samples"

agent = IntegratedFarmerAgent(MODEL_PATH)

agent.process_full_request(
    SAMPLES_DIR / "0a8a68ee-f587-4dea-beec-79d02e7d3fa4___RS_Early.B 8461.JPG",
    SAMPLES_DIR / "farmer_request.mp3",
)

test_text = "आप कैसे हैं और आप क्या कर सकते हैं?"
agent.process_text_input(test_text)