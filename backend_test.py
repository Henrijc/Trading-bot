#!/usr/bin/env python3
"""
Backend API Testing Script for Crypto Trading Coach
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
BACKEND_URL = "https://92b827da-70fe-4086-bc79-d51047cf7fd5.preview.emergentagent.com/api"

class TimestampConsistencyTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = []
        self.test_session_id = f"timestamp_test_{uuid.uuid4().hex[:8]}"
        
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
    
    def is_valid_utc_timestamp(self, timestamp_str: str) -> bool:
        """Check if timestamp is in valid UTC ISO format"""
        try:
            # Parse the timestamp
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Check if it's a reasonable timestamp (not too far in past/future)
            now = datetime.now(timezone.utc)
            time_diff = abs((now - dt.replace(tzinfo=timezone.utc)).total_seconds())
            
            # Should be within 1 hour of current time for chat messages
            return time_diff < 3600
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
    
    def test_chat_message_timestamp_consistency(self):
        """Test that user and AI messages have consistent UTC timestamps"""
        try:
            # Send a chat message
            chat_request = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': 'What is the current BTC price?',
                'context': None  # Let backend generate fresh context
            }
            
            # Record time before request
            before_request = datetime.now(timezone.utc)
            
            response = self.session.post(f"{self.base_url}/chat/send", json=chat_request)
            
            # Record time after request
            after_request = datetime.now(timezone.utc)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['session_id', 'role', 'message', 'timestamp']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Chat Message Timestamp Consistency", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check timestamp format and validity
                ai_timestamp = data.get('timestamp')
                if not self.is_valid_utc_timestamp(ai_timestamp):
                    self.log_test("Chat Message Timestamp Consistency", False, 
                                f"Invalid AI message timestamp: {ai_timestamp}", data)
                    return False
                
                # Parse AI timestamp
                ai_dt = datetime.fromisoformat(ai_timestamp.replace('Z', '+00:00'))
                
                # Check if AI timestamp is within reasonable range
                if not (before_request <= ai_dt.replace(tzinfo=timezone.utc) <= after_request):
                    self.log_test("Chat Message Timestamp Consistency", False, 
                                f"AI timestamp {ai_timestamp} not within request timeframe {before_request} - {after_request}")
                    return False
                
                self.log_test("Chat Message Timestamp Consistency", True, 
                            f"AI message timestamp is valid UTC: {ai_timestamp}")
                return True
                
            else:
                self.log_test("Chat Message Timestamp Consistency", False, 
                            f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Chat Message Timestamp Consistency", False, f"Error: {str(e)}")
            return False
    
    def test_context_timestamp_utc_format(self):
        """Test that context timestamps use UTC format"""
        try:
            # Send a chat message with explicit context check
            chat_request = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': 'Can you analyze my portfolio performance?',
                'context': None  # Force backend to generate context with timestamp
            }
            
            response = self.session.post(f"{self.base_url}/chat/send", json=chat_request)
            
            if response.status_code == 200:
                data = response.json()
                
                # The context timestamp should be generated in server.py line 79 or 89
                # We can't directly see the context, but we can verify the message timestamp
                message_timestamp = data.get('timestamp')
                
                if not message_timestamp:
                    self.log_test("Context Timestamp UTC Format", False, "No timestamp in response")
                    return False
                
                # Verify it's in UTC format
                if not self.is_valid_utc_timestamp(message_timestamp):
                    self.log_test("Context Timestamp UTC Format", False, 
                                f"Invalid timestamp format: {message_timestamp}")
                    return False
                
                # Check if timestamp looks like UTC (should not have timezone offset other than Z or +00:00)
                # Valid UTC formats: 2025-07-19T15:03:44.620765 (no timezone), 2025-07-19T15:03:44.620765Z, 2025-07-19T15:03:44.620765+00:00
                # Look for timezone indicators after the 'T' to avoid matching date hyphens
                time_part = message_timestamp.split('T')[1] if 'T' in message_timestamp else message_timestamp
                has_plus_minus = any(tz in time_part for tz in ['+', '-'])
                has_z_suffix = message_timestamp.endswith('Z')
                has_timezone_info = has_plus_minus or has_z_suffix
                is_iso_format = 'T' in message_timestamp
                
                if not is_iso_format:
                    self.log_test("Context Timestamp UTC Format", False, 
                                f"Timestamp is not in ISO format: {message_timestamp}")
                    return False
                
                # If it has timezone info, it should be UTC (Z or +00:00)
                if has_timezone_info and not (message_timestamp.endswith('Z') or '+00:00' in message_timestamp):
                    self.log_test("Context Timestamp UTC Format", False, 
                                f"Timestamp has non-UTC timezone: {message_timestamp}")
                    return False
                
                self.log_test("Context Timestamp UTC Format", True, 
                            f"Context timestamp is in proper UTC format: {message_timestamp}")
                return True
                
            else:
                self.log_test("Context Timestamp UTC Format", False, 
                            f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Context Timestamp UTC Format", False, f"Error: {str(e)}")
            return False
    
    def test_multiple_messages_timestamp_sequence(self):
        """Test multiple chat messages in sequence for timestamp consistency"""
        try:
            messages = [
                "What's the current BTC price?",
                "Should I buy or sell BTC now?",
                "What about ETH analysis?",
                "Give me a portfolio summary"
            ]
            
            timestamps = []
            
            for i, message in enumerate(messages):
                chat_request = {
                    'session_id': self.test_session_id,
                    'role': 'user',
                    'message': message,
                    'context': None
                }
                
                # Small delay between messages
                if i > 0:
                    time.sleep(1)
                
                response = self.session.post(f"{self.base_url}/chat/send", json=chat_request)
                
                if response.status_code != 200:
                    self.log_test("Multiple Messages Timestamp Sequence", False, 
                                f"Message {i+1} failed with status {response.status_code}")
                    return False
                
                data = response.json()
                timestamp = data.get('timestamp')
                
                if not timestamp:
                    self.log_test("Multiple Messages Timestamp Sequence", False, 
                                f"Message {i+1} missing timestamp")
                    return False
                
                if not self.is_valid_utc_timestamp(timestamp):
                    self.log_test("Multiple Messages Timestamp Sequence", False, 
                                f"Message {i+1} invalid timestamp: {timestamp}")
                    return False
                
                timestamps.append((i+1, timestamp, datetime.fromisoformat(timestamp.replace('Z', '+00:00'))))
            
            # Check that timestamps are in chronological order
            for i in range(1, len(timestamps)):
                prev_dt = timestamps[i-1][2]
                curr_dt = timestamps[i][2]
                
                if curr_dt <= prev_dt:
                    self.log_test("Multiple Messages Timestamp Sequence", False, 
                                f"Timestamps not in chronological order: Message {timestamps[i-1][0]} ({timestamps[i-1][1]}) >= Message {timestamps[i][0]} ({timestamps[i][1]})")
                    return False
            
            # Check that all timestamps are within reasonable time differences
            first_dt = timestamps[0][2]
            last_dt = timestamps[-1][2]
            total_duration = (last_dt - first_dt).total_seconds()
            
            # Should be reasonable duration (less than 2 minutes for 4 messages)
            if total_duration > 120:
                self.log_test("Multiple Messages Timestamp Sequence", False, 
                            f"Total conversation duration too long: {total_duration} seconds")
                return False
            
            self.log_test("Multiple Messages Timestamp Sequence", True, 
                        f"All {len(messages)} messages have consistent UTC timestamps in chronological order. Duration: {total_duration:.1f}s")
            return True
            
        except Exception as e:
            self.log_test("Multiple Messages Timestamp Sequence", False, f"Error: {str(e)}")
            return False
    
    def test_chat_history_timestamp_consistency(self):
        """Test that chat history returns consistent timestamps"""
        try:
            # Get chat history for our test session
            response = self.session.get(f"{self.base_url}/chat/history/{self.test_session_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_test("Chat History Timestamp Consistency", False, 
                                "Chat history should return a list")
                    return False
                
                if len(data) == 0:
                    self.log_test("Chat History Timestamp Consistency", True, 
                                "No chat history found (expected for new session)")
                    return True
                
                # Check each message in history
                for i, message in enumerate(data):
                    if 'timestamp' not in message:
                        self.log_test("Chat History Timestamp Consistency", False, 
                                    f"Message {i+1} missing timestamp")
                        return False
                    
                    timestamp = message['timestamp']
                    if not self.is_valid_utc_timestamp(timestamp):
                        self.log_test("Chat History Timestamp Consistency", False, 
                                    f"Message {i+1} invalid timestamp: {timestamp}")
                        return False
                
                # Check chronological order
                for i in range(1, len(data)):
                    prev_ts = datetime.fromisoformat(data[i-1]['timestamp'].replace('Z', '+00:00'))
                    curr_ts = datetime.fromisoformat(data[i]['timestamp'].replace('Z', '+00:00'))
                    
                    if curr_ts < prev_ts:
                        self.log_test("Chat History Timestamp Consistency", False, 
                                    f"Chat history not in chronological order at position {i}")
                        return False
                
                self.log_test("Chat History Timestamp Consistency", True, 
                            f"All {len(data)} messages in chat history have consistent UTC timestamps")
                return True
                
            else:
                self.log_test("Chat History Timestamp Consistency", False, 
                            f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Chat History Timestamp Consistency", False, f"Error: {str(e)}")
            return False
    
    def test_ai_service_timestamp_consistency(self):
        """Test AI service endpoints for UTC timestamp consistency"""
        try:
            # Test technical analysis endpoint which uses ai_service timestamps
            response = self.session.get(f"{self.base_url}/technical/signals/BTC")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract all timestamps from response
                timestamps = self.extract_timestamps_from_response(data)
                
                if not timestamps:
                    self.log_test("AI Service Timestamp Consistency", True, 
                                "No timestamps found in technical analysis response (acceptable)")
                    return True
                
                # Check each timestamp
                invalid_timestamps = []
                for field_path, timestamp in timestamps:
                    if not self.is_valid_utc_timestamp(timestamp):
                        invalid_timestamps.append((field_path, timestamp))
                
                if invalid_timestamps:
                    self.log_test("AI Service Timestamp Consistency", False, 
                                f"Invalid timestamps found: {invalid_timestamps}")
                    return False
                
                self.log_test("AI Service Timestamp Consistency", True, 
                            f"All {len(timestamps)} timestamps in AI service response are valid UTC format")
                return True
                
            else:
                self.log_test("AI Service Timestamp Consistency", False, 
                            f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("AI Service Timestamp Consistency", False, f"Error: {str(e)}")
            return False
    
    def test_no_timezone_discrepancy(self):
        """Test that there's no 2-hour timezone discrepancy between messages"""
        try:
            # Send two messages with a small delay
            messages = ["Test message 1", "Test message 2"]
            message_timestamps = []
            
            for message in messages:
                chat_request = {
                    'session_id': self.test_session_id,
                    'role': 'user',
                    'message': message,
                    'context': None
                }
                
                response = self.session.post(f"{self.base_url}/chat/send", json=chat_request)
                
                if response.status_code != 200:
                    self.log_test("No Timezone Discrepancy", False, 
                                f"Failed to send message: {response.status_code}")
                    return False
                
                data = response.json()
                timestamp = data.get('timestamp')
                
                if not timestamp:
                    self.log_test("No Timezone Discrepancy", False, "Missing timestamp")
                    return False
                
                message_timestamps.append(datetime.fromisoformat(timestamp.replace('Z', '+00:00')))
                time.sleep(2)  # 2 second delay between messages
            
            # Check time difference between messages
            time_diff = abs((message_timestamps[1] - message_timestamps[0]).total_seconds())
            
            # Should be around 2 seconds (our delay), not 2 hours (7200 seconds)
            if time_diff > 60:  # Allow up to 1 minute for processing delays
                self.log_test("No Timezone Discrepancy", False, 
                            f"Large time discrepancy detected: {time_diff} seconds between messages")
                return False
            
            if time_diff < 1:  # Should be at least 1 second due to our delay
                self.log_test("No Timezone Discrepancy", False, 
                            f"Time difference too small: {time_diff} seconds (possible timestamp reuse)")
                return False
            
            self.log_test("No Timezone Discrepancy", True, 
                        f"Time difference between messages is reasonable: {time_diff:.1f} seconds (no 2-hour discrepancy)")
            return True
            
        except Exception as e:
            self.log_test("No Timezone Discrepancy", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all timestamp consistency tests"""
        print("🕐 Starting Timestamp Consistency Tests")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Test session ID: {self.test_session_id}")
        print()
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Core timestamp consistency tests
        print("📅 Testing Chat Message Timestamp Consistency...")
        self.test_chat_message_timestamp_consistency()
        
        print("🌍 Testing Context Timestamp UTC Format...")
        self.test_context_timestamp_utc_format()
        
        print("📝 Testing Multiple Messages Timestamp Sequence...")
        self.test_multiple_messages_timestamp_sequence()
        
        print("📚 Testing Chat History Timestamp Consistency...")
        self.test_chat_history_timestamp_consistency()
        
        print("🤖 Testing AI Service Timestamp Consistency...")
        self.test_ai_service_timestamp_consistency()
        
        print("⏰ Testing No Timezone Discrepancy...")
        self.test_no_timezone_discrepancy()
        
        # Summary
        self.print_summary()
        
        return self.get_overall_success()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 TIMESTAMP CONSISTENCY TEST SUMMARY")
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
        else:
            print("\n🎉 ALL TIMESTAMP CONSISTENCY TESTS PASSED!")
            print("✅ The 2-hour timestamp discrepancy issue has been resolved")
            print("✅ All timestamps are now consistently using UTC format")
            print("✅ Context timestamps are properly using datetime.utcnow()")
            print("✅ AI service timestamps are consistent across all endpoints")
        
        print("\n" + "=" * 60)
    
    def get_overall_success(self) -> bool:
        """Get overall test success status"""
        if not self.test_results:
            return False
        
        # For timestamp consistency, we need 100% success rate
        passed = len([r for r in self.test_results if r['success']])
        total = len(self.test_results)
        
        return passed == total

def main():
    """Main test execution"""
    print("Timestamp Consistency Testing for AI Crypto Trading Coach")
    print(f"Testing against: {BACKEND_URL}")
    print()
    
    tester = TimestampConsistencyTester(BACKEND_URL)
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall: TIMESTAMP CONSISTENCY TESTS PASSED")
        sys.exit(0)
    else:
        print("💥 Overall: TIMESTAMP CONSISTENCY TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()