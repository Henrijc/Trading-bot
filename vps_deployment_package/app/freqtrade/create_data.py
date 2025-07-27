#!/usr/bin/env python3
"""
Convert existing historical data to FreqAI format
"""

import asyncio
import pandas as pd
import json
from pathlib import Path
import sys

# Add backend services to path
sys.path.append('/app/backend')
from services.historical_data_service import HistoricalDataService

async def create_freqai_data():
    """Create sample data for FreqAI training"""
    
    historical_service = HistoricalDataService()
    data_dir = Path("/app/freqtrade/user_data/data/binance")
    
    # Map our pairs to USDT equivalents for training
    pair_mapping = {
        "BTCZAR": "BTC_USDT-5m.json",
        "ETHZAR": "ETH_USDT-5m.json", 
        "XRPZAR": "XRP_USDT-5m.json"
    }
    
    for our_pair, filename in pair_mapping.items():
        try:
            print(f"Processing {our_pair}...")
            
            # Get historical data
            df = await historical_service.fetch_historical_data(
                our_pair, timeframe='1h', days_back=365
            )
            
            if df.empty:
                print(f"No data for {our_pair}")
                continue
            
            # Convert to FreqAI format (OHLCV with timestamps)
            freqai_data = []
            
            for _, row in df.iterrows():
                freqai_data.append([
                    int(row['timestamp']),  # timestamp in ms
                    float(row['open']),     # open
                    float(row['high']),     # high
                    float(row['low']),      # low
                    float(row['close']),    # close
                    float(row['volume'])    # volume
                ])
            
            # Sort by timestamp
            freqai_data.sort(key=lambda x: x[0])
            
            # Save as JSON file
            output_file = data_dir / filename
            with open(output_file, 'w') as f:
                json.dump(freqai_data, f)
            
            print(f"Created {filename} with {len(freqai_data)} candles")
            
        except Exception as e:
            print(f"Error processing {our_pair}: {e}")

if __name__ == "__main__":
    asyncio.run(create_freqai_data())