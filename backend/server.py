from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import asyncio
import logging
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import numpy as np
# Redis temporarily disabled due to compatibility issues
# try:
#     import aioredis
# except ImportError:
#     aioredis = None
aioredis = None

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import our custom modules
from luno_integration.luno_client import LunoClient
from probability_engine.goal_calculator import GoalProbabilityCalculator
# Temporarily disabled due to dependency issues
# from ai_strategies.freqai_strategy import FreqAITradingStrategy
# from freqtrade.freqtrade_controller import FreqTradeController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Redis connection for real-time data
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')

# FastAPI app
app = FastAPI(title="AI Crypto Trading Bot", version="1.0.0", description="Advanced AI-powered cryptocurrency trading system")
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cryptobot.zikhethele.properties", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TradingConfig(BaseModel):
    daily_target_zar: float = 1000.0
    max_daily_risk_percent: float = 2.0
    allocation_scalping_percent: float = 60.0
    allocation_accumulation_percent: float = 40.0
    max_open_trades: int = 5
    stop_loss_percent: float = 1.5
    take_profit_percent: float = 3.0

class TradeRequest(BaseModel):
    pair: str
    side: str  # 'buy' or 'sell'
    amount: float
    order_type: str = 'market'  # 'market' or 'limit'
    price: Optional[float] = None

class TradingGoals(BaseModel):
    daily_profit_target: float
    weekly_profit_target: float
    monthly_profit_target: float
    accumulation_target_btc: float
    accumulation_target_eth: float

class TradeRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pair: str
    side: str
    amount: float
    price: float
    profit_zar: float
    strategy: str
    confidence: float

class PerformanceMetrics(BaseModel):
    daily_pnl: float
    weekly_pnl: float
    monthly_pnl: float
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    current_balance: float

# Debug: Print ALL environment variables related to Luno
logger.info("=== DEBUGGING ENVIRONMENT VARIABLES ===")
for key, value in os.environ.items():
    if 'LUNO' in key:
        logger.info(f"ENV {key}: {'*' * (len(value) - 4) + value[-4:] if value else 'EMPTY'}")
    elif key in ['MONGO_URL', 'API_TOKEN', 'REDIS_URL']:
        logger.info(f"ENV {key}: {'SET' if value else 'EMPTY'}")

# Check if .env file exists and what it contains
env_file_path = ROOT_DIR / '.env'
logger.info(f".env file exists: {env_file_path.exists()}")

# Also check parent directory .env
parent_env_path = ROOT_DIR.parent / '.env'  
logger.info(f"Parent .env file exists: {parent_env_path.exists()}")

# Global instances
luno_api_key = os.environ.get('LUNO_API_KEY', '').strip().strip('"').strip("'")
luno_api_secret = os.environ.get('LUNO_SECRET', '').strip().strip('"').strip("'")

logger.info(f"Final API Key loaded: '{luno_api_key}'")
logger.info(f"Final API Secret loaded: '{luno_api_secret}'")
logger.info(f"API Key length: {len(luno_api_key)}")
logger.info(f"API Secret length: {len(luno_api_secret)}")

# Check for invisible characters
logger.info(f"API Key bytes: {luno_api_key.encode('utf-8')}")
logger.info(f"API Secret bytes: {luno_api_secret.encode('utf-8')}")

# Check if there are any whitespace issues
logger.info(f"API Key stripped: '{luno_api_key.strip()}'")
logger.info(f"API Secret stripped: '{luno_api_secret.strip()}'")
logger.info(f"API Key == stripped: {luno_api_key == luno_api_key.strip()}")
logger.info(f"API Secret == stripped: {luno_api_secret == luno_api_secret.strip()}")

if not luno_api_key or not luno_api_secret:
    logger.error("CRITICAL: Luno API credentials not set in environment variables!")

