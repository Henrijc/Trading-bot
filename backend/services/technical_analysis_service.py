import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import ccxt
from datetime import datetime, timedelta
import asyncio
import logging

class TechnicalAnalysisService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Initialize exchanges for data
        self.exchanges = {
            'binance': ccxt.binance(),
            'coinbase': ccxt.coinbasepro() 
        }
        
    async def get_historical_data(self, symbol: str, timeframe: str = '1d', limit: int = 100) -> pd.DataFrame:
        """Get historical OHLCV data for a symbol"""
        try:
            # Convert common symbols to exchange format
            symbol_mapping = {
                'BTC': 'BTC/USDT',
                'ETH': 'ETH/USDT', 
                'ADA': 'ADA/USDT',
                'XRP': 'XRP/USDT',
                'SOL': 'SOL/USDT',
                'TRX': 'TRX/USDT',
                'XLM': 'XLM/USDT',
                'HBAR': 'HBAR/USDT'
            }
            
            exchange_symbol = symbol_mapping.get(symbol, f'{symbol}/USDT')
            
            # Try to get data from Binance first
            exchange = self.exchanges['binance']
            ohlcv = exchange.fetch_ohlcv(exchange_symbol, timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            # Return empty DataFrame with proper structure
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI manually without external dependencies"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(prices), index=prices.index)
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        try:
            return prices.rolling(window=period).mean()
        except:
            return pd.Series([0] * len(prices), index=prices.index)
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        try:
            return prices.ewm(span=period).mean()
        except:
            return pd.Series([0] * len(prices), index=prices.index)
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD manually"""
        try:
            ema_fast = self.calculate_ema(prices, fast)
            ema_slow = self.calculate_ema(prices, slow)
            macd_line = ema_fast - ema_slow
            signal_line = self.calculate_ema(macd_line, signal)
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
        except:
            return {
                'macd': pd.Series([0] * len(prices), index=prices.index),
                'signal': pd.Series([0] * len(prices), index=prices.index),
                'histogram': pd.Series([0] * len(prices), index=prices.index)
            }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict:
        """Calculate Bollinger Bands manually"""
        try:
            sma = self.calculate_sma(prices, period)
            std = prices.rolling(window=period).std()
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return {
                'upper': upper_band,
                'middle': sma,
                'lower': lower_band
            }
        except:
            return {
                'upper': pd.Series([0] * len(prices), index=prices.index),
                'middle': pd.Series([0] * len(prices), index=prices.index),
                'lower': pd.Series([0] * len(prices), index=prices.index)
            }
    
    async def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators using pure Python"""
        try:
            if df.empty or len(df) < 14:
                return {
                    'rsi': 50,
                    'macd': {'macd': 0, 'signal': 0, 'histogram': 0},
                    'bollinger_bands': {'upper': 0, 'middle': 0, 'lower': 0},
                    'moving_averages': {'sma_20': 0, 'sma_50': 0, 'ema_12': 0, 'ema_26': 0}
                }
            
            # RSI (14-period)
            rsi_values = self.calculate_rsi(df['close'], 14)
            
            # MACD
            macd_data = self.calculate_macd(df['close'])
            
            # Bollinger Bands
            bb_data = self.calculate_bollinger_bands(df['close'])
            
            # Moving Averages
            sma_20 = self.calculate_sma(df['close'], 20)
            sma_50 = self.calculate_sma(df['close'], 50)
            ema_12 = self.calculate_ema(df['close'], 12)
            ema_26 = self.calculate_ema(df['close'], 26)
            
            # Get latest values safely
            latest_idx = -1
            
            indicators = {
                'rsi': float(rsi_values.iloc[latest_idx]) if not pd.isna(rsi_values.iloc[latest_idx]) else 50,
                'macd': {
                    'macd': float(macd_data['macd'].iloc[latest_idx]) if not pd.isna(macd_data['macd'].iloc[latest_idx]) else 0,
                    'signal': float(macd_data['signal'].iloc[latest_idx]) if not pd.isna(macd_data['signal'].iloc[latest_idx]) else 0,
                    'histogram': float(macd_data['histogram'].iloc[latest_idx]) if not pd.isna(macd_data['histogram'].iloc[latest_idx]) else 0
                },
                'bollinger_bands': {
                    'upper': float(bb_data['upper'].iloc[latest_idx]) if not pd.isna(bb_data['upper'].iloc[latest_idx]) else 0,
                    'middle': float(bb_data['middle'].iloc[latest_idx]) if not pd.isna(bb_data['middle'].iloc[latest_idx]) else 0,
                    'lower': float(bb_data['lower'].iloc[latest_idx]) if not pd.isna(bb_data['lower'].iloc[latest_idx]) else 0
                },
                'moving_averages': {
                    'sma_20': float(sma_20.iloc[latest_idx]) if not pd.isna(sma_20.iloc[latest_idx]) else 0,
                    'sma_50': float(sma_50.iloc[latest_idx]) if not pd.isna(sma_50.iloc[latest_idx]) else 0,
                    'ema_12': float(ema_12.iloc[latest_idx]) if not pd.isna(ema_12.iloc[latest_idx]) else 0,
                    'ema_26': float(ema_26.iloc[latest_idx]) if not pd.isna(ema_26.iloc[latest_idx]) else 0
                }
            }
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {
                'rsi': 50,
                'macd': {'macd': 0, 'signal': 0, 'histogram': 0},
                'bollinger_bands': {'upper': 0, 'middle': 0, 'lower': 0},
                'moving_averages': {'sma_20': 0, 'sma_50': 0, 'ema_12': 0, 'ema_26': 0}
            }
    
    async def analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price trend"""
        try:
            if df.empty or len(df) < 20:
                return {
                    'trend': 'neutral',
                    'strength': 'weak',
                    'direction': 'sideways',
                    'support_levels': [],
                    'resistance_levels': []
                }
            
            # Calculate trend using moving averages
            sma_20 = self.calculate_sma(df['close'], 20)
            sma_50 = self.calculate_sma(df['close'], 50)
            
            current_price = df['close'].iloc[-1]
            sma_20_val = sma_20.iloc[-1]
            sma_50_val = sma_50.iloc[-1]
            
            # Determine trend
            if pd.notna(sma_20_val) and pd.notna(sma_50_val):
                if current_price > sma_20_val > sma_50_val:
                    trend = 'bullish'
                elif current_price < sma_20_val < sma_50_val:
                    trend = 'bearish'
                else:
                    trend = 'neutral'
            else:
                trend = 'neutral'
            
            # Calculate trend strength based on price movement
            price_change_5d = (df['close'].iloc[-1] - df['close'].iloc[-6]) / df['close'].iloc[-6] * 100 if len(df) > 5 else 0
            
            if abs(price_change_5d) > 5:
                strength = 'strong'
            elif abs(price_change_5d) > 2:
                strength = 'moderate'
            else:
                strength = 'weak'
            
            # Simple support/resistance using recent highs/lows
            recent_highs = df['high'].tail(20).nlargest(3).tolist()
            recent_lows = df['low'].tail(20).nsmallest(3).tolist()
            
            return {
                'trend': trend,
                'strength': strength,
                'direction': 'up' if price_change_5d > 0 else 'down' if price_change_5d < 0 else 'sideways',
                'price_change_5d': round(price_change_5d, 2),
                'support_levels': [round(level, 2) for level in recent_lows],
                'resistance_levels': [round(level, 2) for level in recent_highs]
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trend: {e}")
            return {
                'trend': 'neutral',
                'strength': 'weak', 
                'direction': 'sideways',
                'price_change_5d': 0,
                'support_levels': [],
                'resistance_levels': []
            }
    
    async def generate_trading_signals(self, symbol: str, period_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive trading signals for a symbol"""
        try:
            # Get historical data
            df = await self.get_historical_data(symbol, '1d', period_days + 50)
            
            if df.empty:
                return {
                    'error': f'No data available for {symbol}',
                    'recommendation': {'action': 'HOLD', 'confidence': 0},
                    'technical_indicators': {},
                    'trend_analysis': {}
                }
            
            # Calculate indicators
            indicators = await self.calculate_technical_indicators(df)
            trend_analysis = await self.analyze_trend(df)
            
            # Generate trading recommendation
            recommendation = self._generate_recommendation(indicators, trend_analysis, df)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'current_price': float(df['close'].iloc[-1]),
                'recommendation': recommendation,
                'technical_indicators': indicators,
                'trend_analysis': trend_analysis,
                'volume_analysis': {
                    'avg_volume_20d': float(df['volume'].tail(20).mean()),
                    'current_volume': float(df['volume'].iloc[-1]),
                    'volume_trend': 'increasing' if df['volume'].iloc[-1] > df['volume'].tail(20).mean() else 'decreasing'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating trading signals for {symbol}: {e}")
            return {
                'error': str(e),
                'symbol': symbol,
                'recommendation': {'action': 'HOLD', 'confidence': 0},
                'technical_indicators': {},
                'trend_analysis': {}
            }
    
    def _generate_recommendation(self, indicators: Dict, trend: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading recommendation based on technical analysis"""
        try:
            signals = []
            confidence_score = 0
            
            # RSI Analysis
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                signals.append('RSI oversold - potential buy')
                confidence_score += 20
            elif rsi > 70:
                signals.append('RSI overbought - potential sell')
                confidence_score -= 20
            
            # MACD Analysis  
            macd_data = indicators.get('macd', {})
            macd = macd_data.get('macd', 0)
            signal = macd_data.get('signal', 0)
            
            if macd > signal and macd > 0:
                signals.append('MACD bullish crossover')
                confidence_score += 15
            elif macd < signal and macd < 0:
                signals.append('MACD bearish crossover')
                confidence_score -= 15
            
            # Trend Analysis
            trend_direction = trend.get('trend', 'neutral')
            if trend_direction == 'bullish':
                signals.append('Bullish trend confirmed')
                confidence_score += 25
            elif trend_direction == 'bearish':
                signals.append('Bearish trend confirmed')
                confidence_score -= 25
            
            # Moving Average Analysis
            ma_data = indicators.get('moving_averages', {})
            current_price = float(df['close'].iloc[-1])
            sma_20 = ma_data.get('sma_20', 0)
            
            if current_price > sma_20 and sma_20 > 0:
                signals.append('Price above 20-day SMA')
                confidence_score += 10
            elif current_price < sma_20 and sma_20 > 0:
                signals.append('Price below 20-day SMA')
                confidence_score -= 10
            
            # Generate final recommendation
            if confidence_score > 30:
                action = 'BUY'
                confidence = min(confidence_score, 85)
            elif confidence_score < -30:
                action = 'SELL'
                confidence = min(abs(confidence_score), 85)
            else:
                action = 'HOLD'
                confidence = 50
            
            return {
                'action': action,
                'confidence': confidence,
                'signals': signals,
                'score': confidence_score,
                'reasoning': f"Based on {len(signals)} technical indicators showing {action.lower()} signals"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0,
                'signals': ['Error analyzing data'],
                'score': 0,
                'reasoning': 'Technical analysis unavailable'
            }
    
    async def get_market_overview(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get market overview for multiple symbols"""
        try:
            if not symbols:
                symbols = ['BTC', 'ETH', 'ADA', 'XRP', 'SOL']
            
            overview = {
                'timestamp': datetime.utcnow().isoformat(),
                'symbols': {}
            }
            
            # Get signals for each symbol
            for symbol in symbols:
                try:
                    signals = await self.generate_trading_signals(symbol, 14)
                    overview['symbols'][symbol] = {
                        'price': signals.get('current_price', 0),
                        'recommendation': signals.get('recommendation', {}),
                        'trend': signals.get('trend_analysis', {}).get('trend', 'neutral')
                    }
                except Exception as e:
                    self.logger.error(f"Error getting overview for {symbol}: {e}")
                    overview['symbols'][symbol] = {
                        'price': 0,
                        'recommendation': {'action': 'HOLD', 'confidence': 0},
                        'trend': 'error'
                    }
            
            # Calculate market sentiment
            buy_signals = sum(1 for s in overview['symbols'].values() if s['recommendation'].get('action') == 'BUY')
            sell_signals = sum(1 for s in overview['symbols'].values() if s['recommendation'].get('action') == 'SELL')
            total_signals = len(symbols)
            
            if buy_signals > sell_signals:
                market_sentiment = 'bullish'
            elif sell_signals > buy_signals:
                market_sentiment = 'bearish'
            else:
                market_sentiment = 'neutral'
            
            overview['market_sentiment'] = {
                'sentiment': market_sentiment,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'hold_signals': total_signals - buy_signals - sell_signals
            }
            
            return overview
            
        except Exception as e:
            self.logger.error(f"Error getting market overview: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'symbols': {},
                'market_sentiment': {'sentiment': 'error', 'buy_signals': 0, 'sell_signals': 0, 'hold_signals': 0}
            }