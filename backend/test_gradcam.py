"""
Test script to verify Grad-CAM heatmap generation
"""
import sys
sys.path.insert(0, 'app')

import cv2
import numpy as np
from pathlib import Path
from app.utils.image_processing import ImageProcessor
from app.services.ai_service import ai_service

def test_gradcam():
    print("=" * 60)
    print("Testing Real Grad-CAM Heatmap Generation")
    print("=" * 60)
    
    # Load the model
    print("\n1. Loading AI model...")
    ai_service.load_models()
    
    if not ai_service.model_loaded:
        print("❌ Model not loaded. Cannot test Grad-CAM.")
        return False
    
    print("✓ Model loaded successfully")
    
    # Find a test image
    test_image_path = Path("../Model/test_samples/0a8a68ee-f587-4dea-beec-79d02e7d3fa4___RS_Early.B 8461.JPG")
    
    if not test_image_path.exists():
        print(f"❌ Test image not found at: {test_image_path}")
        return False
    
    print(f"\n2. Loading test image: {test_image_path.name}")
    image = cv2.imread(str(test_image_path))
    
    if image is None:
        print("❌ Failed to load image")
        return False
    
    print(f"✓ Image loaded: {image.shape}")
    
    # Test Grad-CAM generation
    print("\n3. Generating Grad-CAM heatmap...")
    try:
        heatmap_overlay, severity_info, raw_heatmap = ImageProcessor.generate_gradcam(
            ai_service.model,
            image
        )
        
        print("✓ Grad-CAM generated successfully!")
        print(f"   - Severity: {severity_info['severity']}")
        print(f"   - Infected Ratio: {severity_info['infected_ratio']}%")
        print(f"   - Heatmap shape: {heatmap_overlay.shape}")
        
        # Save the heatmap overlay
        output_path = "test_gradcam_output.jpg"
        cv2.imwrite(output_path, heatmap_overlay)
        print(f"\n✓ Heatmap overlay saved to: {output_path}")

        # Save the raw heatmap as a standalone colour image
        if raw_heatmap is not None:
            raw_uint8 = np.uint8(255 * np.clip(raw_heatmap, 0, 1))
            raw_colored = cv2.applyColorMap(raw_uint8, cv2.COLORMAP_JET)
            cv2.imwrite("test_raw_heatmap.jpg", raw_colored)
            print("✓ Raw heatmap (standalone) saved to: test_raw_heatmap.jpg")
            
            # Compute how much the overlay differs from the original
            diff = np.mean(np.abs(heatmap_overlay.astype(float) - image.astype(float)))
            print(f"   - Mean pixel diff (overlay vs original): {diff:.2f}")
            
            # Show stats about activation distribution
            flat = raw_heatmap.flatten()
            pct_above_30 = np.mean(flat > 0.30) * 100
            pct_above_50 = np.mean(flat > 0.50) * 100
            pct_above_70 = np.mean(flat > 0.70) * 100
            print(f"   - Activation > 0.3: {pct_above_30:.1f}% of pixels")
            print(f"   - Activation > 0.5: {pct_above_50:.1f}% of pixels")
            print(f"   - Activation > 0.7: {pct_above_70:.1f}% of pixels")
        
        # Test bounding box derivation from Grad-CAM
        print("\n4. Deriving bounding boxes from Grad-CAM heatmap...")
        if raw_heatmap is not None:
            boxes = ImageProcessor.boxes_from_heatmap(
                raw_heatmap, image.shape,
                threshold=0.6,
                min_area_ratio=0.003,
                max_area_ratio=0.35,
            )
            print(f"   - Number of boxes: {len(boxes)}")
            for i, box in enumerate(boxes):
                print(f"   - Box {i+1}: x={box['x']}, y={box['y']}, "
                      f"w={box['width']}, h={box['height']}, "
                      f"conf={box['confidence']:.3f}")
            
            # Draw boxes on a copy and save
            annotated = image.copy()
            for box in boxes:
                x, y = box['x'], box['y']
                w, h = box['width'], box['height']
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.imwrite("test_boxes_output.jpg", annotated)
            print(f"   ✓ Annotated image saved to: test_boxes_output.jpg")
        else:
            print("   ⚠ No raw heatmap available for box derivation")
        
        return True
        
    except Exception as e:
        print(f"❌ Grad-CAM generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gradcam()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Real Grad-CAM is working!")
    else:
        print("❌ TEST FAILED: Check errors above")
    print("=" * 60)
