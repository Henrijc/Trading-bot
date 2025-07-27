"""
FreqAI Data Acquisition Service
Enhanced historical data service specifically for AI model training
"""

import ccxt
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
import json
import pickle
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FreqAIDataService:
    """
    Enhanced data service for AI model training with comprehensive feature engineering
    """
    
    def __init__(self):
        self.exchanges = {}
        self.data_cache = {}
        self.data_dir = Path("/app/freqtrade/user_data/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize exchanges
        self.init_exchanges()
        
        # AI training parameters
        self.min_training_days = 365  # 1 year minimum
        self.max_training_days = 730  # 2 years maximum
        self.required_pairs = ["BTC/ZAR", "ETH/ZAR", "XRP/ZAR"]
        self.timeframes = ["1h", "4h", "1d"]
        
    def init_exchanges(self):
        """Initialize exchanges for data acquisition"""
        try:
            # Luno exchange (primary)
            if os.getenv('LUNO_API_KEY') and os.getenv('LUNO_SECRET'):
                self.exchanges['luno'] = ccxt.luno({
                    'apiKey': os.getenv('LUNO_API_KEY'),
                    'secret': os.getenv('LUNO_SECRET'),
                    'sandbox': False,
                    'enableRateLimit': True,
                })
                logger.info("Luno exchange initialized for AI data")
            
            # Binance as backup for comprehensive data
            self.exchanges['binance'] = ccxt.binance({
                'enableRateLimit': True,
            })
            
            logger.info(f"FreqAI Data Service initialized with exchanges: {list(self.exchanges.keys())}")
            
        except Exception as e:
            logger.error(f"Error initializing exchanges for AI data: {e}")
    
    async def acquire_training_data(self, pair: str, days: int = 365) -> pd.DataFrame:
        """
        Acquire comprehensive historical data for AI training
        
        Args:
            pair: Trading pair (e.g., "BTC/ZAR")
            days: Number of days of historical data
            
        Returns:
            DataFrame with OHLCV data and additional features
        """
        try:
            logger.info(f"Acquiring {days} days of training data for {pair}")
            
            # Try multiple timeframes and exchanges
            all_data = []
            
            for timeframe in self.timeframes:
                for exchange_name, exchange in self.exchanges.items():
                    try:
                        # Calculate the date range
                        end_date = datetime.utcnow()
                        start_date = end_date - timedelta(days=days)
                        
                        # Convert to milliseconds
                        since = int(start_date.timestamp() * 1000)
                        
                        # Fetch data
                        ohlcv = await self._fetch_ohlcv_async(
                            exchange, pair, timeframe, since, days
                        )
                        
                        if ohlcv and len(ohlcv) > 0:
                            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                            df['exchange'] = exchange_name
                            df['timeframe'] = timeframe
                            df['pair'] = pair
                            
                            all_data.append(df)
                            logger.info(f"Successfully acquired {len(df)} candles from {exchange_name} for {pair} {timeframe}")
                            break  # Use first successful exchange for this timeframe
                            
                    except Exception as e:
                        logger.warning(f"Failed to get data from {exchange_name} for {pair} {timeframe}: {e}")
                        continue
            
            if not all_data:
                logger.error(f"No data acquired for {pair}")
                return pd.DataFrame()
            
            # Combine all timeframes (use 1h as primary)
            primary_data = None
            for df in all_data:
                if df['timeframe'].iloc[0] == '1h':
                    primary_data = df
                    break
            
            if primary_data is None:
                primary_data = all_data[0]  # Use first available
            
            # Save raw data for future use
            self._save_training_data(primary_data, pair)
            
            return primary_data
            
        except Exception as e:
            logger.error(f"Error acquiring training data for {pair}: {e}")
            return pd.DataFrame()
    
    async def _fetch_ohlcv_async(self, exchange, pair, timeframe, since, days):
        """Async wrapper for fetching OHLCV data"""
        try:
            # Convert pair format for different exchanges
            symbol = self._convert_pair_format(pair, exchange.id)
            
            if hasattr(exchange, 'fetch_ohlcv'):
                limit = min(1000, days * 24)  # Limit based on exchange constraints
                return exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            else:
                logger.warning(f"Exchange {exchange.id} doesn't support OHLCV")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching OHLCV from {exchange.id}: {e}")
            return []
    
    def _convert_pair_format(self, pair: str, exchange_id: str) -> str:
        """Convert pair format for different exchanges"""
        if exchange_id == 'luno':
            # Luno uses format like XBTZAR
            return pair.replace('BTC', 'XBT').replace('/', '')
        elif exchange_id == 'binance':
            # Binance uses BTC/USDT format, need to adapt for ZAR pairs
            if 'ZAR' in pair:
                # For ZAR pairs, we might need to use USDT equivalents
                base = pair.split('/')[0]
                return f"{base}/USDT"  # Use USDT as approximation
        
        return pair
    
    def _save_training_data(self, df: pd.DataFrame, pair: str):
        """Save training data to disk for future use"""
        try:
            filename = f"{pair.replace('/', '_')}_training_data.pkl"
            filepath = self.data_dir / filename
            
            # Save as pickle for faster loading
            df.to_pickle(filepath)
            
            # Also save as CSV for inspection
            csv_filepath = self.data_dir / f"{pair.replace('/', '_')}_training_data.csv"
            df.to_csv(csv_filepath, index=False)
            
            logger.info(f"Saved training data for {pair} to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving training data for {pair}: {e}")
    
    def load_training_data(self, pair: str) -> Optional[pd.DataFrame]:
        """Load previously saved training data"""
        try:
            filename = f"{pair.replace('/', '_')}_training_data.pkl"
            filepath = self.data_dir / filename
            
            if filepath.exists():
                df = pd.read_pickle(filepath)
                logger.info(f"Loaded training data for {pair}: {len(df)} records")
                return df
            else:
                logger.warning(f"No saved training data found for {pair}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading training data for {pair}: {e}")
            return None
    
    async def prepare_all_training_data(self) -> Dict[str, pd.DataFrame]:
        """Prepare training data for all required pairs"""
        training_data = {}
        
        for pair in self.required_pairs:
            logger.info(f"Preparing training data for {pair}")
            
            # Try to load existing data first
            df = self.load_training_data(pair)
            
            if df is None or len(df) < self.min_training_days * 20:  # Minimum data check
                # Acquire fresh data
                df = await self.acquire_training_data(pair, self.max_training_days)
            
            if df is not None and len(df) > 0:
                training_data[pair] = df
                logger.info(f"Training data ready for {pair}: {len(df)} records")
            else:
                logger.error(f"Failed to prepare training data for {pair}")
        
        return training_data
    
    def get_data_statistics(self, df: pd.DataFrame) -> Dict:
        """Get comprehensive statistics about the training data"""
        if df.empty:
            return {}
        
        return {
            'total_records': len(df),
            'date_range': {
                'start': df['datetime'].min().isoformat(),
                'end': df['datetime'].max().isoformat(),
                'days': (df['datetime'].max() - df['datetime'].min()).days
            },
            'price_range': {
                'min': df['low'].min(),
                'max': df['high'].max(),
                'avg': df['close'].mean()
            },
            'volume_stats': {
                'avg_volume': df['volume'].mean(),
                'max_volume': df['volume'].max(),
                'total_volume': df['volume'].sum()
            },
            'data_quality': {
                'missing_values': df.isnull().sum().sum(),
                'zero_volume_candles': (df['volume'] == 0).sum(),
                'price_consistency': (df['high'] >= df['low']).all()
            }
        }
    
    async def validate_training_data(self) -> Dict[str, bool]:
        """Validate that we have sufficient data for AI training"""
        validation_results = {}
        
        for pair in self.required_pairs:
            df = self.load_training_data(pair)
            
            if df is None or df.empty:
                validation_results[pair] = False
                continue
            
            # Check data quality requirements
            stats = self.get_data_statistics(df)
            
            is_valid = (
                stats.get('total_records', 0) >= self.min_training_days * 20 and  # Sufficient records
                stats.get('date_range', {}).get('days', 0) >= self.min_training_days and  # Time coverage
                stats.get('data_quality', {}).get('missing_values', 999) == 0 and  # No missing data
                stats.get('data_quality', {}).get('price_consistency', False)  # Price consistency
            )
            
            validation_results[pair] = is_valid
            
            if is_valid:
                logger.info(f"Training data validation passed for {pair}")
            else:
                logger.warning(f"Training data validation failed for {pair}: {stats}")
        
        return validation_results