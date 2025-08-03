import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import ccxt
from datetime import datetime, timedelta
import asyncio
import logging

# FIXED: Use pandas-ta instead of TA-Lib to avoid compilation issues
import pandas_ta as ta

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
    
    async def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators using pandas-ta"""
        try:
            if df.empty or len(df) < 14:
                return {
                    'rsi': 50,
                    'macd': {'macd': 0, 'signal': 0, 'histogram': 0},
                    'bollinger_bands': {'upper': 0, 'middle': 0, 'lower': 0},
                    'moving_averages': {'sma_20': 0, 'sma_50': 0, 'ema_12': 0, 'ema_26': 0}
                }
            
            # RSI (14-period)
            df['rsi'] = ta.rsi(df['close'], length=14)
            
            # MACD
            macd_data = ta.macd(df['close'])
            
            # Bollinger Bands
            bb_data = ta.bbands(df['close'], length=20)
            
            # Moving Averages
            df['sma_20'] = ta.sma(df['close'], length=20)
            df['sma_50'] = ta.sma(df['close'], length=50)
            df['ema_12'] = ta.ema(df['close'], length=12)
            df['ema_26'] = ta.ema(df['close'], length=26)
            
            # Get latest values
            latest = df.iloc[-1]
            
            indicators = {
                'rsi': float(latest.get('rsi', 50)) if pd.notna(latest.get('rsi')) else 50,
                'macd': {
                    'macd': float(macd_data['MACD_12_26_9'].iloc[-1]) if len(macd_data) > 0 and 'MACD_12_26_9' in macd_data.columns else 0,
                    'signal': float(macd_data['MACDs_12_26_9'].iloc[-1]) if len(macd_data) > 0 and 'MACDs_12_26_9' in macd_data.columns else 0,
                    'histogram': float(macd_data['MACDh_12_26_9'].iloc[-1]) if len(macd_data) > 0 and 'MACDh_12_26_9' in macd_data.columns else 0
                },
                'bollinger_bands': {
                    'upper': float(bb_data['BBU_20_2.0'].iloc[-1]) if len(bb_data) > 0 and 'BBU_20_2.0' in bb_data.columns else 0,
                    'middle': float(bb_data['BBM_20_2.0'].iloc[-1]) if len(bb_data) > 0 and 'BBM_20_2.0' in bb_data.columns else 0,
                    'lower': float(bb_data['BBL_20_2.0'].iloc[-1]) if len(bb_data) > 0 and 'BBL_20_2.0' in bb_data.columns else 0
                },
                'moving_averages': {
                    'sma_20': float(latest.get('sma_20', 0)) if pd.notna(latest.get('sma_20')) else 0,
                    'sma_50': float(latest.get('sma_50', 0)) if pd.notna(latest.get('sma_50')) else 0,
                    'ema_12': float(latest.get('ema_12', 0)) if pd.notna(latest.get('ema_12')) else 0,
                    'ema_26': float(latest.get('ema_26', 0)) if pd.notna(latest.get('ema_26')) else 0
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
            df['sma_20'] = ta.sma(df['close'], length=20)
            df['sma_50'] = ta.sma(df['close'], length=50)
            
            current_price = df['close'].iloc[-1]
            sma_20 = df['sma_20'].iloc[-1]
            sma_50 = df['sma_50'].iloc[-1]
            
            # Determine trend
            if pd.notna(sma_20) and pd.notna(sma_50):
                if current_price > sma_20 > sma_50:
                    trend = 'bullish'
                elif current_price < sma_20 < sma_50:
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