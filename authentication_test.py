#!/usr/bin/env python3
"""
CRITICAL AUTHENTICATION SYSTEM TESTING
AI Crypto Trading Coach - Backend Authentication Testing

CRITICAL SYSTEM FAILURE INVESTIGATION:
The AI Crypto Trading Coach application has critical authentication failures. 
Despite the login form being properly implemented, no authentication requests 
are reaching the backend successfully.

CURRENT ISSUES TO INVESTIGATE:
1. Frontend login form submits to /api/auth/login but gets no response
2. Direct curl tests to /api/auth/login return 404 Not Found
3. All backend endpoints appear to return 404 despite code showing proper route definitions
4. Backend service shows "RUNNING" status but API endpoints are not accessible

TESTING REQUIREMENTS:
1. Test backend /api/auth/login POST endpoint directly with proper credentials:
   - Username: "Henrijc"
   - Password: "H3nj3n" 
   - TOTP Code: "000000"
2. Verify backend service is properly serving FastAPI application
3. Test other API endpoints to determine if this is a routing issue
4. Check backend logs for any startup errors or missing dependencies
5. Verify authentication service and all dependencies are working

EXPECTED BEHAVIOR:
- POST /api/auth/login should authenticate user and return token + analysis data
- Backend should accept and process login requests
- Authentication should complete successfully allowing access to main dashboard
"""

import requests
import json
import time
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
import subprocess

# Get backend URL from environment
BACKEND_URL = "https://e5da86b9-d0bb-4858-9a9e-eb479f5b9fda.preview.emergentagent.com/api"
BASE_URL = "https://e5da86b9-d0bb-4858-9a9e-eb479f5b9fda.preview.emergentagent.com"

class AuthenticationTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = []
        
        # Test credentials from review request
        self.test_credentials = {
            "username": "Henrijc",
            "password": "H3nj3n",
            "totp_code": "000000"
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
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()
    
    def test_backend_service_status(self):
        """Check if backend service is running via supervisor"""
        try:
            result = subprocess.run(['sudo', 'supervisorctl', 'status', 'backend'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                status_output = result.stdout.strip()
                if "RUNNING" in status_output:
                    self.log_test("Backend Service Status", True, 
                                f"Backend service is running: {status_output}")
                    return True
                else:
                    self.log_test("Backend Service Status", False, 
                                f"Backend service not running: {status_output}")
                    return False
            else:
                self.log_test("Backend Service Status", False, 
                            f"Failed to check service status: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Backend Service Status", False, f"Error checking service: {str(e)}")
            return False
    
    def test_backend_logs(self):
        """Check backend logs for errors"""
        try:
            result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.out.log'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                log_output = result.stdout
                
                # Check for common error patterns
                error_patterns = [
                    'ImportError', 'ModuleNotFoundError', 'SyntaxError', 
                    'ConnectionError', 'Exception', 'Error', 'Failed',
                    'Traceback', 'CRITICAL', 'FATAL'
                ]
                
                errors_found = []
                for pattern in error_patterns:
                    if pattern.lower() in log_output.lower():
                        # Extract lines containing the error
                        error_lines = [line.strip() for line in log_output.split('\n') 
                                     if pattern.lower() in line.lower()]
                        errors_found.extend(error_lines[:3])  # Limit to 3 lines per pattern
                
                if errors_found:
                    self.log_test("Backend Logs Check", False, 
                                f"Errors found in logs: {errors_found[:5]}")  # Show first 5 errors
                    return False
                else:
                    self.log_test("Backend Logs Check", True, 
                                "No critical errors found in recent backend logs")
                    return True
            else:
                self.log_test("Backend Logs Check", False, 
                            f"Failed to read logs: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Backend Logs Check", False, f"Error reading logs: {str(e)}")
            return False
    
    def test_base_url_accessibility(self):
        """Test if the base URL is accessible"""
        try:
            response = self.session.get(BASE_URL, timeout=10)
            
            if response.status_code == 200:
                self.log_test("Base URL Accessibility", True, 
                            f"Base URL accessible, status: {response.status_code}")
                return True
            else:
                self.log_test("Base URL Accessibility", False, 
                            f"Base URL returned status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Base URL Accessibility", False, f"Connection error: {str(e)}")
            return False
    
    def test_api_root_endpoint(self):
        """Test the API root endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', '')
                self.log_test("API Root Endpoint", True, 
                            f"API root accessible: {message}")
                return True
            else:
                self.log_test("API Root Endpoint", False, 
                            f"Status code: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("API Root Endpoint", False, f"Connection error: {str(e)}")
            return False
    
    def test_auth_login_endpoint_exists(self):
        """Test if the auth/login endpoint exists (even if authentication fails)"""
        try:
            # Send a request with invalid credentials to see if endpoint exists
            invalid_credentials = {"username": "invalid", "password": "invalid"}
            
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=invalid_credentials)
            
            # If we get 404, the endpoint doesn't exist
            # If we get 401, 403, or 500, the endpoint exists but authentication failed
            if response.status_code == 404:
                self.log_test("Auth Login Endpoint Exists", False, 
                            f"Endpoint not found (404): {response.text}")
                return False
            elif response.status_code in [401, 403, 422, 500]:
                self.log_test("Auth Login Endpoint Exists", True, 
                            f"Endpoint exists but returned {response.status_code} (expected for invalid credentials)")
                return True
            else:
                self.log_test("Auth Login Endpoint Exists", True, 
                            f"Endpoint exists, returned status: {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("Auth Login Endpoint Exists", False, f"Connection error: {str(e)}")
            return False
    
    def test_auth_login_with_credentials(self):
        """Test authentication with proper credentials"""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=self.test_credentials)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for expected authentication response fields
                expected_fields = ['success', 'token', 'user_id']
                missing_fields = [field for field in expected_fields 
                                if field not in data]
                
                if missing_fields:
                    self.log_test("Auth Login With Credentials", False, 
                                f"Missing expected fields: {missing_fields}, Response: {data}")
                    return False
                
                # Check if authentication was successful
                if data.get('success'):
                    self.log_test("Auth Login With Credentials", True, 
                                f"Authentication successful: {data.get('user_id', 'Unknown user')}")
                    return True
                else:
                    self.log_test("Auth Login With Credentials", False, 
                                f"Authentication failed: {data}")
                    return False
                    
            elif response.status_code == 401:
                self.log_test("Auth Login With Credentials", False, 
                            f"Authentication failed (401): {response.text}")
                return False
            elif response.status_code == 422:
                self.log_test("Auth Login With Credentials", False, 
                            f"Invalid request format (422): {response.text}")
                return False
            else:
                self.log_test("Auth Login With Credentials", False, 
                            f"Unexpected status code {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Auth Login With Credentials", False, f"Connection error: {str(e)}")
            return False
    
    def test_other_api_endpoints(self):
        """Test other API endpoints to determine if this is a routing issue"""
        endpoints_to_test = [
            ("/market/data", "GET"),
            ("/portfolio", "GET"),
            ("/targets/settings", "GET"),
            ("/technical/market-overview", "GET")
        ]
        
        accessible_endpoints = 0
        total_endpoints = len(endpoints_to_test)
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", json={})
                
                # Consider 200, 401, 403, 422, 500 as "endpoint exists"
                # Only 404 means endpoint doesn't exist
                if response.status_code != 404:
                    accessible_endpoints += 1
                    
            except Exception as e:
                # Connection errors suggest broader issues
                continue
        
        if accessible_endpoints == 0:
            self.log_test("Other API Endpoints", False, 
                        f"No API endpoints accessible (0/{total_endpoints})")
            return False
        elif accessible_endpoints < total_endpoints:
            self.log_test("Other API Endpoints", False, 
                        f"Some endpoints accessible ({accessible_endpoints}/{total_endpoints}) - routing issues detected")
            return False
        else:
            self.log_test("Other API Endpoints", True, 
                        f"All tested endpoints accessible ({accessible_endpoints}/{total_endpoints})")
            return True
    
    def test_authentication_service_dependencies(self):
        """Test if authentication service dependencies are working"""
        try:
            # Test if we can access a simple endpoint that doesn't require auth
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code != 200:
                self.log_test("Authentication Service Dependencies", False, 
                            "Basic API not accessible - dependency issues likely")
                return False
            
            # Try to access an endpoint that would use authentication service
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json={"username": "test"})  # Incomplete request
            
            # If we get 422 (validation error), the service is working but request is invalid
            # If we get 500, there might be dependency issues
            # If we get 404, the endpoint doesn't exist
            
            if response.status_code == 404:
                self.log_test("Authentication Service Dependencies", False, 
                            "Authentication endpoint not found")
                return False
            elif response.status_code == 500:
                self.log_test("Authentication Service Dependencies", False, 
                            f"Internal server error (500) - dependency issues: {response.text}")
                return False
            else:
                self.log_test("Authentication Service Dependencies", True, 
                            f"Authentication service responding (status: {response.status_code})")
                return True
                
        except Exception as e:
            self.log_test("Authentication Service Dependencies", False, 
                        f"Error testing dependencies: {str(e)}")
            return False
    
    def test_direct_curl_equivalent(self):
        """Test direct curl equivalent to /api/auth/login"""
        try:
            # This simulates the exact curl command mentioned in the review
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=self.test_credentials,
                headers=headers
            )
            
            if response.status_code == 404:
                self.log_test("Direct Curl Equivalent", False, 
                            f"404 Not Found - endpoint does not exist: {response.text}")
                return False
            elif response.status_code == 200:
                self.log_test("Direct Curl Equivalent", True, 
                            f"Authentication endpoint accessible and returned 200")
                return True
            else:
                self.log_test("Direct Curl Equivalent", True, 
                            f"Endpoint exists but returned {response.status_code} (not 404)")
                return True
                
        except Exception as e:
            self.log_test("Direct Curl Equivalent", False, 
                        f"Connection error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all authentication tests"""
        print("🔐 Starting Critical Authentication System Testing")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print(f"Test credentials: {self.test_credentials['username']}")
        print()
        
        # System-level checks first
        print("🖥️  Testing Backend Service Status...")
        self.test_backend_service_status()
        
        print("📋 Checking Backend Logs...")
        self.test_backend_logs()
        
        # Network connectivity
        print("🌐 Testing Base URL Accessibility...")
        self.test_base_url_accessibility()
        
        print("🔌 Testing API Root Endpoint...")
        self.test_api_root_endpoint()
        
        # Authentication-specific tests
        print("🔍 Testing Auth Login Endpoint Exists...")
        self.test_auth_login_endpoint_exists()
        
        print("🔑 Testing Auth Login With Credentials...")
        self.test_auth_login_with_credentials()
        
        print("🌐 Testing Other API Endpoints...")
        self.test_other_api_endpoints()
        
        print("⚙️  Testing Authentication Service Dependencies...")
        self.test_authentication_service_dependencies()
        
        print("📡 Testing Direct Curl Equivalent...")
        self.test_direct_curl_equivalent()
        
        # Summary
        self.print_summary()
        
        return self.get_overall_success()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📋 CRITICAL AUTHENTICATION SYSTEM TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ CRITICAL ISSUES IDENTIFIED:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
            
            print("\n🔧 RECOMMENDED ACTIONS:")
            
            # Analyze failure patterns and provide recommendations
            failed_test_names = [r['test'] for r in self.test_results if not r['success']]
            
            if "Backend Service Status" in failed_test_names:
                print("  1. Restart backend service: sudo supervisorctl restart backend")
            
            if "Backend Logs Check" in failed_test_names:
                print("  2. Check full backend logs: tail -f /var/log/supervisor/backend.*.log")
            
            if "Auth Login Endpoint Exists" in failed_test_names:
                print("  3. Verify FastAPI router configuration in server.py")
                print("  4. Check if authentication routes are properly included")
            
            if "Base URL Accessibility" in failed_test_names:
                print("  5. Check network connectivity and DNS resolution")
            
            if "Authentication Service Dependencies" in failed_test_names:
                print("  6. Verify all required Python packages are installed")
                print("  7. Check MongoDB connection and authentication service initialization")
                
        else:
            print("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
            print("✅ Backend service is running properly")
            print("✅ Authentication endpoint is accessible")
            print("✅ All dependencies are working correctly")
        
        print("\n" + "=" * 70)
    
    def get_overall_success(self) -> bool:
        """Get overall test success status"""
        if not self.test_results:
            return False
        
        # For authentication, we need high success rate
        passed = len([r for r in self.test_results if r['success']])
        total = len(self.test_results)
        
        # At least 80% success rate required
        return (passed / total) >= 0.8

def main():
    """Main test execution"""
    print("Critical Authentication System Testing for AI Crypto Trading Coach")
    print(f"Testing against: {BACKEND_URL}")
    print()
    
    tester = AuthenticationTester(BACKEND_URL)
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall: AUTHENTICATION SYSTEM TESTS PASSED")
        sys.exit(0)
    else:
        print("💥 Overall: CRITICAL AUTHENTICATION SYSTEM FAILURES DETECTED")
        sys.exit(1)

if __name__ == "__main__":
    main()