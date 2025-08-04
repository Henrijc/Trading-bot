#!/usr/bin/env python3
"""
Deployment Verification Script
This script tests all critical imports to ensure deployment will succeed
"""

import sys
import os

# Add app to path
sys.path.insert(0, '/app')

def test_init_files():
    """Test that all required __init__.py files exist"""
    required_init_files = [
        '/app/__init__.py',
        '/app/backend/__init__.py',
        '/app/backend/services/__init__.py',
        '/app/freqtrade/__init__.py',
        '/app/freqtrade/user_data/__init__.py',
        '/app/freqtrade/user_data/strategies/__init__.py'
    ]
    
    missing_files = []
    for file_path in required_init_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing __init__.py files:")
        for file in missing_files:
            print(f"   {file}")
        return False
    else:
        print("✅ All required __init__.py files exist")
        return True

def test_backend_imports():
    """Test backend service imports"""
    try:
        from backend.services.ai_service import AICoachService
        from backend.services.luno_service import LunoService
        from backend.services.technical_analysis_service import TechnicalAnalysisService
        from backend.services.authentication_service import AuthenticationService
        from backend.services.security_service import SecurityService
        from backend.services.database_service import get_database_client
        from backend.services.emergent_mock import LlmChat, UserMessage
        print("✅ All backend imports successful")
        return True
    except Exception as e:
        print(f"❌ Backend imports failed: {e}")
        return False

def test_freqtrade_imports():
    """Test freqtrade imports"""
    try:
        from freqtrade.user_data.real_freqai_service import RealFreqAIService
        from freqtrade.user_data.strategies.LunoFreqAIStrategy import LunoFreqAIStrategy
        from freqtrade.user_data.strategies.luno_test_strategy import LunoTestStrategy
        print("✅ All freqtrade imports successful")
        return True
    except Exception as e:
        print(f"❌ Freqtrade imports failed: {e}")
        return False

def test_critical_dependencies():
    """Test that critical dependencies are available"""
    try:
        import aiohttp
        import fastapi
        import uvicorn
        import pandas
        import ta
        print("✅ All critical dependencies available")
        return True
    except Exception as e:
        print(f"❌ Critical dependencies missing: {e}")
        return False

def main():
    """Main verification function"""
    print("=== DEPLOYMENT VERIFICATION SCRIPT ===")
    print("Testing all critical components for successful VPS deployment...\n")
    
    tests = [
        ("__init__.py Files", test_init_files),
        ("Backend Imports", test_backend_imports),
        ("Freqtrade Imports", test_freqtrade_imports),
        ("Critical Dependencies", test_critical_dependencies)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print("=== VERIFICATION RESULTS ===")
    print(f"Passed: {passed}/{total} tests")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Deployment should succeed!")
        sys.exit(0)
    else:
        print("💥 SOME TESTS FAILED - Deployment will likely fail!")
        sys.exit(1)

if __name__ == "__main__":
    main()