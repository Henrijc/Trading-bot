#!/usr/bin/env python3
"""
Detailed Investigation of Failed Tests
"""

import requests
import json
import sys

BACKEND_URL = "https://0cfbd3ed-dae1-446a-a9cf-a2c7cbb1213a.preview.emergentagent.com/api"

def investigate_auth_failure():
    """Investigate authentication failure"""
    print("🔍 INVESTIGATING AUTHENTICATION FAILURE")
    print("=" * 50)
    
    session = requests.Session()
    session.timeout = 15
    
    login_data = {
        "username": "Henrijc",
        "password": "H3nj3n",
        "backup_code": "0D6CCC6A"
    }
    
    try:
        response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Keys: {list(data.keys())}")
            print(f"Response Data: {json.dumps(data, indent=2)}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    print()

def investigate_chat_failure():
    """Investigate chat endpoint failure"""
    print("🔍 INVESTIGATING CHAT ENDPOINT FAILURE")
    print("=" * 50)
    
    session = requests.Session()
    session.timeout = 15
    
    chat_data = {
        "session_id": "test_session_123",
        "message": "What's the current BTC price?",
        "context": None
    }
    
    try:
        response = session.post(f"{BACKEND_URL}/chat/send", json=chat_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 422:
            data = response.json()
            print(f"Validation Error: {json.dumps(data, indent=2)}")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    print()

def investigate_market_data_failure():
    """Investigate market data failure"""
    print("🔍 INVESTIGATING MARKET DATA FAILURE")
    print("=" * 50)
    
    session = requests.Session()
    session.timeout = 15
    
    try:
        response = session.get(f"{BACKEND_URL}/market/data")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Type: {type(data)}")
            print(f"Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            print(f"Response Sample: {str(data)[:500]}...")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    print()

def main():
    print("🔍 DETAILED INVESTIGATION OF FAILED TESTS")
    print("=" * 70)
    print()
    
    investigate_auth_failure()
    investigate_chat_failure()
    investigate_market_data_failure()

if __name__ == "__main__":
    main()