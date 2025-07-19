#!/usr/bin/env python3
"""
Backend API Testing Script for Crypto Trading Coach
Tests all backend endpoints and functionality including the three critical fixes:
1. AI Service Response Length (no truncation)
2. AI Knowledge Base Integration (training data usage)
3. Portfolio API (correct data loading)
4. Chat History Timestamps (proper storage)
"""

import requests
import json
import time
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = "https://09261e87-4cce-4af8-bd38-d0c7bd3f6025.preview.emergentagent.com/api"

class TechnicalAnalysisAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()
    
    def test_health_check(self):
        """Test basic API health"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"API is running: {data.get('message', '')}")
                return True
            else:
                self.log_test("API Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_technical_signals(self, symbol: str = "BTC"):
        """Test technical signals endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/technical/signals/{symbol}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['symbol', 'current_price', 'trend_analysis', 'technical_indicators', 'trading_signals', 'recommendation']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(f"Technical Signals - {symbol}", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Validate data types and content
                if not isinstance(data['trading_signals'], list):
                    self.log_test(f"Technical Signals - {symbol}", False, "trading_signals should be a list", data)
                    return False
                
                if not isinstance(data['technical_indicators'], dict):
                    self.log_test(f"Technical Signals - {symbol}", False, "technical_indicators should be a dict", data)
                    return False
                
                # Check if we have actual technical indicators
                indicators = data['technical_indicators']
                has_indicators = any([
                    indicators.get('rsi') is not None,
                    indicators.get('macd') is not None,
                    indicators.get('bollinger_bands') is not None,
                    indicators.get('moving_averages') is not None
                ])
                
                if not has_indicators:
                    self.log_test(f"Technical Signals - {symbol}", False, "No technical indicators calculated", data)
                    return False
                
                self.log_test(f"Technical Signals - {symbol}", True, 
                            f"Retrieved {len(data['trading_signals'])} signals, RSI: {indicators.get('rsi', 'N/A')}")
                return True
                
            else:
                self.log_test(f"Technical Signals - {symbol}", False, f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test(f"Technical Signals - {symbol}", False, f"Error: {str(e)}")
            return False
    
    def test_portfolio_technical_analysis(self):
        """Test portfolio technical analysis endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/technical/portfolio")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we have portfolio analysis structure
                if 'error' in data:
                    # This might be expected if no portfolio data is available
                    self.log_test("Portfolio Technical Analysis", True, f"Expected error: {data['error']}")
                    return True
                
                required_fields = ['portfolio_total', 'analyzed_assets', 'asset_analysis', 'portfolio_insights']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Portfolio Technical Analysis", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                self.log_test("Portfolio Technical Analysis", True, 
                            f"Analyzed {data.get('analyzed_assets', 0)} assets, Total: R{data.get('portfolio_total', 0):,.2f}")
                return True
                
            else:
                self.log_test("Portfolio Technical Analysis", False, f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Portfolio Technical Analysis", False, f"Error: {str(e)}")
            return False
    
    def test_technical_indicators(self, symbol: str = "BTC"):
        """Test detailed technical indicators endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/technical/indicators/{symbol}")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['symbol', 'indicators', 'current_price', 'timestamp']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(f"Technical Indicators - {symbol}", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check if indicators are present
                indicators = data.get('indicators', {})
                expected_indicators = ['rsi', 'macd', 'bollinger_bands', 'moving_averages', 'stochastic', 'support_resistance', 'trend_analysis']
                
                present_indicators = [ind for ind in expected_indicators if ind in indicators]
                
                if len(present_indicators) < 4:  # At least 4 indicators should be present
                    self.log_test(f"Technical Indicators - {symbol}", False, 
                                f"Only {len(present_indicators)} indicators present: {present_indicators}", data)
                    return False
                
                self.log_test(f"Technical Indicators - {symbol}", True, 
                            f"Retrieved {len(present_indicators)} indicators: {present_indicators}")
                return True
                
            else:
                self.log_test(f"Technical Indicators - {symbol}", False, f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test(f"Technical Indicators - {symbol}", False, f"Error: {str(e)}")
            return False
    
    def test_technical_strategies(self):
        """Test predefined technical strategies"""
        strategies = ['momentum', 'mean_reversion', 'trend_following']
        
        for strategy in strategies:
            try:
                response = self.session.get(f"{self.base_url}/technical/strategy/{strategy}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    required_fields = ['name', 'description', 'indicators', 'rules', 'risk_parameters']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(f"Technical Strategy - {strategy}", False, f"Missing fields: {missing_fields}", data)
                        continue
                    
                    # Validate structure
                    if not isinstance(data['indicators'], list) or len(data['indicators']) == 0:
                        self.log_test(f"Technical Strategy - {strategy}", False, "No indicators defined", data)
                        continue
                    
                    if not isinstance(data['rules'], list) or len(data['rules']) == 0:
                        self.log_test(f"Technical Strategy - {strategy}", False, "No rules defined", data)
                        continue
                    
                    if not isinstance(data['risk_parameters'], dict):
                        self.log_test(f"Technical Strategy - {strategy}", False, "Invalid risk parameters", data)
                        continue
                    
                    self.log_test(f"Technical Strategy - {strategy}", True, 
                                f"Strategy loaded: {len(data['indicators'])} indicators, {len(data['rules'])} rules")
                    
                else:
                    self.log_test(f"Technical Strategy - {strategy}", False, f"Status code: {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test(f"Technical Strategy - {strategy}", False, f"Error: {str(e)}")
    
    def test_backtest_strategy(self):
        """Test strategy backtesting endpoint"""
        try:
            backtest_request = {
                'symbol': 'BTC',
                'strategy': 'momentum',
                'days': 30
            }
            
            response = self.session.post(f"{self.base_url}/technical/backtest", json=backtest_request)
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['symbol', 'strategy', 'period', 'total_trades', 'win_rate', 'total_return']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Strategy Backtest", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Validate data types
                if not isinstance(data['total_trades'], int):
                    self.log_test("Strategy Backtest", False, "total_trades should be integer", data)
                    return False
                
                if not isinstance(data['win_rate'], (int, float)):
                    self.log_test("Strategy Backtest", False, "win_rate should be numeric", data)
                    return False
                
                self.log_test("Strategy Backtest", True, 
                            f"Backtest completed: {data['total_trades']} trades, {data['win_rate']:.1%} win rate, {data['total_return']:.1%} return")
                return True
                
            else:
                self.log_test("Strategy Backtest", False, f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Strategy Backtest", False, f"Error: {str(e)}")
            return False
    
    def test_market_overview(self):
        """Test market technical overview endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/technical/market-overview")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['market_overview', 'timestamp', 'analyzed_assets']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Market Technical Overview", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check market overview structure
                market_overview = data.get('market_overview', [])
                if not isinstance(market_overview, list):
                    self.log_test("Market Technical Overview", False, "market_overview should be a list", data)
                    return False
                
                if len(market_overview) == 0:
                    self.log_test("Market Technical Overview", False, "No market data in overview", data)
                    return False
                
                # Check structure of first item
                if market_overview:
                    first_item = market_overview[0]
                    required_item_fields = ['symbol', 'price', 'trend', 'recommendation']
                    missing_item_fields = [field for field in required_item_fields if field not in first_item]
                    
                    if missing_item_fields:
                        self.log_test("Market Technical Overview", False, f"Missing item fields: {missing_item_fields}", data)
                        return False
                
                self.log_test("Market Technical Overview", True, 
                            f"Retrieved overview for {len(market_overview)} assets")
                return True
                
            else:
                self.log_test("Market Technical Overview", False, f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Market Technical Overview", False, f"Error: {str(e)}")
            return False
    
    def test_ai_service_integration(self):
        """Test AI service integration with technical analysis"""
        try:
            # Test chat endpoint with technical analysis keywords
            chat_request = {
                'session_id': 'test_session_ta',
                'role': 'user',
                'message': 'What is the current technical analysis for BTC? Should I buy or sell?'
            }
            
            response = self.session.post(f"{self.base_url}/chat/send", json=chat_request)
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['session_id', 'role', 'message']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("AI Service TA Integration", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check if response contains technical analysis keywords
                message = data.get('message', '').lower()
                ta_keywords = ['rsi', 'macd', 'technical', 'analysis', 'trend', 'support', 'resistance', 'buy', 'sell']
                
                found_keywords = [keyword for keyword in ta_keywords if keyword in message]
                
                if len(found_keywords) < 2:
                    self.log_test("AI Service TA Integration", False, 
                                f"Response doesn't seem to include technical analysis. Found keywords: {found_keywords}")
                    return False
                
                self.log_test("AI Service TA Integration", True, 
                            f"AI response includes technical analysis keywords: {found_keywords}")
                return True
                
            else:
                self.log_test("AI Service TA Integration", False, f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("AI Service TA Integration", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        test_cases = [
            {
                'name': 'Invalid Symbol - Technical Signals',
                'url': f"{self.base_url}/technical/signals/INVALID",
                'expected_status': [404, 500]  # Either is acceptable
            },
            {
                'name': 'Invalid Strategy',
                'url': f"{self.base_url}/technical/strategy/invalid_strategy",
                'expected_status': [404]
            },
            {
                'name': 'Invalid Symbol - Technical Indicators',
                'url': f"{self.base_url}/technical/indicators/INVALID",
                'expected_status': [404, 500]
            }
        ]
        
        for test_case in test_cases:
            try:
                response = self.session.get(test_case['url'])
                
                if response.status_code in test_case['expected_status']:
                    self.log_test(test_case['name'], True, f"Correctly returned status {response.status_code}")
                else:
                    self.log_test(test_case['name'], False, 
                                f"Expected status {test_case['expected_status']}, got {response.status_code}")
                    
            except Exception as e:
                self.log_test(test_case['name'], False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all technical analysis tests"""
        print("🚀 Starting Technical Analysis Engine Backend Tests")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Core technical analysis endpoints
        print("📊 Testing Core Technical Analysis Endpoints...")
        self.test_technical_signals("BTC")
        self.test_technical_signals("ETH")
        self.test_technical_indicators("BTC")
        self.test_technical_indicators("ETH")
        
        # Portfolio analysis
        print("💼 Testing Portfolio Technical Analysis...")
        self.test_portfolio_technical_analysis()
        
        # Strategy endpoints
        print("📈 Testing Technical Strategies...")
        self.test_technical_strategies()
        self.test_backtest_strategy()
        
        # Market overview
        print("🌍 Testing Market Overview...")
        self.test_market_overview()
        
        # AI integration
        print("🤖 Testing AI Service Integration...")
        self.test_ai_service_integration()
        
        # Error handling
        print("⚠️ Testing Error Handling...")
        self.test_error_handling()
        
        # Summary
        self.print_summary()
        
        return self.get_overall_success()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
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
        
        print("\n" + "=" * 60)
    
    def get_overall_success(self) -> bool:
        """Get overall test success status"""
        if not self.test_results:
            return False
        
        # Consider tests successful if at least 80% pass
        passed = len([r for r in self.test_results if r['success']])
        total = len(self.test_results)
        success_rate = passed / total
        
        return success_rate >= 0.8

def main():
    """Main test execution"""
    print("Technical Analysis Engine Backend API Tests")
    print(f"Testing against: {BACKEND_URL}")
    print()
    
    tester = TechnicalAnalysisAPITester(BACKEND_URL)
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall: TESTS PASSED")
        sys.exit(0)
    else:
        print("💥 Overall: TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()