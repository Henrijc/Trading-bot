"""
Historical Data Service for Crypto Trading Coach
Fetches historical data for backtesting trading strategies
"""

import ccxt
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import json
from pathlib import Path

class HistoricalDataService:
    def __init__(self):
        self.exchanges = {}
        self.data_cache = {}
        self.cache_dir = Path("/app/backend/historical_data")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize exchanges
        self.init_exchanges()
    
    def init_exchanges(self):
        """Initialize available exchanges"""
        try:
            # Luno exchange
            if os.getenv('LUNO_API_KEY') and os.getenv('LUNO_SECRET'):
                self.exchanges['luno'] = ccxt.luno({
                    'apiKey': os.getenv('LUNO_API_KEY'),
                    'secret': os.getenv('LUNO_SECRET'),
                    'sandbox': False,
                    'enableRateLimit': True,
                })
            
            # Binance as backup for more historical data
            self.exchanges['binance'] = ccxt.binance({
                'enableRateLimit': True,
            })
            
            print(f"Initialized exchanges: {list(self.exchanges.keys())}")
            
        except Exception as e:
            print(f"Error initializing exchanges: {e}")
    
    def check_luno_support(self):
        """Check what pairs and timeframes Luno supports"""
        if 'luno' not in self.exchanges:
            return {"error": "Luno not configured"}
        
        try:
            luno = self.exchanges['luno']
            markets = luno.load_markets()
            
            # Filter for ZAR pairs
            zar_pairs = {symbol: market for symbol, market in markets.items() 
                        if symbol.endswith('/ZAR')}
            
            # Check supported timeframes
            timeframes = luno.timeframes if hasattr(luno, 'timeframes') else {}
            
            return {
                "zar_pairs": list(zar_pairs.keys()),
                "timeframes": timeframes,
                "has_ohlcv": luno.has['fetchOHLCV'] if hasattr(luno, 'has') else False,
                "markets_count": len(markets)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def fetch_historical_data(self, 
                                  symbol: str, 
                                  timeframe: str = '1h',
                                  days_back: int = 365,
                                  exchange: str = 'luno') -> pd.DataFrame:
        """Fetch historical OHLCV data"""
        try:
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not available")
            
            exchange_obj = self.exchanges[exchange]
            
            # Calculate start time
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)
            
            # Convert to milliseconds
            since = int(start_time.timestamp() * 1000)
            
            print(f"Fetching {symbol} data from {exchange} for {days_back} days...")
            
            # Fetch OHLCV data
            ohlcv_data = []
            current_since = since
            
            while current_since < int(end_time.timestamp() * 1000):
                try:
                    batch = exchange_obj.fetch_ohlcv(
                        symbol, 
                        timeframe, 
                        since=current_since, 
                        limit=500
                    )
                    
                    if not batch:
                        break
                        
                    ohlcv_data.extend(batch)
                    current_since = batch[-1][0] + 1
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"Error fetching batch: {e}")
                    break
            
            if not ohlcv_data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Remove duplicates and sort
            df = df.drop_duplicates().sort_index()
            
            # Cache the data
            cache_file = self.cache_dir / f"{exchange}_{symbol.replace('/', '_')}_{timeframe}_{days_back}d.csv"
            df.to_csv(cache_file)
            
            print(f"Fetched {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return pd.DataFrame()
    
    def load_cached_data(self, symbol: str, timeframe: str = '1h', days_back: int = 365, exchange: str = 'luno') -> Optional[pd.DataFrame]:
        """Load cached historical data"""
        cache_file = self.cache_dir / f"{exchange}_{symbol.replace('/', '_')}_{timeframe}_{days_back}d.csv"
        
        if cache_file.exists():
            try:
                df = pd.read_csv(cache_file, index_col='timestamp', parse_dates=True)
                print(f"Loaded cached data: {len(df)} candles for {symbol}")
                return df
            except Exception as e:
                print(f"Error loading cached data: {e}")
        
        return None
    
    def generate_sample_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """Generate realistic sample data for testing when real data isn't available"""
        print(f"Generating sample data for {symbol} ({days} days)")
        
        # Base prices for different cryptocurrencies
        base_prices = {
            'BTC/ZAR': 1800000,  # ~R1.8M
            'ETH/ZAR': 65000,    # ~R65k  
            'XRP/ZAR': 12,       # ~R12
            'ADA/ZAR': 8,        # ~R8
        }
        
        base_price = base_prices.get(symbol, 50000)
        
        # Generate timestamps (hourly data)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        timestamps = pd.date_range(start=start_date, end=end_date, freq='1H')
        
        # Generate realistic price movements
        np.random.seed(42)  # For reproducible results
        
        # Create price series with trend and volatility
        returns = np.random.normal(0.0001, 0.02, len(timestamps))  # Small positive trend, 2% volatility
        
        # Add some market cycles (bull/bear patterns)
        cycle_length = len(timestamps) // 4
        for i in range(0, len(returns), cycle_length):
            end_idx = min(i + cycle_length, len(returns))
            if (i // cycle_length) % 2 == 0:  # Bull phase
                returns[i:end_idx] += np.linspace(0, 0.001, end_idx - i)
            else:  # Bear phase
                returns[i:end_idx] += np.linspace(0, -0.0005, end_idx - i)
        
        prices = [base_price]
        for r in returns[:-1]:
            prices.append(prices[-1] * (1 + r))
        
        # Generate OHLCV data
        data = []
        for i, (timestamp, close_price) in enumerate(zip(timestamps, prices)):
            # Generate realistic OHLC from close price
            volatility = close_price * 0.005  # 0.5% volatility within candle
            
            high = close_price + np.random.uniform(0, volatility)
            low = close_price - np.random.uniform(0, volatility)
            open_price = prices[i-1] if i > 0 else close_price
            
            # Ensure OHLC logic is correct
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Generate volume (higher volume during price movements)
            price_change = abs(close_price - open_price) / open_price
            base_volume = 1000000
            volume = base_volume * (1 + price_change * 10) * np.random.uniform(0.5, 2.0)
            
            data.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 0)
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # Cache the sample data
        cache_file = self.cache_dir / f"sample_{symbol.replace('/', '_')}_{days}d.csv"
        df.to_csv(cache_file)
        
        print(f"Generated {len(df)} sample candles for {symbol}")
        return df
    
    async def get_historical_data(self, symbol: str, timeframe: str = '1h', days_back: int = 365) -> pd.DataFrame:
        """Get historical data - try cache first, then live data, then sample data"""
        
        # Try to load cached data first
        df = self.load_cached_data(symbol, timeframe, days_back)
        if df is not None and not df.empty:
            return df
        
        # Try to fetch live data from Luno
        df = await self.fetch_historical_data(symbol, timeframe, days_back, 'luno')
        if not df.empty:
            return df
        
        # Try Binance as backup (convert symbol if needed)
        if symbol.endswith('/ZAR'):
            # Try USD pair on Binance and we'll convert later
            usd_symbol = symbol.replace('/ZAR', '/USDT')
            df = await self.fetch_historical_data(usd_symbol, timeframe, days_back, 'binance')
            if not df.empty:
                # Convert USD to ZAR (approximate rate: 1 USD = 18 ZAR)
                usd_to_zar = 18.5
                df[['open', 'high', 'low', 'close']] *= usd_to_zar
                
                # Cache the converted data
                cache_file = self.cache_dir / f"luno_{symbol.replace('/', '_')}_{timeframe}_{days_back}d.csv"
                df.to_csv(cache_file)
                return df
        
        # Generate sample data as last resort
        return self.generate_sample_data(symbol, days_back)

# Test function
async def test_historical_data():
    """Test the historical data service"""
    service = HistoricalDataService()
    
    # Check Luno support
    print("=== Luno Support Check ===")
    luno_info = service.check_luno_support()
    print(json.dumps(luno_info, indent=2))
    
    # Test data fetching for user's preferred pairs
    symbols = ['BTC/ZAR', 'ETH/ZAR', 'XRP/ZAR']
    
    print("\n=== Fetching Historical Data ===")
    for symbol in symbols:
        print(f"\n--- {symbol} ---")
        df = await service.get_historical_data(symbol, '1h', 30)  # 30 days of hourly data
        
        if not df.empty:
            print(f"Data range: {df.index.min()} to {df.index.max()}")
            print(f"Data points: {len(df)}")
            print(f"Price range: R{df['low'].min():.2f} - R{df['high'].max():.2f}")
            print(f"Latest close: R{df['close'].iloc[-1]:.2f}")
        else:
            print("No data available")

if __name__ == "__main__":
    asyncio.run(test_historical_data())