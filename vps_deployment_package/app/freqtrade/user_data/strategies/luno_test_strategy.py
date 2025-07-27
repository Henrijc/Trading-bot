"""
Simple Test Strategy for Luno Trading Bot
This strategy uses basic EMA crossover logic to validate the trading setup
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class LunoTestStrategy:
    """
    Simple test strategy using EMA crossover
    This validates that our trading bot can connect to Luno and process signals
    """
    
    def __init__(self):
        self.name = "LunoTestStrategy"
        self.minimal_roi = {
            "0": 0.10,
            "40": 0.06,
            "100": 0.04,
            "180": 0.02,
            "360": 0.01
        }
        
        self.stoploss = -0.05  # 5% stop loss
        self.trailing_stop = True
        self.trailing_stop_positive = 0.02
        self.trailing_stop_positive_offset = 0.03
        
        # User's requirements: 4% risk management
        self.position_adjustment_enable = True
        self.max_entry_position_adjustment = 2
        
        # Strategy parameters
        self.buy_params = {
            "ema_short": 10,
            "ema_long": 50,
            "rsi_buy": 30
        }
        
        self.sell_params = {
            "rsi_sell": 70
        }
        
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Add technical indicators to the dataframe
        """
        try:
            # EMA indicators
            dataframe['ema_short'] = dataframe['close'].ewm(span=self.buy_params['ema_short']).mean()
            dataframe['ema_long'] = dataframe['close'].ewm(span=self.buy_params['ema_long']).mean()
            
            # RSI
            delta = dataframe['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            dataframe['rsi'] = 100 - (100 / (1 + rs))
            
            # Volume analysis
            dataframe['volume_sma'] = dataframe['volume'].rolling(window=20).mean()
            
            return dataframe
            
        except Exception as e:
            logger.error(f"Error in populate_indicators: {e}")
            return dataframe
    
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Generate buy signals based on EMA crossover and RSI
        """
        try:
            dataframe.loc[
                (
                    # EMA crossover - short EMA crosses above long EMA
                    (dataframe['ema_short'] > dataframe['ema_long']) &
                    (dataframe['ema_short'].shift(1) <= dataframe['ema_long'].shift(1)) &
                    
                    # RSI oversold condition
                    (dataframe['rsi'] < self.buy_params['rsi_buy']) &
                    
                    # Volume confirmation
                    (dataframe['volume'] > dataframe['volume_sma']) &
                    
                    # Basic trend confirmation
                    (dataframe['close'] > dataframe['close'].shift(1))
                ),
                'enter_long'] = 1
            
            return dataframe
            
        except Exception as e:
            logger.error(f"Error in populate_entry_trend: {e}")
            return dataframe
    
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Generate sell signals based on RSI overbought
        """
        try:
            dataframe.loc[
                (
                    # RSI overbought condition
                    (dataframe['rsi'] > self.sell_params['rsi_sell']) |
                    
                    # EMA crossover downward
                    (dataframe['ema_short'] < dataframe['ema_long']) &
                    (dataframe['ema_short'].shift(1) >= dataframe['ema_long'].shift(1))
                ),
                'exit_long'] = 1
                
            return dataframe
            
        except Exception as e:
            logger.error(f"Error in populate_exit_trend: {e}")
            return dataframe
    
    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, 
                          rate: float, time_in_force: str, current_time: datetime,
                          entry_tag: Optional[str], side: str, **kwargs) -> bool:
        """
        Confirm trade entry based on additional checks
        Implements 4% risk management as per user requirements
        """
        try:
            # Get current portfolio value (simulated for now)
            portfolio_value = 154273.71  # User's current capital
            
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
                # This is a simplified check - in production we'd check actual balances
                if amount > 100:  # Only small XRP trades allowed
                    logger.info(f"XRP trade rejected - protecting 1000 XRP reserve")
                    return False
            
            logger.info(f"Trade confirmed: {pair} {side} {amount} at {rate}")
            return True
            
        except Exception as e:
            logger.error(f"Error in confirm_trade_entry: {e}")
            return False
    
    def custom_exit(self, pair: str, trade, current_time: datetime, 
                   current_rate: float, current_profit: float, **kwargs):
        """
        Custom exit logic for advanced profit taking
        """
        try:
            # Take profits at different levels based on user's monthly target
            # Target: R8000/month means ~R267/day profit target
            
            if current_profit > 0.15:  # 15% profit
                return "take_profit_15"
            elif current_profit > 0.10:  # 10% profit
                return "take_profit_10"
            elif current_profit < -0.04:  # 4% loss (strict risk management)
                return "stop_loss_4"
                
            return None
            
        except Exception as e:
            logger.error(f"Error in custom_exit: {e}")
            return None


# Strategy instance
strategy = LunoTestStrategy()

def get_strategy():
    """Return the strategy instance"""
    return strategy