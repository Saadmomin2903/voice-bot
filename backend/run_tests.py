#!/usr/bin/env python3
"""
Test runner script for Voice Bot API
Provides different test execution modes and reporting options
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    if description:
        print(f"🔧 {description}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description or 'Command'} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False

def install_test_dependencies():
    """Install test dependencies"""
    print("📦 Installing test dependencies...")
    cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    return run_command(cmd, "Installing dependencies")

def run_unit_tests():
    """Run unit tests only"""
    cmd = ["python", "-m", "pytest", "-m", "unit", "-v"]
    return run_command(cmd, "Running unit tests")

def run_integration_tests():
    """Run integration tests only"""
    cmd = ["python", "-m", "pytest", "-m", "integration", "-v"]
    return run_command(cmd, "Running integration tests")

def run_all_tests():
    """Run all tests"""
    cmd = ["python", "-m", "pytest", "-v"]
    return run_command(cmd, "Running all tests")

def run_tests_with_coverage():
    """Run tests with coverage report"""
    cmd = ["python", "-m", "pytest", "--cov=.", "--cov-report=html", "--cov-report=term", "-v"]
    return run_command(cmd, "Running tests with coverage")

def run_security_tests():
    """Run security-related tests"""
    cmd = ["python", "-m", "pytest", "-m", "security", "-v"]
    return run_command(cmd, "Running security tests")

def run_fast_tests():
    """Run fast tests (exclude slow tests)"""
    cmd = ["python", "-m", "pytest", "-m", "not slow", "-v"]
    return run_command(cmd, "Running fast tests")

def lint_code():
    """Run code linting"""
    print("🔍 Running code quality checks...")
    
    # Try to run flake8 if available
    try:
        cmd = ["python", "-m", "flake8", ".", "--max-line-length=100", "--exclude=__pycache__,venv,.venv"]
        run_command(cmd, "Running flake8 linting")
    except:
        print("⚠️ flake8 not available, skipping linting")
    
    # Try to run black check if available
    try:
        cmd = ["python", "-m", "black", "--check", "--diff", "."]
        run_command(cmd, "Checking code formatting with black")
    except:
        print("⚠️ black not available, skipping format check")

def generate_test_report():
    """Generate comprehensive test report"""
    print("📊 Generating comprehensive test report...")
    
    # Run tests with detailed reporting
    cmd = [
        "python", "-m", "pytest",
        "--cov=.",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term-missing",
        "--junit-xml=test-results.xml",
        "-v"
    ]
    
    success = run_command(cmd, "Generating test report")
    
    if success:
        print("\n📋 Test Report Generated:")
        print("  • HTML Coverage Report: htmlcov/index.html")
        print("  • XML Coverage Report: coverage.xml")
        print("  • JUnit Test Results: test-results.xml")
        
        # Try to open HTML report
        html_report = Path("htmlcov/index.html")
        if html_report.exists():
            print(f"  • Open HTML report: file://{html_report.absolute()}")

def check_test_environment():
    """Check if test environment is properly set up"""
    print("🔧 Checking test environment...")
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Tests directory not found. Make sure you're in the backend directory.")
        return False
    
    # Check if pytest is available
    try:
        subprocess.run(["python", "-m", "pytest", "--version"], 
                      check=True, capture_output=True)
        print("✅ pytest is available")
    except:
        print("❌ pytest not found. Installing test dependencies...")
        if not install_test_dependencies():
            return False
    
    # Check if required modules can be imported
    try:
        import utils.validation
        import utils.api_key_manager
        print("✅ Core modules can be imported")
    except ImportError as e:
        print(f"❌ Failed to import core modules: {e}")
        return False
    
    print("✅ Test environment is ready")
    return True

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Voice Bot API Test Runner")
    parser.add_argument("--mode", choices=[
        "unit", "integration", "all", "coverage", "security", "fast", "report"
    ], default="all", help="Test execution mode")
    parser.add_argument("--install-deps", action="store_true", 
                       help="Install test dependencies")
    parser.add_argument("--lint", action="store_true", 
                       help="Run code linting")
    parser.add_argument("--check-env", action="store_true", 
                       help="Check test environment")
    
    args = parser.parse_args()
    
    print("🧪 Voice Bot API Test Runner")
    print("="*60)
    
    # Check environment if requested
    if args.check_env:
        if not check_test_environment():
            sys.exit(1)
        return
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_test_dependencies():
            sys.exit(1)
        return
    
    # Run linting if requested
    if args.lint:
        lint_code()
        return
    
    # Ensure test environment is ready
    if not check_test_environment():
        print("\n💡 Try running with --install-deps to install dependencies")
        sys.exit(1)
    
    # Run tests based on mode
    success = False
    
    if args.mode == "unit":
        success = run_unit_tests()
    elif args.mode == "integration":
        success = run_integration_tests()
    elif args.mode == "coverage":
        success = run_tests_with_coverage()
    elif args.mode == "security":
        success = run_security_tests()
    elif args.mode == "fast":
        success = run_fast_tests()
    elif args.mode == "report":
        success = generate_test_report()
    else:  # all
        success = run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
