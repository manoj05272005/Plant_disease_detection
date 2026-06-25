"""
Convert Keras model to TensorFlow Lite format for on-device inference.
Run once: python convert_to_tflite.py
Output: ../frontend/assets/model/crop_disease_model.tflite

Uses SavedModel as an intermediate step to work around Keras 3 + TF 2.16
TFLite converter incompatibility (LLVM 'missing attribute value' error).
"""
import os
import sys
import shutil
import traceback

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "crop_disease_master_model.keras")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "frontend", "assets", "model")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "crop_disease_model.tflite")
SAVED_MODEL_DIR = os.path.join(SCRIPT_DIR, "_saved_model_tmp")

def log(msg):
    print(msg, flush=True)

def convert():
    try:
        log("Step 1/5: Checking model file...")
        if not os.path.exists(MODEL_PATH):
            log(f"ERROR: Model not found at {MODEL_PATH}")
            sys.exit(1)
        size = os.path.getsize(MODEL_PATH) / (1024 * 1024)
        log(f"  Found model: {MODEL_PATH} ({size:.1f} MB)")

        log("Step 2/5: Importing TensorFlow (this takes a while)...")
        import tensorflow as tf
        log(f"  TensorFlow version: {tf.__version__}")

        log("Step 3/5: Loading Keras model...")
        model = tf.keras.models.load_model(MODEL_PATH)
        log(f"  Input shape: {model.input_shape}")
        log(f"  Output shape: {model.output_shape}")

        log("Step 4/5: Exporting as SavedModel (workaround for Keras 3)...")
        # Clean up any previous temp dir
        if os.path.exists(SAVED_MODEL_DIR):
            shutil.rmtree(SAVED_MODEL_DIR)
        model.export(SAVED_MODEL_DIR)
        log(f"  SavedModel exported to: {SAVED_MODEL_DIR}")

        log("Step 5/5: Converting SavedModel to TFLite with float16 quantization...")
        converter = tf.lite.TFLiteConverter.from_saved_model(SAVED_MODEL_DIR)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
        tflite_model = converter.convert()

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(OUTPUT_PATH, "wb") as f:
            f.write(tflite_model)

        size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
        log(f"TFLite model saved to: {OUTPUT_PATH}")
        log(f"Model size: {size_mb:.2f} MB")

        # Clean up temp SavedModel
        shutil.rmtree(SAVED_MODEL_DIR, ignore_errors=True)
        log("Done!")

    except Exception as e:
        log(f"ERROR: {e}")
        traceback.print_exc()
        # Clean up on failure too
        if os.path.exists(SAVED_MODEL_DIR):
            shutil.rmtree(SAVED_MODEL_DIR, ignore_errors=True)
        sys.exit(1)

if __name__ == "__main__":
    convert()
