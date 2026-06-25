"""
AI Model Service
Handles AI model inference for disease detection with real TensorFlow model
"""
import numpy as np
try:
    import tensorflow as tf
except ImportError:
    tf = None
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from app.core.config import settings
from app.utils.image_processing import ImageProcessor
import logging

logger = logging.getLogger(__name__)


class AIModelService:
    """
    AI Model service for crop disease detection using TensorFlow
    """
    
    # Disease labels from the model
    DISEASE_LABELS = None
    
    # Mock disease database (fallback)
    DISEASE_DATABASE = {
        "apple": {
            "Apple___Apple_scab": {
                "name": "Apple Scab",
                "disease_id": "Apple___Apple_scab",
                "confidence_range": (0.72, 0.94)
            },
            "Apple___Black_rot": {
                "name": "Black Rot",
                "disease_id": "Apple___Black_rot",
                "confidence_range": (0.70, 0.92)
            },
            "Apple___Cedar_apple_rust": {
                "name": "Cedar Apple Rust",
                "disease_id": "Apple___Cedar_apple_rust",
                "confidence_range": (0.68, 0.90)
            },
            "Apple___healthy": {
                "name": "Healthy",
                "disease_id": "Apple___healthy",
                "confidence_range": (0.80, 0.98)
            }
        },
        "corn": {
            "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
                "name": "Gray Leaf Spot",
                "disease_id": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
                "confidence_range": (0.70, 0.92)
            },
            "Corn_(maize)___Common_rust_": {
                "name": "Common Rust",
                "disease_id": "Corn_(maize)___Common_rust_",
                "confidence_range": (0.68, 0.90)
            },
            "Corn_(maize)___Northern_Leaf_Blight": {
                "name": "Northern Leaf Blight",
                "disease_id": "Corn_(maize)___Northern_Leaf_Blight",
                "confidence_range": (0.69, 0.91)
            },
            "Corn_(maize)___healthy": {
                "name": "Healthy",
                "disease_id": "Corn_(maize)___healthy",
                "confidence_range": (0.80, 0.98)
            }
        },
        "pepper": {
            "Pepper,_bell___Bacterial_spot": {
                "name": "Bacterial Spot",
                "disease_id": "Pepper,_bell___Bacterial_spot",
                "confidence_range": (0.70, 0.90)
            },
            "Pepper,_bell___healthy": {
                "name": "Healthy",
                "disease_id": "Pepper,_bell___healthy",
                "confidence_range": (0.80, 0.98)
            }
        },
        "potato": {
            "Potato___Early_blight": {
                "name": "Early Blight (Potato)",
                "disease_id": "Potato___Early_blight",
                "confidence_range": (0.72, 0.93)
            },
            "Potato___Late_blight": {
                "name": "Late Blight (Potato)",
                "disease_id": "Potato___Late_blight",
                "confidence_range": (0.70, 0.92)
            },
            "Potato___healthy": {
                "name": "Healthy",
                "disease_id": "Potato___healthy",
                "confidence_range": (0.80, 0.98)
            }
        },
        "strawberry": {
            "Strawberry___Leaf_scorch": {
                "name": "Leaf Scorch",
                "disease_id": "Strawberry___Leaf_scorch",
                "confidence_range": (0.70, 0.90)
            },
            "Strawberry___healthy": {
                "name": "Healthy",
                "disease_id": "Strawberry___healthy",
                "confidence_range": (0.80, 0.98)
            }
        },
        "tomato": {
            "Tomato___Early_blight": {
                "name": "Early Blight",
                "disease_id": "Tomato___Early_blight",
                "confidence_range": (0.75, 0.95)
            },
            "Tomato___Late_blight": {
                "name": "Late Blight",
                "disease_id": "Tomato___Late_blight",
                "confidence_range": (0.70, 0.92)
            },
            "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
                "name": "Yellow Leaf Curl Virus",
                "disease_id": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
                "confidence_range": (0.68, 0.90)
            },
            "Tomato___healthy": {
                "name": "Healthy",
                "disease_id": "Tomato___healthy",
                "confidence_range": (0.80, 0.98)
            }
        }
    }
    
    def __init__(self):
        """Initialize AI model service"""
        self.model = None
        self.label_map = {}
        self.model_loaded = False
        # Don't load on init to allow server to start faster
        # Model will be loaded on first prediction request
        # self.load_models()
    
    def load_models(self):
        """Load TensorFlow Keras model and label map"""
        if tf is None:
            logger.warning("TensorFlow is not installed. AI model cannot be loaded. Using mock predictions.")
            self.model_loaded = False
            self._generate_fallback_labels()
            return
        try:
            model_path = Path(settings.MODEL_PATH) / "crop_disease_master_model.keras"
            label_map_path = Path(settings.MODEL_PATH) / "new_label_map.txt"
            
            if model_path.exists():
                logger.info(f"Loading AI model from {model_path}")
                
                # Try loading with safe_mode=False to handle Keras version mismatches
                # (e.g. quantization_config added in newer Keras versions)
                try:
                    self.model = tf.keras.models.load_model(
                        str(model_path), compile=False, safe_mode=False
                    )
                except TypeError:
                    # Older TF versions don't have safe_mode parameter
                    self.model = tf.keras.models.load_model(
                        str(model_path), compile=False
                    )
                except Exception as e1:
                    logger.warning(f"Standard load failed: {e1}, trying H5 format...")
                    # Try loading as H5 format as fallback
                    h5_path = model_path.with_suffix('.h5')
                    if h5_path.exists():
                        self.model = tf.keras.models.load_model(
                            str(h5_path), compile=False
                        )
                    else:
                        raise e1
                
                logger.info(f"AI model loaded successfully. "
                           f"Input: {self.model.input_shape}, "
                           f"Output: {self.model.output_shape}, "
                           f"Layers: {len(self.model.layers)}")
                self.model_loaded = True
                
                # Build the computational graph so that .input / .output
                # are available (required by Keras 3 Sequential models
                # for Grad-CAM).
                try:
                    dummy = np.zeros((1, 224, 224, 3), dtype=np.float32)
                    self.model.predict(dummy, verbose=0)
                    logger.info("Model graph built successfully")
                except Exception as build_err:
                    logger.warning(f"Model graph build warning: {build_err}")
                
                # Log model layer structure for debugging Grad-CAM
                for i, layer in enumerate(self.model.layers):
                    logger.debug(f"  Layer [{i}]: {layer.name} ({type(layer).__name__})")
                
                # Load label map
                if label_map_path.exists():
                    self._load_label_map(label_map_path)
                else:
                    logger.warning(f"Label map not found at {label_map_path}, using fallback")
                    self._generate_fallback_labels()
            else:
                logger.warning(f"Model file not found at {model_path}, using mock predictions")
                self.model_loaded = False
                
        except Exception as e:
            import traceback
            logger.error(f"Error loading AI model: {e}\n{traceback.format_exc()}")
            self.model_loaded = False
    
    def _load_label_map(self, label_map_path: Path):
        """Load label map from file"""
        try:
            with open(label_map_path, "r", encoding="utf-8") as f:
                raw_lines = [line.strip() for line in f if line.strip()]

            parsed_map: Dict[int, str] = {}
            parsed_list: List[str] = []

            for line in raw_lines:
                if ":" in line:
                    idx_str, label = line.split(":", 1)
                    if idx_str.strip().isdigit():
                        parsed_map[int(idx_str.strip())] = label.strip()
                        continue
                parsed_list.append(line)

            if parsed_map:
                self.label_map = parsed_map
                self.DISEASE_LABELS = [
                    label for _, label in sorted(parsed_map.items())
                ]
            else:
                self.label_map = {idx: label for idx, label in enumerate(parsed_list)}
                self.DISEASE_LABELS = parsed_list

            logger.info(
                "Loaded %s disease labels from label map",
                len(self.DISEASE_LABELS)
            )
            
        except Exception as e:
            logger.error(f"Error loading label map: {e}")
            self._generate_fallback_labels()
    
    def _generate_fallback_labels(self):
        """Generate fallback labels if label map is missing"""
        fallback_labels = [
            "Apple___Apple_scab",
            "Apple___Black_rot",
            "Apple___Cedar_apple_rust",
            "Apple___healthy",
            "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
            "Corn_(maize)___Common_rust_",
            "Corn_(maize)___Northern_Leaf_Blight",
            "Corn_(maize)___healthy",
            "Pepper,_bell___Bacterial_spot",
            "Pepper,_bell___healthy",
            "Potato___Early_blight",
            "Potato___Late_blight",
            "Potato___healthy",
            "Strawberry___Leaf_scorch",
            "Strawberry___healthy",
            "Tomato___Early_blight",
            "Tomato___Late_blight",
            "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
            "Tomato___healthy"
        ]
        self.label_map = {idx: label for idx, label in enumerate(fallback_labels)}
        self.DISEASE_LABELS = fallback_labels
        logger.info(f"Using {len(fallback_labels)} fallback disease labels")
    
    async def predict_disease(
        self,
        image: np.ndarray,
        crop_type: str
    ) -> Dict[str, Any]:
        """
        Predict disease from image using real TensorFlow model
        
        Args:
            image: Input image as numpy array (BGR format from OpenCV)
            crop_type: Type of crop
        
        Returns:
            Prediction results
        """
        try:
            # Load model on first use
            if not self.model_loaded:
                self.load_models()

            # Preprocess image for model
            processed_image = self._preprocess_for_prediction(image)
            
            # Predict using model
            if self.model_loaded and self.model is not None:
                predictions = self._predict_with_model(processed_image)
            else:
                # Fallback to mock predictions
                predictions = await self._mock_predict(crop_type)
            
            # Get top prediction
            disease_id = predictions['primary_disease']
            confidence = predictions['confidence']
            entropy = predictions.get('entropy', 0.0)
            margin = predictions.get('margin', 1.0)
            
            # US13: Multi-signal uncertainty detection
            # Flag as uncertain if ANY of these are true:
            #   1. Confidence below threshold (default 0.85)
            #   2. High entropy (model output is spread across classes — OOD input)
            #   3. Small margin between top-2 predictions (model can't distinguish)
            low_confidence = not self.check_confidence_threshold(confidence)
            high_entropy = entropy > 2.0
            low_margin = margin < 0.10
            is_uncertain = low_confidence or high_entropy or low_margin
            
            if is_uncertain:
                disease_name = "Unknown/Unclear"
                reasons = []
                if low_confidence:
                    reasons.append(f"confidence {confidence:.4f} < {settings.CONFIDENCE_THRESHOLD}")
                if high_entropy:
                    reasons.append(f"entropy {entropy:.4f} > 2.0")
                if low_margin:
                    reasons.append(f"margin {margin:.4f} < 0.10")
                logger.warning(
                    f"Uncertain prediction ({', '.join(reasons)}). "
                    f"Original guess: {disease_id}. Returning Unknown/Unclear."
                )
            else:
                disease_name = self._format_disease_name(disease_id)
            
            # Check if multiple diseases detected
            secondary_diseases = predictions.get('secondary_diseases', [])
            
            # Determine if healthy
            is_healthy = 'healthy' in disease_id.lower()
            
            # Generate Grad-CAM heatmap and severity estimation
            if not is_healthy:
                try:
                    if self.model is None:
                        raise ValueError("Model is not loaded")

                    heatmap_image, severity_info, raw_heatmap = ImageProcessor.generate_gradcam(
                        self.model,
                        image
                    )
                    severity = severity_info.get('severity', 'Unknown')
                    infected_ratio = severity_info.get('infected_ratio', 0.0)

                    # Derive bounding boxes from the Grad-CAM heatmap
                    # so they highlight the actual infected regions.
                    if raw_heatmap is not None:
                        bounding_boxes = ImageProcessor.boxes_from_heatmap(
                            raw_heatmap, image.shape,
                            threshold=0.6,
                            min_area_ratio=0.003,
                            max_area_ratio=0.35,
                        )
                        annotated_image, _ = ImageProcessor.detect_bounding_boxes(
                            image, detection_results=bounding_boxes
                        )
                    else:
                        bounding_boxes = []
                        annotated_image = image
                except Exception as e:
                    import traceback
                    logger.error(f"Grad-CAM generation failed: {e}\n{traceback.format_exc()}")
                    bounding_boxes = []
                    annotated_image = image
                    severity = "unknown"
                    heatmap_image = image
                    infected_ratio = 0.0
            else:
                # Healthy plant - no heatmap needed
                bounding_boxes = []
                severity = "healthy"
                annotated_image = image
                heatmap_image = image
                infected_ratio = 0.0

            severity = self._normalize_severity(severity)
            
            return {
                "disease_id": disease_id,
                "disease_name": disease_name,
                "confidence": float(confidence),
                "is_uncertain": is_uncertain,
                "severity": severity,
                "infected_ratio": infected_ratio,
                "is_healthy": is_healthy,
                "bounding_boxes": bounding_boxes,
                "secondary_diagnoses": secondary_diseases,
                "annotated_image": annotated_image,
                "heatmap_image": heatmap_image,
                "all_predictions": predictions.get('all_predictions', {})
            }
            
        except Exception as e:
            logger.error(f"Error in disease prediction: {e}")
            raise
    
    def _preprocess_for_prediction(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for model prediction
        Model expects MobileNetV2 preprocessing
        """
        try:
            import cv2
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Resize to model input size (224x224 for MobileNetV2)
            resized = cv2.resize(rgb_image, (224, 224))

            # Apply MobileNetV2 preprocessing
            preprocessed = tf.keras.applications.mobilenet_v2.preprocess_input(
                resized.astype(np.float32)
            )

            # Add batch dimension
            batched = np.expand_dims(preprocessed, axis=0)
            
            return batched
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
    
    def _predict_with_model(self, processed_image: np.ndarray) -> Dict[str, Any]:
        """
        Run prediction with loaded TensorFlow model.
        Uses test-time augmentation (TTA) for better accuracy.
        """
        try:
            # Simple prediction (TTA with vertical flip removed —
            # it was hurting accuracy on plant images which have a
            # natural orientation).
            predictions = self.model.predict(processed_image, verbose=0)[0]
            
            # Log all prediction scores for debugging
            logger.info(f"Prediction scores (TTA averaged): {dict(zip([self.label_map.get(i, f'Class_{i}') for i in range(len(predictions))], [f'{p:.4f}' for p in predictions]))}")
            
            # Get top prediction
            top_idx = np.argmax(predictions)
            top_confidence = float(predictions[top_idx])
            primary_disease = self.label_map.get(top_idx, f"Unknown_Class_{top_idx}")
            
            logger.info(f"Top prediction: {primary_disease} ({top_confidence:.4f})")
            
            # --- US13: Additional uncertainty signals ---
            # 1. Entropy check: high entropy means the model is confused / input is OOD
            clipped = np.clip(predictions, 1e-10, 1.0)
            entropy = -np.sum(clipped * np.log(clipped))
            
            # 2. Margin check: small gap between top-2 means model can't distinguish
            sorted_preds = np.sort(predictions)[::-1]
            margin = float(sorted_preds[0] - sorted_preds[1]) if len(sorted_preds) > 1 else 1.0
            
            logger.info(f"Entropy: {entropy:.4f}, Margin (top1-top2): {margin:.4f}")
            
            # Get top 3 predictions for secondary diseases
            top_3_indices = np.argsort(predictions)[-3:][::-1]
            
            secondary_diseases = []
            for idx in top_3_indices[1:]:  # Skip the primary (already got it)
                if predictions[idx] > 0.15:  # Only include if confidence > 15%
                    disease_id = self.label_map.get(idx, f"Unknown_Class_{idx}")
                    secondary_diseases.append({
                        "disease_id": disease_id,
                        "disease_name": self._format_disease_name(disease_id),
                        "confidence": float(predictions[idx])
                    })
            
            # All predictions as dict
            all_predictions = {
                self.label_map.get(i, f"Class_{i}"): float(predictions[i])
                for i in range(len(predictions))
            }
            
            return {
                "primary_disease": primary_disease,
                "confidence": top_confidence,
                "entropy": entropy,
                "margin": margin,
                "secondary_diseases": secondary_diseases,
                "all_predictions": all_predictions
            }
            
        except Exception as e:
            logger.error(f"Error in model prediction: {e}")
            raise

    def _compute_grad_cam(self, processed_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Compute Grad-CAM heatmap for the top prediction.
        Returns a 2D array normalized to [0, 1] or None on failure.
        """
        try:
            if self.model is None:
                return None

            last_conv = self._get_last_conv_layer_name()
            if last_conv is None:
                return None

            grad_model = tf.keras.models.Model(
                [self.model.inputs],
                [self.model.get_layer(last_conv).output, self.model.output]
            )

            with tf.GradientTape() as tape:
                conv_outputs, predictions = grad_model(processed_image)
                pred_index = tf.argmax(predictions[0])
                pred_score = predictions[:, pred_index]

            grads = tape.gradient(pred_score, conv_outputs)
            if grads is None:
                return None

            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
            conv_outputs = conv_outputs[0]
            heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)
            heatmap = tf.maximum(heatmap, 0)
            max_val = tf.reduce_max(heatmap)
            if max_val == 0:
                return None
            heatmap = heatmap / max_val

            return heatmap.numpy()
        except Exception as e:
            logger.error(f"Error generating Grad-CAM: {e}")
            return None

    def _get_last_conv_layer_name(self) -> Optional[str]:
        """Find the last Conv2D layer name in the model."""
        try:
            for layer in reversed(self.model.layers):
                if isinstance(layer, tf.keras.layers.Conv2D):
                    return layer.name
            return None
        except Exception as e:
            logger.error(f"Error locating last conv layer: {e}")
            return None
    
    def _format_disease_name(self, disease_id: str) -> str:
        """Format disease ID to human-readable name"""
        # Replace underscores with spaces and clean up
        name = disease_id.replace('___', ': ').replace('_', ' ')
        
        # Handle special cases
        name = name.replace('(maize)', '').strip()
        name = name.replace('  ', ' ')
        
        return name

    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity labels for consistent downstream use."""
        if severity is None:
            return "unknown"

        normalized = str(severity).strip().lower()
        if normalized in {"low", "medium", "high", "healthy", "unknown"}:
            return normalized

        if normalized in {"moderate", "mid"}:
            return "medium"

        return "unknown"
    
    async def _mock_predict(self, crop_type: str) -> Dict[str, Any]:
        """
        Mock prediction for demonstration
        Replace with actual model inference in production
        """
        import random
        
        crop_diseases = self.DISEASE_DATABASE.get(crop_type, self.DISEASE_DATABASE['tomato'])
        
        # Randomly select a disease
        disease_key = random.choice(list(crop_diseases.keys()))
        disease_info = crop_diseases[disease_key]
        
        # Generate confidence score
        min_conf, max_conf = disease_info['confidence_range']
        confidence = random.uniform(min_conf, max_conf)
        
        # Generate secondary diseases if confidence is high enough
        secondary_diseases = []
        if confidence > 0.70 and not disease_info['disease_id'].endswith('healthy'):
            other_diseases = [d for d in crop_diseases.keys() if d != disease_key]
            if other_diseases and random.random() > 0.7:
                secondary_key = random.choice(other_diseases)
                secondary_diseases.append({
                    "disease_id": crop_diseases[secondary_key]['disease_id'],
                    "disease_name": crop_diseases[secondary_key]['name'],
                    "confidence": random.uniform(0.40, 0.65)
                })
        
        # All predictions
        all_predictions = {
            disease_info['disease_id']: confidence
        }
        
        return {
            "primary_disease": disease_info['disease_id'],
            "confidence": confidence,
            "secondary_diseases": secondary_diseases,
            "all_predictions": all_predictions
        }
    
    def _get_disease_name(self, crop_type: str, disease_id: str) -> str:
        """Get disease name from ID"""
        crop_diseases = self.DISEASE_DATABASE.get(crop_type, {})
        
        for disease_key, disease_info in crop_diseases.items():
            if disease_info['disease_id'] == disease_id:
                return disease_info['name']
        
        return disease_id
    
    async def predict_from_video_frames(
        self,
        frames: List[np.ndarray],
        crop_type: str
    ) -> Dict[str, Any]:
        """
        Predict disease from multiple video frames using majority voting
        
        Args:
            frames: List of frames from video
            crop_type: Type of crop
        
        Returns:
            Aggregated prediction results
        """
        try:
            predictions = []
            
            # Predict for each frame
            for frame in frames:
                result = await self.predict_disease(frame, crop_type)
                predictions.append(result)
            
            # Majority voting
            disease_counts = {}
            for pred in predictions:
                disease_id = pred['disease_id']
                disease_counts[disease_id] = disease_counts.get(disease_id, 0) + 1
            
            # Get most common disease
            majority_disease = max(disease_counts, key=disease_counts.get)
            
            # Find prediction with highest confidence for that disease
            best_prediction = max(
                [p for p in predictions if p['disease_id'] == majority_disease],
                key=lambda x: x['confidence']
            )
            
            return best_prediction
            
        except Exception as e:
            logger.error(f"Error in video frame prediction: {e}")
            raise
    
    def check_confidence_threshold(self, confidence: float) -> bool:
        """Check if confidence meets threshold"""
        return confidence >= settings.CONFIDENCE_THRESHOLD


# Global service instance
ai_service = AIModelService()
