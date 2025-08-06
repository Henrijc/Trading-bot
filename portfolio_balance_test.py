#!/usr/bin/env python3
"""
Portfolio Balance Calculation Test
Specifically tests the portfolio balance calculation issue where total shows R 0.00
"""

import requests
import json
from datetime import datetime

class PortfolioBalanceTest:
    def __init__(self, base_url="https://2dc1c750-84a9-4542-9a13-11d2dbd8d7fe.preview.emergentagent.com/api"):
        self.base_url = base_url
        
    def test_balance_endpoint(self):
        """Test /api/balance endpoint and analyze the data"""
        print("🔍 Testing /api/balance endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/balance", timeout=30)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                balance_data = data.get('data', {})
                
                print("   ✅ Balance endpoint working correctly")
                print("   📊 Balance Data Analysis:")
                
                # Extract crypto balances
                crypto_balances = {}
                for key, value in balance_data.items():
                    if key.endswith('_balance') and value > 0:
                        crypto = key.replace('_balance', '')
                        crypto_balances[crypto] = value
                        print(f"      {crypto}: {value}")
                
                return True, crypto_balances
            else:
                print(f"   ❌ Balance endpoint failed with status {response.status_code}")
                return False, {}
                
        except Exception as e:
            print(f"   ❌ Balance endpoint error: {str(e)}")
            return False, {}
    
    def test_crypto_prices_endpoint(self):
        """Test /api/crypto-prices endpoint and analyze the data"""
        print("\n🔍 Testing /api/crypto-prices endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/crypto-prices", timeout=30)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                price_data = data.get('data', {})
                
                print("   ✅ Crypto prices endpoint working correctly")
                print("   💰 Price Data Analysis:")
                
                usd_to_zar = price_data.get('USD_TO_ZAR', 0)
                print(f"      USD to ZAR rate: {usd_to_zar}")
                
                crypto_prices = {}
                for crypto, price in price_data.items():
                    if crypto != 'USD_TO_ZAR':
                        crypto_prices[crypto] = price
                        print(f"      {crypto}: ${price} USD")
                
                return True, crypto_prices, usd_to_zar
            else:
                print(f"   ❌ Crypto prices endpoint failed with status {response.status_code}")
                return False, {}, 0
                
        except Exception as e:
            print(f"   ❌ Crypto prices endpoint error: {str(e)}")
            return False, {}, 0
    
    def calculate_portfolio_value(self, balances, prices, usd_to_zar):
        """Calculate total portfolio value in ZAR"""
        print("\n🧮 Calculating Portfolio Value...")
        
        total_value_zar = 0
        calculations = []
        
        for crypto, balance in balances.items():
            if crypto in prices:
                usd_price = prices[crypto]
                crypto_value_usd = balance * usd_price
                crypto_value_zar = crypto_value_usd * usd_to_zar
                total_value_zar += crypto_value_zar
                
                calculation = {
                    'crypto': crypto,
                    'balance': balance,
                    'usd_price': usd_price,
                    'value_usd': crypto_value_usd,
                    'value_zar': crypto_value_zar
                }
                calculations.append(calculation)
                
                print(f"   {crypto}: {balance} × ${usd_price} × {usd_to_zar} = R {crypto_value_zar:,.2f}")
            else:
                print(f"   ⚠️  No price data for {crypto}")
        
        print(f"\n   💎 Total Portfolio Value: R {total_value_zar:,.2f}")
        return total_value_zar, calculations
    
    def compare_with_expected_values(self, balances):
        """Compare actual balances with user's expected values"""
        print("\n📋 Comparing with Expected Values...")
        
        expected_values = {
            'BTC': 0.015055,
            'ETH': 0.3063,
            'HBAR': 762,
            'XRP': 1086.45,
            'ADA': 84.00,
            'ETH_staked': 0.0918,
            'HBAR_staked': 152,
            'ADA_staked': 42.00
        }
        
        matches = 0
        total_expected = len(expected_values)
        
        for crypto, expected in expected_values.items():
            actual = balances.get(crypto, 0)
            if abs(actual - expected) < 0.01:  # Allow small differences
                print(f"   ✅ {crypto}: Expected {expected}, Got {actual} - MATCH")
                matches += 1
            else:
                print(f"   ❌ {crypto}: Expected {expected}, Got {actual} - MISMATCH")
        
        print(f"\n   📊 Match Rate: {matches}/{total_expected} ({(matches/total_expected)*100:.1f}%)")
        return matches == total_expected
    
    def run_comprehensive_test(self):
        """Run comprehensive portfolio balance test"""
        print("=" * 80)
        print("🚀 PORTFOLIO BALANCE CALCULATION TEST")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Test started at: {datetime.now()}")
        
        # Test balance endpoint
        balance_success, balances = self.test_balance_endpoint()
        
        # Test crypto prices endpoint
        prices_success, prices, usd_to_zar = self.test_crypto_prices_endpoint()
        
        if balance_success and prices_success:
            # Calculate portfolio value
            total_value, calculations = self.calculate_portfolio_value(balances, prices, usd_to_zar)
            
            # Compare with expected values
            values_match = self.compare_with_expected_values(balances)
            
            # Final analysis
            print("\n" + "=" * 80)
            print("📊 FINAL ANALYSIS")
            print("=" * 80)
            
            if total_value > 0:
                print(f"✅ Portfolio calculation working: R {total_value:,.2f}")
                print("   The backend APIs are returning correct data and calculations work.")
                
                if not values_match:
                    print("⚠️  However, actual balances don't match user's expected values.")
                    print("   This suggests the user's screenshot may be outdated or from a different account.")
                
            else:
                print("❌ Portfolio shows R 0.00 - ISSUE CONFIRMED")
                print("   Possible causes:")
                print("   1. All crypto balances are zero")
                print("   2. Price data is missing or zero")
                print("   3. USD to ZAR conversion rate is zero")
                print("   4. Frontend calculation logic has bugs")
            
            # Detailed breakdown for debugging
            print("\n🔧 DEBUG INFORMATION:")
            print(f"   Balance endpoint working: {balance_success}")
            print(f"   Prices endpoint working: {prices_success}")
            print(f"   USD to ZAR rate: {usd_to_zar}")
            print(f"   Number of crypto holdings: {len(balances)}")
            print(f"   Number of price entries: {len(prices)}")
            
            return total_value > 0
        else:
            print("\n❌ CRITICAL: One or both API endpoints are failing")
            print("   Cannot calculate portfolio value without working APIs")
            return False

def main():
    """Main test execution"""
    tester = PortfolioBalanceTest()
    
    try:
        success = tester.run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())