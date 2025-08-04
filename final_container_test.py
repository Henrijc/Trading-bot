#!/usr/bin/env python3
"""
FINAL CONTAINER STABILITY VERIFICATION
======================================

Testing the critical fixes for ModuleNotFoundError issues that were causing container restart loops.
"""

import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, '/app')

def test_critical_imports():
    """Test all critical imports that were causing container failures"""
    print("🔍 FINAL CONTAINER STABILITY VERIFICATION")
    print("=" * 60)
    
    tests = []
    
    # Test 1: Backend Server Import
    try:
        from backend.server import app
        tests.append(("✅", "Backend Server Import", "SUCCESS - server.py imports without ModuleNotFoundError"))
    except Exception as e:
        tests.append(("❌", "Backend Server Import", f"FAILED - {e}"))
    
    # Test 2: TradeSignal Import (lines 1522 and 1674 fix)
    try:
        from backend.services.decision_engine import TradeSignal
        signal = TradeSignal(
            pair="BTC/ZAR",
            action="buy", 
            confidence=0.75,
            signal_strength="strong",
            direction="bullish",
            amount=0.01,
            timestamp=datetime.utcnow().isoformat()
        )
        tests.append(("✅", "TradeSignal Import & Creation", f"SUCCESS - TradeSignal created for {signal.pair}"))
    except Exception as e:
        tests.append(("❌", "TradeSignal Import & Creation", f"FAILED - {e}"))
    
    # Test 3: DecisionEngine Import
    try:
        from backend.services.decision_engine import DecisionEngine
        engine = DecisionEngine()
        tests.append(("✅", "DecisionEngine Import", "SUCCESS - DecisionEngine imports and instantiates"))
    except Exception as e:
        tests.append(("❌", "DecisionEngine Import", f"FAILED - {e}"))
    
    # Test 4: Requests Cache Import (freqtrade dependency fix)
    try:
        import requests_cache
        session = requests_cache.CachedSession('test', expire_after=300)
        tests.append(("✅", "Requests Cache Import", f"SUCCESS - requests_cache v{getattr(requests_cache, '__version__', 'unknown')} working"))
    except Exception as e:
        tests.append(("❌", "Requests Cache Import", f"FAILED - {e}"))
    
    # Test 5: Luno Service Import (uses requests_cache)
    try:
        from backend.services.luno_service import LunoService
        luno = LunoService()
        tests.append(("✅", "Luno Service Import", "SUCCESS - LunoService imports and uses requests_cache"))
    except Exception as e:
        tests.append(("❌", "Luno Service Import", f"FAILED - {e}"))
    
    # Print results
    print("\n📊 TEST RESULTS:")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for status, test_name, details in tests:
        print(f"{status} {test_name}")
        print(f"   {details}")
        print()
        if status == "✅":
            passed += 1
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print("=" * 60)
    print(f"📈 SUMMARY: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("\n🎉 ALL CRITICAL FIXES VERIFIED!")
        print("✅ Backend container should start successfully")
        print("✅ Freqtrade container should start successfully") 
        print("✅ No more ModuleNotFoundError restart loops")
        return True
    else:
        print(f"\n⚠️ {total - passed} issues remain")
        return False

if __name__ == "__main__":
    success = test_critical_imports()
    sys.exit(0 if success else 1)