luno_client = LunoClient(
    api_key=luno_api_key,
    api_secret=luno_api_secret
)
goal_calculator = GoalProbabilityCalculator()
# Temporarily disabled due to dependency issues
# freqtrade_controller = FreqTradeController()
# ai_strategy = FreqAITradingStrategy()
freqtrade_controller = None
ai_strategy = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Authentication
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Implement proper JWT validation here
    if token != os.environ.get('API_TOKEN', 'secure_token_123'):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# API Routes

@app.get("/api/")
async def root():
    return {"message": "AI Crypto Trading Bot API", "version": "1.0.0", "status": "active"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Luno connection
        luno_status = await luno_client.get_balance()
        
        # Check MongoDB
        await db.trades.find_one()
        
        # Check FreqTrade
        ft_status = await freqtrade_controller.get_status() if freqtrade_controller else False
        
        return {
            "status": "healthy",
            "services": {
                "luno": "connected" if luno_status else "disconnected",
                "database": "connected",
                "freqtrade": "running" if ft_status else "disabled"
            },
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.get("/api/balance")
async def get_balance():
    """Get current account balance from Luno"""
    try:
        balance = await luno_client.get_balance()
        
        # Add staking information if available
        try:
            staking_balance = await luno_client.get_staking_balance()
            if staking_balance:
                balance.update(staking_balance)
        except Exception as e:
            logger.warning(f"Staking balance fetch failed: {e}")
        
        return {"status": "success", "data": balance}
    except Exception as e:
        logger.error(f"Balance fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crypto-prices")
async def get_crypto_prices():
    """Get USD prices for cryptocurrencies that don't have ZAR pairs"""
    try:
        # Updated prices for all your holdings
        usd_prices = {
            "HBAR": 0.062,  # $0.062 per HBAR
            "ETH": 2400.0,  # $2400 per ETH
            "XRP": 0.58,    # $0.58 per XRP
            "ADA": 0.45,    # $0.45 per ADA
            "TRX": 0.16,    # $0.16 per TRX
            "XLM": 0.12,    # $0.12 per XLM
            "DOT": 5.20,    # $5.20 per DOT
            "NEAR": 3.50,   # $3.50 per NEAR
            "SOL": 145.0,   # $145 per SOL
            "DOGE": 0.08,   # $0.08 per DOGE
            "BERA": 0.50,   # $0.50 per BERA (estimated)
            "USD_TO_ZAR": 18.50  # Exchange rate
        }
        
        return {"status": "success", "data": usd_prices}
    except Exception as e:
        logger.error(f"Crypto prices fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-data/{pair}")
async def get_market_data(pair: str):
    """Get current market data for a trading pair"""
    try:
        ticker = await luno_client.get_ticker(pair)
        orderbook = await luno_client.get_orderbook(pair)
        
        return {
            "status": "success",
            "data": {
                "ticker": ticker,
                "orderbook": orderbook,
                "timestamp": datetime.utcnow()
            }
        }
    except Exception as e:
        logger.error(f"Market data fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trade")
async def execute_trade(trade_request: TradeRequest, token: str = Depends(verify_token)):
    """Execute a manual trade"""
    try:
        # Validate trade request
        if trade_request.amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid trade amount")
        
        # Execute trade via Luno
        result = await luno_client.place_order(
            pair=trade_request.pair,
            order_type=trade_request.order_type,
            side=trade_request.side,
            volume=trade_request.amount,
            price=trade_request.price
        )
        
        # Record trade in database
        trade_record = TradeRecord(
            pair=trade_request.pair,
            side=trade_request.side,
            amount=trade_request.amount,
            price=result.get('price', 0),
            profit_zar=0,  # Will be calculated later
            strategy="manual",
            confidence=1.0
        )
        
        await db.trades.insert_one(trade_record.dict())
        
        # Broadcast trade update
        await manager.broadcast(json.dumps({
            "type": "trade_executed",
            "data": trade_record.dict()
        }))
        
        return {"status": "success", "data": result}
        
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/goals/probability")
async def get_goal_probability():
    """Get probability of achieving daily/weekly/monthly goals"""
    try:
        # Get recent performance data
        recent_trades = await db.trades.find(
            {"timestamp": {"$gte": datetime.utcnow() - timedelta(days=30)}}
        ).to_list(1000)
        
        # Calculate probabilities
        daily_prob = goal_calculator.calculate_daily_probability(recent_trades, target_zar=1000)
        weekly_prob = goal_calculator.calculate_weekly_probability(recent_trades, target_zar=7000)
        monthly_prob = goal_calculator.calculate_monthly_probability(recent_trades, target_zar=30000)
        
        # Get current progress
        today_trades = await db.trades.find(
            {"timestamp": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}}
        ).to_list(1000)
        
        daily_progress = sum(trade.get('profit_zar', 0) for trade in today_trades)
        
        return {
            "status": "success",
            "data": {
                "probabilities": {
                    "daily_target_1000": daily_prob,
                    "weekly_target_7000": weekly_prob,
                    "monthly_target_30000": monthly_prob
                },
                "current_progress": {
                    "daily_profit": daily_progress,
                    "target": 1000,
                    "progress_percent": (daily_progress / 1000) * 100
                },
                "confidence_level": goal_calculator.get_confidence_level(recent_trades)
            }
        }
        
    except Exception as e:
        logger.error(f"Goal probability calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance")
async def get_performance_metrics():
    """Get comprehensive performance metrics"""
    try:
        # Get trades from different time periods
        now = datetime.utcnow()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        daily_trades = await db.trades.find({"timestamp": {"$gte": day_start}}).to_list(1000)
        weekly_trades = await db.trades.find({"timestamp": {"$gte": week_start}}).to_list(1000)
        monthly_trades = await db.trades.find({"timestamp": {"$gte": month_start}}).to_list(1000)
        
        # Calculate metrics
        metrics = PerformanceMetrics(
            daily_pnl=sum(trade.get('profit_zar', 0) for trade in daily_trades),
            weekly_pnl=sum(trade.get('profit_zar', 0) for trade in weekly_trades),
            monthly_pnl=sum(trade.get('profit_zar', 0) for trade in monthly_trades),
            total_trades=len(monthly_trades),
            win_rate=goal_calculator.calculate_win_rate(monthly_trades),
            sharpe_ratio=goal_calculator.calculate_sharpe_ratio(monthly_trades),
            max_drawdown=goal_calculator.calculate_max_drawdown(monthly_trades),
            current_balance=(await luno_client.get_balance()).get('ZAR_balance', 0)
        )
        
        return {"status": "success", "data": metrics.dict()}
        
    except Exception as e:
        logger.error(f"Performance metrics calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai-strategy/status")
async def get_ai_strategy_status():
    """Get current AI strategy status and predictions"""
    try:
        if not ai_strategy:
            return {
                "status": "success",
                "data": {
                    "strategy_status": "disabled",
                    "predictions": [],
                    "model_confidence": 0.0,
                    "last_retrain": None,
                    "next_retrain": None,
                    "message": "AI strategy temporarily disabled due to dependency issues"
                }
            }
        
        status = await ai_strategy.get_status()
        predictions = await ai_strategy.get_current_predictions()
        
        return {
            "status": "success",
            "data": {
                "strategy_status": status,
                "predictions": predictions,
                "model_confidence": ai_strategy.get_model_confidence(),
                "last_retrain": ai_strategy.last_retrain_time,
                "next_retrain": ai_strategy.next_retrain_time
            }
        }
        
    except Exception as e:
        logger.error(f"AI strategy status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-strategy/configure")
async def configure_ai_strategy(config: TradingConfig, token: str = Depends(verify_token)):
    """Configure AI trading strategy parameters"""
    try:
        if not ai_strategy:
            return {"status": "error", "message": "AI strategy temporarily disabled due to dependency issues"}
        
        await ai_strategy.update_config(config.dict())
        await db.config.replace_one({}, config.dict(), upsert=True)
        
        return {"status": "success", "message": "AI strategy configured successfully"}
        
    except Exception as e:
        logger.error(f"AI strategy configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trading/start")
async def start_automated_trading(token: str = Depends(verify_token)):
    """Start automated trading"""
    try:
        if not ai_strategy or not freqtrade_controller:
            return {"status": "error", "message": "AI trading temporarily disabled due to dependency issues"}
        
        await ai_strategy.start_trading()
        await freqtrade_controller.start()
        
        return {"status": "success", "message": "Automated trading started"}
        
    except Exception as e:
        logger.error(f"Failed to start automated trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trading/stop")
async def stop_automated_trading(token: str = Depends(verify_token)):
    """Stop automated trading"""
    try:
        if not ai_strategy or not freqtrade_controller:
            return {"status": "error", "message": "AI trading temporarily disabled due to dependency issues"}
        
        await ai_strategy.stop_trading()
        await freqtrade_controller.stop()
        
        return {"status": "success", "message": "Automated trading stopped"}
        
    except Exception as e:
        logger.error(f"Failed to stop automated trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades/history")
async def get_trade_history(limit: int = 100, skip: int = 0):
    """Get trading history"""
    try:
        trades = await db.trades.find().sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        total_count = await db.trades.count_documents({})
        
        return {
            "status": "success",
            "data": {
                "trades": trades,
                "total_count": total_count,
                "limit": limit,
                "skip": skip
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/api/ws/live-data")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time trading data"""
    await manager.connect(websocket)
    try:
        while True:
            # Send live data every 5 seconds
            data = {
                "type": "live_update",
                "timestamp": datetime.utcnow().isoformat(),
                "balance": await luno_client.get_balance(),
                "active_trades": await ai_strategy.get_active_trades() if ai_strategy else [],
                "daily_pnl": await get_daily_pnl()
            }
            
            await manager.send_personal_message(json.dumps(data), websocket)
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def get_daily_pnl():
    """Helper function to get daily P&L"""
    day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_trades = await db.trades.find({"timestamp": {"$gte": day_start}}).to_list(1000)
    return sum(trade.get('profit_zar', 0) for trade in daily_trades)

# Background task to monitor and execute AI trading
async def ai_trading_loop():
    """Background task for AI trading execution"""
    while True:
        try:
            if ai_strategy and ai_strategy.is_trading_active:
                # Get AI predictions
                signals = await ai_strategy.get_trading_signals()
                
                # Execute trades based on signals
                for signal in signals:
                    if signal['confidence'] > 0.7:  # Only execute high-confidence signals
                        trade_result = await luno_client.place_order(
                            pair=signal['pair'],
                            order_type='market',
                            side=signal['side'],
                            volume=signal['amount']
                        )
                        
                        # Record the trade
                        trade_record = TradeRecord(
                            pair=signal['pair'],
                            side=signal['side'],
                            amount=signal['amount'],
                            price=trade_result.get('price', 0),
                            profit_zar=0,  # Will be calculated when trade closes
                            strategy="freqai",
                            confidence=signal['confidence']
                        )
                        
                        await db.trades.insert_one(trade_record.dict())
                        
                        # Broadcast trade
                        await manager.broadcast(json.dumps({
                            "type": "ai_trade_executed",
                            "data": trade_record.dict()
                        }))
                        
                        logger.info(f"AI trade executed: {signal}")
                
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"AI trading loop error: {e}")
            await asyncio.sleep(60)

# Start background tasks on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting AI Crypto Trading Bot")
    
    # Initialize Redis connection if available
    if aioredis:
        try:
            app.state.redis = await aioredis.from_url(redis_url)
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            app.state.redis = None
    else:
        logger.warning("aioredis not available, Redis features disabled")
        app.state.redis = None
    
    # Start AI trading loop
    asyncio.create_task(ai_trading_loop())
    
    logger.info("AI Crypto Trading Bot started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Crypto Trading Bot")
    
    # Close database connection
    client.close()
    
    # Close Redis connection
    if hasattr(app.state, 'redis'):
        await app.state.redis.close()
    
    logger.info("AI Crypto Trading Bot shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)