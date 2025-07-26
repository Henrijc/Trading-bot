"""
Luno Trading Bot - Freqtrade-inspired standalone trading system
This bot manages live trading on Luno exchange with AI-driven decision making
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add the backend directory to Python path so we can import our services
sys.path.append('/app/backend')
sys.path.append('/app/freqtrade/user_data')

from services.luno_service import LunoService
from services.technical_analysis_service import TechnicalAnalysisService
from services.historical_data_service import HistoricalDataService
from freqai_service import FreqAIService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/freqtrade/user_data/logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LunoTradingBot:
    """
    Main trading bot class - inspired by Freqtrade architecture
    """
    
    def __init__(self, config_path: str = "/app/freqtrade/config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.is_running = False
        self.trades = {}
        self.trade_id_counter = 1
        
        # Initialize services
        self.luno_service = LunoService()
        self.ta_service = TechnicalAnalysisService()
        self.historical_service = HistoricalDataService()
        self.freqai_service = FreqAIService()
        
        # Load strategy
        self.strategy = self._load_strategy()
        
        logger.info("Luno Trading Bot initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _load_strategy(self):
        """Load trading strategy"""
        try:
            strategy_path = Path(self.config['strategy_path'])
            sys.path.append(str(strategy_path))
            
            # Try to import the FreqAI strategy first
            try:
                from LunoFreqAIStrategy import LunoFreqAIStrategy
                strategy = LunoFreqAIStrategy()
                logger.info(f"FreqAI Strategy '{strategy.__class__.__name__}' loaded successfully")
                return strategy
            except ImportError:
                # Fallback to test strategy
                from luno_test_strategy import get_strategy
                strategy = get_strategy()
                logger.info(f"Fallback Strategy '{strategy.name}' loaded successfully")
                return strategy
                
        except Exception as e:
            logger.error(f"Failed to load strategy: {e}")
            raise
    
    async def start_bot(self):
        """Start the trading bot"""
        try:
            if self.is_running:
                return {"status": "already_running"}
            
            self.is_running = True
            logger.info("Trading bot started")
            
            # Start main trading loop in background
            asyncio.create_task(self._trading_loop())
            
            return {
                "status": "started",
                "message": "Trading bot is now running",
                "dry_run": self.config.get("dry_run", True),
                "pairs": self.config["exchange"]["pair_whitelist"]
            }
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            self.is_running = False
            raise
    
    async def stop_bot(self):
        """Stop the trading bot"""
        try:
            self.is_running = False
            logger.info("Trading bot stopped")
            
            return {
                "status": "stopped",
                "message": "Trading bot has been stopped",
                "open_trades": len(self.trades)
            }
        except Exception as e:
            logger.error(f"Failed to stop bot: {e}")
            raise
    
    async def get_status(self):
        """Get current bot status"""
        try:
            return {
                "status": "running" if self.is_running else "stopped",
                "strategy": self.strategy.name,
                "dry_run": self.config.get("dry_run", True),
                "open_trades_count": len(self.trades),
                "pairs": self.config["exchange"]["pair_whitelist"],
                "uptime": "00:00:00",  # TODO: Calculate actual uptime
                "total_profit": self._calculate_total_profit()
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            raise
    
    async def _trading_loop(self):
        """Main trading loop"""
        logger.info("Starting main trading loop")
        
        while self.is_running:
            try:
                # Process each trading pair
                for pair in self.config["exchange"]["pair_whitelist"]:
                    await self._process_pair(pair)
                
                # Wait for next iteration
                await asyncio.sleep(self.config["internals"]["process_throttle_secs"])
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying
        
        logger.info("Trading loop stopped")
    
    async def _process_pair(self, pair: str):
        """Process trading signals for a specific pair using FreqAI predictions"""
        try:
            # Get historical data
            symbol = pair.replace("/", "")  # BTC/ZAR -> BTCZAR
            df = await self.historical_service.get_historical_data(symbol, days=50)
            
            if df.empty:
                logger.warning(f"No historical data for {pair}")
                return
            
            # Get FreqAI prediction
            ai_prediction = await self.freqai_service.get_prediction(pair, df)
            
            # Apply strategy indicators (fallback if AI fails)
            df = self.strategy.populate_indicators(df, {"pair": pair})
            df = self.strategy.populate_entry_trend(df, {"pair": pair})
            df = self.strategy.populate_exit_trend(df, {"pair": pair})
            
            # Enhanced decision making with AI predictions
            if 'error' not in ai_prediction:
                # Use AI predictions as primary signal
                await self._process_ai_signals(pair, df, ai_prediction)
            else:
                logger.warning(f"AI prediction failed for {pair}, using technical analysis fallback")
                # Fallback to traditional technical analysis
                await self._process_traditional_signals(pair, df)
            
        except Exception as e:
            logger.error(f"Error processing pair {pair}: {e}")
    
    async def _process_ai_signals(self, pair: str, df: pd.DataFrame, ai_prediction: Dict):
        """Process AI-enhanced trading signals"""
        try:
            prediction_value = ai_prediction.get('prediction_roc_5', 0)
            confidence = ai_prediction.get('confidence', 0)
            direction = ai_prediction.get('direction', 'neutral')
            
            logger.info(f"AI Signal for {pair}: {direction} (prediction: {prediction_value:.4f}, confidence: {confidence:.2f})")
            
            # Check for entry signals (AI-driven)
            if self._has_ai_entry_signal(prediction_value, confidence, direction, pair):
                await self._process_entry_signal(pair, df, signal_type='ai', ai_data=ai_prediction)
            
            # Check existing trades for AI-enhanced exit signals
            await self._process_ai_exit_signals(pair, df, ai_prediction)
            
        except Exception as e:
            logger.error(f"Error processing AI signals for {pair}: {e}")
    
    async def _process_traditional_signals(self, pair: str, df: pd.DataFrame):
        """Process traditional technical analysis signals"""
        try:
            # Check for entry signals
            if self._has_entry_signal(df, pair):
                await self._process_entry_signal(pair, df, signal_type='technical')
            
            # Check existing trades for exit signals
            await self._process_exit_signals(pair, df)
            
        except Exception as e:
            logger.error(f"Error processing traditional signals for {pair}: {e}")
    
    def _has_ai_entry_signal(self, prediction: float, confidence: float, direction: str, pair: str) -> bool:
        """Check if there's an AI-driven entry signal"""
        try:
            # AI signal thresholds
            min_prediction_threshold = 0.02  # Minimum 2% predicted return
            min_confidence_threshold = 0.6   # Minimum 60% confidence
            
            # Strong bullish AI signal
            ai_bullish = (
                prediction > min_prediction_threshold and
                confidence > min_confidence_threshold and
                direction == 'bullish'
            )
            
            if ai_bullish:
                logger.info(f"AI Entry Signal: {pair} - Prediction: {prediction:.4f}, Confidence: {confidence:.2f}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking AI entry signal for {pair}: {e}")
            return False
    
    async def _process_ai_exit_signals(self, pair: str, df: pd.DataFrame, ai_prediction: Dict):
        """Process AI-enhanced exit signals for existing trades"""
        try:
            # Find trades for this pair
            pair_trades = {tid: trade for tid, trade in self.trades.items() 
                          if trade['pair'] == pair and trade['status'] == 'open'}
            
            if not pair_trades:
                return
            
            current_price = df.iloc[-1]['close']
            prediction_value = ai_prediction.get('prediction_roc_5', 0)
            confidence = ai_prediction.get('confidence', 0)
            direction = ai_prediction.get('direction', 'neutral')
            
            for trade_id, trade in pair_trades.items():
                # Calculate current profit
                entry_rate = trade['entry_rate']
                current_profit = (current_price - entry_rate) / entry_rate
                trade['profit'] = current_profit
                
                # AI-enhanced exit logic
                should_exit = False
                exit_reason = None
                
                # Strong bearish AI signal
                if (prediction_value < -0.015 and confidence > 0.6 and direction == 'bearish'):
                    should_exit = True
                    exit_reason = "ai_bearish_signal"
                
                # AI confidence drops significantly
                elif confidence < 0.3:
                    should_exit = True
                    exit_reason = "ai_low_confidence"
                
                # Traditional exit conditions enhanced with AI
                elif current_profit > 0.08 and direction != 'bullish':  # Take profit if AI not bullish
                    should_exit = True
                    exit_reason = "ai_enhanced_profit_taking"
                
                elif current_profit < -0.03 and direction == 'bearish':  # Stop loss if AI bearish
                    should_exit = True
                    exit_reason = "ai_enhanced_stop_loss"
                
                # Execute exit if needed
                if should_exit:
                    await self._execute_exit(trade_id, current_price, exit_reason)
                    logger.info(f"AI Exit: {pair} - {exit_reason} (AI: {direction}, Confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error processing AI exit signals for {pair}: {e}")
    
    def _has_entry_signal(self, df: pd.DataFrame, pair: str) -> bool:
        """Check if there's an entry signal"""
        try:
            if df.empty or 'enter_long' not in df.columns:
                return False
            
            # Check the most recent signal
            latest_signal = df.iloc[-1]['enter_long'] if 'enter_long' in df.columns else 0
            return latest_signal == 1
            
        except Exception as e:
            logger.error(f"Error checking entry signal for {pair}: {e}")
            return False
    
    async def _process_entry_signal(self, pair: str, df: pd.DataFrame):
        """Process entry signal and potentially create trade"""
        try:
            # Check if we already have a trade for this pair
            if any(trade['pair'] == pair for trade in self.trades.values()):
                logger.info(f"Already have open trade for {pair}")
                return
            
            # Check max open trades
            if len(self.trades) >= self.config.get("max_open_trades", 3):
                logger.info("Maximum open trades reached")
                return
            
            # Get current price
            current_price = df.iloc[-1]['close']
            
            # Calculate position size (4% risk as per user requirements)
            portfolio_value = 154273.71  # User's capital
            risk_amount = portfolio_value * 0.04  # R6170.95
            position_size = risk_amount / current_price
            
            # Confirm trade entry using strategy
            if self.strategy.confirm_trade_entry(
                pair=pair,
                order_type="market",
                amount=position_size,
                rate=current_price,
                time_in_force="gtc",
                current_time=datetime.utcnow(),
                entry_tag="strategy_entry",
                side="buy"
            ):
                # Create trade
                trade_id = str(self.trade_id_counter)
                self.trade_id_counter += 1
                
                trade = {
                    "trade_id": trade_id,
                    "pair": pair,
                    "side": "buy",
                    "amount": position_size,
                    "entry_rate": current_price,
                    "entry_time": datetime.utcnow().isoformat(),
                    "status": "open",
                    "profit": 0.0,
                    "exit_rate": None,
                    "exit_time": None
                }
                
                if self.config.get("dry_run", True):
                    # Dry run - just log the trade
                    logger.info(f"DRY RUN: Created trade {trade_id} for {pair}: {position_size:.6f} at {current_price}")
                    self.trades[trade_id] = trade
                else:
                    # Live trading - execute via Luno API
                    # TODO: Implement actual Luno order execution
                    logger.info(f"LIVE: Would create trade {trade_id} for {pair}")
                    self.trades[trade_id] = trade
            
        except Exception as e:
            logger.error(f"Error processing entry signal for {pair}: {e}")
    
    async def _process_exit_signals(self, pair: str, df: pd.DataFrame):
        """Process exit signals for existing trades"""
        try:
            # Find trades for this pair
            pair_trades = {tid: trade for tid, trade in self.trades.items() 
                          if trade['pair'] == pair and trade['status'] == 'open'}
            
            if not pair_trades:
                return
            
            current_price = df.iloc[-1]['close']
            
            for trade_id, trade in pair_trades.items():
                # Calculate current profit
                entry_rate = trade['entry_rate']
                current_profit = (current_price - entry_rate) / entry_rate
                trade['profit'] = current_profit
                
                # Check for exit signal
                should_exit = False
                exit_reason = None
                
                # Strategy exit signal
                if df.iloc[-1].get('exit_long', 0) == 1:
                    should_exit = True
                    exit_reason = "strategy_exit"
                
                # Custom exit logic
                custom_exit = self.strategy.custom_exit(
                    pair=pair,
                    trade=trade,
                    current_time=datetime.utcnow(),
                    current_rate=current_price,
                    current_profit=current_profit
                )
                
                if custom_exit:
                    should_exit = True
                    exit_reason = custom_exit
                
                # Execute exit if needed
                if should_exit:
                    await self._execute_exit(trade_id, current_price, exit_reason)
            
        except Exception as e:
            logger.error(f"Error processing exit signals for {pair}: {e}")
    
    async def _execute_exit(self, trade_id: str, exit_price: float, reason: str):
        """Execute trade exit"""
        try:
            trade = self.trades[trade_id]
            
            # Update trade
            trade['exit_rate'] = exit_price
            trade['exit_time'] = datetime.utcnow().isoformat()
            trade['status'] = 'closed'
            trade['exit_reason'] = reason
            
            # Calculate final profit
            entry_rate = trade['entry_rate']
            profit_pct = (exit_price - entry_rate) / entry_rate * 100
            profit_zar = trade['amount'] * (exit_price - entry_rate)
            
            if self.config.get("dry_run", True):
                logger.info(f"DRY RUN: Closed trade {trade_id} - {reason}: {profit_pct:.2f}% (R{profit_zar:.2f})")
            else:
                # Live trading - execute via Luno API
                logger.info(f"LIVE: Would close trade {trade_id} - {reason}")
            
        except Exception as e:
            logger.error(f"Error executing exit for trade {trade_id}: {e}")
    
    def _calculate_total_profit(self) -> float:
        """Calculate total profit from all trades"""
        try:
            total_profit = 0.0
            for trade in self.trades.values():
                if trade['status'] == 'closed':
                    entry_rate = trade['entry_rate']
                    exit_rate = trade['exit_rate']
                    profit = trade['amount'] * (exit_rate - entry_rate)
                    total_profit += profit
            return total_profit
        except Exception as e:
            logger.error(f"Error calculating total profit: {e}")
            return 0.0
    
    async def get_trades(self) -> List[Dict]:
        """Get all trades"""
        return list(self.trades.values())


