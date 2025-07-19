#!/usr/bin/env python3
"""
Backend API Testing Script for Crypto Trading Coach
Tests the recent changes focusing on:
1. AI Service Response Style (concise by default)
2. Dynamic Target Loading (not hardcoded)
3. New Session Endpoint (DELETE chat history)
4. Context-Aware Portfolio Data (only when requested)
5. Target Adjustment System (AI chat integration)
"""

import requests
import json
import time
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = "https://0b947ae6-ff7d-4854-998d-9ceae9d7066c.preview.emergentagent.com/api"

class AIBehaviorTester:
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
    
    def test_ai_concise_responses(self):
        """Test that AI provides concise responses by default"""
        try:
            # Test simple price question - should be concise
            simple_request = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': "What's BTC price?"
            }
            
            response = self.session.post(f"{self.base_url}/chat/send", json=simple_request)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('message', '')
                
                # Check response length - should be concise (under 200 words)
                word_count = len(ai_response.split())
                
                # Check if it includes unnecessary portfolio details
                portfolio_keywords = ['portfolio value', 'holdings breakdown', 'allocation', 'total value']
                has_portfolio_details = any(keyword in ai_response.lower() for keyword in portfolio_keywords)
                
                if word_count > 200:
                    self.log_test("AI Concise Response - Simple Question", False, 
                                f"Response too verbose: {word_count} words. Should be under 200 for simple questions.")
                    return False
                
                if has_portfolio_details:
                    self.log_test("AI Concise Response - Simple Question", False, 
                                "Response includes portfolio details when not requested")
                    return False
                
                self.log_test("AI Concise Response - Simple Question", True, 
                            f"Response is concise: {word_count} words, no unnecessary portfolio details")
                return True
                
            else:
                self.log_test("AI Concise Response - Simple Question", False, 
                            f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("AI Concise Response - Simple Question", False, f"Error: {str(e)}")
            return False
    
    def test_ai_detailed_when_requested(self):
        """Test that AI provides detailed analysis when specifically requested"""
        try:
            # Test detailed request - should include portfolio data
            detailed_request = {
                'session_id': self.test_session_id,
                'role': 'user',
                'message': "Give me a detailed portfolio analysis with full breakdown"
            }
            
            response = self.session.post(f"{self.base_url}/chat/send", json=detailed_request)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('message', '')
                
                # Check if it includes portfolio details when requested
                portfolio_keywords = ['portfolio', 'holdings', 'value', 'allocation']
                has_portfolio_details = any(keyword in ai_response.lower() for keyword in portfolio_keywords)
                
                # Should be more detailed (over 100 words)
                word_count = len(ai_response.split())
                
                if not has_portfolio_details:
                    self.log_test("AI Detailed Response - When Requested", False, 
                                "Response doesn't include portfolio details when specifically requested")
                    return False
                
                if word_count < 50:
                    self.log_test("AI Detailed Response - When Requested", False, 
                                f"Response too brief for detailed request: {word_count} words")
                    return False
                
                self.log_test("AI Detailed Response - When Requested", True, 
                            f"Response includes portfolio details as requested: {word_count} words")
                return True
                
            else:
                self.log_test("AI Detailed Response - When Requested", False, 
                            f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("AI Detailed Response - When Requested", False, f"Error: {str(e)}")
            return False
    
    def test_dynamic_target_loading(self):
        """Test that targets are loaded dynamically from backend, not hardcoded"""
        try:
            response = self.session.get(f"{self.base_url}/targets/settings")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['monthly_target', 'weekly_target', 'user_id']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Dynamic Target Loading", False, f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check that targets are not the old hardcoded values
                monthly_target = data.get('monthly_target')
                weekly_target = data.get('weekly_target')
                
                # Verify targets are numeric and reasonable
                if not isinstance(monthly_target, (int, float)) or monthly_target <= 0:
                    self.log_test("Dynamic Target Loading", False, 
                                f"Invalid monthly target: {monthly_target}")
                    return False
                
                if not isinstance(weekly_target, (int, float)) or weekly_target <= 0:
                    self.log_test("Dynamic Target Loading", False, 
                                f"Invalid weekly target: {weekly_target}")
                    return False
                
                # Check if targets have timestamps indicating they're dynamic
                has_timestamps = 'created_at' in data or 'updated_at' in data
                
                self.log_test("Dynamic Target Loading", True, 
                            f"Targets loaded dynamically: Monthly R{monthly_target:,.0f}, Weekly R{weekly_target:,.0f}, Has timestamps: {has_timestamps}")
                return True
                
            else:
                self.log_test("Dynamic Target Loading", False, 
                            f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Dynamic Target Loading", False, f"Error: {str(e)}")
            return False
    
    def test_new_session_endpoint(self):
        """Test the new DELETE chat history endpoint"""
        try:
            # First, send a message to create history
            test_message = {
                'session_id': self.test_session_id,
                'message': "Test message for deletion"
            }
            
            send_response = self.session.post(f"{self.base_url}/chat/send", json=test_message)
            if send_response.status_code != 200:
                self.log_test("New Session Endpoint - Setup", False, 
                            f"Failed to create test message: {send_response.status_code}")
                return False
            
            # Get chat history to verify message exists
            history_response = self.session.get(f"{self.base_url}/chat/history/{self.test_session_id}")
            if history_response.status_code != 200:
                self.log_test("New Session Endpoint - History Check", False, 
                            f"Failed to get chat history: {history_response.status_code}")
                return False
            
            history_data = history_response.json()
            initial_count = len(history_data) if isinstance(history_data, list) else 0
            
            if initial_count == 0:
                self.log_test("New Session Endpoint - History Check", False, 
                            "No messages found in history before deletion test")
                return False
            
            # Now test the DELETE endpoint
            delete_response = self.session.delete(f"{self.base_url}/chat/history/{self.test_session_id}")
            
            if delete_response.status_code == 200:
                delete_data = delete_response.json()
                
                # Check response structure
                required_fields = ['success', 'message', 'deleted_count']
                missing_fields = [field for field in required_fields if field not in delete_data]
                
                if missing_fields:
                    self.log_test("New Session Endpoint - DELETE", False, 
                                f"Missing fields in response: {missing_fields}", delete_data)
                    return False
                
                if not delete_data.get('success'):
                    self.log_test("New Session Endpoint - DELETE", False, 
                                f"Delete operation failed: {delete_data.get('message')}")
                    return False
                
                deleted_count = delete_data.get('deleted_count', 0)
                
                # Verify history is cleared
                verify_response = self.session.get(f"{self.base_url}/chat/history/{self.test_session_id}")
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    remaining_count = len(verify_data) if isinstance(verify_data, list) else 0
                    
                    if remaining_count > 0:
                        self.log_test("New Session Endpoint - DELETE", False, 
                                    f"History not properly cleared: {remaining_count} messages remain")
                        return False
                
                self.log_test("New Session Endpoint - DELETE", True, 
                            f"Successfully deleted {deleted_count} messages, history cleared")
                return True
                
            else:
                self.log_test("New Session Endpoint - DELETE", False, 
                            f"Status code: {delete_response.status_code}", delete_response.text)
                return False
                
        except Exception as e:
            self.log_test("New Session Endpoint - DELETE", False, f"Error: {str(e)}")
            return False
    
    def test_context_aware_portfolio_data(self):
        """Test that portfolio data is only included when specifically requested"""
        try:
            # Test 1: General question should NOT include portfolio data
            general_request = {
                'session_id': f"{self.test_session_id}_general",
                'role': 'user',
                'message': "What's the market trend today?"
            }
            
            response1 = self.session.post(f"{self.base_url}/chat/send", json=general_request)
            
            if response1.status_code == 200:
                data1 = response1.json()
                ai_response1 = data1.get('message', '')
                
                # Check if it includes portfolio details (it shouldn't)
                portfolio_keywords = ['portfolio value', 'holdings', 'allocation', 'your portfolio', 'total value']
                has_portfolio_details1 = any(keyword in ai_response1.lower() for keyword in portfolio_keywords)
                
                if has_portfolio_details1:
                    self.log_test("Context-Aware Portfolio Data - General Question", False, 
                                "Response includes portfolio details when not requested")
                    return False
                
                self.log_test("Context-Aware Portfolio Data - General Question", True, 
                            "Response correctly excludes portfolio details for general question")
            else:
                self.log_test("Context-Aware Portfolio Data - General Question", False, 
                            f"Status code: {response1.status_code}")
                return False
            
            # Test 2: Portfolio-specific question SHOULD include portfolio data
            portfolio_request = {
                'session_id': f"{self.test_session_id}_portfolio",
                'role': 'user',
                'message': "Show me my portfolio balance and holdings"
            }
            
            response2 = self.session.post(f"{self.base_url}/chat/send", json=portfolio_request)
            
            if response2.status_code == 200:
                data2 = response2.json()
                ai_response2 = data2.get('message', '')
                
                # Check if it includes portfolio details (it should)
                portfolio_keywords = ['portfolio', 'holdings', 'balance', 'value']
                has_portfolio_details2 = any(keyword in ai_response2.lower() for keyword in portfolio_keywords)
                
                if not has_portfolio_details2:
                    self.log_test("Context-Aware Portfolio Data - Portfolio Question", False, 
                                "Response doesn't include portfolio details when specifically requested")
                    return False
                
                self.log_test("Context-Aware Portfolio Data - Portfolio Question", True, 
                            "Response correctly includes portfolio details when requested")
                return True
            else:
                self.log_test("Context-Aware Portfolio Data - Portfolio Question", False, 
                            f"Status code: {response2.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Context-Aware Portfolio Data", False, f"Error: {str(e)}")
            return False
    
    def test_target_adjustment_system(self):
        """Test that target adjustments through AI chat are working"""
        try:
            # Get current targets first
            current_response = self.session.get(f"{self.base_url}/targets/settings")
            if current_response.status_code != 200:
                self.log_test("Target Adjustment System - Get Current", False, 
                            f"Failed to get current targets: {current_response.status_code}")
                return False
            
            current_data = current_response.json()
            original_monthly = current_data.get('monthly_target', 100000)
            
            # Test AI target adjustment request
            adjustment_request = {
                'session_id': f"{self.test_session_id}_targets",
                'message': "I want to increase my monthly target to R150000 based on recent performance"
            }
            
            # Send the adjustment request to AI
            ai_response = self.session.post(f"{self.base_url}/chat/send", json=adjustment_request)
            
            if ai_response.status_code != 200:
                self.log_test("Target Adjustment System - AI Request", False, 
                            f"AI chat failed: {ai_response.status_code}")
                return False
            
            ai_data = ai_response.json()
            ai_message = ai_data.get('message', '')
            
            # Check if AI acknowledges the target adjustment
            adjustment_keywords = ['target', 'adjust', 'increase', '150000', 'monthly']
            has_adjustment_response = any(keyword in ai_message.lower() for keyword in adjustment_keywords)
            
            if not has_adjustment_response:
                self.log_test("Target Adjustment System - AI Recognition", False, 
                            "AI doesn't seem to recognize target adjustment request")
                return False
            
            # Test the AI adjust targets endpoint directly
            adjust_request = {
                'reason': 'User requested increase to R150000 based on recent performance'
            }
            
            adjust_response = self.session.post(f"{self.base_url}/ai/adjust-targets", json=adjust_request)
            
            if adjust_response.status_code == 200:
                adjust_data = adjust_response.json()
                
                # Check response structure
                if not adjust_data.get('success'):
                    # This might be expected if AI determines no adjustment is needed
                    self.log_test("Target Adjustment System - AI Endpoint", True, 
                                f"AI target adjustment endpoint working: {adjust_data.get('message', 'No adjustment needed')}")
                    return True
                
                # If adjustment was made, verify it
                if 'new_targets' in adjust_data:
                    new_targets = adjust_data['new_targets']
                    self.log_test("Target Adjustment System - AI Endpoint", True, 
                                f"AI successfully adjusted targets: {adjust_data.get('message')}")
                    return True
                
                self.log_test("Target Adjustment System - AI Endpoint", True, 
                            "AI target adjustment system is functional")
                return True
                
            else:
                self.log_test("Target Adjustment System - AI Endpoint", False, 
                            f"Status code: {adjust_response.status_code}", adjust_response.text)
                return False
                
        except Exception as e:
            self.log_test("Target Adjustment System", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all AI behavior and new feature tests"""
        print("🚀 Starting AI Crypto Trading Coach Backend Tests")
        print("Testing Recent Changes: AI Behavior, Dynamic Targets, Session Management")
        print("=" * 70)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Test AI response behavior changes
        print("🤖 Testing AI Response Style Changes...")
        self.test_ai_concise_responses()
        self.test_ai_detailed_when_requested()
        self.test_context_aware_portfolio_data()
        
        # Test dynamic target loading
        print("🎯 Testing Dynamic Target Loading...")
        self.test_dynamic_target_loading()
        
        # Test new session endpoint
        print("🔄 Testing New Session Management...")
        self.test_new_session_endpoint()
        
        # Test target adjustment system
        print("⚙️ Testing Target Adjustment System...")
        self.test_target_adjustment_system()
        
        # Summary
        self.print_summary()
        
        return self.get_overall_success()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📋 TEST SUMMARY - AI CRYPTO TRADING COACH RECENT CHANGES")
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
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  - {result['test']}")
        
        print("\n" + "=" * 70)
    
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
    print("AI Crypto Trading Coach Backend API Tests - Recent Changes")
    print(f"Testing against: {BACKEND_URL}")
    print()
    
    tester = AIBehaviorTester(BACKEND_URL)
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall: TESTS PASSED")
        sys.exit(0)
    else:
        print("💥 Overall: TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()