"""
Quick Test Execution Script

This script provides a simple way to verify the test suite is working.
"""
import subprocess
import sys

def main():
    """Run a quick test to verify setup"""
    print("=" * 80)
    print("Testing Backend - Quick Verification")
    print("=" * 80)
    
    # Test 1: Check test discovery
    print("\n1. Checking test discovery...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("   ✓ Test discovery successful")
        # Count tests
        lines = result.stdout.split('\n')
        for line in lines:
            if 'test' in line.lower():
                print(f"   {line}")
    else:
        print("   ✗ Test discovery failed")
        print(result.stderr)
    
    # Test 2: Run a simple unit test
    print("\n2. Running sample unit tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/test_config.py", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("   ✓ Unit tests passed")
    else:
        print("   ⚠ Some unit tests failed (this is expected if app code needs updates)")
    
    # Show summary
    lines = result.stdout.split('\n')
    for line in lines:
        if 'passed' in line.lower() or 'failed' in line.lower():
            print(f"   {line}")
    
    print("\n" + "=" * 80)
    print("Quick test verification complete!")
    print("=" * 80)
    print("\nTo run all tests:")
    print("  pytest -v")
    print("\nTo run with coverage:")
    print("  pytest --cov=app --cov-report=html")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
