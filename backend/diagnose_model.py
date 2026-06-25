"""
Diagnostic script to inspect model architecture and test Grad-CAM
"""
import sys
sys.path.insert(0, '.')

import numpy as np
import tensorflow as tf
import cv2
from pathlib import Path

def main():
    print("=" * 60)
    print("MODEL ARCHITECTURE DIAGNOSTICS")
    print("=" * 60)

    # 1. Load the model
    model_path = Path("models/crop_disease_master_model.keras")
    if not model_path.exists():
        print(f"ERROR: Model not found at {model_path}")
        return

    print("\n1. Loading model...")
    model = tf.keras.models.load_model(str(model_path), compile=False)
    print(f"   Model type: {type(model).__name__}")
    print(f"   Input shape: {model.input_shape}")
    print(f"   Output shape: {model.output_shape}")
    print(f"   Total layers: {len(model.layers)}")

    # 2. Print layer structure
    print("\n2. Layer structure (top-level):")
    for i, layer in enumerate(model.layers):
        print(f"   [{i}] {layer.name} ({type(layer).__name__}) -> output: {layer.output_shape}")

    # 3. Check if layers[0] is a Model (base model)
    print("\n3. Checking model.layers[0]...")
    first_layer = model.layers[0]
    is_model = isinstance(first_layer, tf.keras.Model)
    print(f"   Is Model/Functional: {is_model}")
    print(f"   Name: {first_layer.name}")
    print(f"   Type: {type(first_layer).__name__}")

    if is_model:
        print(f"   Sub-layers: {len(first_layer.layers)}")
        # Find last conv layer in base model
        last_conv = None
        for layer in reversed(first_layer.layers):
            if isinstance(layer, tf.keras.layers.Conv2D):
                last_conv = layer.name
                break
        print(f"   Last Conv2D in base: {last_conv}")
    else:
        print("   WARNING: layers[0] is NOT a sub-model!")
        print("   This means the Grad-CAM code in image_processing.py will break")
        print("   because it does: base_model = model.layers[0]")
        
        # Find all Conv2D layers in the ENTIRE model
        print("\n   All Conv2D layers in model:")
        conv_layers = []
        for layer in model.layers:
            if isinstance(layer, tf.keras.layers.Conv2D):
                conv_layers.append(layer.name)
                print(f"     - {layer.name}: {layer.output_shape}")
        
        if not conv_layers:
            # Check for nested functional models
            print("\n   Searching nested models for Conv2D layers...")
            for layer in model.layers:
                if isinstance(layer, tf.keras.Model):
                    print(f"\n   Found sub-model: {layer.name}")
                    for sub_layer in layer.layers:
                        if isinstance(sub_layer, tf.keras.layers.Conv2D):
                            conv_layers.append(f"{layer.name}/{sub_layer.name}")
                            print(f"     - {sub_layer.name}: {sub_layer.output_shape}")

    # 4. Test Grad-CAM with a synthetic image
    print("\n4. Testing Grad-CAM with synthetic image...")
    fake_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    
    # Prepare input
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(
        fake_image.astype(np.float32)
    )
    img_array = np.expand_dims(img_array, axis=0)
    
    # Try the current approach used in image_processing.py
    print("\n   Testing current Grad-CAM approach (base_model = model.layers[0])...")
    try:
        base_model = model.layers[0]
        
        if not isinstance(base_model, tf.keras.Model):
            print(f"   PROBLEM: model.layers[0] = {type(base_model).__name__}, not a Model")
            print("   Cannot use model.layers[0] as base_model for Grad-CAM")
            
            # Try alternative: find the last conv layer directly in the model
            print("\n   Trying alternative: direct model Grad-CAM...")
            test_direct_gradcam(model, img_array)
        else:
            # Find last conv layer
            last_conv_name = None
            for layer in reversed(base_model.layers):
                if isinstance(layer, tf.keras.layers.Conv2D):
                    last_conv_name = layer.name
                    break
            
            if last_conv_name is None:
                print("   PROBLEM: No Conv2D layer found in base_model")
            else:
                print(f"   Using conv layer: {last_conv_name}")
                conv_layer = base_model.get_layer(last_conv_name)
                
                # Build grad model
                x = base_model.output
                for head_layer in model.layers[1:]:
                    x = head_layer(x)
                preds = x
                
                grad_model = tf.keras.models.Model(
                    inputs=base_model.input,
                    outputs=[conv_layer.output, preds],
                )
                
                with tf.GradientTape() as tape:
                    conv_outputs, predictions = grad_model(img_array)
                    pred_index = tf.argmax(predictions[0])
                    loss = predictions[:, pred_index]
                
                grads = tape.gradient(loss, conv_outputs)
                if grads is None:
                    print("   PROBLEM: Gradients are None!")
                else:
                    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
                    heatmap = tf.reduce_sum(conv_outputs[0] * pooled_grads, axis=-1)
                    heatmap = tf.maximum(heatmap, 0)
                    heatmap_np = heatmap.numpy()
                    max_val = np.max(heatmap_np)
                    min_val = np.min(heatmap_np)
                    mean_val = np.mean(heatmap_np)
                    
                    print(f"   Heatmap stats: min={min_val:.6f}, max={max_val:.6f}, mean={mean_val:.6f}")
                    
                    if max_val < 1e-6:
                        print("   PROBLEM: Heatmap is all zeros! Gradients not flowing.")
                    else:
                        print("   SUCCESS: Heatmap has non-zero values!")
                        
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n   Trying alternative: direct model Grad-CAM...")
        test_direct_gradcam(model, img_array)


def test_direct_gradcam(model, img_array):
    """Test Grad-CAM using the model directly (not model.layers[0])"""
    try:
        # Find the last Conv2D layer in the entire model graph
        last_conv_name = None
        for layer in reversed(model.layers):
            if isinstance(layer, tf.keras.layers.Conv2D):
                last_conv_name = layer.name
                break
            if isinstance(layer, tf.keras.Model):
                for sub_layer in reversed(layer.layers):
                    if isinstance(sub_layer, tf.keras.layers.Conv2D):
                        last_conv_name = sub_layer.name
                        # Use the sub-model approach
                        print(f"   Found Conv2D '{last_conv_name}' inside sub-model '{layer.name}'")
                        
                        grad_model = tf.keras.models.Model(
                            inputs=model.input,
                            outputs=[layer.get_layer(last_conv_name).output, model.output],
                        )
                        
                        with tf.GradientTape() as tape:
                            conv_outputs, predictions = grad_model(img_array)
                            pred_index = tf.argmax(predictions[0])
                            loss = predictions[:, pred_index]
                        
                        grads = tape.gradient(loss, conv_outputs)
                        if grads is None:
                            print("   PROBLEM: Gradients are None with direct approach!")
                        else:
                            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
                            heatmap = tf.reduce_sum(conv_outputs[0] * pooled_grads, axis=-1)
                            heatmap = tf.maximum(heatmap, 0)
                            heatmap_np = heatmap.numpy()
                            max_val = np.max(heatmap_np)
                            print(f"   Direct Grad-CAM heatmap max: {max_val:.6f}")
                            if max_val > 1e-6:
                                print("   SUCCESS: Direct approach works!")
                            else:
                                print("   PROBLEM: Still zero with direct approach")
                        return
                if last_conv_name:
                    break
        
        if last_conv_name is None:
            print("   No Conv2D layer found anywhere in the model!")
            
    except Exception as e:
        print(f"   Direct approach FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
