#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE AUTHENTICATION SYSTEM TEST
AI Crypto Trading Coach - Complete Authentication Testing

This test verifies that the authentication system is fully functional
after fixing the critical routing issue.
"""

import requests
import json
import time
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = "https://92b827da-70fe-4086-bc79-d51047cf7fd5.preview.emergentagent.com/api"

class FinalAuthenticationTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = []
        
        # Test credentials from review request
        self.test_credentials = {
            "username": "Henrijc",
            "password": "H3nj3n",
            "backup_code": "0D6CCC6A"  # Valid backup code
        }
        
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
        print()
    
    def test_authentication_endpoint_exists(self):
        """Test that authentication endpoint exists and is accessible"""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json={"username": "invalid"})
            
            if response.status_code == 404:
                self.log_test("Authentication Endpoint Exists", False, 
                            "Endpoint returns 404 Not Found")
                return False
            else:
                self.log_test("Authentication Endpoint Exists", True, 
                            f"Endpoint accessible (status: {response.status_code})")
                return True
                
        except Exception as e:
            self.log_test("Authentication Endpoint Exists", False, f"Error: {str(e)}")
            return False
    
    def test_successful_authentication(self):
        """Test successful authentication with valid credentials"""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=self.test_credentials)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for successful authentication
                if data.get('success'):
                    # Verify expected fields
                    required_fields = ['access_token', 'user_data', 'login_analysis']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test("Successful Authentication", False, 
                                    f"Missing fields: {missing_fields}")
                        return False
                    
                    # Verify user data
                    user_data = data.get('user_data', {})
                    if user_data.get('username') != self.test_credentials['username']:
                        self.log_test("Successful Authentication", False, 
                                    f"Username mismatch: expected {self.test_credentials['username']}, got {user_data.get('username')}")
                        return False
                    
                    # Verify login analysis exists
                    login_analysis = data.get('login_analysis', {})
                    if not login_analysis.get('portfolio_summary'):
                        self.log_test("Successful Authentication", False, 
                                    "Missing portfolio summary in login analysis")
                        return False
                    
                    self.log_test("Successful Authentication", True, 
                                f"Authentication successful for user: {user_data.get('username')}")
                    return True
                else:
                    self.log_test("Successful Authentication", False, 
                                f"Authentication failed: {data.get('error', 'Unknown error')}")
                    return False
            else:
                self.log_test("Successful Authentication", False, 
                            f"HTTP error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Successful Authentication", False, f"Error: {str(e)}")
            return False
    
    def test_invalid_credentials_handling(self):
        """Test that invalid credentials are properly rejected"""
        try:
            invalid_credentials = {
                "username": "invalid_user",
                "password": "invalid_password",
                "totp_code": "000000"
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=invalid_credentials)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('success'):
                    self.log_test("Invalid Credentials Handling", True, 
                                f"Invalid credentials properly rejected: {data.get('error', 'Authentication failed')}")
                    return True
                else:
                    self.log_test("Invalid Credentials Handling", False, 
                                "Invalid credentials were accepted (security issue)")
                    return False
            else:
                self.log_test("Invalid Credentials Handling", True, 
                            f"Invalid credentials rejected with HTTP {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("Invalid Credentials Handling", False, f"Error: {str(e)}")
            return False
    
    def test_authentication_response_structure(self):
        """Test that authentication response has proper structure"""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=self.test_credentials)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    # Check response structure
                    expected_structure = {
                        'success': bool,
                        'access_token': str,
                        'token_type': str,
                        'user_data': dict,
                        'login_analysis': dict
                    }
                    
                    structure_issues = []
                    for field, expected_type in expected_structure.items():
                        if field not in data:
                            structure_issues.append(f"Missing field: {field}")
                        elif not isinstance(data[field], expected_type):
                            structure_issues.append(f"Wrong type for {field}: expected {expected_type.__name__}, got {type(data[field]).__name__}")
                    
                    if structure_issues:
                        self.log_test("Authentication Response Structure", False, 
                                    f"Structure issues: {structure_issues}")
                        return False
                    
                    # Check login analysis structure
                    login_analysis = data['login_analysis']
                    required_analysis_fields = ['portfolio_summary', 'ai_recommendations']
                    missing_analysis_fields = [field for field in required_analysis_fields 
                                             if field not in login_analysis]
                    
                    if missing_analysis_fields:
                        self.log_test("Authentication Response Structure", False, 
                                    f"Missing login analysis fields: {missing_analysis_fields}")
                        return False
                    
                    self.log_test("Authentication Response Structure", True, 
                                "Authentication response has proper structure")
                    return True
                else:
                    self.log_test("Authentication Response Structure", True, 
                                "Error response structure is valid")
                    return True
            else:
                self.log_test("Authentication Response Structure", False, 
                            f"Unexpected HTTP status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Authentication Response Structure", False, f"Error: {str(e)}")
            return False
    
    def test_other_auth_endpoints(self):
        """Test other authentication endpoints are accessible"""
        endpoints_to_test = [
            ("/auth/setup-2fa", "POST"),
            ("/auth/verify-2fa", "POST")
        ]
        
        accessible_count = 0
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", json={})
                else:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                
                # 404 means endpoint doesn't exist, anything else means it exists
                if response.status_code != 404:
                    accessible_count += 1
                    
            except Exception:
                continue
        
        if accessible_count == len(endpoints_to_test):
            self.log_test("Other Auth Endpoints", True, 
                        f"All {len(endpoints_to_test)} auth endpoints accessible")
            return True
        else:
            self.log_test("Other Auth Endpoints", False, 
                        f"Only {accessible_count}/{len(endpoints_to_test)} auth endpoints accessible")
            return False
    
    def run_all_tests(self):
        """Run all final authentication tests"""
        print("🔐 FINAL COMPREHENSIVE AUTHENTICATION SYSTEM TESTING")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print(f"Test credentials: {self.test_credentials['username']}")
        print()
        
        print("🔍 Testing Authentication Endpoint Exists...")
        self.test_authentication_endpoint_exists()
        
        print("✅ Testing Successful Authentication...")
        self.test_successful_authentication()
        
        print("❌ Testing Invalid Credentials Handling...")
        self.test_invalid_credentials_handling()
        
        print("📋 Testing Authentication Response Structure...")
        self.test_authentication_response_structure()
        
        print("🔗 Testing Other Auth Endpoints...")
        self.test_other_auth_endpoints()
        
        # Summary
        self.print_summary()
        
        return self.get_overall_success()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📋 FINAL AUTHENTICATION SYSTEM TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ REMAINING ISSUES:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
            print("✅ Authentication endpoint is fully functional")
            print("✅ Valid credentials are accepted and return proper tokens")
            print("✅ Invalid credentials are properly rejected")
            print("✅ Response structure is correct and complete")
            print("✅ All authentication endpoints are accessible")
            print("\n🔧 CRITICAL ISSUE RESOLVED:")
            print("✅ Fixed FastAPI router registration order")
            print("✅ Authentication endpoints now properly registered")
            print("✅ No more 404 Not Found errors for /api/auth/login")
        
        print("\n" + "=" * 70)
    
    def get_overall_success(self) -> bool:
        """Get overall test success status"""
        if not self.test_results:
            return False
        
        passed = len([r for r in self.test_results if r['success']])
        total = len(self.test_results)
        
        # Require 100% success for final authentication test
        return passed == total

def main():
    """Main test execution"""
    print("Final Comprehensive Authentication System Testing")
    print(f"Testing against: {BACKEND_URL}")
    print()
    
    tester = FinalAuthenticationTester(BACKEND_URL)
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall: AUTHENTICATION SYSTEM FULLY FUNCTIONAL")
        sys.exit(0)
    else:
        print("💥 Overall: AUTHENTICATION SYSTEM HAS REMAINING ISSUES")
        sys.exit(1)

if __name__ == "__main__":
    main()