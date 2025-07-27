#!/usr/bin/env python3
"""
Create sample OHLCV data for FreqAI training
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def create_sample_ohlcv(pair_name, base_price, volatility, days=365):
    """Create realistic OHLCV data for testing"""
    
    # Generate timestamps (5min intervals)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    timestamps = []
    current_time = start_time
    while current_time <= end_time:
        timestamps.append(int(current_time.timestamp() * 1000))
        current_time += timedelta(minutes=5)
    
    # Generate realistic price data
    np.random.seed(42)  # For reproducible data
    
    data = []
    current_price = base_price
    
    for i, timestamp in enumerate(timestamps):
        # Random walk with some trend
        price_change = np.random.normal(0, volatility * current_price)
        current_price = max(current_price + price_change, current_price * 0.95)  # Prevent too much drop
        
        # Generate OHLC from close price
        high = current_price * (1 + abs(np.random.normal(0, 0.01)))
        low = current_price * (1 - abs(np.random.normal(0, 0.01)))
        open_price = current_price + np.random.normal(0, volatility * current_price * 0.5)
        
        # Ensure OHLC relationships are correct
        high = max(high, current_price, open_price, low)
        low = min(low, current_price, open_price, high)
        
        # Volume (more volume during high volatility)
        volume = abs(np.random.normal(1000000, 500000))
        
        data.append([
            timestamp,
            round(open_price, 2),
            round(high, 2),
            round(low, 2),
            round(current_price, 2),
            round(volume, 2)
        ])
    
    return data

def main():
    """Create sample data files"""
    data_dir = Path("/app/freqtrade/user_data/data/binance")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create data for different pairs
    pairs_config = {
        "BTC_USDT-5m.json": {"base_price": 45000, "volatility": 0.02},  # 2% volatility
        "ETH_USDT-5m.json": {"base_price": 2500, "volatility": 0.03},   # 3% volatility  
        "XRP_USDT-5m.json": {"base_price": 0.65, "volatility": 0.04}    # 4% volatility
    }
    
    for filename, config in pairs_config.items():
        print(f"Creating {filename}...")
        
        data = create_sample_ohlcv(
            filename, 
            config["base_price"], 
            config["volatility"],
            days=365
        )
        
        # Save to file
        output_file = data_dir / filename
        with open(output_file, 'w') as f:
            json.dump(data, f)
        
        print(f"Created {filename} with {len(data)} candles")

if __name__ == "__main__":
    main()