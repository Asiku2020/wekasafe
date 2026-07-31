#!/usr/bin/env python3
"""
WekaSafe Backend Setup Test Script
Tests all critical components before deployment
"""

import os
import sys
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_test(name, passed, message=""):
    """Print test result"""
    status = "[PASS]" if passed else "[FAIL]"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {name}")
    if message:
        print(f"      {message}")

def test_dependencies():
    """Test if all required packages are installed"""
    print_header("Testing Dependencies")
    
    required = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'pydantic',
        'python-jose', 'passlib', 'python-multipart',
        'python-dotenv', 'aiofiles', 'jinja2'
    ]
    
    all_installed = True
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print_test(f"Package: {package}", True)
        except ImportError:
            print_test(f"Package: {package}", False, "Not installed")
            all_installed = False
    
    return all_installed

def test_env_file():
    """Test if .env file exists and has required variables"""
    print_header("Testing Environment Configuration")
    
    if not os.path.exists('.env'):
        print_test(".env file exists", False, "File not found")
        return False
    
    print_test(".env file exists", True)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'JWT_SECRET',
        'MAIL_HOST',
        'MAIL_PORT',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_FROM',
        'ADMIN_EMAIL'
    ]
    
    all_vars_set = True
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your-'):
            print_test(f"Env var: {var}", False, "Not configured")
            all_vars_set = False
        else:
            print_test(f"Env var: {var}", True)
    
    # Check JWT_SECRET strength
    jwt_secret = os.getenv('JWT_SECRET', '')
    if len(jwt_secret) < 32:
        print_test("JWT_SECRET strength", False, "Should be at least 32 characters")
        all_vars_set = False
    else:
        print_test("JWT_SECRET strength", True)
    
    return all_vars_set

def test_directories():
    """Test if required directories exist"""
    print_header("Testing Directory Structure")
    
    required_dirs = [
        'templates',
        'static',
        'uploads'
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        exists = os.path.isdir(dir_name)
        print_test(f"Directory: {dir_name}/", exists)
        if not exists:
            all_exist = False
            # Try to create it
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"      Created directory: {dir_name}/")
            except Exception as e:
                print(f"      Error creating directory: {e}")
    
    return all_exist

def test_templates():
    """Test if all required templates exist"""
    print_header("Testing HTML Templates")
    
    required_templates = [
        'login.html',
        'dashboard.html',
        'quotes.html',
        'incidents.html',
        'incident_detail.html'
    ]
    
    all_exist = True
    for template in required_templates:
        path = os.path.join('templates', template)
        exists = os.path.isfile(path)
        print_test(f"Template: {template}", exists)
        if not exists:
            all_exist = False
    
    return all_exist

def test_core_files():
    """Test if all core Python files exist"""
    print_header("Testing Core Application Files")
    
    required_files = [
        'main.py',
        'auth.py',
        'models.py',
        'schemas.py',
        'utils.py',
        'database.py',
        'requirements.txt'
    ]
    
    all_exist = True
    for filename in required_files:
        exists = os.path.isfile(filename)
        print_test(f"File: {filename}", exists)
        if not exists:
            all_exist = False
    
    return all_exist

def test_database_models():
    """Test if database models can be imported"""
    print_header("Testing Database Models")
    
    try:
        from database import Base, engine
        from models import User, Quote, Incident
        
        print_test("Import database module", True)
        print_test("Import User model", True)
        print_test("Import Quote model", True)
        print_test("Import Incident model", True)
        
        # Test database creation
        try:
            Base.metadata.create_all(bind=engine)
            print_test("Database tables creation", True)
        except Exception as e:
            print_test("Database tables creation", False, str(e))
            return False
        
        return True
        
    except ImportError as e:
        print_test("Import models", False, str(e))
        return False

def test_email_config():
    """Test email configuration (without sending)"""
    print_header("Testing Email Configuration")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    host = os.getenv('MAIL_HOST')
    port = os.getenv('MAIL_PORT')
    username = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    
    # Check configuration
    config_ok = True
    
    if not host or host == 'smtp.gmail.com':
        print_test("MAIL_HOST configured", bool(host))
        if not host:
            config_ok = False
    
    if not port or port == '587':
        print_test("MAIL_PORT configured", bool(port))
        if not port:
            config_ok = False
    
    if not username or 'your-email' in username:
        print_test("MAIL_USERNAME configured", False, "Please set your email")
        config_ok = False
    else:
        print_test("MAIL_USERNAME configured", True)
    
    if not password or 'your-' in password:
        print_test("MAIL_PASSWORD configured", False, "Please set your app password")
        config_ok = False
    else:
        print_test("MAIL_PASSWORD configured", True)
    
    return config_ok

def test_security():
    """Test security utilities"""
    print_header("Testing Security Functions")
    
    try:
        from utils import hash_password, verify_password
        
        # Test password hashing
        test_pass = "TestPassword123"
        hashed = hash_password(test_pass)
        
        print_test("Password hashing", True)
        
        # Test password verification
        valid = verify_password(test_pass, hashed)
        print_test("Password verification (correct)", valid)
        
        invalid = verify_password("WrongPassword", hashed)
        print_test("Password verification (incorrect)", not invalid)
        
        return True
        
    except Exception as e:
        print_test("Security functions", False, str(e))
        return False

def main():
    """Run all tests"""
    print("\n")
    print("*" * 60)
    print("  WekaSafe Backend Setup Test")
    print("*" * 60)
    
    results = {
        "Dependencies": test_dependencies(),
        "Environment": test_env_file(),
        "Directories": test_directories(),
        "Templates": test_templates(),
        "Core Files": test_core_files(),
        "Database": test_database_models(),
        "Email Config": test_email_config(),
        "Security": test_security()
    }
    
    print_header("Test Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        print_test(test_name, result)
    
    print("\n" + "="*60)
    print(f"  Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n✓ All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Start the server: uvicorn main:app --reload")
        print("2. Visit: http://localhost:8000/admin/setup")
        print("3. Create your admin account")
        print("4. Login at: http://localhost:8000/admin/login")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Run: pip install -r requirements.txt")
        print("- Configure your .env file with real credentials")
        print("- Make sure all template files are in templates/")
        return 1

if __name__ == "__main__":
    sys.exit(main())