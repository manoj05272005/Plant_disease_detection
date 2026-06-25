"""
Test Runner Script

Run this script to execute all tests with coverage report.

Usage:
    python run_tests.py                # Run all tests
    python run_tests.py --unit         # Run only unit tests
    python run_tests.py --integration  # Run only integration tests
    python run_tests.py --coverage     # Run with detailed coverage report
"""
import sys
import subprocess
from pathlib import Path


def run_tests(args=None):
    """Run pytest with specified arguments"""
    
    # Base pytest command
    cmd = ["pytest"]
    
    if args is None:
        args = sys.argv[1:]
    
    # Parse custom arguments
    if "--unit" in args:
        cmd.extend(["-m", "unit"])
        args.remove("--unit")
    elif "--integration" in args:
        cmd.extend(["-m", "integration"])
        args.remove("--integration")
    elif "--coverage" in args:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
        args.remove("--coverage")
    
    # Add remaining arguments
    cmd.extend(args)
    
    # Default arguments if none specified
    if len(cmd) == 1:
        cmd.extend(["-v", "--tb=short"])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 80)
    
    # Run pytest
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
