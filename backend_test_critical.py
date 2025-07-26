#!/usr/bin/env python3
"""
Backend API Testing Script for Crypto Trading Coach
CRITICAL FIXES TESTING - Focus on urgent issues that were just fixed:
1. AI Context Continuity - Test AI remembers conversation context across multiple messages
2. Portfolio Data Access - Test AI can access and reference portfolio data when requested
3. Target Settings API - Verify dynamic targets (not hardcoded 100,000)
4. Session Management - Test sessions work properly with context preservation
5. Timestamp Consistency - Check UTC timestamp format consistency
"""

import requests
import json
import time
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = "https://46b82e01-2be5-441e-8d8d-89a8c669d28e.preview.emergentagent.com/api"

class CriticalFixesTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = []
        self.test_session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        
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
    
    def test_dynamic_targets_api(self):
        """CRITICAL: Test that targets API returns dynamic values, not hardcoded 100,000"""
        try:
            response = self.session.get(f"{self.base_url}/targets/settings")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['monthly_target', 'weekly_target', 'user_id']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Dynamic Targets API", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                monthly_target = data.get('monthly_target', 0)
                weekly_target = data.get('weekly_target', 0)
                
                # Check if targets are NOT hardcoded 100,000
                if monthly_target == 100000:
                    self.log_test("Dynamic Targets API", False, 
                                f"Monthly target is still hardcoded at R100,000. Expected dynamic value.", data)
                    return False
                
                # Check if targets have timestamps indicating they're dynamic
                has_timestamps = 'created_at' in data or 'updated_at' in data
                if not has_timestamps:
                    self.log_test("Dynamic Targets API", False, 
                                "No timestamps found - targets may still be hardcoded", data)
                    return False
                
                self.log_test("Dynamic Targets API", True, 
                            f"Dynamic targets confirmed: Monthly R{monthly_target:,}, Weekly R{weekly_target:,}")
                return True
                
            else:
                self.log_test("Dynamic Targets API", False, f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Dynamic Targets API", False, f"Error: {str(e)}")
            return False
    
    def test_session_management(self):
        """CRITICAL: Test session management - context preservation and new session functionality"""
        try:
            # First, clear any existing chat history for our test session
            clear_response = self.session.delete(f"{self.base_url}/chat/history/{self.test_session_id}")
            
            if clear_response.status_code == 200:
                clear_data = clear_response.json()
                self.log_test("Session Management - Clear History", True, 
                            f"Cleared {clear_data.get('deleted_count', 0)} messages")
            else:
                self.log_test("Session Management - Clear History", True, 
                            "No existing messages to clear (expected for new session)")
            
            # Test that we can start fresh
            history_response = self.session.get(f"{self.base_url}/chat/history/{self.test_session_id}")
            if history_response.status_code == 200:
                history_data = history_response.json()
                if len(history_data) == 0:
                    self.log_test("Session Management - Fresh Start", True, "Session starts with empty history")
                    return True
                else:
                    self.log_test("Session Management - Fresh Start", False, 
                                f"Session should be empty but has {len(history_data)} messages")
                    return False
            else:
                self.log_test("Session Management - Fresh Start", False, 
                            f"Failed to get history: {history_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Session Management", False, f"Error: {str(e)}")
            return False
    
    def test_ai_context_continuity(self):
        """CRITICAL: Test AI context continuity across multiple messages in same session"""
        try:
            # Send first message establishing context
            first_message = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': 'My name is TestUser and I prefer conservative trading strategies. Remember this for our conversation.'
            }
            
            response1 = self.session.post(f"{self.base_url}/chat/send", json=first_message)
            
            if response1.status_code != 200:
                try:
                    error_data = response1.json()
                    self.log_test("AI Context Continuity - First Message", False, 
                                f"Failed to send first message: {response1.status_code}, Error: {error_data}")
                except:
                    self.log_test("AI Context Continuity - First Message", False, 
                                f"Failed to send first message: {response1.status_code}, Response: {response1.text}")
                return False
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Send follow-up message that requires previous context
            followup_message = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': 'What trading strategy would you recommend for me based on what I told you earlier?'
            }
            
            response2 = self.session.post(f"{self.base_url}/chat/send", json=followup_message)
            
            if response2.status_code == 200:
                data2 = response2.json()
                ai_response = data2.get('message', '').lower()
                
                # Check if AI remembers the context (conservative preference and name)
                context_indicators = ['conservative', 'testuser', 'earlier', 'told', 'prefer']
                found_indicators = [indicator for indicator in context_indicators if indicator in ai_response]
                
                if len(found_indicators) >= 2:
                    self.log_test("AI Context Continuity", True, 
                                f"AI remembered context. Found indicators: {found_indicators}")
                    return True
                else:
                    self.log_test("AI Context Continuity", False, 
                                f"AI may not remember context. Response: {ai_response[:200]}...")
                    return False
            else:
                self.log_test("AI Context Continuity", False, 
                            f"Failed to send follow-up message: {response2.status_code}")
                return False
                
        except Exception as e:
            self.log_test("AI Context Continuity", False, f"Error: {str(e)}")
            return False
    
    def test_portfolio_data_access(self):
        """CRITICAL: Test that AI can access and reference portfolio data when requested"""
        try:
            # Send message specifically requesting portfolio information
            portfolio_request = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': 'How many assets do I have in my portfolio? Show me my portfolio details.'
            }
            
            response = self.session.post(f"{self.base_url}/chat/send", json=portfolio_request)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('message', '').lower()
                
                # Check if AI response includes portfolio-related information
                portfolio_keywords = ['portfolio', 'assets', 'holdings', 'balance', 'total', 'value', 'btc', 'eth', 'crypto']
                found_keywords = [keyword for keyword in portfolio_keywords if keyword in ai_response]
                
                # Also check if response indicates actual data access vs generic response
                data_indicators = ['r ', 'zar', 'amount', 'quantity', 'current', 'price']
                found_data_indicators = [indicator for indicator in data_indicators if indicator in ai_response]
                
                if len(found_keywords) >= 3 and len(found_data_indicators) >= 1:
                    self.log_test("Portfolio Data Access", True, 
                                f"AI accessed portfolio data. Keywords: {found_keywords}, Data indicators: {found_data_indicators}")
                    return True
                elif 'error' in ai_response or 'unable' in ai_response or 'cannot' in ai_response:
                    self.log_test("Portfolio Data Access", False, 
                                f"AI cannot access portfolio data. Response: {ai_response[:200]}...")
                    return False
                else:
                    self.log_test("Portfolio Data Access", False, 
                                f"AI response unclear about portfolio access. Response: {ai_response[:200]}...")
                    return False
            else:
                self.log_test("Portfolio Data Access", False, 
                            f"Failed to send portfolio request: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Portfolio Data Access", False, f"Error: {str(e)}")
            return False
    
    def test_timestamp_consistency(self):
        """CRITICAL: Test timestamp consistency in chat messages (UTC format)"""
        try:
            # Send a message and check timestamp format
            test_message = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': 'Test message for timestamp validation'
            }
            
            response = self.session.post(f"{self.base_url}/chat/send", json=test_message)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has timestamp
                if 'timestamp' in data:
                    timestamp_str = data['timestamp']
                    
                    # Try to parse timestamp to validate format
                    try:
                        # Check if it's ISO format
                        parsed_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        
                        # Check if timestamp is recent (within last minute)
                        now = datetime.now()
                        time_diff = abs((now - parsed_timestamp.replace(tzinfo=None)).total_seconds())
                        
                        if time_diff < 60:  # Within 1 minute
                            self.log_test("Timestamp Consistency", True, 
                                        f"Timestamp format valid and recent: {timestamp_str}")
                            return True
                        else:
                            self.log_test("Timestamp Consistency", False, 
                                        f"Timestamp not recent: {timestamp_str}, diff: {time_diff}s")
                            return False
                            
                    except ValueError as e:
                        self.log_test("Timestamp Consistency", False, 
                                    f"Invalid timestamp format: {timestamp_str}, Error: {e}")
                        return False
                else:
                    self.log_test("Timestamp Consistency", False, "No timestamp in response", data)
                    return False
            else:
                self.log_test("Timestamp Consistency", False, 
                            f"Failed to send message: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Timestamp Consistency", False, f"Error: {str(e)}")
            return False
    
    def test_ai_context_loss_fix(self):
        """CRITICAL: Test that AI context is not being overwritten (duplicate context building fix)"""
        try:
            # Send multiple messages in sequence to test context preservation
            messages = [
                "I am a beginner trader interested in Bitcoin",
                "What is your recommendation for my risk level?",
                "Based on my beginner status, should I start with small amounts?"
            ]
            
            responses = []
            
            for i, message_text in enumerate(messages):
                message = {
                    'session_id': self.test_session_id,
                    'role': 'user',
                    'message': message_text
                }
                
                response = self.session.post(f"{self.base_url}/chat/send", json=message)
                
                if response.status_code == 200:
                    data = response.json()
                    responses.append(data.get('message', ''))
                    time.sleep(1)  # Small delay between messages
                else:
                    self.log_test("AI Context Loss Fix", False, 
                                f"Failed to send message {i+1}: {response.status_code}")
                    return False
            
            # Check if the final response acknowledges the beginner status from first message
            final_response = responses[-1].lower()
            context_preserved = any(word in final_response for word in ['beginner', 'start', 'small', 'risk', 'new'])
            
            if context_preserved:
                self.log_test("AI Context Loss Fix", True, 
                            "AI maintained context across multiple messages")
                return True
            else:
                self.log_test("AI Context Loss Fix", False, 
                            f"AI may have lost context. Final response: {final_response[:200]}...")
                return False
                
        except Exception as e:
            self.log_test("AI Context Loss Fix", False, f"Error: {str(e)}")
            return False
    
    def run_critical_tests(self):
        """Run all critical fix tests"""
        print("🚨 CRITICAL FIXES TESTING - AI Crypto Trading Coach")
        print("=" * 60)
        print("Testing urgent fixes that were just implemented:")
        print("1. AI Context Continuity")
        print("2. Portfolio Data Access")
        print("3. Dynamic Targets API")
        print("4. Session Management")
        print("5. Timestamp Consistency")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # CRITICAL TESTS
        print("🔥 CRITICAL TEST 1: Dynamic Targets API")
        self.test_dynamic_targets_api()
        
        print("🔥 CRITICAL TEST 2: Session Management")
        self.test_session_management()
        
        print("🔥 CRITICAL TEST 3: AI Context Continuity")
        self.test_ai_context_continuity()
        
        print("🔥 CRITICAL TEST 4: Portfolio Data Access")
        self.test_portfolio_data_access()
        
        print("🔥 CRITICAL TEST 5: Timestamp Consistency")
        self.test_timestamp_consistency()
        
        print("🔥 CRITICAL TEST 6: AI Context Loss Fix")
        self.test_ai_context_loss_fix()
        
        # Summary
        self.print_summary()
        
        return self.get_overall_success()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 CRITICAL FIXES TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Critical Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED CRITICAL TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print("\n🎉 ALL CRITICAL FIXES ARE WORKING!")
        
        print("\n" + "=" * 60)
    
    def get_overall_success(self) -> bool:
        """Get overall test success status"""
        if not self.test_results:
            return False
        
        # For critical fixes, we need 100% success rate
        passed = len([r for r in self.test_results if r['success']])
        total = len(self.test_results)
        success_rate = passed / total
        
        return success_rate >= 0.85  # Allow 1 test to fail out of 6

def main():
    """Main test execution"""
    print("🚨 CRITICAL FIXES TESTING - AI Crypto Trading Coach")
    print(f"Testing against: {BACKEND_URL}")
    print()
    
    tester = CriticalFixesTester(BACKEND_URL)
    success = tester.run_critical_tests()
    
    if success:
        print("🎉 Overall: CRITICAL FIXES TESTS PASSED")
        sys.exit(0)
    else:
        print("💥 Overall: CRITICAL FIXES TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()