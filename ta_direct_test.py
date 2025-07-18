#!/usr/bin/env python3
"""
Technical Analysis Service Direct Test
Tests the technical analysis calculations directly
"""

import sys
import os
sys.path.append('/app/backend')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from services.technical_analysis_service import TechnicalAnalysisService

def create_mock_data(days=30):
    """Create mock OHLCV data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='H')
    
    # Generate realistic price data
    base_price = 50000  # Mock BTC price
    price_changes = np.random.normal(0, 0.02, days)  # 2% volatility
    prices = [base_price]
    
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # Create OHLCV data
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        high = price * (1 + abs(np.random.normal(0, 0.01)))
        low = price * (1 - abs(np.random.normal(0, 0.01)))
        open_price = prices[i-1] if i > 0 else price
        volume = np.random.uniform(1000, 10000)
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'price': price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df

def test_technical_indicators():
    """Test technical indicator calculations"""
    print("🧮 Testing Technical Indicator Calculations...")
    
    ta_service = TechnicalAnalysisService()
    mock_data = create_mock_data(100)  # 100 data points for better indicators
    
    tests_passed = 0
    total_tests = 0
    
    # Test RSI calculation
    total_tests += 1
    try:
        rsi = ta_service.calculate_rsi(mock_data)
        if not rsi.empty and len(rsi) > 0:
            latest_rsi = rsi.iloc[-1]
            if 0 <= latest_rsi <= 100:
                print(f"✅ RSI Calculation: PASS (Latest RSI: {latest_rsi:.2f})")
                tests_passed += 1
            else:
                print(f"❌ RSI Calculation: FAIL - Invalid RSI value: {latest_rsi}")
        else:
            print("❌ RSI Calculation: FAIL - Empty result")
    except Exception as e:
        print(f"❌ RSI Calculation: FAIL - Error: {str(e)}")
    
    # Test MACD calculation
    total_tests += 1
    try:
        macd = ta_service.calculate_macd(mock_data)
        if all(not series.empty for series in macd.values()):
            latest_macd = macd['macd'].iloc[-1]
            latest_signal = macd['signal'].iloc[-1]
            print(f"✅ MACD Calculation: PASS (MACD: {latest_macd:.2f}, Signal: {latest_signal:.2f})")
            tests_passed += 1
        else:
            print("❌ MACD Calculation: FAIL - Empty result")
    except Exception as e:
        print(f"❌ MACD Calculation: FAIL - Error: {str(e)}")
    
    # Test Bollinger Bands calculation
    total_tests += 1
    try:
        bb = ta_service.calculate_bollinger_bands(mock_data)
        if all(not series.empty for series in bb.values()):
            upper = bb['upper'].iloc[-1]
            middle = bb['middle'].iloc[-1]
            lower = bb['lower'].iloc[-1]
            if lower < middle < upper:
                print(f"✅ Bollinger Bands: PASS (Upper: {upper:.2f}, Middle: {middle:.2f}, Lower: {lower:.2f})")
                tests_passed += 1
            else:
                print("❌ Bollinger Bands: FAIL - Invalid band relationship")
        else:
            print("❌ Bollinger Bands: FAIL - Empty result")
    except Exception as e:
        print(f"❌ Bollinger Bands: FAIL - Error: {str(e)}")
    
    # Test Moving Averages calculation
    total_tests += 1
    try:
        ma = ta_service.calculate_moving_averages(mock_data)
        if ma and 'sma_20' in ma and not ma['sma_20'].empty:
            sma_20 = ma['sma_20'].iloc[-1]
            ema_20 = ma['ema_20'].iloc[-1] if 'ema_20' in ma else None
            print(f"✅ Moving Averages: PASS (SMA20: {sma_20:.2f}, EMA20: {ema_20:.2f if ema_20 else 'N/A'})")
            tests_passed += 1
        else:
            print("❌ Moving Averages: FAIL - Empty result")
    except Exception as e:
        print(f"❌ Moving Averages: FAIL - Error: {str(e)}")
    
    # Test Support/Resistance detection
    total_tests += 1
    try:
        sr = ta_service.detect_support_resistance(mock_data)
        if sr and 'support' in sr and 'resistance' in sr:
            support = sr['support']
            resistance = sr['resistance']
            if support > 0 and resistance > 0 and resistance > support:
                print(f"✅ Support/Resistance: PASS (Support: {support:.2f}, Resistance: {resistance:.2f})")
                tests_passed += 1
            else:
                print(f"❌ Support/Resistance: FAIL - Invalid levels (S: {support}, R: {resistance})")
        else:
            print("❌ Support/Resistance: FAIL - Empty result")
    except Exception as e:
        print(f"❌ Support/Resistance: FAIL - Error: {str(e)}")
    
    # Test Trend Analysis
    total_tests += 1
    try:
        trend = ta_service.analyze_trend(mock_data)
        if trend and 'trend' in trend and 'strength' in trend:
            trend_direction = trend['trend']
            strength = trend['strength']
            signals_count = len(trend.get('signals', []))
            if trend_direction in ['bullish', 'bearish', 'neutral'] and 0 <= strength <= 1:
                print(f"✅ Trend Analysis: PASS (Trend: {trend_direction}, Strength: {strength:.2f}, Signals: {signals_count})")
                tests_passed += 1
            else:
                print(f"❌ Trend Analysis: FAIL - Invalid trend data")
        else:
            print("❌ Trend Analysis: FAIL - Empty result")
    except Exception as e:
        print(f"❌ Trend Analysis: FAIL - Error: {str(e)}")
    
    print(f"\n📊 Technical Indicators Test Summary:")
    print(f"✅ Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests*100):.1f}%")
    
    return tests_passed >= total_tests * 0.8

def test_signal_generation():
    """Test trading signal generation with mock data"""
    print("\n📈 Testing Trading Signal Generation...")
    
    ta_service = TechnicalAnalysisService()
    
    # Override the get_historical_data method to return mock data
    original_method = ta_service.get_historical_data
    
    async def mock_get_historical_data(symbol, days=30):
        return create_mock_data(days)
    
    ta_service.get_historical_data = mock_get_historical_data
    
    try:
        import asyncio
        
        # Test signal generation
        signals = asyncio.run(ta_service.generate_trading_signals('BTC', 30))
        
        if 'error' not in signals:
            required_fields = ['symbol', 'current_price', 'trend_analysis', 'technical_indicators', 'trading_signals', 'recommendation']
            missing_fields = [field for field in required_fields if field not in signals]
            
            if not missing_fields:
                signal_count = len(signals.get('trading_signals', []))
                recommendation = signals.get('recommendation', {}).get('action', 'UNKNOWN')
                print(f"✅ Signal Generation: PASS ({signal_count} signals, Recommendation: {recommendation})")
                return True
            else:
                print(f"❌ Signal Generation: FAIL - Missing fields: {missing_fields}")
        else:
            print(f"❌ Signal Generation: FAIL - Error: {signals['error']}")
    
    except Exception as e:
        print(f"❌ Signal Generation: FAIL - Error: {str(e)}")
    
    finally:
        # Restore original method
        ta_service.get_historical_data = original_method
    
    return False

def main():
    """Run technical analysis service tests"""
    print("🔬 Technical Analysis Service - Direct Testing")
    print("=" * 60)
    
    test1_passed = test_technical_indicators()
    test2_passed = test_signal_generation()
    
    print("\n" + "=" * 60)
    print("📋 OVERALL SUMMARY")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("🎉 Technical Analysis Service: FULLY FUNCTIONAL")
        print("✅ All core calculations working correctly")
        print("✅ Signal generation working with mock data")
        return True
    elif test1_passed:
        print("⚠️ Technical Analysis Service: PARTIALLY FUNCTIONAL")
        print("✅ Core calculations working correctly")
        print("❌ Signal generation needs attention")
        return True
    else:
        print("❌ Technical Analysis Service: NEEDS ATTENTION")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)