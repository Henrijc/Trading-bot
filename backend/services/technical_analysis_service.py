import pandas as pd
import ta  # Import the pure Python technical analysis library
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalysisService:
    def __init__(self):
        logger.info("TechnicalAnalysisService initialized with 'ta' library.")

    def calculate_indicators(self, data: pd.DataFrame):
        df = data.copy() # Work on a copy to avoid modifying original DataFrame

        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()

        # MACD
        macd_indicator = ta.trend.MACD(df['close'])
        df['macd'] = macd_indicator.macd()
        df['macd_signal'] = macd_indicator.macd_signal()
        df['macd_histogram'] = macd_indicator.macd_diff()

        # Bollinger Bands
        bb_indicator = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bb_indicator.bollinger_hband()
        df['bb_middle'] = bb_indicator.bollinger_mavg()
        df['bb_lower'] = bb_indicator.bollinger_lband()

        # SMA (Simple Moving Average) - Example for additional indicator
        df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()

        # EMA (Exponential Moving Average) - Example for additional indicator
        df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()

        # Return the DataFrame with new indicator columns
        return df

    def get_latest_indicators(self, data: pd.DataFrame):
        """Calculates indicators and returns the latest values."""
        df = self.calculate_indicators(data) # Calculate all, then pick latest
        
        latest_values = {
            'rsi': df['rsi'].iloc[-1] if not df['rsi'].empty else None,
            'macd': df['macd'].iloc[-1] if not df['macd'].empty else None,
            'macd_signal': df['macd_signal'].iloc[-1] if not df['macd_signal'].empty else None,
            'macd_histogram': df['macd_histogram'].iloc[-1] if not df['macd_histogram'].empty else None,
            'bb_upper': df['bb_upper'].iloc[-1] if not df['bb_upper'].empty else None,
            'bb_middle': df['bb_middle'].iloc[-1] if not df['bb_middle'].empty else None,
            'bb_lower': df['bb_lower'].iloc[-1] if not df['bb_lower'].empty else None,
            'sma_20': df['sma_20'].iloc[-1] if not df['sma_20'].empty else None,
            'ema_12': df['ema_12'].iloc[-1] if not df['ema_12'].empty else None,
        }
        return latest_values

if __name__ == '__main__':
    # Example Usage (for testing/demonstration)
    print("Testing TechnicalAnalysisService...")
    # Create some dummy data mimicking OHLCV
    data = {
        'open': [100, 102, 101, 105, 103, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130],
        'high': [103, 104, 103, 106, 105, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132],
        'low': [99, 100, 99, 102, 101, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128],
        'close': [101, 103, 102, 104, 104, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131],
        'volume': [1000, 1100, 900, 1200, 1050, 1300, 1150, 1250, 1100, 1400, 1200, 1350, 1100, 1450, 1250, 1300, 1150, 1250, 1000, 1300, 1100, 1200, 950, 1100, 1050, 1200, 1150, 1000, 1300, 1250]
    }
    sample_df = pd.DataFrame(data).set_index('timestamp')

    ta_service = TechnicalAnalysisService()
    df_with_indicators = ta_service.calculate_indicators(sample_df)

    print("DataFrame with Indicators:")
    print(df_with_indicators.tail()) # Show last few rows with new columns

    latest = ta_service.get_latest_indicators(sample_df)
    print("\nLatest Indicator Values:")
    print(latest)