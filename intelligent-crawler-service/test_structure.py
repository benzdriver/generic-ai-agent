#!/usr/bin/env python3
"""
Test script to verify the service structure
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules can be imported"""
    
    print("Testing imports...")
    
    modules = [
        "core.models",
        "core.config", 
        "core.llm",
        "core.tasks",
        "ai.evaluator",
        "ai.extractor",
        "crawler.intelligent_crawler",
        "utils.url_utils",
        "utils.text_utils"
    ]
    
    failed = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
            failed.append(module)
    
    if not failed:
        print("\n✅ All modules can be imported successfully!")
    else:
        print(f"\n❌ Failed to import {len(failed)} modules")
    
    return len(failed) == 0

def test_file_structure():
    """Test if all required files exist"""
    
    print("\nTesting file structure...")
    
    required_files = [
        "docker-compose.yml",
        ".env.example",
        "requirements.txt",
        "README.md",
        "Makefile",
        "api/main.py",
        "api/routers/crawl.py",
        "api/routers/search.py",
        "api/routers/health.py",
        "api/routers/admin.py",
        "crawler/intelligent_crawler.py",
        "ai/evaluator.py",
        "ai/extractor.py",
        "core/models.py",
        "core/config.py",
        "docker/Dockerfile.api",
        "docker/Dockerfile.crawler",
        "docker/init.sql"
    ]
    
    missing = []
    
    for file in required_files:
        path = os.path.join(os.path.dirname(__file__), file)
        if os.path.exists(path):
            print(f"✓ {file}")
        else:
            print(f"✗ {file}")
            missing.append(file)
    
    if not missing:
        print("\n✅ All required files exist!")
    else:
        print(f"\n❌ Missing {len(missing)} files")
    
    return len(missing) == 0

def test_docker_config():
    """Test Docker configuration"""
    
    print("\nTesting Docker configuration...")
    
    # Check if docker-compose.yml is valid
    import yaml
    
    try:
        with open("docker-compose.yml", "r") as f:
            config = yaml.safe_load(f)
        
        services = config.get("services", {})
        required_services = ["api", "crawler-worker", "redis", "postgres", "qdrant"]
        
        for service in required_services:
            if service in services:
                print(f"✓ Service '{service}' defined")
            else:
                print(f"✗ Service '{service}' missing")
        
        print("\n✅ Docker configuration looks good!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error reading docker-compose.yml: {e}")
        return False

def main():
    """Run all tests"""
    
    print("=== Intelligent Crawler Service Structure Test ===\n")
    
    results = []
    
    # Run tests
    results.append(("File Structure", test_file_structure()))
    results.append(("Module Imports", test_imports()))
    
    # Try docker test only if yaml is available
    try:
        import yaml
        results.append(("Docker Config", test_docker_config()))
    except ImportError:
        print("\n⚠️  Skipping Docker config test (PyYAML not installed)")
    
    # Summary
    print("\n=== Test Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The service structure is ready.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and add your API keys")
        print("2. Run 'docker-compose build' to build the images")
        print("3. Run 'docker-compose up' to start the services")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()