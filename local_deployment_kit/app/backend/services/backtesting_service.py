"""
Custom Backtesting Engine for AI Crypto Trading Coach
Implements the user's specific requirements:
- R8000/month profit target
- Keep 1000 XRP long-term 
- 4% risk management
- Stop-loss strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass
from enum import Enum

class TradeAction(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime]
    pair: str
    action: TradeAction
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    entry_value: float  # In ZAR
    exit_value: Optional[float]  # In ZAR
    profit_loss: float
    profit_percentage: float
    stop_loss_price: float
    reason: str  # Entry/exit reason
    
    def is_open(self) -> bool:
        return self.exit_time is None

@dataclass
class BacktestResult:
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_profit: float
    total_percentage: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit_per_trade: float
    max_drawdown: float
    sharpe_ratio: float
    monthly_returns: List[float]
    trades: List[Trade]
    daily_portfolio_value: pd.Series

class CryptoBacktester:
    def __init__(self, 
                 initial_capital: float = 154273.71,  # User's current portfolio value
                 risk_per_trade: float = 0.04,       # 4% risk per trade
                 monthly_target: float = 8000,        # R8000/month target
                 xrp_hold_amount: float = 1000):      # 1000 XRP to hold long-term
        
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.monthly_target = monthly_target
        self.xrp_hold_amount = xrp_hold_amount
        
        # Trading state
        self.current_capital = initial_capital
        self.available_capital = initial_capital
        self.trades = []
        self.open_positions = {}
        self.daily_values = {}
        
        # XRP long-term hold (subtract from available trading capital)
        self.xrp_reserved_value = 0  # Will be set when we see XRP price
        
        # Performance tracking
        self.portfolio_values = []
        self.timestamps = []
        
    def calculate_position_size(self, entry_price: float, stop_loss_price: float) -> float:
        """Calculate position size based on 4% risk rule"""
        if entry_price <= stop_loss_price:
            return 0
        
        risk_amount = self.available_capital * self.risk_per_trade
        price_risk = entry_price - stop_loss_price
        position_size_zar = risk_amount / (price_risk / entry_price)
        
        # Don't risk more than available capital
        position_size_zar = min(position_size_zar, self.available_capital * 0.3)  # Max 30% per trade
        
        return position_size_zar
    
    def calculate_stop_loss(self, entry_price: float, action: TradeAction) -> float:
        """Calculate stop-loss price"""
        if action == TradeAction.BUY:
            return entry_price * 0.96  # 4% below entry for long positions
        else:
            return entry_price * 1.04  # 4% above entry for short positions
    
    def check_rsi_signal(self, data: pd.DataFrame, idx: int, period: int = 14) -> TradeAction:
        """Simple RSI-based trading signal"""
        if idx < period:
            return TradeAction.HOLD
        
        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[idx]
        
        # Trading signals
        if current_rsi < 30:  # Oversold - potential buy
            return TradeAction.BUY
        elif current_rsi > 70:  # Overbought - potential sell
            return TradeAction.SELL
        else:
            return TradeAction.HOLD
    
    def check_bollinger_bands_signal(self, data: pd.DataFrame, idx: int, period: int = 20, std_dev: int = 2) -> TradeAction:
        """Bollinger Bands trading signal"""
        if idx < period:
            return TradeAction.HOLD
        
        # Calculate Bollinger Bands
        rolling_mean = data['close'].rolling(window=period).mean()
        rolling_std = data['close'].rolling(window=period).std()
        upper_band = rolling_mean + (rolling_std * std_dev)
        lower_band = rolling_mean - (rolling_std * std_dev)
        
        current_price = data['close'].iloc[idx]
        current_upper = upper_band.iloc[idx]
        current_lower = lower_band.iloc[idx]
        
        # Trading signals
        if current_price <= current_lower:  # Price at lower band - buy signal
            return TradeAction.BUY
        elif current_price >= current_upper:  # Price at upper band - sell signal
            return TradeAction.SELL
        else:
            return TradeAction.HOLD
    
    def get_trading_signal(self, data: pd.DataFrame, idx: int, pair: str) -> TradeAction:
        """Combined trading signal logic"""
        rsi_signal = self.check_rsi_signal(data, idx)
        bb_signal = self.check_bollinger_bands_signal(data, idx)
        
        # Don't trade XRP if it's meant for long-term holding
        if pair == 'XRP/ZAR':
            # Only trade XRP if we have excess beyond 1000 XRP hold requirement
            xrp_price = data['close'].iloc[idx]
            xrp_hold_value = self.xrp_hold_amount * xrp_price
            
            if self.xrp_reserved_value == 0:
                self.xrp_reserved_value = xrp_hold_value
                self.available_capital -= xrp_hold_value
                print(f"Reserved R{xrp_hold_value:.2f} for 1000 XRP long-term hold")
            
            # Only trade XRP in extreme conditions
            if rsi_signal == TradeAction.BUY and bb_signal == TradeAction.BUY:
                return TradeAction.BUY
            elif rsi_signal == TradeAction.SELL and bb_signal == TradeAction.SELL:
                return TradeAction.SELL
            else:
                return TradeAction.HOLD
        
        # For other pairs, use combined signals
        if rsi_signal == bb_signal and rsi_signal != TradeAction.HOLD:
            return rsi_signal
        elif rsi_signal == TradeAction.BUY or bb_signal == TradeAction.BUY:
            return TradeAction.BUY
        elif rsi_signal == TradeAction.SELL or bb_signal == TradeAction.SELL:
            return TradeAction.SELL
        else:
            return TradeAction.HOLD
    
    def execute_trade(self, data: pd.DataFrame, idx: int, pair: str, action: TradeAction, reason: str):
        """Execute a trade"""
        timestamp = data.index[idx]
        price = data['close'].iloc[idx]
        
        if action == TradeAction.BUY:
            # Check if we already have an open position
            if pair in self.open_positions:
                return
            
            stop_loss_price = self.calculate_stop_loss(price, action)
            position_size_zar = self.calculate_position_size(price, stop_loss_price)
            
            if position_size_zar < 100:  # Minimum trade size R100
                return
            
            quantity = position_size_zar / price
            
            trade = Trade(
                entry_time=timestamp,
                exit_time=None,
                pair=pair,
                action=action,
                entry_price=price,
                exit_price=None,
                quantity=quantity,
                entry_value=position_size_zar,
                exit_value=None,
                profit_loss=0,
                profit_percentage=0,
                stop_loss_price=stop_loss_price,
                reason=reason
            )
            
            self.trades.append(trade)
            self.open_positions[pair] = trade
            self.available_capital -= position_size_zar
            
            print(f"[{timestamp}] BUY {pair}: R{position_size_zar:.2f} @ R{price:.2f} (Stop-loss: R{stop_loss_price:.2f})")
        
        elif action == TradeAction.SELL:
            # Close existing position
            if pair in self.open_positions:
                trade = self.open_positions[pair]
                
                trade.exit_time = timestamp
                trade.exit_price = price
                trade.exit_value = trade.quantity * price
                trade.profit_loss = trade.exit_value - trade.entry_value
                trade.profit_percentage = (trade.profit_loss / trade.entry_value) * 100
                
                self.available_capital += trade.exit_value
                
                print(f"[{timestamp}] SELL {pair}: R{trade.exit_value:.2f} @ R{price:.2f} (P&L: R{trade.profit_loss:.2f})")
                
                del self.open_positions[pair]
    
    def check_stop_losses(self, data: pd.DataFrame, idx: int):
        """Check and execute stop-losses for open positions"""
        timestamp = data.index[idx]
        current_prices = {'BTC/ZAR': data['close'].iloc[idx] if 'BTC' in str(data.index[0]) else None,
                         'ETH/ZAR': data['close'].iloc[idx] if 'ETH' in str(data.index[0]) else None,
                         'XRP/ZAR': data['close'].iloc[idx] if 'XRP' in str(data.index[0]) else None}
        
        positions_to_close = []
        
        for pair, trade in self.open_positions.items():
            current_price = data['close'].iloc[idx]  # Assuming single pair backtests
            
            # Check stop-loss
            if trade.action == TradeAction.BUY and current_price <= trade.stop_loss_price:
                positions_to_close.append((pair, "Stop-loss triggered"))
            
        # Close positions that hit stop-loss
        for pair, reason in positions_to_close:
            trade = self.open_positions[pair]
            current_price = data['close'].iloc[idx]
            
            trade.exit_time = timestamp
            trade.exit_price = current_price
            trade.exit_value = trade.quantity * current_price
            trade.profit_loss = trade.exit_value - trade.entry_value
            trade.profit_percentage = (trade.profit_loss / trade.entry_value) * 100
            
            self.available_capital += trade.exit_value
            
            print(f"[{timestamp}] STOP-LOSS {pair}: R{trade.exit_value:.2f} @ R{current_price:.2f} (Loss: R{trade.profit_loss:.2f})")
            
            del self.open_positions[pair]
    
    def backtest(self, data: pd.DataFrame, pair: str) -> BacktestResult:
        """Run backtest on historical data"""
        print(f"\n=== Starting Backtest for {pair} ===")
        print(f"Initial Capital: R{self.initial_capital:,.2f}")
        print(f"Target Monthly Profit: R{self.monthly_target:,.2f}")
        print(f"Risk per Trade: {self.risk_per_trade*100}%")
        print(f"Data Period: {data.index[0]} to {data.index[-1]}")
        print(f"Total Candles: {len(data)}")
        
        for idx in range(1, len(data)):
            timestamp = data.index[idx]
            
            # Check stop-losses first
            self.check_stop_losses(data, idx)
            
            # Get trading signal
            signal = self.get_trading_signal(data, idx, pair)
            
            # Execute trades based on signal
            if signal == TradeAction.BUY:
                self.execute_trade(data, idx, pair, signal, "RSI + Bollinger Bands buy signal")
            elif signal == TradeAction.SELL:
                self.execute_trade(data, idx, pair, signal, "RSI + Bollinger Bands sell signal")
            
            # Track portfolio value
            current_value = self.available_capital
            for open_pair, trade in self.open_positions.items():
                current_market_price = data['close'].iloc[idx]
                current_value += trade.quantity * current_market_price
            
            # Add XRP hold value
            if pair == 'XRP/ZAR':
                current_value += self.xrp_reserved_value
            
            self.daily_values[timestamp] = current_value
            self.portfolio_values.append(current_value)
            self.timestamps.append(timestamp)
        
        # Close any remaining open positions
        final_timestamp = data.index[-1]
        final_price = data['close'].iloc[-1]
        
        for pair_name, trade in list(self.open_positions.items()):
            trade.exit_time = final_timestamp
            trade.exit_price = final_price
            trade.exit_value = trade.quantity * final_price
            trade.profit_loss = trade.exit_value - trade.entry_value
            trade.profit_percentage = (trade.profit_loss / trade.entry_value) * 100
            
            self.available_capital += trade.exit_value
            print(f"[{final_timestamp}] CLOSE {pair_name}: R{trade.exit_value:.2f} @ R{final_price:.2f} (P&L: R{trade.profit_loss:.2f})")
        
        self.open_positions.clear()
        
        # Calculate results
        return self.calculate_results(data)
    
    def calculate_results(self, data: pd.DataFrame) -> BacktestResult:
        """Calculate backtest results"""
        final_capital = self.available_capital + self.xrp_reserved_value
        total_profit = final_capital - self.initial_capital
        total_percentage = (total_profit / self.initial_capital) * 100
        
        # Trade statistics
        completed_trades = [t for t in self.trades if not t.is_open()]
        winning_trades = [t for t in completed_trades if t.profit_loss > 0]
        losing_trades = [t for t in completed_trades if t.profit_loss < 0]
        
        win_rate = len(winning_trades) / len(completed_trades) * 100 if completed_trades else 0
        avg_profit_per_trade = sum(t.profit_loss for t in completed_trades) / len(completed_trades) if completed_trades else 0
        
        # Calculate max drawdown
        portfolio_series = pd.Series(self.portfolio_values, index=self.timestamps)
        rolling_max = portfolio_series.expanding().max()
        drawdown = (portfolio_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        # Calculate monthly returns
        monthly_values = portfolio_series.resample('M').last()
        monthly_returns = monthly_values.pct_change().dropna() * 100
        
        # Sharpe ratio (simplified)
        if len(monthly_returns) > 1:
            sharpe_ratio = monthly_returns.mean() / monthly_returns.std() if monthly_returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        result = BacktestResult(
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_profit=total_profit,
            total_percentage=total_percentage,
            total_trades=len(completed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            avg_profit_per_trade=avg_profit_per_trade,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            monthly_returns=monthly_returns.tolist(),
            trades=completed_trades,
            daily_portfolio_value=portfolio_series
        )
        
        return result
    
    def print_results(self, result: BacktestResult):
        """Print formatted backtest results"""
        print(f"\n{'='*60}")
        print(f"BACKTEST RESULTS")
        print(f"{'='*60}")
        print(f"Period: {result.start_date.strftime('%Y-%m-%d')} to {result.end_date.strftime('%Y-%m-%d')}")
        print(f"Duration: {(result.end_date - result.start_date).days} days")
        
        print(f"\nPORTFOLIO PERFORMANCE:")
        print(f"Initial Capital: R{result.initial_capital:,.2f}")
        print(f"Final Capital: R{result.final_capital:,.2f}")
        print(f"Total Profit: R{result.total_profit:,.2f}")
        print(f"Total Return: {result.total_percentage:.2f}%")
        
        # Monthly performance vs target
        months = (result.end_date - result.start_date).days / 30.44
        actual_monthly_profit = result.total_profit / months if months > 0 else 0
        print(f"Average Monthly Profit: R{actual_monthly_profit:,.2f}")
        print(f"Target Monthly Profit: R{self.monthly_target:,.2f}")
        target_achievement = (actual_monthly_profit / self.monthly_target) * 100 if self.monthly_target > 0 else 0
        print(f"Target Achievement: {target_achievement:.1f}%")
        
        print(f"\nTRADING STATISTICS:")
        print(f"Total Trades: {result.total_trades}")
        print(f"Winning Trades: {result.winning_trades}")
        print(f"Losing Trades: {result.losing_trades}")
        print(f"Win Rate: {result.win_rate:.1f}%")
        print(f"Average Profit per Trade: R{result.avg_profit_per_trade:.2f}")
        print(f"Max Drawdown: {result.max_drawdown:.2f}%")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        
        if result.monthly_returns:
            print(f"Best Month: {max(result.monthly_returns):.2f}%")
            print(f"Worst Month: {min(result.monthly_returns):.2f}%")
        
        print(f"\nRISK ASSESSMENT:")
        risk_score = "LOW" if result.max_drawdown > -10 else "MEDIUM" if result.max_drawdown > -20 else "HIGH"
        print(f"Risk Level: {risk_score}")
        print(f"Capital Preservation: {'GOOD' if result.total_profit > 0 else 'POOR'}")
        
        print(f"\n{'='*60}")
        
        # Show recent trades
        if result.trades:
            print(f"LAST 5 TRADES:")
            for trade in result.trades[-5:]:
                status = "WIN" if trade.profit_loss > 0 else "LOSS"
                print(f"  {trade.entry_time.strftime('%Y-%m-%d %H:%M')} | {trade.pair} | "
                     f"R{trade.entry_value:.2f} -> R{trade.exit_value:.2f} | "
                     f"{trade.profit_percentage:.1f}% | {status}")
        
        return result

# Test function to run backtests
async def run_backtest_analysis():
    """Run comprehensive backtest analysis"""
    from historical_data_service import HistoricalDataService
    
    # Initialize services
    data_service = HistoricalDataService()
    
    # Test pairs according to user requirements
    test_pairs = ['BTC/ZAR', 'ETH/ZAR', 'XRP/ZAR']
    
    results = {}
    
    for pair in test_pairs:
        print(f"\n{'#'*60}")
        print(f"BACKTESTING {pair}")
        print(f"{'#'*60}")
        
        # Get historical data (90 days for faster testing)
        data = await data_service.get_historical_data(pair, '1h', 90)
        
        if data.empty:
            print(f"No data available for {pair}")
            continue
        
        # Initialize backtester
        backtester = CryptoBacktester(
            initial_capital=154273.71,  # User's current portfolio
            risk_per_trade=0.04,        # 4% risk per trade
            monthly_target=8000,        # R8000/month target
            xrp_hold_amount=1000        # 1000 XRP long-term hold
        )
        
        # Run backtest
        result = backtester.backtest(data, pair)
        
        # Print and store results
        backtester.print_results(result)
        results[pair] = result
    
    # Summary comparison
    if results:
        print(f"\n{'='*80}")
        print(f"MULTI-PAIR COMPARISON")
        print(f"{'='*80}")
        
        for pair, result in results.items():
            months = (result.end_date - result.start_date).days / 30.44
            monthly_profit = result.total_profit / months if months > 0 else 0
            print(f"{pair:>10} | Total: R{result.total_profit:>8,.0f} | "
                 f"Monthly: R{monthly_profit:>6,.0f} | Win Rate: {result.win_rate:>5.1f}% | "
                 f"Drawdown: {result.max_drawdown:>5.1f}%")
    
    return results

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_backtest_analysis())