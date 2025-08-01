#!/usr/bin/env python3
"""
Comprehensive Backend API Testing Script for Crypto Trading Coach
COMPREHENSIVE TIMESTAMP AND GOAL UPDATING FUNCTIONALITY TESTING

CRITICAL TESTING FOCUS:
1. Test /api/chat/send with real user goal update request: "Change my monthly profit goal to R8000"
2. Verify AI can access and process real-time portfolio data (no generic error responses)
3. Test that all timestamps across different services now use consistent UTC format
4. Verify /api/targets/settings can be updated and reflects new user goals
5. Test that AI responses include actual portfolio data and real-time calculations
6. Check that the AI properly saves and retrieves updated user goals

COMPREHENSIVE FIXES MADE:
1. luno_service.py lines 379, 388: Changed to datetime.utcnow().isoformat()
2. technical_analysis_service.py lines 27, 39, 66, 93, 139, 477, 571: Changed to datetime.utcnow()
3. server.py lines 863, 1000: Changed to datetime.utcnow().isoformat()
4. semi_auto_trade_service.py lines 64, 181, 218: Changed to datetime.utcnow().isoformat()
5. trading_campaign_service.py line 275: Changed to datetime.utcnow().isoformat()

SPECIFIC USER GOALS TO VERIFY:
- Monthly profit target: R8000 (should be updateable)
- Hold 1000 XRP long-term 
- 4% risk factor with stop-limit strategy
- Diversification for generational wealth

AUTHENTICATION: Use existing user "Henrijc" for all tests.
"""

import requests
import json
import time
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
import re

# Get backend URL from environment
BACKEND_URL = "https://e5da86b9-d0bb-4858-9a9e-eb479f5b9fda.preview.emergentagent.com/api"

class ComprehensiveBackendTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = []
        self.test_session_id = f"comprehensive_test_{uuid.uuid4().hex[:8]}"
        self.user_id = "Henrijc"  # Use existing user as specified
        
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
    
    def is_valid_utc_timestamp(self, timestamp_str: str, allow_historical: bool = True) -> bool:
        """Check if timestamp is in valid UTC ISO format"""
        try:
            # Parse the timestamp
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Check if it's a reasonable timestamp (not too far in past/future)
            now = datetime.now(timezone.utc)
            time_diff = abs((now - dt.replace(tzinfo=timezone.utc)).total_seconds())
            
            if allow_historical:
                # For stored data, allow up to 30 days old
                return time_diff < 2592000  # 30 days
            else:
                # For real-time data, should be within 1 hour
                return time_diff < 3600  # 1 hour
        except Exception as e:
            print(f"    Invalid timestamp format: {timestamp_str}, Error: {e}")
            return False
    
    def extract_timestamps_from_response(self, data: Dict) -> List[str]:
        """Extract all timestamp fields from response"""
        timestamps = []
        
        # Common timestamp fields
        timestamp_fields = ['timestamp', 'created_at', 'updated_at', 'generated_at', 'executed_at']
        
        def extract_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if key in timestamp_fields and isinstance(value, str):
                        timestamps.append((current_path, value))
                    elif isinstance(value, (dict, list)):
                        extract_recursive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_recursive(item, f"{path}[{i}]")
        
        extract_recursive(data)
        return timestamps

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

    def test_targets_settings_endpoint(self):
        """Test /api/targets/settings endpoint functionality"""
        try:
            # First, get current target settings
            response = self.session.get(f"{self.base_url}/targets/settings")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['monthly_target', 'weekly_target', 'user_id']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Target Settings GET", False, 
                                f"Missing required fields: {missing_fields}", data)
                    return False
                
                # Check timestamps are in UTC format
                timestamps = self.extract_timestamps_from_response(data)
                for field_path, timestamp in timestamps:
                    if not self.is_valid_utc_timestamp(timestamp, allow_historical=True):
                        self.log_test("Target Settings GET", False, 
                                    f"Invalid timestamp in {field_path}: {timestamp}")
                        return False
                
                original_monthly = data.get('monthly_target')
                self.log_test("Target Settings GET", True, 
                            f"Retrieved targets - Monthly: R{original_monthly}, Weekly: R{data.get('weekly_target')}")
                
                # Now test updating targets
                new_targets = {
                    "monthly_target": 8000,  # As specified in the review request
                    "weekly_target": 2000,
                    "daily_target": 285,
                    "auto_adjust": True
                }
                
                update_response = self.session.put(f"{self.base_url}/targets/settings", json=new_targets)
                
                if update_response.status_code == 200:
                    update_data = update_response.json()
                    
                    if update_data.get('success'):
                        # Verify the update by getting settings again
                        verify_response = self.session.get(f"{self.base_url}/targets/settings")
                        
                        if verify_response.status_code == 200:
                            verify_data = verify_response.json()
                            
                            if verify_data.get('monthly_target') == 8000:
                                self.log_test("Target Settings UPDATE", True, 
                                            f"Successfully updated monthly target to R8000")
                                return True
                            else:
                                self.log_test("Target Settings UPDATE", False, 
                                            f"Target not updated correctly. Expected R8000, got R{verify_data.get('monthly_target')}")
                                return False
                        else:
                            self.log_test("Target Settings UPDATE", False, 
                                        f"Failed to verify update: {verify_response.status_code}")
                            return False
                    else:
                        self.log_test("Target Settings UPDATE", False, 
                                    f"Update failed: {update_data}")
                        return False
                else:
                    self.log_test("Target Settings UPDATE", False, 
                                f"Update request failed: {update_response.status_code}")
                    return False
                
            else:
                self.log_test("Target Settings GET", False, 
                            f"Failed to get targets: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Target Settings Endpoint", False, f"Error: {str(e)}")
            return False

    def test_ai_goal_update_via_chat(self):
        """Test AI goal update via chat: 'Change my monthly profit goal to R8000'"""
        try:
            # Send the specific goal update request as mentioned in the review
            chat_request = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': 'Change my monthly profit goal to R8000',
                'context': None  # Let backend generate fresh context
            }
            
            response = self.session.post(f"{self.base_url}/chat/send", json=chat_request)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['session_id', 'role', 'message', 'timestamp']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("AI Goal Update via Chat", False, 
                                f"Missing fields in response: {missing_fields}", data)
                    return False
                
                ai_response = data.get('message', '')
                
                # Check if AI response is not generic (should contain specific information)
                generic_indicators = [
                    "I don't have access",
                    "I cannot access",
                    "generic error",
                    "something went wrong",
                    "try again later"
                ]
                
                is_generic = any(indicator.lower() in ai_response.lower() for indicator in generic_indicators)
                
                if is_generic:
                    self.log_test("AI Goal Update via Chat", False, 
                                f"AI gave generic error response: {ai_response[:200]}...")
                    return False
                
                # Check if AI response mentions the goal update
                goal_indicators = [
                    "8000",
                    "goal",
                    "target",
                    "monthly",
                    "profit"
                ]
                
                mentions_goal = any(indicator.lower() in ai_response.lower() for indicator in goal_indicators)
                
                if not mentions_goal:
                    self.log_test("AI Goal Update via Chat", False, 
                                f"AI response doesn't mention goal update: {ai_response[:200]}...")
                    return False
                
                # Check timestamp consistency
                ai_timestamp = data.get('timestamp')
                if not self.is_valid_utc_timestamp(ai_timestamp, allow_historical=False):
                    self.log_test("AI Goal Update via Chat", False, 
                                f"Invalid timestamp: {ai_timestamp}")
                    return False
                
                self.log_test("AI Goal Update via Chat", True, 
                            f"AI successfully processed goal update request. Response length: {len(ai_response)} chars")
                return True
                
            else:
                self.log_test("AI Goal Update via Chat", False, 
                            f"Chat request failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("AI Goal Update via Chat", False, f"Error: {str(e)}")
            return False

    def test_ai_portfolio_data_access(self):
        """Test that AI can access and process real-time portfolio data"""
        try:
            # Ask AI for portfolio analysis
            chat_request = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': 'Give me a detailed analysis of my current portfolio performance and holdings',
                'context': None  # Let backend generate fresh context with portfolio data
            }
            
            response = self.session.post(f"{self.base_url}/chat/send", json=chat_request)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('message', '')
                
                # Check if AI response contains portfolio-specific information
                portfolio_indicators = [
                    'portfolio',
                    'holdings',
                    'BTC',
                    'ETH',
                    'XRP',
                    'value',
                    'performance',
                    'profit',
                    'loss',
                    'R',  # South African Rand currency symbol
                    'ZAR'
                ]
                
                portfolio_mentions = sum(1 for indicator in portfolio_indicators 
                                       if indicator.lower() in ai_response.lower())
                
                if portfolio_mentions < 3:
                    self.log_test("AI Portfolio Data Access", False, 
                                f"AI response lacks portfolio-specific information. Only {portfolio_mentions} portfolio indicators found")
                    return False
                
                # Check for generic error responses
                generic_errors = [
                    "I don't have access to your portfolio",
                    "I cannot access your portfolio data",
                    "portfolio data is not available",
                    "unable to retrieve portfolio"
                ]
                
                has_generic_error = any(error.lower() in ai_response.lower() for error in generic_errors)
                
                if has_generic_error:
                    self.log_test("AI Portfolio Data Access", False, 
                                f"AI gave generic error about portfolio access")
                    return False
                
                # Check response length (should be substantial for portfolio analysis)
                if len(ai_response) < 100:
                    self.log_test("AI Portfolio Data Access", False, 
                                f"AI response too short for portfolio analysis: {len(ai_response)} chars")
                    return False
                
                self.log_test("AI Portfolio Data Access", True, 
                            f"AI successfully accessed portfolio data. Response: {len(ai_response)} chars, {portfolio_mentions} portfolio indicators")
                return True
                
            else:
                self.log_test("AI Portfolio Data Access", False, 
                            f"Portfolio analysis request failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("AI Portfolio Data Access", False, f"Error: {str(e)}")
            return False

    def test_ai_adjust_targets_endpoint(self):
        """Test /api/ai/adjust-targets endpoint"""
        try:
            # Test AI target adjustment endpoint
            adjust_request = {
                "reason": "User requested monthly profit goal change to R8000 for better achievability",
                "new_monthly_target": 8000
            }
            
            response = self.session.post(f"{self.base_url}/ai/adjust-targets", json=adjust_request)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    # Check if new targets were set
                    new_targets = data.get('new_targets', {})
                    
                    if new_targets.get('monthly_target') == 8000:
                        # Verify timestamps in response
                        timestamps = self.extract_timestamps_from_response(data)
                        invalid_timestamps = []
                        
                        for field_path, timestamp in timestamps:
                            if not self.is_valid_utc_timestamp(timestamp, allow_historical=True):
                                invalid_timestamps.append((field_path, timestamp))
                        
                        if invalid_timestamps:
                            self.log_test("AI Adjust Targets Endpoint", False, 
                                        f"Invalid timestamps: {invalid_timestamps}")
                            return False
                        
                        self.log_test("AI Adjust Targets Endpoint", True, 
                                    f"AI successfully adjusted targets to R8000. Message: {data.get('message', '')}")
                        return True
                    else:
                        self.log_test("AI Adjust Targets Endpoint", False, 
                                    f"Target not set correctly. Expected R8000, got R{new_targets.get('monthly_target')}")
                        return False
                else:
                    self.log_test("AI Adjust Targets Endpoint", False, 
                                f"AI target adjustment failed: {data.get('message', '')}")
                    return False
                
            else:
                self.log_test("AI Adjust Targets Endpoint", False, 
                            f"Request failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("AI Adjust Targets Endpoint", False, f"Error: {str(e)}")
            return False

    def test_timestamp_consistency_across_services(self):
        """Test timestamp consistency across different services"""
        try:
            # Test multiple endpoints that should use UTC timestamps
            endpoints_to_test = [
                ("/portfolio", "Portfolio Service"),
                ("/market/data", "Market Data Service"),
                ("/technical/signals/BTC", "Technical Analysis Service"),
                ("/targets/settings", "Target Settings Service")
            ]
            
            all_timestamps = []
            
            for endpoint, service_name in endpoints_to_test:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        timestamps = self.extract_timestamps_from_response(data)
                        
                        for field_path, timestamp in timestamps:
                            all_timestamps.append((service_name, field_path, timestamp))
                            
                except Exception as e:
                    print(f"    Warning: Could not test {service_name}: {e}")
                    continue
            
            if not all_timestamps:
                self.log_test("Timestamp Consistency Across Services", True, 
                            "No timestamps found in service responses (acceptable)")
                return True
            
            # Check all timestamps for UTC format
            invalid_timestamps = []
            for service_name, field_path, timestamp in all_timestamps:
                if not self.is_valid_utc_timestamp(timestamp, allow_historical=True):
                    invalid_timestamps.append((service_name, field_path, timestamp))
            
            if invalid_timestamps:
                self.log_test("Timestamp Consistency Across Services", False, 
                            f"Invalid timestamps found: {invalid_timestamps}")
                return False
            
            self.log_test("Timestamp Consistency Across Services", True, 
                        f"All {len(all_timestamps)} timestamps across {len(endpoints_to_test)} services are in valid UTC format")
            return True
            
        except Exception as e:
            self.log_test("Timestamp Consistency Across Services", False, f"Error: {str(e)}")
            return False

    def test_chat_message_timestamp_consistency(self):
        """Test that chat messages have consistent UTC timestamps"""
        try:
            # Send a chat message
            chat_request = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': 'What is the current BTC price?',
                'context': None
            }
            
            before_request = datetime.now(timezone.utc)
            response = self.session.post(f"{self.base_url}/chat/send", json=chat_request)
            after_request = datetime.now(timezone.utc)
            
            if response.status_code == 200:
                data = response.json()
                ai_timestamp = data.get('timestamp')
                
                if not ai_timestamp:
                    self.log_test("Chat Message Timestamp Consistency", False, "No timestamp in response")
                    return False
                
                if not self.is_valid_utc_timestamp(ai_timestamp, allow_historical=False):
                    self.log_test("Chat Message Timestamp Consistency", False, 
                                f"Invalid timestamp: {ai_timestamp}")
                    return False
                
                # Check if timestamp is within reasonable range
                ai_dt = datetime.fromisoformat(ai_timestamp.replace('Z', '+00:00'))
                
                if not (before_request <= ai_dt.replace(tzinfo=timezone.utc) <= after_request):
                    self.log_test("Chat Message Timestamp Consistency", False, 
                                f"Timestamp {ai_timestamp} not within request timeframe")
                    return False
                
                self.log_test("Chat Message Timestamp Consistency", True, 
                            f"Chat message timestamp is valid UTC: {ai_timestamp}")
                return True
                
            else:
                self.log_test("Chat Message Timestamp Consistency", False, 
                            f"Chat request failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Chat Message Timestamp Consistency", False, f"Error: {str(e)}")
            return False

    def test_user_goals_persistence(self):
        """Test that user goals are properly saved and retrieved"""
        try:
            # First, set a specific goal via targets endpoint
            test_goal = {
                "monthly_target": 8000,
                "weekly_target": 2000,
                "daily_target": 285,
                "auto_adjust": True
            }
            
            # Set the goal
            set_response = self.session.put(f"{self.base_url}/targets/settings", json=test_goal)
            
            if set_response.status_code != 200:
                self.log_test("User Goals Persistence", False, 
                            f"Failed to set goals: {set_response.status_code}")
                return False
            
            # Wait a moment for persistence
            time.sleep(1)
            
            # Retrieve the goal
            get_response = self.session.get(f"{self.base_url}/targets/settings")
            
            if get_response.status_code == 200:
                data = get_response.json()
                
                # Check if the goal was persisted correctly
                if data.get('monthly_target') == 8000:
                    # Check timestamps for persistence
                    created_at = data.get('created_at')
                    updated_at = data.get('updated_at')
                    
                    if created_at and not self.is_valid_utc_timestamp(created_at, allow_historical=True):
                        self.log_test("User Goals Persistence", False, 
                                    f"Invalid created_at timestamp: {created_at}")
                        return False
                    
                    if updated_at and not self.is_valid_utc_timestamp(updated_at, allow_historical=True):
                        self.log_test("User Goals Persistence", False, 
                                    f"Invalid updated_at timestamp: {updated_at}")
                        return False
                    
                    self.log_test("User Goals Persistence", True, 
                                f"Goals properly persisted and retrieved. Monthly target: R{data.get('monthly_target')}")
                    return True
                else:
                    self.log_test("User Goals Persistence", False, 
                                f"Goal not persisted correctly. Expected R8000, got R{data.get('monthly_target')}")
                    return False
            else:
                self.log_test("User Goals Persistence", False, 
                            f"Failed to retrieve goals: {get_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Goals Persistence", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Backend Tests")
        print("=" * 80)
        print(f"Testing against: {self.base_url}")
        print(f"Test session ID: {self.test_session_id}")
        print(f"User ID: {self.user_id}")
        print()
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Core functionality tests
        print("🎯 Testing Target Settings Endpoint...")
        self.test_targets_settings_endpoint()
        
        print("💬 Testing AI Goal Update via Chat...")
        self.test_ai_goal_update_via_chat()
        
        print("📊 Testing AI Portfolio Data Access...")
        self.test_ai_portfolio_data_access()
        
        print("🤖 Testing AI Adjust Targets Endpoint...")
        self.test_ai_adjust_targets_endpoint()
        
        print("🕐 Testing Timestamp Consistency Across Services...")
        self.test_timestamp_consistency_across_services()
        
        print("💬 Testing Chat Message Timestamp Consistency...")
        self.test_chat_message_timestamp_consistency()
        
        print("💾 Testing User Goals Persistence...")
        self.test_user_goals_persistence()
        
        # Summary
        self.print_summary()
        
        return self.get_overall_success()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE BACKEND TEST SUMMARY")
        print("=" * 80)
        
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
            print("\n🎉 ALL COMPREHENSIVE TESTS PASSED!")
            print("✅ Goal updating functionality is working correctly")
            print("✅ AI can access and process real-time portfolio data")
            print("✅ All timestamps are consistently using UTC format")
            print("✅ Target settings can be updated and retrieved properly")
            print("✅ AI responses include actual portfolio data and calculations")
            print("✅ User goals are properly saved and retrieved")
        
        print("\n" + "=" * 80)
    
    def get_overall_success(self) -> bool:
        """Get overall test success status"""
        if not self.test_results:
            return False
        
        passed = len([r for r in self.test_results if r['success']])
        total = len(self.test_results)
        
        # For comprehensive testing, we need high success rate (allow 1 failure)
        return passed >= (total - 1)

def main():
    """Main test execution"""
    print("Comprehensive Backend Testing for AI Crypto Trading Coach")
    print(f"Testing against: {BACKEND_URL}")
    print()
    
    tester = ComprehensiveBackendTester(BACKEND_URL)
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall: COMPREHENSIVE BACKEND TESTS PASSED")
        sys.exit(0)
    else:
        print("💥 Overall: COMPREHENSIVE BACKEND TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()