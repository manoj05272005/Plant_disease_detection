"""
Image Processing Utilities
Handles blur detection, heatmap generation, and image quality checks
"""
import cv2
import numpy as np
try:
    import tensorflow as tf
except ImportError:
    tf = None
from typing import Tuple, Dict, Any, List, Optional
from app.core.config import settings
import base64
import logging
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Image processing utilities for crop disease detection"""
    
    @staticmethod
    def decode_base64_image(base64_string: str) -> np.ndarray:
        """Decode base64 image string to numpy array"""
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            img_bytes = base64.b64decode(base64_string)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            return img
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            raise ValueError("Invalid image data")
    
    @staticmethod
    def encode_image_to_base64(image: np.ndarray, format: str = '.jpg') -> str:
        """Encode numpy array image to base64 string"""
        try:
            _, buffer = cv2.imencode(format, image)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{img_base64}"
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            raise
    
    @staticmethod
    def check_blur(image: np.ndarray, threshold: int = None) -> Dict[str, Any]:
        """
        Check if image is blurry using Laplacian variance method
        
        Args:
            image: Input image as numpy array
            threshold: Blur detection threshold (default from settings)
        
        Returns:
            Dictionary with blur check results
        """
        if threshold is None:
            threshold = settings.BLUR_THRESHOLD
        
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()
            
            is_acceptable = bool(variance >= threshold)
            
            return {
                "is_acceptable": is_acceptable,
                "blur_score": float(variance),
                "blur_threshold": threshold,
                "message": "Image quality is good" if is_acceptable else "Image is too blurry. Please retake with a stable camera."
            }
        except Exception as e:
            logger.error(f"Error in blur detection: {e}")
            raise
    
    @staticmethod
    def generate_gradcam(
        model,
        image: np.ndarray,
        layer_name: Optional[str] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Generate Grad-CAM++ heatmap overlay for the predicted class.

        Uses Grad-CAM++ (weighted combination of positive partial
        derivatives) for better multi-spot localization, and per-pixel
        alpha blending so only significantly activated regions are
        coloured — the rest of the image stays untouched.

        Args:
            model: TensorFlow/Keras model
            image: Original image as numpy array (BGR format)
            layer_name: Name of convolutional layer to use (auto-detected if None)

        Returns:
            Tuple of (heatmap_overlay, severity_info, raw_heatmap_normalized)
            raw_heatmap_normalized is a 2D float array in [0, 1] at the
            original image resolution, or None on error.
        """
        if tf is None:
            logger.warning("TensorFlow is not installed. Skipping Grad-CAM heatmap generation.")
            return image, {"severity": "Unknown", "infected_ratio": 0.0}, None
        try:
            # -----------------------------------------------------------
            # 1. Find the target convolutional layer (model-agnostic)
            # -----------------------------------------------------------
            target_layer = None

            if layer_name is not None:
                try:
                    target_layer = model.get_layer(layer_name)
                except ValueError:
                    for layer in model.layers:
                        if isinstance(layer, tf.keras.Model):
                            try:
                                target_layer = layer.get_layer(layer_name)
                                break
                            except ValueError:
                                continue

            if target_layer is None:
                # Auto-detect: last Conv2D in the model graph
                for layer in reversed(model.layers):
                    if isinstance(layer, tf.keras.layers.Conv2D):
                        target_layer = layer
                        break

                if target_layer is None:
                    for layer in reversed(model.layers):
                        if isinstance(layer, tf.keras.Model):
                            for sub_layer in reversed(layer.layers):
                                if isinstance(sub_layer, tf.keras.layers.Conv2D):
                                    target_layer = sub_layer
                                    break
                            if target_layer is not None:
                                break

                if target_layer is None:
                    for layer in reversed(model.layers):
                        if 'conv' in layer.name.lower():
                            target_layer = layer
                            break
                        if isinstance(layer, tf.keras.Model):
                            for sub_layer in reversed(layer.layers):
                                if 'conv' in sub_layer.name.lower():
                                    target_layer = sub_layer
                                    break
                            if target_layer is not None:
                                break

            if target_layer is None:
                raise ValueError("No convolutional layer found anywhere in the model.")

            logger.info(f"Grad-CAM++ target layer: {target_layer.name} ({type(target_layer).__name__})")

            # -----------------------------------------------------------
            # 2. Build the Grad-CAM model
            # -----------------------------------------------------------
            try:
                model_input = model.input
                model_output = model.output
                grad_model = tf.keras.models.Model(
                    inputs=model_input,
                    outputs=[target_layer.output, model_output],
                )
            except (AttributeError, ValueError) as seq_err:
                logger.info(
                    "model.input unavailable (%s); "
                    "rebuilding graph from base sub-model for Grad-CAM++",
                    seq_err,
                )
                base_model = None
                for layer in model.layers:
                    if isinstance(layer, tf.keras.Model):
                        base_model = layer
                        break
                if base_model is None:
                    raise ValueError(
                        "Cannot build Grad-CAM++: no Functional sub-model "
                        "found in Sequential model."
                    )
                x = base_model.output
                for head_layer in model.layers[model.layers.index(base_model) + 1:]:
                    x = head_layer(x)
                grad_model = tf.keras.models.Model(
                    inputs=base_model.input,
                    outputs=[target_layer.output, x],
                )

            # -----------------------------------------------------------
            # 3. Preprocess the input image
            # -----------------------------------------------------------
            img_resized = cv2.resize(image, (224, 224))
            img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
            img_array = tf.keras.applications.mobilenet_v2.preprocess_input(
                img_rgb.astype(np.float32)
            )
            img_tensor = tf.constant(np.expand_dims(img_array, axis=0))

            # -----------------------------------------------------------
            # 4. Compute gradients (Grad-CAM++)
            # -----------------------------------------------------------
            with tf.GradientTape() as tape:
                conv_outputs, predictions = grad_model(img_tensor)
                pred_index = tf.argmax(predictions[0])
                loss = predictions[:, pred_index]

            # First-order gradients w.r.t. conv feature maps
            grads = tape.gradient(loss, conv_outputs)

            if grads is None:
                raise ValueError(
                    f"Gradients are None — the graph from layer "
                    f"'{target_layer.name}' to the output may be disconnected."
                )

            # -----------------------------------------------------------
            # 5. Compute Grad-CAM++ heatmap
            # -----------------------------------------------------------
            conv_out = conv_outputs[0]  # (H, W, C)
            grads_val = grads[0]        # (H, W, C)

            # Grad-CAM++ alpha weights (closed-form using first-order
            # gradients only — Chattopadhay et al. 2018, Eq. 9-10).
            grads_sq = grads_val ** 2
            grads_cb = grads_val ** 3
            sum_act = tf.reduce_sum(conv_out, axis=(0, 1), keepdims=True)
            denom = 2.0 * grads_sq + sum_act * grads_cb + 1e-8
            alpha_c = grads_sq / denom
            # Only positive partial derivatives contribute
            weights = tf.reduce_sum(
                alpha_c * tf.nn.relu(grads_val), axis=(0, 1)
            )

            # Weighted combination of feature maps
            heatmap = tf.reduce_sum(weights * conv_out, axis=-1)

            # ReLU and normalize
            heatmap = heatmap.numpy()
            heatmap = np.maximum(heatmap, 0)
            max_val = np.max(heatmap)

            if max_val < 1e-8:
                logger.warning("Heatmap is all zeros, applying abs-gradient fallback")
                abs_grads = tf.reduce_mean(tf.abs(grads), axis=-1)[0]
                heatmap = abs_grads.numpy()
                heatmap = np.maximum(heatmap, 0)
                max_val = np.max(heatmap)

            if max_val > 1e-8:
                heatmap = heatmap / max_val
            else:
                logger.warning("Heatmap still zero after fallback")
                heatmap = np.zeros_like(heatmap)

            # -----------------------------------------------------------
            # 6. Enhance contrast — make hot spots stand out more
            # -----------------------------------------------------------
            # Power transform suppresses low activations and
            # sharpens the peaks around actual disease spots.
            heatmap = np.power(heatmap, 2.0)
            hm_max = np.max(heatmap)
            if hm_max > 1e-8:
                heatmap = heatmap / hm_max

            # -----------------------------------------------------------
            # 7. Create overlay with per-pixel alpha blending
            # -----------------------------------------------------------
            heatmap_resized = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
            heatmap_uint8 = np.uint8(255 * heatmap_resized)

            # Apply colormap (JET: blue=cold, red=hot)
            heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

            # Per-pixel alpha: areas with low activation keep original
            # image, high activation areas show the heatmap colour.
            # Suppress activation below 35 % so only disease-relevant
            # regions get coloured; the rest stays as the clear original.
            alpha = heatmap_resized.copy()
            alpha[alpha < 0.35] = 0.0           # hard cut-off
            alpha = np.clip(alpha * 1.3, 0, 0.85)  # scale up, cap at 0.85
            alpha_3ch = np.stack([alpha] * 3, axis=-1)

            overlay = (
                image.astype(np.float32) * (1 - alpha_3ch)
                + heatmap_colored.astype(np.float32) * alpha_3ch
            ).astype(np.uint8)

            # Estimate severity from heatmap
            severity_info = ImageProcessor.estimate_severity_from_heatmap(heatmap_uint8)

            logger.info(
                f"Grad-CAM++ generated: heatmap_max={max_val:.4f}, "
                f"severity={severity_info.get('severity')}, "
                f"infected_ratio={severity_info.get('infected_ratio')}%"
            )

            return overlay, severity_info, heatmap_resized

        except Exception as e:
            import traceback
            logger.error(f"Grad-CAM++ heatmap generation FAILED: {e}\n{traceback.format_exc()}")
            return image, {"severity": "Unknown", "infected_ratio": 0.0}, None
    
    @staticmethod
    def estimate_severity_from_heatmap(heatmap: np.ndarray) -> Dict[str, Any]:
        """
        Estimate disease severity from heatmap intensity.
        
        Args:
            heatmap: Grayscale heatmap (0-255)
        
        Returns:
            Dictionary with severity level and infected ratio
        """
        try:
            # Threshold to isolate "hot" infected zones
            _, binary_map = cv2.threshold(heatmap, 200, 255, cv2.THRESH_BINARY)
            
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
        except Exception as e:
            logger.error(f"Error estimating severity: {e}")
            return {"severity": "Unknown", "infected_ratio": 0.0}
    
    @staticmethod
    def generate_heatmap(
        image: np.ndarray,
        gradients: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        DEPRECATED: Use generate_gradcam() instead.
        Legacy method kept for backward compatibility.
        """
        logger.warning("generate_heatmap() is deprecated. Use generate_gradcam() instead.")
        try:
            if gradients is None:
                # Return original image if no gradients provided
                return image
            else:
                # Use actual gradients
                heatmap = cv2.resize(gradients, (image.shape[1], image.shape[0]))
                heatmap = (heatmap * 255).astype(np.uint8)
            
            # Apply colormap
            heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            
            # Overlay on original image
            overlay = cv2.addWeighted(image, 0.6, heatmap_colored, 0.4, 0)
            
            return overlay
        except Exception as e:
            logger.error(f"Error generating heatmap: {e}")
            return image

    @staticmethod
    def generate_heatmap_from_cam(image: np.ndarray, cam: np.ndarray) -> np.ndarray:
        """
        Overlay a Grad-CAM heatmap on the original image.

        Args:
            image: Original BGR image
            cam: 2D heatmap array normalized to [0, 1]

        Returns:
            Image with heatmap overlay
        """
        try:
            heatmap = cv2.resize(cam, (image.shape[1], image.shape[0]))
            heatmap = np.clip(heatmap, 0.0, 1.0)
            heatmap_uint8 = (heatmap * 255).astype(np.uint8)
            heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
            overlay = cv2.addWeighted(image, 0.6, heatmap_colored, 0.4, 0)
            return overlay
        except Exception as e:
            logger.error(f"Error generating heatmap from CAM: {e}")
            return image

    @staticmethod
    def boxes_from_heatmap(
        cam: np.ndarray,
        image_shape: Tuple[int, int, int],
        threshold: float = 0.6,
        min_area_ratio: float = 0.003,
        max_area_ratio: float = 0.35
    ) -> List[Dict[str, Any]]:
        """
        Derive tight bounding boxes from a Grad-CAM heatmap.

        Uses a high threshold + morphological operations to isolate
        individual hot-spots rather than one large blob.

        Args:
            cam: 2D heatmap array normalized to [0, 1]
            image_shape: Original image shape (H, W, C)
            threshold: Heatmap threshold for binarization (higher = tighter)
            min_area_ratio: Minimum box area as fraction of image area
            max_area_ratio: Maximum box area as fraction of image area

        Returns:
            List of bounding boxes with confidence
        """
        try:
            height, width = image_shape[:2]
            total_area = height * width
            heatmap = cv2.resize(cam, (width, height))
            heatmap = np.clip(heatmap, 0.0, 1.0)

            # Binarize at the chosen threshold
            heatmap_uint8 = (heatmap * 255).astype(np.uint8)
            _, binary = cv2.threshold(
                heatmap_uint8,
                int(threshold * 255),
                255,
                cv2.THRESH_BINARY
            )

            # Morphological opening (erode then dilate) to break apart
            # large connected regions into smaller disease-spot clusters.
            kernel_size = max(3, int(min(height, width) * 0.03))
            if kernel_size % 2 == 0:
                kernel_size += 1
            kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
            )
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            min_area = total_area * min_area_ratio
            max_area = total_area * max_area_ratio
            boxes: List[Dict[str, Any]] = []

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h

                # Skip tiny noise
                if area < min_area:
                    continue

                # If a single contour is still too large, try to
                # subdivide it by re-thresholding the ROI at a
                # higher level.
                if area > max_area:
                    sub_boxes = ImageProcessor._subdivide_box(
                        heatmap, x, y, w, h, min_area, max_area,
                        depth=0
                    )
                    boxes.extend(sub_boxes)
                    continue

                roi = heatmap[y:y + h, x:x + w]
                confidence = float(np.max(roi)) if roi.size else 0.0

                boxes.append({
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h),
                    "confidence": round(confidence, 3)
                })

            # Sort by confidence descending
            boxes.sort(key=lambda b: b["confidence"], reverse=True)

            # Keep at most 8 boxes to avoid cluttering the UI
            return boxes[:8]
        except Exception as e:
            logger.error(f"Error deriving boxes from heatmap: {e}")
            return []

    @staticmethod
    def _subdivide_box(
        heatmap: np.ndarray,
        x: int, y: int, w: int, h: int,
        min_area: float, max_area: float,
        depth: int = 0
    ) -> List[Dict[str, Any]]:
        """Recursively split an oversized box by raising the threshold."""
        if depth > 3:
            # Stop recursion — return the box as-is
            roi = heatmap[y:y + h, x:x + w]
            return [{
                "x": int(x), "y": int(y),
                "width": int(w), "height": int(h),
                "confidence": round(float(np.max(roi)), 3)
            }]

        roi = heatmap[y:y + h, x:x + w]
        # Raise threshold: use the 75th percentile of this ROI
        new_thresh = float(np.percentile(roi, 75))
        roi_uint8 = (roi * 255).astype(np.uint8)
        _, sub_binary = cv2.threshold(
            roi_uint8, int(new_thresh * 255), 255, cv2.THRESH_BINARY
        )

        k = max(3, int(min(w, h) * 0.05))
        if k % 2 == 0:
            k += 1
        kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        sub_binary = cv2.morphologyEx(sub_binary, cv2.MORPH_OPEN, kern)

        contours, _ = cv2.findContours(
            sub_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        results: List[Dict[str, Any]] = []
        for cnt in contours:
            bx, by, bw, bh = cv2.boundingRect(cnt)
            area = bw * bh
            if area < min_area:
                continue
            # Translate back to image coordinates
            abs_x, abs_y = x + bx, y + by
            if area > max_area:
                results.extend(ImageProcessor._subdivide_box(
                    heatmap, abs_x, abs_y, bw, bh,
                    min_area, max_area, depth + 1
                ))
            else:
                sub_roi = heatmap[abs_y:abs_y + bh, abs_x:abs_x + bw]
                results.append({
                    "x": int(abs_x), "y": int(abs_y),
                    "width": int(bw), "height": int(bh),
                    "confidence": round(float(np.max(sub_roi)), 3)
                })

        # If subdivision produced nothing, return the original box
        if not results:
            return [{
                "x": int(x), "y": int(y),
                "width": int(w), "height": int(h),
                "confidence": round(float(np.max(roi)), 3)
            }]
        return results
    
    @staticmethod
    def detect_bounding_boxes(
        image: np.ndarray,
        detection_results: Optional[List[Dict]] = None
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Draw bounding boxes on infected areas
        
        Args:
            image: Input image
            detection_results: Detection results with coordinates
        
        Returns:
            Tuple of (annotated image, bounding box list)
        """
        try:
            annotated_image = image.copy()
            bounding_boxes = []
            
            if detection_results is None:
                # Mock detection for demonstration
                height, width = image.shape[:2]
                
                # Create a sample bounding box (in production, use actual model output)
                box = {
                    "x": int(width * 0.3),
                    "y": int(height * 0.3),
                    "width": int(width * 0.4),
                    "height": int(height * 0.4),
                    "confidence": 0.92
                }
                detection_results = [box]
            
            for detection in detection_results:
                x = detection["x"]
                y = detection["y"]
                w = detection["width"]
                h = detection["height"]
                confidence = detection.get("confidence", 0.0)
                
                # Draw rectangle
                cv2.rectangle(
                    annotated_image,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0) if confidence > 0.8 else (0, 255, 255),
                    2
                )
                
                # Draw confidence score
                label = f"{confidence:.2%}"
                cv2.putText(
                    annotated_image,
                    label,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )
                
                bounding_boxes.append({
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "confidence": confidence
                })
            
            return annotated_image, bounding_boxes
        except Exception as e:
            logger.error(f"Error detecting bounding boxes: {e}")
            return image, []
    
    @staticmethod
    def calculate_severity(
        image: np.ndarray,
        bounding_boxes: List[Dict[str, Any]]
    ) -> str:
        """
        Calculate disease severity based on affected area
        
        Args:
            image: Input image
            bounding_boxes: List of detected bounding boxes
        
        Returns:
            Severity level string
        """
        try:
            if not bounding_boxes:
                return "healthy"
            
            height, width = image.shape[:2]
            total_area = height * width
            
            # Calculate total affected area
            affected_area = sum(box["width"] * box["height"] for box in bounding_boxes)
            
            # Calculate percentage
            affected_percentage = affected_area / total_area
            
            # Determine severity
            if affected_percentage < settings.SEVERITY_LOW_THRESHOLD:
                return "low"
            elif affected_percentage < settings.SEVERITY_MEDIUM_THRESHOLD:
                return "medium"
            else:
                return "high"
        except Exception as e:
            logger.error(f"Error calculating severity: {e}")
            return "medium"
    
    @staticmethod
    def preprocess_image_for_model(image: np.ndarray, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray:
        """
        Preprocess image for model inference
        
        Args:
            image: Input image
            target_size: Target size for model input
        
        Returns:
            Preprocessed image
        """
        try:
            # Resize
            resized = cv2.resize(image, target_size)
            
            # Convert BGR to RGB
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # Normalize to [0, 1]
            normalized = rgb.astype(np.float32) / 255.0
            
            # Add batch dimension
            batched = np.expand_dims(normalized, axis=0)
            
            return batched
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
    
    @staticmethod
    def extract_frames_from_video(video_path: str, num_frames: int = 3) -> List[np.ndarray]:
        """
        Extract key frames from video for multi-angle analysis
        
        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
        
        Returns:
            List of extracted frames
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate frame indices to extract
            indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
            
            frames = []
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
            
            cap.release()
            return frames
        except Exception as e:
            logger.error(f"Error extracting frames from video: {e}")
            return []
