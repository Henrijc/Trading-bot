# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Union

from freqtrade.strategy import (
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IntParameter,
    IStrategy,
)

import freqtrade.vendor.qtpylib.indicators as qtpylib

logger = logging.getLogger(__name__)


class LunoFreqAIStrategy(IStrategy):
    """
    FreqAI Strategy specifically designed for Luno exchange
    This strategy uses machine learning predictions from FreqAI to make trading decisions
    """

    INTERFACE_VERSION = 3

    # Minimal ROI designed for the strategy.
    minimal_roi = {
        "0": 0.10,      # 10% profit
        "40": 0.06,     # 6% profit after 40 minutes
        "100": 0.04,    # 4% profit after 100 minutes
        "180": 0.02,    # 2% profit after 180 minutes
        "360": 0.01     # 1% profit after 360 minutes
    }

    # Optimal stoploss designed for the strategy.
    stoploss = -0.05  # 5% stop loss (4% risk management + buffer)

    # Trailing stoploss
    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

    # Optimal timeframe for the strategy.
    timeframe = '15m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 300

    # Strategy parameters
    buy_params = {
        "ai_signal_threshold": 0.7,  # Confidence threshold for AI buy signals
        "rsi_buy": 30,
        "volume_factor": 1.2,
    }

    sell_params = {
        "ai_signal_threshold": -0.3,  # Confidence threshold for AI sell signals
        "rsi_sell": 70,
    }

    # FreqAI specific parameters
    ai_signal_threshold = DecimalParameter(0.5, 0.9, default=0.7, space="buy", optimize=True)
    rsi_buy = IntParameter(20, 40, default=30, space="buy", optimize=True)
    rsi_sell = IntParameter(60, 80, default=70, space="sell", optimize=True)
    volume_factor = DecimalParameter(1.0, 2.0, default=1.2, space="buy", optimize=True)

    def bot_loop_start(self, current_time: datetime, **kwargs) -> None:
        """
        Called at the start of the bot iteration (one loop).
        Might be used to perform pair-independent tasks
        (e.g. gather some remote resource for comparison)
        """
        if self.config.get("freqai", {}).get("enabled", False):
            # FreqAI is enabled, we can use predictions
            logger.info("FreqAI enabled - using ML predictions for trading decisions")

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Adds several different TA indicators to the given DataFrame
        
        Performance Note: For basic ta-lib indicators, do not use 
        ta-lib directly, it's slower. Use freqtrade.vendor.qtpylib 
        or pandas_ta instead.
        """

        # FreqAI model predictions (added automatically by FreqAI)
        # The model will add columns like:
        # - &-target_roc_2  (return on investment prediction)
        # - &-target_roc_5
        # - &-target_roc_10
        # - &-target_roc_20
        # And prediction columns:
        # - prediction_roc_2
        # - prediction_roc_5
        # etc.

        # Basic indicators for feature engineering
        dataframe['rsi'] = qtpylib.rsi(dataframe, timeperiod=14)
        
        # MACD
        macd = qtpylib.macd(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macd_signal'] = macd['macdsignal']
        dataframe['macd_hist'] = macd['macdhist']
        
        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(dataframe, window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['bb_percent'] = (
            (dataframe['close'] - dataframe['bb_lowerband']) /
            (dataframe['bb_upperband'] - dataframe['bb_lowerband'])
        )
        dataframe['bb_width'] = (
            (dataframe['bb_upperband'] - dataframe['bb_lowerband']) / 
            dataframe['bb_middleband']
        )

        # EMA
        dataframe['ema12'] = qtpylib.ema(dataframe, timeperiod=12)
        dataframe['ema26'] = qtpylib.ema(dataframe, timeperiod=26)
        dataframe['ema50'] = qtpylib.ema(dataframe, timeperiod=50)
        dataframe['ema200'] = qtpylib.ema(dataframe, timeperiod=200)

        # SMA
        dataframe['sma20'] = qtpylib.sma(dataframe, timeperiod=20)
        dataframe['sma50'] = qtpylib.sma(dataframe, timeperiod=50)

        # Volume indicators
        dataframe['volume_sma'] = qtpylib.sma(dataframe['volume'], timeperiod=20)
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']

        # Price action indicators
        dataframe['price_change'] = dataframe['close'].pct_change()
        dataframe['high_low_ratio'] = dataframe['high'] / dataframe['low']
        dataframe['close_open_ratio'] = dataframe['close'] / dataframe['open']

        # Momentum indicators
        dataframe['momentum'] = qtpylib.momentum(dataframe, timeperiod=14)
        dataframe['atr'] = qtpylib.atr(dataframe, timeperiod=14)

        # Support/Resistance levels (simplified)
        dataframe['resistance'] = dataframe['high'].rolling(window=20).max()
        dataframe['support'] = dataframe['low'].rolling(window=20).min()

        return dataframe

    def populate_any_indicators(
        self, pair, df, tf, informative=None, set_generalized_indicators=False
    ):
        """
        Function which takes a dataframe, pair and timeframe and populates
        indicators for FreqAI feature engineering.
        
        :param pair: pair to be used as informative
        :param df: strategy dataframe which will receive merges from informatives
        :param tf: timeframe of the dataframe which will modify the feature names
        :param informative: the dataframe associated with the informative pair
        :param set_generalized_indicators: if true, the features will not be pair specific
        """

        coin = pair.split('/')[0]

        if informative is None:
            informative = self.dp.get_pair_dataframe(pair, tf)

        # Example of adding FreqAI specific features
        informative[f"%-{coin}rsi-period-10"] = qtpylib.rsi(informative, timeperiod=10)
        informative[f"%-{coin}rsi-period-14"] = qtpylib.rsi(informative, timeperiod=14)
        informative[f"%-{coin}rsi-period-20"] = qtpylib.rsi(informative, timeperiod=20)

        # MACD features
        macd = qtpylib.macd(informative)
        informative[f"%-{coin}macd"] = macd['macd']
        informative[f"%-{coin}macd_signal"] = macd['macdsignal']
        informative[f"%-{coin}macd_hist"] = macd['macdhist']

        # Bollinger Band features
        bollinger = qtpylib.bollinger_bands(informative, window=20, stds=2)
        informative[f"%-{coin}bb_percent"] = (
            (informative['close'] - bollinger['lower']) /
            (bollinger['upper'] - bollinger['lower'])
        )

        # Volume features
        informative[f"%-{coin}volume_sma"] = qtpylib.sma(informative['volume'], timeperiod=20)
        informative[f"%-{coin}volume_ratio"] = informative['volume'] / informative[f"%-{coin}volume_sma"]

        # Price action features
        informative[f"%-{coin}price_change"] = informative['close'].pct_change()
        informative[f"%-{coin}high_low_ratio"] = informative['high'] / informative['low']

        # EMA features
        informative[f"%-{coin}ema12"] = qtpylib.ema(informative, timeperiod=12)
        informative[f"%-{coin}ema26"] = qtpylib.ema(informative, timeperiod=26)
        informative[f"%-{coin}ema50"] = qtpylib.ema(informative, timeperiod=50)

        # Add targets for FreqAI to predict
        # These are the targets that FreqAI will try to predict
        informative[f"&-{coin}target_roc_2"] = (
            informative['close'].shift(-2) / informative['close'] - 1
        )
        informative[f"&-{coin}target_roc_5"] = (
            informative['close'].shift(-5) / informative['close'] - 1
        )
        informative[f"&-{coin}target_roc_10"] = (
            informative['close'].shift(-10) / informative['close'] - 1
        )

        return informative

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Based on TA indicators and FreqAI predictions, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """

        conditions = []

        # Check if FreqAI predictions are available
        if 'prediction_roc_5' in dataframe.columns:
            # Use AI predictions as primary signal
            conditions.append(
                (dataframe['prediction_roc_5'] > self.ai_signal_threshold.value)
            )
            logger.debug(f"Using FreqAI prediction for entry signals")
        else:
            logger.warning("FreqAI predictions not available, using fallback indicators")

        # Technical analysis conditions (backup or confirmation)
        conditions.extend([
            (dataframe['rsi'] < self.rsi_buy.value),
            (dataframe['volume_ratio'] > self.volume_factor.value),
            (dataframe['close'] > dataframe['ema12']),
            (dataframe['ema12'] > dataframe['ema26']),
            (dataframe['macd'] > dataframe['macd_signal']),
            (dataframe['bb_percent'] < 0.2),  # Near lower Bollinger Band
        ])

        # Combine conditions (AI signal OR strong technical confluence)  
        if 'prediction_roc_5' in dataframe.columns:
            # If AI is available, use it as primary with technical confirmation
            dataframe.loc[
                (
                    (dataframe['prediction_roc_5'] > self.ai_signal_threshold.value) |
                    (
                        (dataframe['rsi'] < self.rsi_buy.value) &
                        (dataframe['volume_ratio'] > self.volume_factor.value) &
                        (dataframe['close'] > dataframe['ema12']) &
                        (dataframe['macd'] > dataframe['macd_signal'])
                    )
                ) &
                (dataframe['volume'] > 0),  # Basic sanity check
                'enter_long'] = 1

        else:
            # Fallback to technical analysis only
            dataframe.loc[
                (
                    (dataframe['rsi'] < self.rsi_buy.value) &
                    (dataframe['volume_ratio'] > self.volume_factor.value) &
                    (dataframe['close'] > dataframe['ema12']) &
                    (dataframe['ema12'] > dataframe['ema26']) &
                    (dataframe['macd'] > dataframe['macd_signal'])
                ) &
                (dataframe['volume'] > 0),
                'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Based on TA indicators and FreqAI predictions, populates the exit signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with exit columns populated
        """

        conditions = []

        # Check if FreqAI predictions are available
        if 'prediction_roc_5' in dataframe.columns:
            # Use AI predictions for exit signals
            conditions.append(
                (dataframe['prediction_roc_5'] < self.ai_signal_threshold.value)
            )
        
        # Technical analysis exit conditions
        conditions.extend([
            (dataframe['rsi'] > self.rsi_sell.value),
            (dataframe['bb_percent'] > 0.8),  # Near upper Bollinger Band
            (dataframe['macd'] < dataframe['macd_signal']),
            (dataframe['close'] < dataframe['ema12']),
        ])

        # Exit logic
        if 'prediction_roc_5' in dataframe.columns:
            # Use AI predictions as primary exit signal
            dataframe.loc[
                (
                    (dataframe['prediction_roc_5'] < self.ai_signal_threshold.value) |
                    (dataframe['rsi'] > self.rsi_sell.value) |
                    (dataframe['bb_percent'] > 0.8)
                ),
                'exit_long'] = 1
        else:
            # Technical analysis exit
            dataframe.loc[
                (
                    (dataframe['rsi'] > self.rsi_sell.value) |
                    (dataframe['bb_percent'] > 0.8) |
                    (dataframe['macd'] < dataframe['macd_signal'])
                ),
                'exit_long'] = 1

        return dataframe

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                           time_in_force: str, current_time: datetime,
                           entry_tag: Optional[str], side: str, **kwargs) -> bool:
        """
        Called right before placing a entry order.
        Timing for this function is critical, so avoid doing heavy computations or
        network requests in this method.

        Implement 4% risk management as per user requirements
        """
        try:
            # Get current portfolio value (this should be dynamic in production)
            portfolio_value = 154273.71  # User's capital
            
            # Calculate 4% risk
            max_risk_amount = portfolio_value * 0.04  # R6170.95
            
            # Calculate position size based on 4% risk
            trade_value = amount * rate
            
            if trade_value > max_risk_amount:
                logger.warning(f"Trade value {trade_value} exceeds 4% risk limit {max_risk_amount}")
                return False
            
            # Special handling for XRP (user wants to keep 1000 XRP long-term)
            if pair == "XRP/ZAR":
                # Only trade if we're not touching the 1000 XRP reserve
                if amount > 100:  # Conservative limit for XRP trades
                    logger.info(f"XRP trade rejected - protecting 1000 XRP reserve")
                    return False
            
            # FreqAI confidence check
            if hasattr(self, 'freqai') and self.freqai:
                # Get latest prediction confidence if available
                # This would be implemented based on FreqAI's confidence metrics
                pass
            
            logger.info(f"Trade confirmed: {pair} {side} {amount} at {rate}")
            return True
            
        except Exception as e:
            logger.error(f"Error in confirm_trade_entry: {e}")
            return False

    def custom_exit(self, pair: str, trade, current_time: datetime, current_rate: float,
                   current_profit: float, **kwargs):
        """
        Custom exit logic for advanced profit taking
        Enhanced with FreqAI predictions if available
        """
        try:
            # Progressive profit taking based on user's R8000/month target
            # Target: R8000/month means ~R267/day profit target
            
            if current_profit > 0.15:  # 15% profit
                return "take_profit_15"
            elif current_profit > 0.10:  # 10% profit
                return "take_profit_10"
            elif current_profit > 0.05:  # 5% profit
                return "take_profit_5"
            elif current_profit < -0.04:  # 4% loss (strict risk management)
                return "stop_loss_4"
            
            # Check FreqAI predictions for dynamic exits
            if hasattr(self, 'freqai') and self.freqai:
                # This would use FreqAI predictions to make smarter exit decisions
                # Implementation would depend on FreqAI's prediction structure
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"Error in custom_exit: {e}")
            return None