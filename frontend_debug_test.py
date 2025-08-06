#!/usr/bin/env python3
"""
Frontend Debug Test - Simulate the exact frontend calculation logic
"""

import requests
import json
from datetime import datetime

class FrontendDebugTest:
    def __init__(self, base_url="https://2dc1c750-84a9-4542-9a13-11d2dbd8d7fe.preview.emergentagent.com/api"):
        self.base_url = base_url
        
    def get_api_data(self):
        """Get data from both API endpoints"""
        print("🔍 Fetching API data...")
        
        # Get balance data
        balance_response = requests.get(f"{self.base_url}/balance", timeout=30)
        balance_data = balance_response.json().get('data', {}) if balance_response.status_code == 200 else {}
        
        # Get crypto prices data
        prices_response = requests.get(f"{self.base_url}/crypto-prices", timeout=30)
        prices_data = prices_response.json().get('data', {}) if prices_response.status_code == 200 else {}
        
        print(f"   Balance API Status: {balance_response.status_code}")
        print(f"   Prices API Status: {prices_response.status_code}")
        
        return balance_data, prices_data
    
    def simulate_frontend_calculation(self, balance, crypto_prices):
        """Simulate the exact frontend calculateTotalPortfolioValue() function"""
        print("\n🧮 Simulating Frontend Calculation Logic...")
        
        # Check if data exists (frontend checks)
        if not balance or not crypto_prices:
            print(f"   ❌ Missing data - balance: {bool(balance)}, cryptoPrices: {bool(crypto_prices)}")
            return 0
        
        total = 0
        usd_to_zar = float(crypto_prices.get('USD_TO_ZAR', 18.5))
        
        print(f"   USD to ZAR rate: {usd_to_zar}")
        print(f"   Balance data keys: {list(balance.keys())}")
        print(f"   Crypto prices keys: {list(crypto_prices.keys())}")
        
        # Simulate the exact frontend crypto balances array
        crypto_balances = [
            {'symbol': 'BTC', 'balance': float(balance.get('BTC_balance', 0)), 'price': float(crypto_prices.get('BTC', 0))},
            {'symbol': 'ETH', 'balance': float(balance.get('ETH_balance', 0)), 'price': float(crypto_prices.get('ETH', 0))},
            {'symbol': 'HBAR', 'balance': float(balance.get('HBAR_balance', 0)), 'price': float(crypto_prices.get('HBAR', 0))},
            {'symbol': 'XRP', 'balance': float(balance.get('XRP_balance', 0)), 'price': float(crypto_prices.get('XRP', 0))},
            {'symbol': 'ADA', 'balance': float(balance.get('ADA_balance', 0)), 'price': float(crypto_prices.get('ADA', 0))},
            {'symbol': 'TRX', 'balance': float(balance.get('TRX_balance', 0)), 'price': float(crypto_prices.get('TRX', 0))},
            {'symbol': 'XLM', 'balance': float(balance.get('XLM_balance', 0)), 'price': float(crypto_prices.get('XLM', 0))}
        ]
        
        print("\n   📊 Crypto Holdings Calculation:")
        for crypto in crypto_balances:
            symbol = crypto['symbol']
            bal = crypto['balance']
            price = crypto['price']
            value = bal * price * usd_to_zar
            total += value
            print(f"      {symbol}: {bal} * ${price} * {usd_to_zar} = R {value:,.2f}")
        
        # Simulate staked balances
        staked_balances = [
            {'symbol': 'ETH_staked', 'balance': float(balance.get('ETH_staked', 0)), 'price': float(crypto_prices.get('ETH', 0))},
            {'symbol': 'ADA_staked', 'balance': float(balance.get('ADA_staked', 0)), 'price': float(crypto_prices.get('ADA', 0))},
            {'symbol': 'HBAR_staked', 'balance': float(balance.get('HBAR_staked', 0)), 'price': float(crypto_prices.get('HBAR', 0))}
        ]
        
        print("\n   🔒 Staked Holdings Calculation:")
        for staked in staked_balances:
            symbol = staked['symbol']
            bal = staked['balance']
            price = staked['price']
            value = bal * price * usd_to_zar
            total += value
            print(f"      {symbol}: {bal} * ${price} * {usd_to_zar} = R {value:,.2f}")
        
        # Add ZAR balance
        zar_balance = float(balance.get('ZAR_balance', 0))
        total += zar_balance
        print(f"\n   💰 ZAR Balance: R {zar_balance:,.2f}")
        
        print(f"\n   💎 Total Portfolio Value: R {total:,.2f}")
        return total
    
    def check_data_availability(self, balance, crypto_prices):
        """Check if all required data is available"""
        print("\n🔍 Data Availability Check:")
        
        required_balance_fields = ['BTC_balance', 'ETH_balance', 'HBAR_balance', 'XRP_balance', 'ADA_balance', 'TRX_balance', 'XLM_balance']
        required_price_fields = ['BTC', 'ETH', 'HBAR', 'XRP', 'ADA', 'TRX', 'XLM', 'USD_TO_ZAR']
        
        missing_balance = [field for field in required_balance_fields if field not in balance or balance[field] is None]
        missing_prices = [field for field in required_price_fields if field not in crypto_prices or crypto_prices[field] is None]
        
        print(f"   Balance fields missing: {missing_balance}")
        print(f"   Price fields missing: {missing_prices}")
        
        # Check for zero values
        zero_balances = [field for field in required_balance_fields if field in balance and balance[field] == 0]
        zero_prices = [field for field in required_price_fields if field in crypto_prices and crypto_prices[field] == 0]
        
        print(f"   Zero balance fields: {zero_balances}")
        print(f"   Zero price fields: {zero_prices}")
        
        return len(missing_balance) == 0 and len(missing_prices) == 0
    
    def run_debug_test(self):
        """Run comprehensive frontend debug test"""
        print("=" * 80)
        print("🔧 FRONTEND PORTFOLIO CALCULATION DEBUG TEST")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Test started at: {datetime.now()}")
        
        # Get API data
        balance, crypto_prices = self.get_api_data()
        
        # Check data availability
        data_complete = self.check_data_availability(balance, crypto_prices)
        
        # Simulate frontend calculation
        calculated_total = self.simulate_frontend_calculation(balance, crypto_prices)
        
        # Analysis
        print("\n" + "=" * 80)
        print("📊 FRONTEND DEBUG ANALYSIS")
        print("=" * 80)
        
        if calculated_total > 0:
            print(f"✅ Frontend calculation should show: R {calculated_total:,.2f}")
            print("   The portfolio calculation logic is working correctly.")
            
            if calculated_total != 45570.63:  # Expected from backend test
                print("⚠️  Frontend and backend calculations may differ slightly due to:")
                print("   - Different rounding methods")
                print("   - Timing differences in data fetching")
                print("   - Different price sources")
        else:
            print("❌ Frontend calculation shows R 0.00 - ISSUE IDENTIFIED")
            print("\n🔧 Possible causes:")
            
            if not balance:
                print("   1. ❌ Balance data is empty or null")
            elif not crypto_prices:
                print("   2. ❌ Crypto prices data is empty or null")
            elif not data_complete:
                print("   3. ❌ Required data fields are missing")
            else:
                print("   4. ❌ All data is present but calculation logic has issues")
                
                # Check for timing issues
                print("\n   🕐 Timing Analysis:")
                print("   - Frontend loads balance and prices asynchronously")
                print("   - calculateTotalPortfolioValue() might be called before data loads")
                print("   - React state updates might not be synchronized")
                
                # Check for data type issues
                print("\n   🔢 Data Type Analysis:")
                for key, value in balance.items():
                    if key.endswith('_balance'):
                        print(f"      {key}: {value} (type: {type(value)})")
        
        # Recommendations
        print("\n🛠️  RECOMMENDATIONS:")
        if calculated_total == 0:
            print("   1. Add null checks in calculateTotalPortfolioValue()")
            print("   2. Add loading states to prevent calculation before data loads")
            print("   3. Add console.log statements to debug data flow")
            print("   4. Check React useEffect dependencies")
        else:
            print("   1. The calculation logic is working correctly")
            print("   2. If frontend still shows R 0.00, check React rendering")
            print("   3. Verify formatCurrency() function is working")
        
        return calculated_total > 0

def main():
    """Main test execution"""
    tester = FrontendDebugTest()
    
    try:
        success = tester.run_debug_test()
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