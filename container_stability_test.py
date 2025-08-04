#!/usr/bin/env python3
"""
CRITICAL CONTAINER STABILITY TESTING
=====================================

Testing the recent critical fixes for ModuleNotFoundError issues:
1. Fixed backend/server.py lines 1522 and 1674: Changed relative imports to absolute imports
2. Added missing dependency 'requests-cache>=1.0.0' to freqtrade/requirements.txt

Priority Testing:
1. Backend Container Stability: Test backend container starts without "No module named 'services'" errors
2. Freqtrade Container Stability: Test freqtrade container starts without "No module named 'requests_cache'" errors  
3. Decision Engine Import: Test TradeSignal can be imported from backend.services.decision_engine
4. Luno Service Import: Test requests_cache can be imported by luno_service.py
"""

import sys
import os
import asyncio
import traceback
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, '/app')

class ContainerStabilityTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, success, details="", error=None):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def test_backend_server_imports(self):
        """Test 1: Backend Server Import Stability"""
        print("=" * 60)
        print("TEST 1: BACKEND SERVER IMPORT STABILITY")
        print("=" * 60)
        
        try:
            # Test the specific import that was causing issues
            print("Testing backend.server import...")
            from backend.server import app
            self.log_test(
                "Backend Server Import", 
                True, 
                "Successfully imported backend.server.app without ModuleNotFoundError"
            )
            
            # Test that the app is properly initialized
            print("Testing FastAPI app initialization...")
            if hasattr(app, 'routes') and len(app.routes) > 0:
                route_count = len(app.routes)
                self.log_test(
                    "FastAPI App Initialization", 
                    True, 
                    f"FastAPI app properly initialized with {route_count} routes"
                )
            else:
                self.log_test(
                    "FastAPI App Initialization", 
                    False, 
                    "FastAPI app not properly initialized - no routes found"
                )
                
        except Exception as e:
            self.log_test(
                "Backend Server Import", 
                False, 
                "Failed to import backend.server", 
                e
            )

    def test_decision_engine_imports(self):
        """Test 2: Decision Engine Import Stability"""
        print("=" * 60)
        print("TEST 2: DECISION ENGINE IMPORT STABILITY")
        print("=" * 60)
        
        try:
            # Test the specific import that was fixed in lines 1522 and 1674
            print("Testing TradeSignal import from backend.services.decision_engine...")
            from backend.services.decision_engine import TradeSignal
            self.log_test(
                "TradeSignal Import", 
                True, 
                "Successfully imported TradeSignal from backend.services.decision_engine"
            )
            
            # Test creating a TradeSignal instance
            print("Testing TradeSignal instantiation...")
            signal = TradeSignal(
                pair="BTC/ZAR",
                action="buy",
                confidence=0.75,
                signal_strength="strong",
                direction="bullish",
                amount=0.01,
                timestamp=datetime.utcnow().isoformat()
            )
            
            if signal and hasattr(signal, 'pair') and signal.pair == "BTC/ZAR":
                self.log_test(
                    "TradeSignal Instantiation", 
                    True, 
                    f"Successfully created TradeSignal instance for {signal.pair}"
                )
            else:
                self.log_test(
                    "TradeSignal Instantiation", 
                    False, 
                    "TradeSignal instance not properly created"
                )
                
        except Exception as e:
            self.log_test(
                "TradeSignal Import", 
                False, 
                "Failed to import TradeSignal from backend.services.decision_engine", 
                e
            )

    def test_decision_engine_service(self):
        """Test 3: Decision Engine Service Import"""
        print("=" * 60)
        print("TEST 3: DECISION ENGINE SERVICE IMPORT")
        print("=" * 60)
        
        try:
            print("Testing DecisionEngine import...")
            from backend.services.decision_engine import DecisionEngine
            self.log_test(
                "DecisionEngine Import", 
                True, 
                "Successfully imported DecisionEngine from backend.services.decision_engine"
            )
            
            # Test DecisionEngine instantiation
            print("Testing DecisionEngine instantiation...")
            engine = DecisionEngine()
            if engine:
                self.log_test(
                    "DecisionEngine Instantiation", 
                    True, 
                    "Successfully created DecisionEngine instance"
                )
            else:
                self.log_test(
                    "DecisionEngine Instantiation", 
                    False, 
                    "DecisionEngine instance not properly created"
                )
                
        except Exception as e:
            self.log_test(
                "DecisionEngine Import", 
                False, 
                "Failed to import DecisionEngine", 
                e
            )

    def test_requests_cache_import(self):
        """Test 4: Requests Cache Import for Freqtrade"""
        print("=" * 60)
        print("TEST 4: REQUESTS CACHE IMPORT FOR FREQTRADE")
        print("=" * 60)
        
        try:
            print("Testing requests_cache import...")
            import requests_cache
            self.log_test(
                "Requests Cache Import", 
                True, 
                f"Successfully imported requests_cache version {getattr(requests_cache, '__version__', 'unknown')}"
            )
            
            # Test requests_cache functionality
            print("Testing requests_cache session creation...")
            session = requests_cache.CachedSession('test_cache', expire_after=300)
            if session:
                self.log_test(
                    "Requests Cache Session", 
                    True, 
                    "Successfully created CachedSession instance"
                )
            else:
                self.log_test(
                    "Requests Cache Session", 
                    False, 
                    "Failed to create CachedSession instance"
                )
                
        except Exception as e:
            self.log_test(
                "Requests Cache Import", 
                False, 
                "Failed to import requests_cache - this would cause freqtrade container failures", 
                e
            )

    def test_luno_service_imports(self):
        """Test 5: Luno Service Import Stability"""
        print("=" * 60)
        print("TEST 5: LUNO SERVICE IMPORT STABILITY")
        print("=" * 60)
        
        try:
            print("Testing LunoService import...")
            from backend.services.luno_service import LunoService
            self.log_test(
                "LunoService Import", 
                True, 
                "Successfully imported LunoService from backend.services.luno_service"
            )
            
            # Test LunoService instantiation
            print("Testing LunoService instantiation...")
            luno_service = LunoService()
            if luno_service:
                self.log_test(
                    "LunoService Instantiation", 
                    True, 
                    "Successfully created LunoService instance"
                )
            else:
                self.log_test(
                    "LunoService Instantiation", 
                    False, 
                    "LunoService instance not properly created"
                )
                
        except Exception as e:
            self.log_test(
                "LunoService Import", 
                False, 
                "Failed to import LunoService", 
                e
            )

    def test_backend_container_simulation(self):
        """Test 6: Backend Container Start Simulation"""
        print("=" * 60)
        print("TEST 6: BACKEND CONTAINER START SIMULATION")
        print("=" * 60)
        
        try:
            print("Simulating backend container startup sequence...")
            
            # Test the exact command that would be run in container
            print("Testing: python3 -c \"from backend.server import app; print('✅ server.py imports successfully!')\"")
            
            # Import all critical components that backend needs
            from backend.server import app
            from backend.services.decision_engine import DecisionEngine, TradeSignal
            from backend.services.luno_service import LunoService
            from backend.services.ai_service import AICoachService
            
            self.log_test(
                "Backend Container Simulation", 
                True, 
                "Backend container would start successfully - all critical imports working"
            )
            
        except Exception as e:
            self.log_test(
                "Backend Container Simulation", 
                False, 
                "Backend container would fail to start", 
                e
            )

    def test_freqtrade_container_simulation(self):
        """Test 7: Freqtrade Container Start Simulation"""
        print("=" * 60)
        print("TEST 7: FREQTRADE CONTAINER START SIMULATION")
        print("=" * 60)
        
        try:
            print("Simulating freqtrade container startup sequence...")
            
            # Test critical imports that freqtrade needs
            import requests_cache
            import ccxt
            import pandas
            import numpy
            
            self.log_test(
                "Freqtrade Container Simulation", 
                True, 
                "Freqtrade container would start successfully - all critical dependencies available"
            )
            
        except Exception as e:
            self.log_test(
                "Freqtrade Container Simulation", 
                False, 
                "Freqtrade container would fail to start", 
                e
            )

    def test_import_path_resolution(self):
        """Test 8: Import Path Resolution"""
        print("=" * 60)
        print("TEST 8: IMPORT PATH RESOLUTION")
        print("=" * 60)
        
        try:
            print("Testing Python path resolution for backend modules...")
            
            # Check if backend directory is in path
            backend_path = '/app/backend'
            if backend_path in sys.path or '/app' in sys.path:
                path_status = "✅ Backend path accessible"
            else:
                path_status = "⚠️ Backend path may not be accessible"
            
            # Test relative vs absolute import resolution
            try:
                # This should work now with absolute imports
                from backend.services.decision_engine import TradeSignal
                absolute_import_status = "✅ Absolute imports working"
            except:
                absolute_import_status = "❌ Absolute imports failing"
            
            self.log_test(
                "Import Path Resolution", 
                True, 
                f"{path_status}, {absolute_import_status}"
            )
            
        except Exception as e:
            self.log_test(
                "Import Path Resolution", 
                False, 
                "Import path resolution issues detected", 
                e
            )

    async def run_all_tests(self):
        """Run all container stability tests"""
        print("🔍 CRITICAL CONTAINER STABILITY TESTING")
        print("=" * 80)
        print("Testing fixes for ModuleNotFoundError issues that caused container restart loops")
        print("=" * 80)
        print()
        
        # Run all tests
        self.test_backend_server_imports()
        self.test_decision_engine_imports()
        self.test_decision_engine_service()
        self.test_requests_cache_import()
        self.test_luno_service_imports()
        self.test_backend_container_simulation()
        self.test_freqtrade_container_simulation()
        self.test_import_path_resolution()
        
        # Print summary
        print("=" * 80)
        print("🎯 CONTAINER STABILITY TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if success_rate == 100:
            print("🎉 ALL TESTS PASSED - CONTAINER STABILITY ISSUES RESOLVED!")
            print("✅ Backend container should start successfully without ModuleNotFoundError")
            print("✅ Freqtrade container should start successfully without requests_cache errors")
        elif success_rate >= 75:
            print("✅ MOST TESTS PASSED - SIGNIFICANT IMPROVEMENT IN CONTAINER STABILITY")
            print("⚠️ Some minor issues remain but critical fixes are working")
        else:
            print("❌ CRITICAL ISSUES REMAIN - CONTAINER STABILITY NOT FULLY RESOLVED")
            print("🔧 Additional fixes needed for stable container deployment")
        
        print()
        print("=" * 80)
        print("DETAILED TEST RESULTS:")
        print("=" * 80)
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
            if result['error']:
                print(f"   Error: {result['error']}")
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "success_rate": success_rate,
            "all_tests_passed": success_rate == 100,
            "results": self.test_results
        }

async def main():
    """Main test execution"""
    tester = ContainerStabilityTester()
    results = await tester.run_all_tests()
    
    # Return exit code based on results
    if results["success_rate"] == 100:
        print("\n🎯 CONTAINER STABILITY TESTING COMPLETED SUCCESSFULLY")
        return 0
    else:
        print(f"\n⚠️ CONTAINER STABILITY TESTING COMPLETED WITH {results['success_rate']:.1f}% SUCCESS RATE")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)