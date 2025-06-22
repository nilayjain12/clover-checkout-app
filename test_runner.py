#!/usr/bin/env python3
"""
Test Runner for Clover Checkout App Requirements
This script runs all tests and generates a comprehensive report
"""

import subprocess
import sys
import os
import json
from datetime import datetime

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_requirements():
    """Check if all required packages are installed"""
    print("🔍 Checking requirements...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "requests",
        "pytest",
        "httpx"
    ]
    
    missing_packages = []
    for package in required_packages:
        success, _, _ = run_command(f"python -c 'import {package}'")
        if not success:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Install missing packages with: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def run_unit_tests():
    """Run unit tests"""
    print("\n🧪 Running unit tests...")
    
    success, stdout, stderr = run_command("pytest test_main.py -v")
    
    if success:
        print("✅ Unit tests passed")
        return True
    else:
        print("❌ Unit tests failed")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return False

def run_requirement_tests():
    """Run requirement tests"""
    print("\n📋 Running requirement tests...")
    
    success, stdout, stderr = run_command("pytest test_requirements.py -v")
    
    if success:
        print("✅ Requirement tests passed")
        return True
    else:
        print("❌ Requirement tests failed")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return False

def test_api_endpoints():
    """Test API endpoints manually"""
    print("\n🌐 Testing API endpoints...")
    
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        endpoints_to_test = [
            ("/", "Main page"),
            ("/health", "Health check"),
            ("/auth/status", "Auth status"),
            ("/transactions", "Transactions"),
            ("/auth/login", "Login redirect")
        ]
        
        results = []
        for endpoint, description in endpoints_to_test:
            try:
                response = client.get(endpoint)
                if response.status_code in [200, 302]:
                    print(f"✅ {description} ({endpoint}): {response.status_code}")
                    results.append(True)
                else:
                    print(f"❌ {description} ({endpoint}): {response.status_code}")
                    results.append(False)
            except Exception as e:
                print(f"❌ {description} ({endpoint}): Error - {e}")
                results.append(False)
        
        return all(results)
    
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False

def test_payment_flow():
    """Test the complete payment flow"""
    print("\n💳 Testing payment flow...")
    
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Test payment endpoint without authentication
        payment_data = {"amount": 10.00, "description": "Test Payment"}
        response = client.post("/pay", json=payment_data)
        
        if response.status_code == 401:
            print("✅ Payment endpoint correctly requires authentication")
            return True
        else:
            print(f"❌ Payment endpoint should require authentication, got: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error testing payment flow: {e}")
        return False

def check_file_structure():
    """Check if all required files exist"""
    print("\n📁 Checking file structure...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
        "QUICKSTART.md",
        "app/__init__.py",
        "app/clover_service.py",
        "app/token_utils.py",
        "app/transaction_utils.py",
        "static/index.html",
        "test_main.py",
        "test_requirements.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files exist")
    return True

def generate_report(results):
    """Generate a comprehensive test report"""
    print("\n" + "="*60)
    print("📊 TEST REPORT")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print("\n" + "="*60)
    
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED! Your application meets all requirements.")
    else:
        print(f"⚠️  {failed_tests} test(s) failed. Please review the issues above.")
    
    # Save report to file
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "success_rate": (passed_tests/total_tests)*100,
        "results": results
    }
    
    with open("test_report.json", "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: test_report.json")

def main():
    """Main test runner function"""
    print("🚀 Clover Checkout App - Requirement Test Runner")
    print("="*60)
    
    results = {}
    
    # Run all tests
    results["Requirements Check"] = check_requirements()
    results["File Structure"] = check_file_structure()
    results["Unit Tests"] = run_unit_tests()
    results["Requirement Tests"] = run_requirement_tests()
    results["API Endpoints"] = test_api_endpoints()
    results["Payment Flow"] = test_payment_flow()
    
    # Generate report
    generate_report(results)
    
    # Return appropriate exit code
    if all(results.values()):
        print("\n🎯 All requirements are satisfied!")
        sys.exit(0)
    else:
        print("\n🔧 Some requirements need attention.")
        sys.exit(1)

if __name__ == "__main__":
    main() 