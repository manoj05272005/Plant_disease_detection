"""
Quick test script to verify backend setup
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        import tensorflow as tf
        print(f"✓ TensorFlow {tf.__version__}")
    except ImportError as e:
        print(f"✗ TensorFlow import failed: {e}")
        return False
    
    try:
        import fastapi
        print(f"✓ FastAPI {fastapi.__version__}")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    try:
        import motor
        print("✓ Motor (MongoDB async driver)")
    except ImportError as e:
        print(f"✗ Motor import failed: {e}")
        return False
    
    try:
        from app.core.config import settings
        print(f"✓ Config loaded: {settings.APP_NAME}")
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False
    
    try:
        from app.services.ai_service import ai_service
        print(f"✓ AI Service initialized, Model loaded: {ai_service.model_loaded}")
    except Exception as e:
        print(f"✗ AI Service initialization failed: {e}")
        return False
    
    try:
        from app.models.schemas import CropType, DiagnosisResponse
        print("✓ Pydantic schemas imported")
    except Exception as e:
        print(f"✗ Schema import failed: {e}")
        return False
    
    print("\n✓ All imports successful!")
    return True

def test_directories():
    """Test required directories exist"""
    print("\nChecking directories...")
    
    required_dirs = [
        "uploads/images",
        "uploads/heatmaps",
        "uploads/reports",
        "models",
        "logs"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - missing!")
            all_exist = False
    
    return all_exist

def test_model_files():
    """Test model files exist"""
    print("\nChecking model files...")
    
    model_path = Path("models/crop_disease_master_model.keras")
    label_path = Path("models/new_label_map.txt")
    
    all_exist = True
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✓ Model file exists ({size_mb:.2f} MB)")
    else:
        print("✗ Model file missing: models/crop_disease_master_model.keras")
        all_exist = False
    
    if label_path.exists():
        with open(label_path, 'r', encoding='utf-8') as f:
            labels = [line.strip() for line in f if line.strip()]
        print(f"✓ Label map exists ({len(labels)} classes)")
    else:
        print("✗ Label map missing: models/new_label_map.txt")
        all_exist = False
    
    return all_exist

def test_env_file():
    """Test .env file exists and has required fields"""
    print("\nChecking .env file...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("✗ .env file not found!")
        return False
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    required_vars = [
        "MONGODB_URL",
        "SECRET_KEY",
        "MODEL_PATH"
    ]
    
    all_found = True
    for var in required_vars:
        if var in content:
            print(f"✓ {var} configured")
        else:
            print(f"✗ {var} missing!")
            all_found = False
    
    return all_found

if __name__ == "__main__":
    print("="*50)
    print("Backend Verification Test")
    print("="*50)
    print()
    
    tests = [
        ("Environment File", test_env_file),
        ("Directories", test_directories),
        ("Model Files", test_model_files),
        ("Python Imports", test_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
        print()
    
    print("="*50)
    print("Test Summary")
    print("="*50)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print()
    if all_passed:
        print("✓ All tests passed! Backend is ready to start.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)
