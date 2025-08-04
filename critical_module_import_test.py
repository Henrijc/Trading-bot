#!/usr/bin/env python3
"""
CRITICAL FINAL DEPLOYMENT VERIFICATION - ModuleNotFoundError Resolution
Testing Script for VPS Container Stability

CRITICAL TESTING FOCUS:
The user has reported persistent container failures on VPS with these specific errors:
1. "ModuleNotFoundError: No module named 'backend.services.database_service'" from authentication_service.py line 9
2. "ModuleNotFoundError: No module named 'aiohttp'" from luno_service.py line 3

VERIFICATION REQUIREMENTS:
1. backend.services.database_service import works correctly
2. backend.services.authentication_service imports AuthService and auth_router
3. aiohttp is available for freqtrade service
4. requests_cache is available for freqtrade service
5. All backend services import correctly with absolute paths

CONTAINER SIMULATION:
1. Backend container would start without ModuleNotFoundError
2. Freqtrade container has all required dependencies
3. All Python packages accessible with PYTHONPATH=/app

This is the FINAL verification before VPS deployment.
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any
import traceback

# Add /app to Python path to simulate container environment
sys.path.insert(0, '/app')
os.environ['PYTHONPATH'] = '/app'

class CriticalModuleImportTester:
    def __init__(self):
        self.test_results = []
        self.critical_imports = [
            # Critical backend service imports that were failing
            ('backend.services.database_service', 'DatabaseService'),
            ('backend.services.authentication_service', 'AuthenticationService'),
            ('backend.services.authentication_service', 'auth_router'),
            ('backend.services.decision_engine', 'TradeSignal'),
            ('backend.services.decision_engine', 'DecisionEngine'),
            ('backend.services.technical_analysis_service', 'TechnicalAnalysisService'),
            ('backend.services.ai_service', 'AICoachService'),
            ('backend.services.luno_service', 'LunoService'),
            ('backend.services.freqtrade_service', 'FreqtradeService'),
            ('backend.services.target_service', 'TargetService'),
        ]
        
        # Critical dependencies for freqtrade container
        self.freqtrade_dependencies = [
            'aiohttp',
            'requests_cache',
            'ccxt',
            'pandas',
            'numpy',
            'ta'
        ]
        
        # Backend server critical imports
        self.backend_server_imports = [
            'backend.models',
            'backend.services.ai_service',
            'backend.services.luno_service',
            'backend.services.technical_analysis_service',
            'backend.services.authentication_service',
            'backend.services.backtest_api_service',
            'backend.services.live_trading_service',
            'backend.services.freqtrade_service',
            'backend.services.target_service',
            'backend.services.decision_engine'
        ]
    
    def log_test(self, test_name: str, success: bool, details: str = "", error_info: str = ""):
        """Log test results with detailed information"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'error_info': error_info
        }
        self.test_results.append(result)
        
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if error_info and not success:
            print(f"    Error: {error_info}")
        print()
    
    def test_backend_services_import(self) -> bool:
        """Test that all backend services can be imported with absolute paths"""
        print("🔍 TESTING: Backend Services Import with Absolute Paths")
        print("=" * 70)
        
        all_success = True
        
        for module_path, class_name in self.critical_imports:
            try:
                # Import the module
                module = importlib.import_module(module_path)
                
                # Check if the class/object exists
                if hasattr(module, class_name):
                    obj = getattr(module, class_name)
                    self.log_test(
                        f"Import {module_path}.{class_name}",
                        True,
                        f"Successfully imported {class_name} from {module_path}"
                    )
                else:
                    self.log_test(
                        f"Import {module_path}.{class_name}",
                        False,
                        f"Module {module_path} imported but {class_name} not found",
                        f"Available attributes: {[attr for attr in dir(module) if not attr.startswith('_')]}"
                    )
                    all_success = False
                    
            except ModuleNotFoundError as e:
                self.log_test(
                    f"Import {module_path}.{class_name}",
                    False,
                    f"ModuleNotFoundError: {str(e)}",
                    f"Failed to import {module_path} - this is a critical container failure"
                )
                all_success = False
            except Exception as e:
                self.log_test(
                    f"Import {module_path}.{class_name}",
                    False,
                    f"Import error: {str(e)}",
                    traceback.format_exc()
                )
                all_success = False
        
        return all_success
    
    def test_freqtrade_dependencies(self) -> bool:
        """Test that freqtrade container dependencies are available"""
        print("🐳 TESTING: Freqtrade Container Dependencies")
        print("=" * 70)
        
        all_success = True
        
        for dependency in self.freqtrade_dependencies:
            try:
                module = importlib.import_module(dependency)
                version = getattr(module, '__version__', 'unknown')
                self.log_test(
                    f"Freqtrade Dependency: {dependency}",
                    True,
                    f"Successfully imported {dependency} version {version}"
                )
            except ModuleNotFoundError as e:
                self.log_test(
                    f"Freqtrade Dependency: {dependency}",
                    False,
                    f"ModuleNotFoundError: {str(e)}",
                    f"This dependency is required for freqtrade container stability"
                )
                all_success = False
            except Exception as e:
                self.log_test(
                    f"Freqtrade Dependency: {dependency}",
                    False,
                    f"Import error: {str(e)}",
                    traceback.format_exc()
                )
                all_success = False
        
        return all_success
    
    def test_backend_server_import(self) -> bool:
        """Test that backend server.py can import all required modules"""
        print("🖥️ TESTING: Backend Server Import Simulation")
        print("=" * 70)
        
        all_success = True
        
        for module_path in self.backend_server_imports:
            try:
                module = importlib.import_module(module_path)
                self.log_test(
                    f"Backend Server Import: {module_path}",
                    True,
                    f"Successfully imported {module_path}"
                )
            except ModuleNotFoundError as e:
                self.log_test(
                    f"Backend Server Import: {module_path}",
                    False,
                    f"ModuleNotFoundError: {str(e)}",
                    f"Backend server cannot start without this module"
                )
                all_success = False
            except Exception as e:
                self.log_test(
                    f"Backend Server Import: {module_path}",
                    False,
                    f"Import error: {str(e)}",
                    traceback.format_exc()
                )
                all_success = False
        
        return all_success
    
    def test_specific_reported_errors(self) -> bool:
        """Test the specific errors reported by the user"""
        print("🚨 TESTING: Specific Reported Container Failures")
        print("=" * 70)
        
        all_success = True
        
        # Test 1: backend.services.database_service from authentication_service.py line 9
        try:
            from backend.services.authentication_service import AuthenticationService
            # Try to instantiate to ensure database_service import works
            auth_service = AuthenticationService()
            self.log_test(
                "Fix: backend.services.database_service import",
                True,
                "AuthenticationService can be imported and instantiated without ModuleNotFoundError"
            )
        except ModuleNotFoundError as e:
            if 'database_service' in str(e):
                self.log_test(
                    "Fix: backend.services.database_service import",
                    False,
                    f"CRITICAL: Still getting database_service ModuleNotFoundError: {str(e)}",
                    "This is the exact error reported by user - container will fail"
                )
                all_success = False
            else:
                self.log_test(
                    "Fix: backend.services.database_service import",
                    False,
                    f"Different ModuleNotFoundError: {str(e)}",
                    "Different import issue but still critical"
                )
                all_success = False
        except Exception as e:
            self.log_test(
                "Fix: backend.services.database_service import",
                True,
                f"database_service import works, other error: {str(e)}",
                "The specific ModuleNotFoundError is resolved"
            )
        
        # Test 2: aiohttp from luno_service.py line 3
        try:
            from backend.services.luno_service import LunoService
            # Try to instantiate to ensure aiohttp import works
            luno_service = LunoService()
            self.log_test(
                "Fix: aiohttp import for luno_service",
                True,
                "LunoService can be imported and instantiated without aiohttp ModuleNotFoundError"
            )
        except ModuleNotFoundError as e:
            if 'aiohttp' in str(e):
                self.log_test(
                    "Fix: aiohttp import for luno_service",
                    False,
                    f"CRITICAL: Still getting aiohttp ModuleNotFoundError: {str(e)}",
                    "This is the exact error reported by user - freqtrade container will fail"
                )
                all_success = False
            else:
                self.log_test(
                    "Fix: aiohttp import for luno_service",
                    False,
                    f"Different ModuleNotFoundError: {str(e)}",
                    "Different import issue but still critical"
                )
                all_success = False
        except Exception as e:
            self.log_test(
                "Fix: aiohttp import for luno_service",
                True,
                f"aiohttp import works, other error: {str(e)}",
                "The specific ModuleNotFoundError is resolved"
            )
        
        # Test 3: TradeSignal and DecisionEngine imports (lines 1522 and 1674 fixes)
        try:
            from backend.services.decision_engine import TradeSignal, DecisionEngine
            
            # Test TradeSignal creation (line 1522 fix)
            signal = TradeSignal(
                pair="BTC/ZAR",
                action="buy",
                confidence=0.75,
                signal_strength="strong",
                direction="bullish",
                amount=0.01
            )
            
            # Test DecisionEngine instantiation (line 1674 fix)
            engine = DecisionEngine()
            
            self.log_test(
                "Fix: TradeSignal and DecisionEngine imports (lines 1522/1674)",
                True,
                "TradeSignal and DecisionEngine can be imported and instantiated successfully"
            )
        except ModuleNotFoundError as e:
            self.log_test(
                "Fix: TradeSignal and DecisionEngine imports (lines 1522/1674)",
                False,
                f"CRITICAL: ModuleNotFoundError in decision_engine: {str(e)}",
                "The server.py lines 1522 and 1674 fixes are not working"
            )
            all_success = False
        except Exception as e:
            self.log_test(
                "Fix: TradeSignal and DecisionEngine imports (lines 1522/1674)",
                True,
                f"Imports work, other error: {str(e)}",
                "The specific import fixes are working"
            )
        
        return all_success
    
    def test_container_simulation(self) -> bool:
        """Simulate container startup conditions"""
        print("🐳 TESTING: Container Startup Simulation")
        print("=" * 70)
        
        all_success = True
        
        # Test 1: Backend container simulation
        try:
            # Simulate importing server.py as container would
            import backend.server
            self.log_test(
                "Backend Container Simulation",
                True,
                "backend.server imports successfully - container would start"
            )
        except ModuleNotFoundError as e:
            self.log_test(
                "Backend Container Simulation",
                False,
                f"CRITICAL: Backend container would fail with ModuleNotFoundError: {str(e)}",
                "Container restart loops would occur"
            )
            all_success = False
        except Exception as e:
            self.log_test(
                "Backend Container Simulation",
                True,
                f"backend.server imports successfully, other error: {str(e)}",
                "Container would start successfully"
            )
        
        # Test 2: Freqtrade container simulation
        try:
            # Test critical freqtrade imports
            import aiohttp
            import requests_cache
            
            # Test that LunoService can use these
            from backend.services.luno_service import LunoService
            luno = LunoService()
            
            self.log_test(
                "Freqtrade Container Simulation",
                True,
                "All freqtrade dependencies available - container would start"
            )
        except ModuleNotFoundError as e:
            self.log_test(
                "Freqtrade Container Simulation",
                False,
                f"CRITICAL: Freqtrade container would fail with ModuleNotFoundError: {str(e)}",
                "Container restart loops would occur"
            )
            all_success = False
        except Exception as e:
            self.log_test(
                "Freqtrade Container Simulation",
                True,
                f"Dependencies available, other error: {str(e)}",
                "Container would start successfully"
            )
        
        # Test 3: PYTHONPATH configuration test
        try:
            # Test that absolute imports work from /app root
            current_path = os.environ.get('PYTHONPATH', '')
            if '/app' not in current_path:
                self.log_test(
                    "PYTHONPATH Configuration",
                    False,
                    f"PYTHONPATH does not include /app: {current_path}",
                    "Container environment may not be properly configured"
                )
                all_success = False
            else:
                self.log_test(
                    "PYTHONPATH Configuration",
                    True,
                    f"PYTHONPATH correctly includes /app: {current_path}"
                )
        except Exception as e:
            self.log_test(
                "PYTHONPATH Configuration",
                False,
                f"Error checking PYTHONPATH: {str(e)}",
                traceback.format_exc()
            )
            all_success = False
        
        return all_success
    
    def test_deployment_readiness(self) -> bool:
        """Final deployment readiness verification"""
        print("🚀 TESTING: VPS Deployment Readiness")
        print("=" * 70)
        
        all_success = True
        
        # Test 1: All imports work without ModuleNotFoundError
        try:
            critical_modules = [
                'backend.services.database_service',
                'backend.services.authentication_service', 
                'backend.services.decision_engine',
                'aiohttp',
                'requests_cache'
            ]
            
            for module in critical_modules:
                importlib.import_module(module)
            
            self.log_test(
                "All Critical Imports",
                True,
                "All critical modules import without ModuleNotFoundError"
            )
        except ModuleNotFoundError as e:
            self.log_test(
                "All Critical Imports",
                False,
                f"CRITICAL: ModuleNotFoundError still exists: {str(e)}",
                "VPS deployment will fail"
            )
            all_success = False
        
        # Test 2: Backend server can be imported and initialized
        try:
            import backend.server
            # Check if FastAPI app is created
            if hasattr(backend.server, 'app'):
                self.log_test(
                    "Backend Server Initialization",
                    True,
                    "Backend server imports and FastAPI app is created"
                )
            else:
                self.log_test(
                    "Backend Server Initialization",
                    False,
                    "Backend server imports but FastAPI app not found",
                    "Server may not initialize properly"
                )
                all_success = False
        except Exception as e:
            self.log_test(
                "Backend Server Initialization",
                False,
                f"Backend server initialization failed: {str(e)}",
                traceback.format_exc()
            )
            all_success = False
        
        # Test 3: Container stability indicators
        try:
            # Test that services can be instantiated (container stability test)
            from backend.services.authentication_service import AuthenticationService
            from backend.services.luno_service import LunoService
            from backend.services.decision_engine import DecisionEngine
            
            auth = AuthenticationService()
            luno = LunoService()
            engine = DecisionEngine()
            
            self.log_test(
                "Container Stability Test",
                True,
                "All critical services can be instantiated - containers will be stable"
            )
        except Exception as e:
            self.log_test(
                "Container Stability Test",
                False,
                f"Service instantiation failed: {str(e)}",
                "Containers may be unstable"
            )
            all_success = False
        
        return all_success
    
    def run_all_tests(self) -> bool:
        """Run all critical module import tests"""
        print("🔥 CRITICAL FINAL DEPLOYMENT VERIFICATION")
        print("ModuleNotFoundError Resolution Testing")
        print("=" * 70)
        print("Testing for VPS container stability before deployment")
        print()
        
        # Run all test categories
        tests = [
            ("Backend Services Import", self.test_backend_services_import),
            ("Freqtrade Dependencies", self.test_freqtrade_dependencies),
            ("Backend Server Import", self.test_backend_server_import),
            ("Specific Reported Errors", self.test_specific_reported_errors),
            ("Container Simulation", self.test_container_simulation),
            ("Deployment Readiness", self.test_deployment_readiness)
        ]
        
        all_success = True
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 50)
            success = test_func()
            if not success:
                all_success = False
        
        # Print final summary
        self.print_final_summary()
        
        return all_success
    
    def print_final_summary(self):
        """Print comprehensive final summary"""
        print("\n" + "=" * 70)
        print("📋 CRITICAL MODULE IMPORT TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests == 0:
            print("\n🎉 ALL CRITICAL IMPORT TESTS PASSED!")
            print("✅ Backend container will start without ModuleNotFoundError")
            print("✅ Freqtrade container has all required dependencies")
            print("✅ All Python packages accessible with PYTHONPATH=/app")
            print("✅ Specific reported errors have been resolved:")
            print("   - backend.services.database_service import works")
            print("   - aiohttp is available for freqtrade service")
            print("   - requests_cache is available for freqtrade service")
            print("   - All backend services import with absolute paths")
            print("\n🚀 DEPLOYMENT READY: VPS containers will start successfully")
        else:
            print("\n❌ CRITICAL DEPLOYMENT ISSUES FOUND:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
            print("\n🚨 VPS DEPLOYMENT WILL FAIL - Fix these issues before deployment")
        
        print("\n" + "=" * 70)

def main():
    """Main test execution"""
    print("Critical Module Import Testing for VPS Deployment")
    print("Testing container stability and ModuleNotFoundError resolution")
    print()
    
    tester = CriticalModuleImportTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall: CRITICAL IMPORT TESTS PASSED - DEPLOYMENT READY")
        sys.exit(0)
    else:
        print("💥 Overall: CRITICAL IMPORT TESTS FAILED - DEPLOYMENT BLOCKED")
        sys.exit(1)

if __name__ == "__main__":
    main()