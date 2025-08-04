#!/usr/bin/env python3
"""
Deployment Verification Test for AI Crypto Trading Coach Backend
Testing core functionality after deployment fixes
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://0cfbd3ed-dae1-446a-a9cf-a2c7cbb1213a.preview.emergentagent.com/api"

class DeploymentVerificationTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 15
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        print()
    
    def test_health_check(self):
        """Test 1: Health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', '')
                self.log_test("Health Check Endpoint", True, f"API responding: {message}")
                return True
            else:
                self.log_test("Health Check Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check Endpoint", False, f"Connection error: {str(e)}")
            return False
    
    def test_authentication_login(self):
        """Test 2: Authentication login endpoint"""
        try:
            # Test with valid credentials from .env
            login_data = {
                "username": "Henrijc",
                "password": "H3nj3n",
                "backup_code": "0D6CCC6A"  # First backup code from .env
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data and 'user_data' in data:
                    self.log_test("Authentication Login", True, "Login successful with JWT token")
                    return True
                else:
                    self.log_test("Authentication Login", False, "Missing token or user_data in response")
                    return False
            else:
                self.log_test("Authentication Login", False, f"Status code: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Login", False, f"Error: {str(e)}")
            return False
    
    def test_ai_chat_endpoint(self):
        """Test 3: AI service chat endpoint"""
        try:
            chat_data = {
                "session_id": "test_session_123",
                "message": "What's the current BTC price?",
                "context": None
            }
            
            response = self.session.post(f"{self.base_url}/chat/send", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'role' in data:
                    message_length = len(data.get('message', ''))
                    self.log_test("AI Chat Endpoint", True, f"AI responded with {message_length} characters")
                    return True
                else:
                    self.log_test("AI Chat Endpoint", False, "Missing message or role in response")
                    return False
            else:
                self.log_test("AI Chat Endpoint", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("AI Chat Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_trading_service_endpoints(self):
        """Test 4: Trading service endpoints"""
        try:
            # Test portfolio endpoint
            response = self.session.get(f"{self.base_url}/portfolio")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    self.log_test("Trading Service - Portfolio", True, "Portfolio data retrieved successfully")
                    portfolio_success = True
                else:
                    self.log_test("Trading Service - Portfolio", False, "Invalid portfolio data format")
                    portfolio_success = False
            else:
                self.log_test("Trading Service - Portfolio", False, f"Portfolio endpoint status: {response.status_code}")
                portfolio_success = False
            
            # Test market data endpoint
            response = self.session.get(f"{self.base_url}/market/data")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    self.log_test("Trading Service - Market Data", True, "Market data retrieved successfully")
                    market_success = True
                else:
                    self.log_test("Trading Service - Market Data", False, "Invalid market data format")
                    market_success = False
            else:
                self.log_test("Trading Service - Market Data", False, f"Market data endpoint status: {response.status_code}")
                market_success = False
            
            return portfolio_success and market_success
                
        except Exception as e:
            self.log_test("Trading Service Endpoints", False, f"Error: {str(e)}")
            return False
    
    def test_database_connectivity(self):
        """Test 5: Database connectivity via target settings"""
        try:
            # Test getting target settings (requires DB connection)
            response = self.session.get(f"{self.base_url}/targets/settings")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'user_id' in data:
                    self.log_test("Database Connectivity", True, "Database connection working - target settings retrieved")
                    return True
                else:
                    self.log_test("Database Connectivity", False, "Invalid target settings response format")
                    return False
            else:
                self.log_test("Database Connectivity", False, f"Target settings endpoint status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Database Connectivity", False, f"Error: {str(e)}")
            return False
    
    def test_technical_analysis_endpoints(self):
        """Test 6: Technical analysis endpoints"""
        try:
            # Test technical signals endpoint
            response = self.session.get(f"{self.base_url}/technical/signals/BTC")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    self.log_test("Technical Analysis", True, "Technical analysis endpoint working")
                    return True
                else:
                    self.log_test("Technical Analysis", False, "Invalid technical analysis response")
                    return False
            else:
                self.log_test("Technical Analysis", False, f"Technical analysis status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Technical Analysis", False, f"Error: {str(e)}")
            return False
    
    def test_backtesting_endpoints(self):
        """Test 7: Backtesting system endpoints"""
        try:
            # Test backtest health endpoint
            response = self.session.get(f"{self.base_url}/backtest/health")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    self.log_test("Backtesting System", True, "Backtesting endpoints accessible")
                    return True
                else:
                    self.log_test("Backtesting System", False, "Invalid backtest health response")
                    return False
            else:
                self.log_test("Backtesting System", False, f"Backtest health status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Backtesting System", False, f"Error: {str(e)}")
            return False
    
    def test_bot_control_endpoints(self):
        """Test 8: Bot control endpoints"""
        try:
            # Test bot status endpoint
            response = self.session.get(f"{self.base_url}/bot/status")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    self.log_test("Bot Control System", True, "Bot control endpoints accessible")
                    return True
                else:
                    self.log_test("Bot Control System", False, "Invalid bot status response")
                    return False
            else:
                self.log_test("Bot Control System", False, f"Bot status endpoint status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Bot Control System", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all deployment verification tests"""
        print("🚀 AI Crypto Trading Coach - Deployment Verification Tests")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print()
        
        # Run all tests
        tests = [
            self.test_health_check,
            self.test_authentication_login,
            self.test_ai_chat_endpoint,
            self.test_trading_service_endpoints,
            self.test_database_connectivity,
            self.test_technical_analysis_endpoints,
            self.test_backtesting_endpoints,
            self.test_bot_control_endpoints
        ]
        
        for test in tests:
            test()
        
        # Summary
        self.print_summary()
        return self.get_overall_success()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 70)
        print("📋 DEPLOYMENT VERIFICATION SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print("\n🎉 ALL DEPLOYMENT VERIFICATION TESTS PASSED!")
            print("✅ Backend is fully functional after deployment fixes")
        
        print("=" * 70)
    
    def get_overall_success(self) -> bool:
        """Get overall test success status"""
        if not self.test_results:
            return False
        
        passed = len([r for r in self.test_results if r['success']])
        total = len(self.test_results)
        
        return passed == total

def main():
    """Main test execution"""
    print("Deployment Verification Testing for AI Crypto Trading Coach Backend")
    print()
    
    tester = DeploymentVerificationTester(BACKEND_URL)
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall: DEPLOYMENT VERIFICATION PASSED")
        sys.exit(0)
    else:
        print("💥 Overall: DEPLOYMENT VERIFICATION FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()