# Global bot instance
bot = LunoTradingBot()

# FastAPI application for REST API
app = FastAPI(title="Luno Trading Bot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://34.121.6.206:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/api/v1/status")
async def get_bot_status():
    """Get bot status"""
    try:
        return await bot.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/start")
async def start_bot():
    """Start the trading bot"""
    try:
        return await bot.start_bot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/stop")
async def stop_bot():
    """Stop the trading bot"""
    try:
        return await bot.stop_bot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/trades")
async def get_trades():
    """Get all trades"""
    try:
        trades = await bot.get_trades()
        return {"trades": trades, "count": len(trades)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/profit")
async def get_profit():
    """Get profit summary"""
    try:
        total_profit = bot._calculate_total_profit()
        trades = await bot.get_trades()
        
        closed_trades = [t for t in trades if t['status'] == 'closed']
        winning_trades = [t for t in closed_trades if t['profit'] > 0]
        
        return {
            "total_profit": total_profit,
            "total_trades": len(closed_trades),
            "winning_trades": len(winning_trades),
            "win_rate": len(winning_trades) / len(closed_trades) if closed_trades else 0,
            "avg_profit": total_profit / len(closed_trades) if closed_trades else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# FreqAI endpoints - NEW
@app.post("/api/v1/freqai/train")
async def train_freqai_models():
    """Train FreqAI models for all pairs"""
    try:
        results = await bot.freqai_service.train_all_models()
        return {"training_results": results, "message": "FreqAI model training completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/freqai/status")
async def get_freqai_status():
    """Get FreqAI model status"""
    try:
        status = bot.freqai_service.get_model_status()
        return {"freqai_status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/freqai/predict/{pair}")
async def get_freqai_prediction(pair: str):
    """Get FreqAI prediction for a specific pair"""
    try:
        # Get recent data for prediction
        symbol = pair.replace("/", "")
        df = await bot.historical_service.get_historical_data(symbol, days=50)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {pair}")
        
        prediction = await bot.freqai_service.get_prediction(pair, df)
        return {"pair": pair, "prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Health check"""
    return {"message": "Luno Trading Bot API is running", "status": "healthy"}

if __name__ == "__main__":
    # Run the bot API server
    uvicorn.run(
        "luno_trading_bot:app",
        host="0.0.0.0",
        port=8082,
        reload=False,
        access_log=True
    )