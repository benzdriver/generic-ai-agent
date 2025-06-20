#!/usr/bin/env python3
"""
Run tests locally without Docker
"""

import subprocess
import sys
import os

def main():
    """Run tests locally"""
    
    print("=== Running Tests Locally ===\n")
    
    # Set test environment variables
    os.environ['TESTING'] = 'true'
    os.environ['API_URL'] = 'http://localhost:8080'
    
    # Change to the service directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Install test dependencies if needed
    print("Installing test dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "httpx"], 
                   capture_output=True)
    
    # Run pytest
    print("\nRunning tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                           capture_output=False)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())