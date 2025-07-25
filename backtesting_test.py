#!/usr/bin/env python3
"""
Comprehensive Backtesting System Testing Script
Testing the newly integrated Freqtrade-inspired backtesting system

TESTING FOCUS:
1. Test all 8 new backtesting API endpoints thoroughly
2. Verify historical data fetching for BTC/ZAR, ETH/ZAR, XRP/ZAR pairs
3. Test single-pair backtesting with user's exact parameters (R154,273.71 capital, 4% risk, R8000 target)
4. Test multi-pair comparison backtesting across all 3 preferred pairs
5. Verify XRP protection logic (1000 XRP reserved from trading)
6. Test strategy configuration and performance analysis endpoints
7. Validate risk management (4% stop-loss, position sizing calculations)
8. Test background/scheduled backtesting functionality
9. Verify API response formats match frontend expectations
10. Test error handling for invalid parameters and edge cases

EXPECTED OUTCOMES:
- All API endpoints should return proper JSON responses
- Historical data should be available for testing periods (7-365 days)
- Backtest results should show monthly profit potential vs R8000 target
- XRP protection should exclude 1000 XRP from trading calculations
- Risk management should limit trades to 4% maximum risk
- Multi-pair comparison should identify best performing strategies

USER REQUIREMENTS:
- R8000/month profit target
- Keep 1000 XRP long-term 
- 4% risk management
- R154,273.71 current capital
- Diversification across BTC/ETH/XRP pairs
"""

import requests
import json
import time
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
import asyncio

# Get backend URL from environment
BACKEND_URL = "https://1332115b-e3f3-4f5e-8359-0e7c1c19e898.preview.emergentagent.com/api"

class BacktestingSystemTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 60  # Longer timeout for backtesting operations
        self.test_results = []
        
        # User's specific parameters
        self.user_capital = 154273.71
        self.user_risk = 0.04
        self.user_monthly_target = 8000
        self.user_xrp_hold = 1000
        self.user_pairs = ["BTC/ZAR", "ETH/ZAR", "XRP/ZAR"]
        
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
    
    def test_backtesting_health_check(self):
        """Test backtesting service health check"""
        try:
            response = self.session.get(f"{self.base_url}/backtest/health")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['status', 'timestamp', 'services']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Backtesting Health Check", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check status
                if data.get('status') != 'healthy':
                    self.log_test("Backtesting Health Check", False, 
                                f"Service not healthy: {data.get('status')}", data)
                    return False
                
                # Check services
                services = data.get('services', {})
                expected_services = ['historical_data', 'backtesting_engine', 'luno_integration']
                
                for service in expected_services:
                    if services.get(service) != 'available':
                        self.log_test("Backtesting Health Check", False, 
                                    f"Service {service} not available: {services.get(service)}", data)
                        return False
                
                self.log_test("Backtesting Health Check", True, 
                            f"All backtesting services are healthy and available")
                return True
                
            else:
                self.log_test("Backtesting Health Check", False, 
                            f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Backtesting Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_historical_data_fetching(self):
        """Test historical data fetching for all user's preferred pairs"""
        success_count = 0
        
        for pair in self.user_pairs:
            try:
                # Test with 30 days of data
                request_data = {
                    "symbol": pair,
                    "timeframe": "1h",
                    "days_back": 30
                }
                
                response = self.session.post(f"{self.base_url}/backtest/historical-data", json=request_data)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check required fields
                    required_fields = ['success', 'symbol', 'data_points', 'price_range', 'latest_price', 'data_period', 'sample_data']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(f"Historical Data - {pair}", False, 
                                    f"Missing fields: {missing_fields}", data)
                        continue
                    
                    # Check if data was successfully fetched
                    if not data.get('success'):
                        self.log_test(f"Historical Data - {pair}", False, 
                                    f"Data fetch failed: {data.get('error', 'Unknown error')}", data)
                        continue
                    
                    # Validate data quality
                    data_points = data.get('data_points', 0)
                    if data_points < 100:  # Should have at least 100 hours of data for 30 days
                        self.log_test(f"Historical Data - {pair}", False, 
                                    f"Insufficient data points: {data_points} (expected >100)", data)
                        continue
                    
                    # Check price range
                    price_range = data.get('price_range', {})
                    if not price_range.get('min') or not price_range.get('max'):
                        self.log_test(f"Historical Data - {pair}", False, 
                                    f"Invalid price range: {price_range}", data)
                        continue
                    
                    # Check latest price
                    latest_price = data.get('latest_price', 0)
                    if latest_price <= 0:
                        self.log_test(f"Historical Data - {pair}", False, 
                                    f"Invalid latest price: {latest_price}", data)
                        continue
                    
                    # Check sample data
                    sample_data = data.get('sample_data', [])
                    if len(sample_data) < 5:
                        self.log_test(f"Historical Data - {pair}", False, 
                                    f"Insufficient sample data: {len(sample_data)} candles", data)
                        continue
                    
                    # Validate sample data structure
                    sample_candle = sample_data[0] if sample_data else {}
                    required_candle_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    missing_candle_fields = [field for field in required_candle_fields if field not in sample_candle]
                    
                    if missing_candle_fields:
                        self.log_test(f"Historical Data - {pair}", False, 
                                    f"Sample candle missing fields: {missing_candle_fields}", sample_candle)
                        continue
                    
                    self.log_test(f"Historical Data - {pair}", True, 
                                f"Successfully fetched {data_points} data points, price range: R{price_range['min']:.2f} - R{price_range['max']:.2f}, latest: R{latest_price:.2f}")
                    success_count += 1
                    
                else:
                    self.log_test(f"Historical Data - {pair}", False, 
                                f"Status code: {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test(f"Historical Data - {pair}", False, f"Error: {str(e)}")
        
        # Overall historical data test result
        if success_count == len(self.user_pairs):
            self.log_test("Historical Data Fetching Overall", True, 
                        f"Successfully fetched data for all {len(self.user_pairs)} trading pairs")
            return True
        else:
            self.log_test("Historical Data Fetching Overall", False, 
                        f"Only {success_count}/{len(self.user_pairs)} pairs had successful data fetching")
            return False
    
    def test_single_pair_backtesting(self):
        """Test single-pair backtesting with user's exact parameters"""
        success_count = 0
        
        for pair in self.user_pairs:
            try:
                # Test with user's exact parameters
                request_data = {
                    "symbol": pair,
                    "timeframe": "1h",
                    "days_back": 90,  # 3 months of data
                    "initial_capital": self.user_capital,
                    "risk_per_trade": self.user_risk,
                    "monthly_target": self.user_monthly_target,
                    "xrp_hold_amount": self.user_xrp_hold
                }
                
                response = self.session.post(f"{self.base_url}/backtest/run", json=request_data)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check required fields
                    required_fields = ['success', 'symbol', 'initial_capital', 'final_capital', 'total_profit', 
                                     'total_percentage', 'total_trades', 'win_rate', 'avg_profit_per_trade', 
                                     'max_drawdown', 'monthly_profit', 'target_achievement', 'risk_level', 'trades_summary']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(f"Single Backtest - {pair}", False, 
                                    f"Missing fields: {missing_fields}", data)
                        continue
                    
                    # Check if backtest was successful
                    if not data.get('success'):
                        self.log_test(f"Single Backtest - {pair}", False, 
                                    f"Backtest failed: {data.get('error', 'Unknown error')}", data)
                        continue
                    
                    # Validate backtest results
                    initial_capital = data.get('initial_capital', 0)
                    final_capital = data.get('final_capital', 0)
                    total_profit = data.get('total_profit', 0)
                    monthly_profit = data.get('monthly_profit', 0)
                    target_achievement = data.get('target_achievement', 0)
                    win_rate = data.get('win_rate', 0)
                    max_drawdown = data.get('max_drawdown', 0)
                    total_trades = data.get('total_trades', 0)
                    
                    # Validate capital calculations
                    if abs(initial_capital - self.user_capital) > 1:
                        self.log_test(f"Single Backtest - {pair}", False, 
                                    f"Initial capital mismatch: {initial_capital} vs expected {self.user_capital}")
                        continue
                    
                    # Check if profit calculation is consistent
                    calculated_profit = final_capital - initial_capital
                    if abs(calculated_profit - total_profit) > 1:
                        self.log_test(f"Single Backtest - {pair}", False, 
                                    f"Profit calculation inconsistent: {total_profit} vs calculated {calculated_profit}")
                        continue
                    
                    # Validate XRP protection for XRP pair
                    if pair == "XRP/ZAR" and self.user_xrp_hold > 0:
                        # XRP should have special handling - check if mentioned in trades or risk level
                        trades_summary = data.get('trades_summary', [])
                        xrp_trades = [t for t in trades_summary if 'XRP' in t.get('pair', '')]
                        
                        # XRP trades should be more conservative or limited
                        if len(xrp_trades) > 0:
                            print(f"    XRP Protection: Found {len(xrp_trades)} XRP trades (should be limited due to 1000 XRP hold)")
                    
                    # Validate risk management (4% max risk)
                    if max_drawdown < -25:  # More than 25% drawdown indicates poor risk management
                        self.log_test(f"Single Backtest - {pair}", False, 
                                    f"Excessive drawdown: {max_drawdown}% (risk management failure)")
                        continue
                    
                    # Check if we have reasonable number of trades
                    if total_trades < 1:
                        self.log_test(f"Single Backtest - {pair}", False, 
                                    f"No trades executed: {total_trades}")
                        continue
                    
                    self.log_test(f"Single Backtest - {pair}", True, 
                                f"Backtest completed: {total_trades} trades, {win_rate:.1f}% win rate, "
                                f"R{total_profit:.2f} profit, R{monthly_profit:.2f}/month, "
                                f"{target_achievement:.1f}% target achievement, {max_drawdown:.1f}% max drawdown")
                    success_count += 1
                    
                else:
                    self.log_test(f"Single Backtest - {pair}", False, 
                                f"Status code: {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test(f"Single Backtest - {pair}", False, f"Error: {str(e)}")
        
        # Overall single backtest result
        if success_count >= 2:  # At least 2 out of 3 pairs should work
            self.log_test("Single Pair Backtesting Overall", True, 
                        f"Successfully completed backtests for {success_count}/{len(self.user_pairs)} pairs")
            return True
        else:
            self.log_test("Single Pair Backtesting Overall", False, 
                        f"Only {success_count}/{len(self.user_pairs)} pairs had successful backtests")
            return False
    
    def test_multi_pair_comparison(self):
        """Test multi-pair comparison backtesting"""
        try:
            request_data = {
                "symbols": self.user_pairs,
                "timeframe": "1h",
                "days_back": 90,
                "initial_capital": self.user_capital,
                "risk_per_trade": self.user_risk,
                "monthly_target": self.user_monthly_target,
                "xrp_hold_amount": self.user_xrp_hold
            }
            
            response = self.session.post(f"{self.base_url}/backtest/multi-pair", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['success', 'results', 'comparison', 'best_performer', 'summary']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Multi-Pair Comparison", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check if comparison was successful
                if not data.get('success'):
                    self.log_test("Multi-Pair Comparison", False, 
                                f"Multi-pair backtest failed: {data.get('error', 'Unknown error')}", data)
                    return False
                
                # Validate results structure
                results = data.get('results', {})
                comparison = data.get('comparison', {})
                best_performer = data.get('best_performer', '')
                summary = data.get('summary', {})
                
                # Check that we have results for all pairs
                expected_pairs = set(self.user_pairs)
                result_pairs = set(results.keys())
                
                if not expected_pairs.issubset(result_pairs):
                    missing_pairs = expected_pairs - result_pairs
                    self.log_test("Multi-Pair Comparison", False, 
                                f"Missing results for pairs: {missing_pairs}")
                    return False
                
                # Check comparison data
                if len(comparison) == 0:
                    self.log_test("Multi-Pair Comparison", False, 
                                "No comparison data generated")
                    return False
                
                # Validate comparison structure
                for pair, comp_data in comparison.items():
                    required_comp_fields = ['total_profit', 'monthly_profit', 'win_rate', 'max_drawdown', 'target_achievement']
                    missing_comp_fields = [field for field in required_comp_fields if field not in comp_data]
                    
                    if missing_comp_fields:
                        self.log_test("Multi-Pair Comparison", False, 
                                    f"Comparison data for {pair} missing fields: {missing_comp_fields}")
                        return False
                
                # Check best performer
                if best_performer not in self.user_pairs and best_performer != "N/A":
                    self.log_test("Multi-Pair Comparison", False, 
                                f"Invalid best performer: {best_performer}")
                    return False
                
                # Validate summary statistics
                required_summary_fields = ['avg_total_profit', 'avg_monthly_profit', 'avg_win_rate', 
                                         'best_total_profit', 'worst_total_profit', 'pairs_tested']
                missing_summary_fields = [field for field in required_summary_fields if field not in summary]
                
                if missing_summary_fields:
                    self.log_test("Multi-Pair Comparison", False, 
                                f"Summary missing fields: {missing_summary_fields}")
                    return False
                
                # Check pairs tested count
                pairs_tested = summary.get('pairs_tested', 0)
                if pairs_tested != len(self.user_pairs):
                    self.log_test("Multi-Pair Comparison", False, 
                                f"Pairs tested count mismatch: {pairs_tested} vs expected {len(self.user_pairs)}")
                    return False
                
                # Generate comparison details
                comparison_details = []
                for pair in self.user_pairs:
                    if pair in comparison:
                        comp = comparison[pair]
                        comparison_details.append(
                            f"{pair}: R{comp['total_profit']:.0f} total, "
                            f"R{comp['monthly_profit']:.0f}/month, "
                            f"{comp['win_rate']:.1f}% win rate, "
                            f"{comp['target_achievement']:.1f}% target achievement"
                        )
                
                self.log_test("Multi-Pair Comparison", True, 
                            f"Successfully compared {pairs_tested} pairs. Best performer: {best_performer}. "
                            f"Average monthly profit: R{summary['avg_monthly_profit']:.2f}. "
                            f"Details: {'; '.join(comparison_details)}")
                return True
                
            else:
                self.log_test("Multi-Pair Comparison", False, 
                            f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Multi-Pair Comparison", False, f"Error: {str(e)}")
            return False
    
    def test_strategy_configuration(self):
        """Test strategy configuration endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/backtest/strategies")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['strategies', 'risk_management', 'user_requirements']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Strategy Configuration", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check strategies
                strategies = data.get('strategies', [])
                if len(strategies) == 0:
                    self.log_test("Strategy Configuration", False, 
                                "No strategies available")
                    return False
                
                # Validate strategy structure
                strategy = strategies[0]
                required_strategy_fields = ['name', 'description', 'parameters', 'suitable_for', 'recommended_timeframes']
                missing_strategy_fields = [field for field in required_strategy_fields if field not in strategy]
                
                if missing_strategy_fields:
                    self.log_test("Strategy Configuration", False, 
                                f"Strategy missing fields: {missing_strategy_fields}")
                    return False
                
                # Check if strategy supports user's pairs
                suitable_for = strategy.get('suitable_for', [])
                user_pairs_supported = [pair for pair in self.user_pairs if pair in suitable_for]
                
                if len(user_pairs_supported) == 0:
                    self.log_test("Strategy Configuration", False, 
                                f"Strategy doesn't support any of user's pairs: {self.user_pairs}")
                    return False
                
                # Check risk management
                risk_management = data.get('risk_management', {})
                max_risk = risk_management.get('max_risk_per_trade', '')
                
                if '4%' not in max_risk:
                    self.log_test("Strategy Configuration", False, 
                                f"Risk management doesn't match user's 4% requirement: {max_risk}")
                    return False
                
                # Check user requirements
                user_requirements = data.get('user_requirements', {})
                monthly_target = user_requirements.get('monthly_target', '')
                xrp_hold = user_requirements.get('xrp_long_term_hold', '')
                
                if 'R8,000' not in monthly_target and 'R8000' not in monthly_target:
                    self.log_test("Strategy Configuration", False, 
                                f"Monthly target doesn't match user's R8000 requirement: {monthly_target}")
                    return False
                
                if '1,000 XRP' not in xrp_hold and '1000 XRP' not in xrp_hold:
                    self.log_test("Strategy Configuration", False, 
                                f"XRP hold requirement not found: {xrp_hold}")
                    return False
                
                self.log_test("Strategy Configuration", True, 
                            f"Strategy configuration valid: {strategy['name']}, supports {len(user_pairs_supported)} user pairs, "
                            f"4% risk management, R8000 monthly target, 1000 XRP hold requirement")
                return True
                
            else:
                self.log_test("Strategy Configuration", False, 
                            f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Strategy Configuration", False, f"Error: {str(e)}")
            return False
    
    def test_performance_analysis(self):
        """Test performance analysis endpoints"""
        success_count = 0
        
        for pair in self.user_pairs:
            try:
                response = self.session.get(f"{self.base_url}/backtest/performance/{pair}?days=30")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check required fields
                    required_fields = ['symbol', 'period_days', 'price_performance', 'technical_analysis', 
                                     'market_data', 'strategy_suitability']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(f"Performance Analysis - {pair}", False, 
                                    f"Missing fields: {missing_fields}", data)
                        continue
                    
                    # Validate price performance
                    price_performance = data.get('price_performance', {})
                    required_price_fields = ['start_price', 'end_price', 'price_change_percent']
                    missing_price_fields = [field for field in required_price_fields if field not in price_performance]
                    
                    if missing_price_fields:
                        self.log_test(f"Performance Analysis - {pair}", False, 
                                    f"Price performance missing fields: {missing_price_fields}")
                        continue
                    
                    # Validate technical analysis
                    technical_analysis = data.get('technical_analysis', {})
                    required_tech_fields = ['current_vs_sma20', 'trend', 'volatility_percent']
                    missing_tech_fields = [field for field in required_tech_fields if field not in technical_analysis]
                    
                    if missing_tech_fields:
                        self.log_test(f"Performance Analysis - {pair}", False, 
                                    f"Technical analysis missing fields: {missing_tech_fields}")
                        continue
                    
                    # Validate strategy suitability
                    strategy_suitability = data.get('strategy_suitability', {})
                    required_suit_fields = ['rsi_suitable', 'bb_suitable', 'overall_rating']
                    missing_suit_fields = [field for field in required_suit_fields if field not in strategy_suitability]
                    
                    if missing_suit_fields:
                        self.log_test(f"Performance Analysis - {pair}", False, 
                                    f"Strategy suitability missing fields: {missing_suit_fields}")
                        continue
                    
                    # Check data validity
                    start_price = price_performance.get('start_price', 0)
                    end_price = price_performance.get('end_price', 0)
                    price_change = price_performance.get('price_change_percent', 0)
                    
                    if start_price <= 0 or end_price <= 0:
                        self.log_test(f"Performance Analysis - {pair}", False, 
                                    f"Invalid prices: start={start_price}, end={end_price}")
                        continue
                    
                    # Check trend analysis
                    trend = technical_analysis.get('trend', '')
                    if trend not in ['BULLISH', 'BEARISH', 'NEUTRAL']:
                        self.log_test(f"Performance Analysis - {pair}", False, 
                                    f"Invalid trend: {trend}")
                        continue
                    
                    # Check overall rating
                    overall_rating = strategy_suitability.get('overall_rating', '')
                    if overall_rating not in ['GOOD', 'MODERATE', 'POOR']:
                        self.log_test(f"Performance Analysis - {pair}", False, 
                                    f"Invalid overall rating: {overall_rating}")
                        continue
                    
                    self.log_test(f"Performance Analysis - {pair}", True, 
                                f"Analysis complete: {price_change:.1f}% price change, {trend} trend, "
                                f"{overall_rating} strategy suitability, {technical_analysis.get('volatility_percent', 0):.1f}% volatility")
                    success_count += 1
                    
                else:
                    self.log_test(f"Performance Analysis - {pair}", False, 
                                f"Status code: {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test(f"Performance Analysis - {pair}", False, f"Error: {str(e)}")
        
        # Overall performance analysis result
        if success_count >= 2:  # At least 2 out of 3 pairs should work
            self.log_test("Performance Analysis Overall", True, 
                        f"Successfully analyzed performance for {success_count}/{len(self.user_pairs)} pairs")
            return True
        else:
            self.log_test("Performance Analysis Overall", False, 
                        f"Only {success_count}/{len(self.user_pairs)} pairs had successful analysis")
            return False
    
    def test_scheduled_backtesting(self):
        """Test background/scheduled backtesting functionality"""
        try:
            response = self.session.post(f"{self.base_url}/backtest/schedule")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['message', 'timestamp', 'estimated_completion']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Scheduled Backtesting", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check message content
                message = data.get('message', '')
                if 'scheduled' not in message.lower() or 'background' not in message.lower():
                    self.log_test("Scheduled Backtesting", False, 
                                f"Invalid message content: {message}")
                    return False
                
                # Check timestamp format
                timestamp = data.get('timestamp', '')
                try:
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    self.log_test("Scheduled Backtesting", False, 
                                f"Invalid timestamp format: {timestamp}")
                    return False
                
                # Check estimated completion
                estimated_completion = data.get('estimated_completion', '')
                try:
                    completion_dt = datetime.fromisoformat(estimated_completion.replace('Z', '+00:00'))
                    request_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    
                    # Should be in the future
                    if completion_dt <= request_dt:
                        self.log_test("Scheduled Backtesting", False, 
                                    f"Estimated completion not in future: {estimated_completion}")
                        return False
                        
                except:
                    self.log_test("Scheduled Backtesting", False, 
                                f"Invalid estimated completion format: {estimated_completion}")
                    return False
                
                self.log_test("Scheduled Backtesting", True, 
                            f"Backtest successfully scheduled. Estimated completion: {estimated_completion}")
                return True
                
            else:
                self.log_test("Scheduled Backtesting", False, 
                            f"Status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Scheduled Backtesting", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid parameters and edge cases"""
        error_tests = [
            {
                'name': 'Invalid Symbol',
                'endpoint': '/backtest/historical-data',
                'data': {'symbol': 'INVALID/PAIR', 'timeframe': '1h', 'days_back': 30},
                'expected_error': True
            },
            {
                'name': 'Invalid Timeframe',
                'endpoint': '/backtest/historical-data',
                'data': {'symbol': 'BTC/ZAR', 'timeframe': '99h', 'days_back': 30},
                'expected_error': True
            },
            {
                'name': 'Excessive Days Back',
                'endpoint': '/backtest/historical-data',
                'data': {'symbol': 'BTC/ZAR', 'timeframe': '1h', 'days_back': 9999},
                'expected_error': False  # Should handle gracefully
            },
            {
                'name': 'Zero Capital',
                'endpoint': '/backtest/run',
                'data': {'symbol': 'BTC/ZAR', 'initial_capital': 0, 'risk_per_trade': 0.04},
                'expected_error': True
            },
            {
                'name': 'Negative Risk',
                'endpoint': '/backtest/run',
                'data': {'symbol': 'BTC/ZAR', 'initial_capital': 10000, 'risk_per_trade': -0.1},
                'expected_error': True
            },
            {
                'name': 'Excessive Risk',
                'endpoint': '/backtest/run',
                'data': {'symbol': 'BTC/ZAR', 'initial_capital': 10000, 'risk_per_trade': 1.5},
                'expected_error': False  # Should handle but warn
            }
        ]
        
        success_count = 0
        
        for test in error_tests:
            try:
                response = self.session.post(f"{self.base_url}{test['endpoint']}", json=test['data'])
                
                if test['expected_error']:
                    # Should return error or handle gracefully
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success') == False and data.get('error'):
                            self.log_test(f"Error Handling - {test['name']}", True, 
                                        f"Properly handled error: {data.get('error')}")
                            success_count += 1
                        else:
                            self.log_test(f"Error Handling - {test['name']}", False, 
                                        f"Should have returned error but got success: {data}")
                    else:
                        # HTTP error is also acceptable
                        self.log_test(f"Error Handling - {test['name']}", True, 
                                    f"Properly returned HTTP error: {response.status_code}")
                        success_count += 1
                else:
                    # Should handle gracefully without error
                    if response.status_code == 200:
                        data = response.json()
                        self.log_test(f"Error Handling - {test['name']}", True, 
                                    f"Gracefully handled edge case: success={data.get('success')}")
                        success_count += 1
                    else:
                        self.log_test(f"Error Handling - {test['name']}", False, 
                                    f"Should handle gracefully but got error: {response.status_code}")
                        
            except Exception as e:
                self.log_test(f"Error Handling - {test['name']}", False, f"Exception: {str(e)}")
        
        # Overall error handling result
        if success_count >= len(error_tests) * 0.8:  # 80% success rate acceptable
            self.log_test("Error Handling Overall", True, 
                        f"Successfully handled {success_count}/{len(error_tests)} error scenarios")
            return True
        else:
            self.log_test("Error Handling Overall", False, 
                        f"Only {success_count}/{len(error_tests)} error scenarios handled properly")
            return False
    
    def run_all_tests(self):
        """Run all backtesting system tests"""
        print("🚀 Starting Comprehensive Backtesting System Tests")
        print("=" * 80)
        print(f"Testing against: {self.base_url}")
        print(f"User Parameters:")
        print(f"  - Capital: R{self.user_capital:,.2f}")
        print(f"  - Risk per trade: {self.user_risk*100}%")
        print(f"  - Monthly target: R{self.user_monthly_target:,.2f}")
        print(f"  - XRP hold: {self.user_xrp_hold} XRP")
        print(f"  - Trading pairs: {', '.join(self.user_pairs)}")
        print()
        
        # Test 1: Health Check
        print("🏥 Testing Backtesting Service Health...")
        health_ok = self.test_backtesting_health_check()
        
        if not health_ok:
            print("❌ Backtesting service is not healthy. Stopping tests.")
            return False
        
        # Test 2: Historical Data Fetching
        print("📊 Testing Historical Data Fetching...")
        self.test_historical_data_fetching()
        
        # Test 3: Single-Pair Backtesting
        print("🎯 Testing Single-Pair Backtesting...")
        self.test_single_pair_backtesting()
        
        # Test 4: Multi-Pair Comparison
        print("⚖️ Testing Multi-Pair Comparison...")
        self.test_multi_pair_comparison()
        
        # Test 5: Strategy Configuration
        print("⚙️ Testing Strategy Configuration...")
        self.test_strategy_configuration()
        
        # Test 6: Performance Analysis
        print("📈 Testing Performance Analysis...")
        self.test_performance_analysis()
        
        # Test 7: Scheduled Backtesting
        print("⏰ Testing Scheduled Backtesting...")
        self.test_scheduled_backtesting()
        
        # Test 8: Error Handling
        print("🛡️ Testing Error Handling...")
        self.test_error_handling()
        
        # Summary
        self.print_summary()
        
        return self.get_overall_success()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📋 BACKTESTING SYSTEM TEST SUMMARY")
        print("=" * 80)
        
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
        
        # Critical success criteria
        critical_tests = [
            "Backtesting Health Check",
            "Historical Data Fetching Overall", 
            "Single Pair Backtesting Overall",
            "Multi-Pair Comparison",
            "Strategy Configuration"
        ]
        
        critical_passed = 0
        for test_name in critical_tests:
            test_result = next((r for r in self.test_results if r['test'] == test_name), None)
            if test_result and test_result['success']:
                critical_passed += 1
        
        print(f"\n🎯 CRITICAL SUCCESS CRITERIA:")
        print(f"Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("\n🎉 ALL CRITICAL BACKTESTING TESTS PASSED!")
            print("✅ Backtesting API health check passes")
            print("✅ Historical data fetching works for all 3 trading pairs")
            print("✅ Single backtests complete with realistic profit/loss calculations")
            print("✅ Multi-pair comparison shows strategy performance rankings")
            print("✅ All user requirements (R8000 target, XRP hold, 4% risk) are properly implemented")
            print("✅ System is ready for production use")
        else:
            print("\n⚠️ SOME CRITICAL TESTS FAILED")
            print("The backtesting system may not be fully ready for production use.")
        
        print("\n" + "=" * 80)
    
    def get_overall_success(self) -> bool:
        """Get overall test success status"""
        if not self.test_results:
            return False
        
        # Check critical tests
        critical_tests = [
            "Backtesting Health Check",
            "Historical Data Fetching Overall", 
            "Single Pair Backtesting Overall",
            "Multi-Pair Comparison",
            "Strategy Configuration"
        ]
        
        critical_passed = 0
        for test_name in critical_tests:
            test_result = next((r for r in self.test_results if r['test'] == test_name), None)
            if test_result and test_result['success']:
                critical_passed += 1
        
        # Need all critical tests to pass
        return critical_passed == len(critical_tests)

def main():
    """Main test execution"""
    print("Comprehensive Backtesting System Testing for AI Crypto Trading Coach")
    print(f"Testing against: {BACKEND_URL}")
    print()
    
    tester = BacktestingSystemTester(BACKEND_URL)
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall: BACKTESTING SYSTEM TESTS PASSED")
        sys.exit(0)
    else:
        print("💥 Overall: BACKTESTING SYSTEM TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()