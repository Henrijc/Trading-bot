#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for AI Crypto Trading Bot
Tests all endpoints and functionality
"""

import requests
import sys
import json
from datetime import datetime
import time

class CryptoTradingBotTester:
    def __init__(self, base_url="https://c4f8c171-e749-4803-818b-d36ffd3514cb.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = "secure_token_123"  # From backend .env
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def run_test(self, name, method, endpoint, expected_status=200, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        
        # Default headers
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)
        
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
                if success:
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
            except:
                response_data = response.text[:200] if response.text else "No response body"
                print(f"   Response Text: {response_data}")
            
            self.log_test(name, success, 
                         f"Expected {expected_status}, got {response.status_code}", 
                         response_data)
            
            return success, response_data

        except requests.exceptions.Timeout:
            self.log_test(name, False, "Request timeout (30s)")
            return False, {}
        except requests.exceptions.ConnectionError:
            self.log_test(name, False, "Connection error - service may be down")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "")

    def test_health_check(self):
        """Test health check endpoint"""
        return self.run_test("Health Check", "GET", "health")

    def test_balance(self):
        """Test balance endpoint"""
        return self.run_test("Account Balance", "GET", "balance")

    def test_market_data(self):
        """Test market data endpoint"""
        return self.run_test("Market Data XBTZAR", "GET", "market-data/XBTZAR")

    def test_performance_metrics(self):
        """Test performance metrics endpoint"""
        return self.run_test("Performance Metrics", "GET", "performance")

    def test_goals_probability(self):
        """Test goals probability endpoint"""
        return self.run_test("Goals Probability", "GET", "goals/probability")

    def test_ai_strategy_status(self):
        """Test AI strategy status endpoint"""
        return self.run_test("AI Strategy Status", "GET", "ai-strategy/status")

    def test_trade_history(self):
        """Test trade history endpoint"""
        return self.run_test("Trade History", "GET", "trades/history")

    def test_crypto_prices(self):
        """Test crypto prices endpoint (NEW in Phase 3)"""
        success, response_data = self.run_test("Crypto Prices", "GET", "crypto-prices")
        
        # Additional validation for crypto prices response format
        if success and response_data:
            expected_cryptos = ["BTC", "ETH", "HBAR", "XRP", "ADA", "TRX", "XLM", "DOGE"]
            data = response_data.get('data', {})
            
            missing_cryptos = [crypto for crypto in expected_cryptos if crypto not in data]
            if missing_cryptos:
                print(f"   ⚠️  Missing crypto prices: {missing_cryptos}")
            
            if 'USD_TO_ZAR' not in data:
                print(f"   ⚠️  Missing USD_TO_ZAR conversion rate")
            
            if 'timestamp' not in response_data:
                print(f"   ⚠️  Missing timestamp in response")
                
            print(f"   📊 Found prices for: {list(data.keys())}")
        
        return success, response_data

    def test_trading_signals(self):
        """Test trading signals endpoint"""
        success, response_data = self.run_test("Trading Signals", "GET", "trading-signals", expected_status=200)
        
        # Note: This endpoint may return 500 due to FreqTrade being disabled - this is expected
        if not success and response_data:
            print(f"   ℹ️  Trading signals may be unavailable due to FreqTrade being disabled (expected)")
        
        return success, response_data

    def test_ai_strategy_configure(self):
        """Test AI strategy configuration (requires auth)"""
        headers = {'Authorization': f'Bearer {self.token}'}
        config_data = {
            "daily_target_zar": 1000.0,
            "max_daily_risk_percent": 2.0,
            "allocation_scalping_percent": 60.0,
            "allocation_accumulation_percent": 40.0,
            "max_open_trades": 5,
            "stop_loss_percent": 1.5,
            "take_profit_percent": 3.0
        }
        return self.run_test("AI Strategy Configure", "POST", "ai-strategy/configure", 
                           expected_status=200, data=config_data, headers=headers)

    def test_trading_start(self):
        """Test start automated trading (requires auth)"""
        headers = {'Authorization': f'Bearer {self.token}'}
        return self.run_test("Start Automated Trading", "POST", "trading/start", 
                           expected_status=200, headers=headers)

    def test_trading_stop(self):
        """Test stop automated trading (requires auth)"""
        headers = {'Authorization': f'Bearer {self.token}'}
        return self.run_test("Stop Automated Trading", "POST", "trading/stop", 
                           expected_status=200, headers=headers)

    def test_manual_trade(self):
        """Test manual trade execution (requires auth)"""
        headers = {'Authorization': f'Bearer {self.token}'}
        trade_data = {
            "pair": "XBTZAR",
            "side": "buy",
            "amount": 0.001,
            "order_type": "market"
        }
        return self.run_test("Manual Trade Execution", "POST", "trade", 
                           expected_status=200, data=trade_data, headers=headers)

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("🚀 STARTING AI CRYPTO TRADING BOT BACKEND TESTS")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Test started at: {datetime.now()}")
        
        # Basic endpoint tests (no auth required)
        print("\n📋 TESTING PUBLIC ENDPOINTS")
        print("-" * 40)
        
        self.test_root_endpoint()
        self.test_health_check()
        self.test_balance()
        self.test_market_data()
        self.test_crypto_prices()  # NEW: Test crypto prices endpoint
        self.test_trading_signals()  # Test trading signals endpoint
        self.test_performance_metrics()
        self.test_goals_probability()
        self.test_ai_strategy_status()
        self.test_trade_history()
        
        # Authenticated endpoint tests
        print("\n🔐 TESTING AUTHENTICATED ENDPOINTS")
        print("-" * 40)
        
        self.test_ai_strategy_configure()
        self.test_trading_start()
        self.test_trading_stop()
        
        # Note: Manual trade test is commented out to avoid actual trading
        # self.test_manual_trade()
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # Show critical service status
        health_test = next((test for test in self.test_results if test['test'] == 'Health Check'), None)
        if health_test and health_test['success'] and health_test['response_data']:
            print("\n🏥 SERVICE HEALTH STATUS:")
            services = health_test['response_data'].get('services', {})
            for service, status in services.items():
                status_icon = "✅" if status in ['connected', 'running'] else "❌"
                print(f"   {status_icon} {service.capitalize()}: {status}")
        
        print(f"\nTest completed at: {datetime.now()}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = CryptoTradingBotTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())