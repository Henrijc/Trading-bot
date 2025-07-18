import pandas as pd
import numpy as np
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from services.luno_service import LunoService
import ta
from ta.utils import dropna
from ta.volatility import BollingerBands
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator

class TechnicalAnalysisService:
    def __init__(self):
        self.luno_service = LunoService()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        
    async def get_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical price data for technical analysis"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{days}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    return cached_data
            
            # Since Luno doesn't provide historical data directly, we'll use CoinGecko
            symbol_mapping = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'ADA': 'cardano',
                'XRP': 'ripple',
                'SOL': 'solana',
                'TRX': 'tron',
                'XLM': 'stellar',
                'HBAR': 'hedera-hashgraph',
                'LTC': 'litecoin',
                'DOGE': 'dogecoin',
                'DOT': 'polkadot',
                'AVAX': 'avalanche-2',
                'ATOM': 'cosmos',
                'ALGO': 'algorand',
                'BCH': 'bitcoin-cash'
            }
            
            coin_id = symbol_mapping.get(symbol, symbol.lower())
            
            # Get historical data from CoinGecko
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly' if days <= 30 else 'daily'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Convert to DataFrame
                prices = data.get('prices', [])
                volumes = data.get('total_volumes', [])
                
                if not prices:
                    return pd.DataFrame()
                
                df = pd.DataFrame(prices, columns=['timestamp', 'price'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # Add volume data if available
                if volumes:
                    volume_df = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
                    volume_df['timestamp'] = pd.to_datetime(volume_df['timestamp'], unit='ms')
                    volume_df.set_index('timestamp', inplace=True)
                    df = df.join(volume_df, how='left')
                
                # Add OHLC data (approximated from price)
                df['open'] = df['price'].shift(1)
                df['high'] = df['price'].rolling(window=2, min_periods=1).max()
                df['low'] = df['price'].rolling(window=2, min_periods=1).min()
                df['close'] = df['price']
                
                # Fill NaN values
                df = df.fillna(method='ffill').fillna(method='bfill')
                
                # Cache the data
                self.cache[cache_key] = (df, datetime.now())
                
                return df
            else:
                print(f"Error fetching historical data: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI (Relative Strength Index)"""
        try:
            if df.empty or 'close' not in df.columns:
                return pd.Series()
            
            rsi = RSIIndicator(close=df['close'], window=period)
            return rsi.rsi()
        except Exception as e:
            print(f"Error calculating RSI: {e}")
            return pd.Series()
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        try:
            if df.empty or 'close' not in df.columns:
                return {'macd': pd.Series(), 'signal': pd.Series(), 'histogram': pd.Series()}
            
            macd = MACD(close=df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
            
            return {
                'macd': macd.macd(),
                'signal': macd.macd_signal(),
                'histogram': macd.macd_diff()
            }
        except Exception as e:
            print(f"Error calculating MACD: {e}")
            return {'macd': pd.Series(), 'signal': pd.Series(), 'histogram': pd.Series()}
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            if df.empty or 'close' not in df.columns:
                return {'upper': pd.Series(), 'middle': pd.Series(), 'lower': pd.Series()}
            
            bb = BollingerBands(close=df['close'], window=period, window_dev=std_dev)
            
            return {
                'upper': bb.bollinger_hband(),
                'middle': bb.bollinger_mavg(),
                'lower': bb.bollinger_lband()
            }
        except Exception as e:
            print(f"Error calculating Bollinger Bands: {e}")
            return {'upper': pd.Series(), 'middle': pd.Series(), 'lower': pd.Series()}
    
    def calculate_moving_averages(self, df: pd.DataFrame, periods: List[int] = [10, 20, 50, 200]) -> Dict[str, pd.Series]:
        """Calculate Simple and Exponential Moving Averages"""
        try:
            if df.empty or 'close' not in df.columns:
                return {}
            
            results = {}
            
            for period in periods:
                # Simple Moving Average
                sma = SMAIndicator(close=df['close'], window=period)
                results[f'sma_{period}'] = sma.sma_indicator()
                
                # Exponential Moving Average
                ema = EMAIndicator(close=df['close'], window=period)
                results[f'ema_{period}'] = ema.ema_indicator()
            
            return results
        except Exception as e:
            print(f"Error calculating moving averages: {e}")
            return {}
    
    def calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator"""
        try:
            if df.empty or not all(col in df.columns for col in ['high', 'low', 'close']):
                return {'%k': pd.Series(), '%d': pd.Series()}
            
            stoch = StochasticOscillator(
                high=df['high'], 
                low=df['low'], 
                close=df['close'], 
                window=k_period, 
                smooth_window=d_period
            )
            
            return {
                '%k': stoch.stoch(),
                '%d': stoch.stoch_signal()
            }
        except Exception as e:
            print(f"Error calculating Stochastic: {e}")
            return {'%k': pd.Series(), '%d': pd.Series()}
    
    def detect_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """Detect support and resistance levels"""
        try:
            if df.empty or 'close' not in df.columns:
                return {'support': 0, 'resistance': 0}
            
            # Find local minima and maxima
            closes = df['close'].tail(window * 2)
            
            # Support: recent low levels
            support = closes.rolling(window=window).min().tail(1).iloc[0]
            
            # Resistance: recent high levels
            resistance = closes.rolling(window=window).max().tail(1).iloc[0]
            
            return {
                'support': float(support),
                'resistance': float(resistance)
            }
        except Exception as e:
            print(f"Error detecting support/resistance: {e}")
            return {'support': 0, 'resistance': 0}
    
    def analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze current trend using multiple indicators"""
        try:
            if df.empty:
                return {'trend': 'neutral', 'strength': 0, 'signals': []}
            
            signals = []
            bullish_signals = 0
            bearish_signals = 0
            
            # Get latest values
            latest_close = df['close'].iloc[-1]
            
            # Moving Average Analysis
            ma_data = self.calculate_moving_averages(df, [10, 20, 50])
            if ma_data:
                ma_10 = ma_data['sma_10'].iloc[-1] if not ma_data['sma_10'].empty else 0
                ma_20 = ma_data['sma_20'].iloc[-1] if not ma_data['sma_20'].empty else 0
                ma_50 = ma_data['sma_50'].iloc[-1] if not ma_data['sma_50'].empty else 0
                
                if ma_10 > ma_20 > ma_50:
                    signals.append("Strong bullish trend: Short MA > Medium MA > Long MA")
                    bullish_signals += 2
                elif ma_10 > ma_20:
                    signals.append("Bullish trend: Short MA > Medium MA")
                    bullish_signals += 1
                elif ma_10 < ma_20 < ma_50:
                    signals.append("Strong bearish trend: Short MA < Medium MA < Long MA")
                    bearish_signals += 2
                elif ma_10 < ma_20:
                    signals.append("Bearish trend: Short MA < Medium MA")
                    bearish_signals += 1
            
            # RSI Analysis
            rsi = self.calculate_rsi(df)
            if not rsi.empty:
                current_rsi = rsi.iloc[-1]
                if current_rsi > 70:
                    signals.append(f"RSI overbought: {current_rsi:.1f}")
                    bearish_signals += 1
                elif current_rsi < 30:
                    signals.append(f"RSI oversold: {current_rsi:.1f}")
                    bullish_signals += 1
                elif current_rsi > 50:
                    signals.append(f"RSI bullish: {current_rsi:.1f}")
                    bullish_signals += 0.5
                else:
                    signals.append(f"RSI bearish: {current_rsi:.1f}")
                    bearish_signals += 0.5
            
            # MACD Analysis
            macd_data = self.calculate_macd(df)
            if not macd_data['macd'].empty:
                macd_current = macd_data['macd'].iloc[-1]
                signal_current = macd_data['signal'].iloc[-1]
                
                if macd_current > signal_current:
                    signals.append("MACD bullish: MACD above signal line")
                    bullish_signals += 1
                else:
                    signals.append("MACD bearish: MACD below signal line")
                    bearish_signals += 1
            
            # Bollinger Bands Analysis
            bb_data = self.calculate_bollinger_bands(df)
            if not bb_data['upper'].empty:
                upper = bb_data['upper'].iloc[-1]
                lower = bb_data['lower'].iloc[-1]
                
                if latest_close > upper:
                    signals.append("Price above upper Bollinger Band - potential reversal")
                    bearish_signals += 0.5
                elif latest_close < lower:
                    signals.append("Price below lower Bollinger Band - potential bounce")
                    bullish_signals += 0.5
            
            # Determine overall trend
            net_signals = bullish_signals - bearish_signals
            
            if net_signals > 1:
                trend = "bullish"
                strength = min(net_signals / 3, 1.0)  # Normalize to 0-1
            elif net_signals < -1:
                trend = "bearish"
                strength = min(abs(net_signals) / 3, 1.0)
            else:
                trend = "neutral"
                strength = 0.5
            
            return {
                'trend': trend,
                'strength': strength,
                'signals': signals,
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals
            }
            
        except Exception as e:
            print(f"Error analyzing trend: {e}")
            return {'trend': 'neutral', 'strength': 0, 'signals': []}
    
    async def generate_trading_signals(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive trading signals for a symbol"""
        try:
            # Get historical data
            df = await self.get_historical_data(symbol, days)
            
            if df.empty:
                return {'symbol': symbol, 'error': 'No historical data available'}
            
            # Calculate all indicators
            rsi = self.calculate_rsi(df)
            macd = self.calculate_macd(df)
            bb = self.calculate_bollinger_bands(df)
            ma = self.calculate_moving_averages(df)
            stoch = self.calculate_stochastic(df)
            sr = self.detect_support_resistance(df)
            trend = self.analyze_trend(df)
            
            # Get current price
            current_price = df['close'].iloc[-1]
            
            # Generate specific trading signals
            signals = []
            
            # RSI Signals
            if not rsi.empty:
                current_rsi = rsi.iloc[-1]
                if current_rsi < 30:
                    signals.append({
                        'type': 'BUY',
                        'reason': f'RSI oversold at {current_rsi:.1f}',
                        'strength': 'strong',
                        'indicator': 'RSI'
                    })
                elif current_rsi > 70:
                    signals.append({
                        'type': 'SELL',
                        'reason': f'RSI overbought at {current_rsi:.1f}',
                        'strength': 'strong',
                        'indicator': 'RSI'
                    })
            
            # MACD Signals
            if not macd['macd'].empty and len(macd['macd']) >= 2:
                current_macd = macd['macd'].iloc[-1]
                prev_macd = macd['macd'].iloc[-2]
                current_signal = macd['signal'].iloc[-1]
                prev_signal = macd['signal'].iloc[-2]
                
                # MACD crossover
                if prev_macd <= prev_signal and current_macd > current_signal:
                    signals.append({
                        'type': 'BUY',
                        'reason': 'MACD bullish crossover',
                        'strength': 'medium',
                        'indicator': 'MACD'
                    })
                elif prev_macd >= prev_signal and current_macd < current_signal:
                    signals.append({
                        'type': 'SELL',
                        'reason': 'MACD bearish crossover',
                        'strength': 'medium',
                        'indicator': 'MACD'
                    })
            
            # Bollinger Bands Signals
            if not bb['upper'].empty:
                upper = bb['upper'].iloc[-1]
                lower = bb['lower'].iloc[-1]
                
                if current_price <= lower:
                    signals.append({
                        'type': 'BUY',
                        'reason': 'Price touching lower Bollinger Band',
                        'strength': 'medium',
                        'indicator': 'Bollinger Bands'
                    })
                elif current_price >= upper:
                    signals.append({
                        'type': 'SELL',
                        'reason': 'Price touching upper Bollinger Band',
                        'strength': 'medium',
                        'indicator': 'Bollinger Bands'
                    })
            
            # Support/Resistance Signals
            if sr['support'] > 0 and sr['resistance'] > 0:
                if current_price <= sr['support'] * 1.02:  # Within 2% of support
                    signals.append({
                        'type': 'BUY',
                        'reason': f'Price near support level at {sr["support"]:.2f}',
                        'strength': 'medium',
                        'indicator': 'Support/Resistance'
                    })
                elif current_price >= sr['resistance'] * 0.98:  # Within 2% of resistance
                    signals.append({
                        'type': 'SELL',
                        'reason': f'Price near resistance level at {sr["resistance"]:.2f}',
                        'strength': 'medium',
                        'indicator': 'Support/Resistance'
                    })
            
            # Compile final analysis
            return {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': datetime.now().isoformat(),
                'trend_analysis': trend,
                'technical_indicators': {
                    'rsi': rsi.iloc[-1] if not rsi.empty else None,
                    'macd': {
                        'macd': macd['macd'].iloc[-1] if not macd['macd'].empty else None,
                        'signal': macd['signal'].iloc[-1] if not macd['signal'].empty else None,
                        'histogram': macd['histogram'].iloc[-1] if not macd['histogram'].empty else None
                    },
                    'bollinger_bands': {
                        'upper': bb['upper'].iloc[-1] if not bb['upper'].empty else None,
                        'middle': bb['middle'].iloc[-1] if not bb['middle'].empty else None,
                        'lower': bb['lower'].iloc[-1] if not bb['lower'].empty else None
                    },
                    'support_resistance': sr,
                    'moving_averages': {
                        key: value.iloc[-1] if not value.empty else None
                        for key, value in ma.items()
                    }
                },
                'trading_signals': signals,
                'recommendation': self._generate_recommendation(signals, trend),
                'data_points': len(df)
            }
            
        except Exception as e:
            print(f"Error generating trading signals for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def _generate_recommendation(self, signals: List[Dict], trend: Dict) -> Dict[str, Any]:
        """Generate overall recommendation based on signals"""
        try:
            buy_signals = [s for s in signals if s['type'] == 'BUY']
            sell_signals = [s for s in signals if s['type'] == 'SELL']
            
            buy_strength = sum(2 if s['strength'] == 'strong' else 1 for s in buy_signals)
            sell_strength = sum(2 if s['strength'] == 'strong' else 1 for s in sell_signals)
            
            if buy_strength > sell_strength + 1:
                action = 'BUY'
                confidence = min(buy_strength / 5, 1.0)
            elif sell_strength > buy_strength + 1:
                action = 'SELL'
                confidence = min(sell_strength / 5, 1.0)
            else:
                action = 'HOLD'
                confidence = 0.5
            
            return {
                'action': action,
                'confidence': confidence,
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'trend': trend['trend'],
                'trend_strength': trend['strength']
            }
            
        except Exception as e:
            print(f"Error generating recommendation: {e}")
            return {'action': 'HOLD', 'confidence': 0.5}
    
    async def analyze_portfolio_technical(self, portfolio_data: Dict) -> Dict[str, Any]:
        """Analyze entire portfolio using technical analysis"""
        try:
            holdings = portfolio_data.get('holdings', [])
            
            if not holdings:
                return {'error': 'No holdings to analyze'}
            
            analysis_results = []
            
            for holding in holdings:
                symbol = holding['symbol']
                try:
                    # Get technical analysis for each asset
                    signals = await self.generate_trading_signals(symbol)
                    signals['holding_value'] = holding['value']
                    signals['allocation'] = holding['allocation']
                    analysis_results.append(signals)
                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
                    continue
            
            # Generate portfolio-level insights
            portfolio_insights = self._generate_portfolio_insights(analysis_results)
            
            return {
                'portfolio_total': portfolio_data.get('total_value', 0),
                'analyzed_assets': len(analysis_results),
                'asset_analysis': analysis_results,
                'portfolio_insights': portfolio_insights,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing portfolio technical: {e}")
            return {'error': str(e)}
    
    def _generate_portfolio_insights(self, analysis_results: List[Dict]) -> Dict[str, Any]:
        """Generate portfolio-level insights from individual asset analysis"""
        try:
            total_value = sum(r.get('holding_value', 0) for r in analysis_results)
            
            # Count recommendations by type
            buy_assets = []
            sell_assets = []
            hold_assets = []
            
            for result in analysis_results:
                if 'recommendation' in result:
                    action = result['recommendation']['action']
                    if action == 'BUY':
                        buy_assets.append(result['symbol'])
                    elif action == 'SELL':
                        sell_assets.append(result['symbol'])
                    else:
                        hold_assets.append(result['symbol'])
            
            # Calculate portfolio risk score
            risk_score = self._calculate_portfolio_risk_score(analysis_results)
            
            # Generate rebalancing suggestions
            rebalancing_suggestions = self._generate_rebalancing_suggestions(analysis_results)
            
            return {
                'total_assets': len(analysis_results),
                'buy_recommendations': len(buy_assets),
                'sell_recommendations': len(sell_assets),
                'hold_recommendations': len(hold_assets),
                'buy_assets': buy_assets,
                'sell_assets': sell_assets,
                'risk_score': risk_score,
                'rebalancing_suggestions': rebalancing_suggestions,
                'overall_trend': self._determine_overall_trend(analysis_results)
            }
            
        except Exception as e:
            print(f"Error generating portfolio insights: {e}")
            return {}
    
    def _calculate_portfolio_risk_score(self, analysis_results: List[Dict]) -> float:
        """Calculate overall portfolio risk score based on technical indicators"""
        try:
            risk_factors = 0
            total_factors = 0
            
            for result in analysis_results:
                if 'technical_indicators' in result:
                    indicators = result['technical_indicators']
                    
                    # RSI risk
                    if indicators.get('rsi'):
                        rsi = indicators['rsi']
                        if rsi > 70 or rsi < 30:
                            risk_factors += 1
                        total_factors += 1
                    
                    # Trend risk
                    if 'trend_analysis' in result:
                        trend_strength = result['trend_analysis'].get('strength', 0)
                        if trend_strength > 0.8:  # Very strong trend (could reverse)
                            risk_factors += 0.5
                        total_factors += 1
            
            if total_factors == 0:
                return 0.5  # Neutral risk
            
            return min(risk_factors / total_factors, 1.0)
            
        except Exception as e:
            print(f"Error calculating portfolio risk score: {e}")
            return 0.5
    
    def _generate_rebalancing_suggestions(self, analysis_results: List[Dict]) -> List[Dict]:
        """Generate suggestions for portfolio rebalancing"""
        try:
            suggestions = []
            
            for result in analysis_results:
                symbol = result.get('symbol', '')
                recommendation = result.get('recommendation', {})
                allocation = result.get('allocation', 0)
                
                if recommendation.get('action') == 'SELL' and allocation > 20:
                    suggestions.append({
                        'action': 'REDUCE',
                        'asset': symbol,
                        'reason': f'Technical analysis suggests selling {symbol}, consider reducing allocation from {allocation:.1f}%',
                        'current_allocation': allocation,
                        'suggested_allocation': max(allocation * 0.7, 5)
                    })
                elif recommendation.get('action') == 'BUY' and allocation < 5:
                    suggestions.append({
                        'action': 'INCREASE',
                        'asset': symbol,
                        'reason': f'Technical analysis suggests buying {symbol}, consider increasing allocation from {allocation:.1f}%',
                        'current_allocation': allocation,
                        'suggested_allocation': min(allocation * 1.5, 15)
                    })
            
            return suggestions
            
        except Exception as e:
            print(f"Error generating rebalancing suggestions: {e}")
            return []
    
    def _determine_overall_trend(self, analysis_results: List[Dict]) -> str:
        """Determine overall market trend from portfolio analysis"""
        try:
            bullish_count = 0
            bearish_count = 0
            neutral_count = 0
            
            for result in analysis_results:
                trend_analysis = result.get('trend_analysis', {})
                trend = trend_analysis.get('trend', 'neutral')
                
                if trend == 'bullish':
                    bullish_count += 1
                elif trend == 'bearish':
                    bearish_count += 1
                else:
                    neutral_count += 1
            
            if bullish_count > bearish_count + neutral_count:
                return 'bullish'
            elif bearish_count > bullish_count + neutral_count:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            print(f"Error determining overall trend: {e}")
            return 'neutral'