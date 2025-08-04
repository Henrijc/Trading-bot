"""
FastAPI Integration for Freqtrade-style Backtesting
Integrates historical data and backtesting capabilities into the existing AI Crypto Trading Coach
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path

# Import our new services
from backend.services.historical_data_service import HistoricalDataService
from backend.services.backtesting_service import CryptoBacktester, BacktestResult, TradeAction

# Import existing services
from services.luno_service import LunoService

# Create router for backtesting endpoints
backtest_router = APIRouter(prefix="/backtest", tags=["backtesting"])

# Pydantic models for API requests/responses
class BacktestRequest(BaseModel):
    symbol: str = "BTC/ZAR"
    timeframe: str = "1h"
    days_back: int = 90
    initial_capital: float = 154273.71
    risk_per_trade: float = 0.04
    monthly_target: float = 8000
    xrp_hold_amount: float = 1000

class BacktestResponse(BaseModel):
    success: bool
    symbol: str
    initial_capital: float
    final_capital: float
    total_profit: float
    total_percentage: float
    total_trades: int
    win_rate: float
    avg_profit_per_trade: float
    max_drawdown: float
    monthly_profit: float
    target_achievement: float
    risk_level: str
    trades_summary: List[Dict]
    error: Optional[str] = None

class HistoricalDataRequest(BaseModel):
    symbol: str = "BTC/ZAR"
    timeframe: str = "1h"
    days_back: int = 30

class HistoricalDataResponse(BaseModel):
    success: bool
    symbol: str
    data_points: int
    price_range: Dict[str, float]
    latest_price: float
    data_period: Dict[str, str]
    sample_data: List[Dict]
    error: Optional[str] = None

class MultiPairBacktestRequest(BaseModel):
    symbols: List[str] = ["BTC/ZAR", "ETH/ZAR", "XRP/ZAR"]
    timeframe: str = "1h"
    days_back: int = 90
    initial_capital: float = 154273.71
    risk_per_trade: float = 0.04
    monthly_target: float = 8000
    xrp_hold_amount: float = 1000

class MultiPairBacktestResponse(BaseModel):
    success: bool
    results: Dict[str, BacktestResponse]
    comparison: Dict[str, Dict[str, float]]
    best_performer: str
    summary: Dict[str, float]
    error: Optional[str] = None

# Global instances
data_service = HistoricalDataService()
luno_service = LunoService()

@backtest_router.get("/health")
async def backtest_health():
    """Health check for backtesting service"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "historical_data": "available",
            "backtesting_engine": "available",
            "luno_integration": "available"
        }
    }

@backtest_router.post("/historical-data", response_model=HistoricalDataResponse)
async def get_historical_data(request: HistoricalDataRequest):
    """Get historical market data for a specific symbol"""
    try:
        # Fetch historical data
        data = await data_service.get_historical_data(
            symbol=request.symbol,
            timeframe=request.timeframe,
            days_back=request.days_back
        )
        
        if data.empty:
            return HistoricalDataResponse(
                success=False,
                symbol=request.symbol,
                data_points=0,
                price_range={"min": 0, "max": 0},
                latest_price=0,
                data_period={"start": "", "end": ""},
                sample_data=[],
                error="No data available for the specified symbol and timeframe"
            )
        
        # Prepare response data
        price_range = {
            "min": float(data['low'].min()),
            "max": float(data['high'].max())
        }
        
        data_period = {
            "start": data.index[0].strftime('%Y-%m-%d %H:%M:%S'),
            "end": data.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Sample data (last 10 candles)
        sample_data = []
        for i in range(max(0, len(data) - 10), len(data)):
            row = data.iloc[i]
            sample_data.append({
                "timestamp": data.index[i].strftime('%Y-%m-%d %H:%M:%S'),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row['volume'])
            })
        
        return HistoricalDataResponse(
            success=True,
            symbol=request.symbol,
            data_points=len(data),
            price_range=price_range,
            latest_price=float(data['close'].iloc[-1]),
            data_period=data_period,
            sample_data=sample_data
        )
        
    except Exception as e:
        return HistoricalDataResponse(
            success=False,
            symbol=request.symbol,
            data_points=0,
            price_range={"min": 0, "max": 0},
            latest_price=0,
            data_period={"start": "", "end": ""},
            sample_data=[],
            error=str(e)
        )

@backtest_router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """Run a backtest for a single trading pair"""
    try:
        # Get historical data
        data = await data_service.get_historical_data(
            symbol=request.symbol,
            timeframe=request.timeframe,
            days_back=request.days_back
        )
        
        if data.empty:
            return BacktestResponse(
                success=False,
                symbol=request.symbol,
                initial_capital=request.initial_capital,
                final_capital=request.initial_capital,
                total_profit=0,
                total_percentage=0,
                total_trades=0,
                win_rate=0,
                avg_profit_per_trade=0,
                max_drawdown=0,
                monthly_profit=0,
                target_achievement=0,
                risk_level="N/A",
                trades_summary=[],
                error="No historical data available"
            )
        
        # Initialize backtester
        backtester = CryptoBacktester(
            initial_capital=request.initial_capital,
            risk_per_trade=request.risk_per_trade,
            monthly_target=request.monthly_target,
            xrp_hold_amount=request.xrp_hold_amount
        )
        
        # Run backtest
        result = backtester.backtest(data, request.symbol)
        
        # Calculate monthly profit
        months = (result.end_date - result.start_date).days / 30.44
        monthly_profit = result.total_profit / months if months > 0 else 0
        
        # Calculate target achievement
        target_achievement = (monthly_profit / request.monthly_target) * 100 if request.monthly_target > 0 else 0
        
        # Determine risk level
        risk_level = "LOW" if result.max_drawdown > -10 else "MEDIUM" if result.max_drawdown > -20 else "HIGH"
        
        # Prepare trades summary (last 10 trades)
        trades_summary = []
        for trade in result.trades[-10:]:
            trades_summary.append({
                "entry_time": trade.entry_time.strftime('%Y-%m-%d %H:%M'),
                "exit_time": trade.exit_time.strftime('%Y-%m-%d %H:%M') if trade.exit_time else None,
                "pair": trade.pair,
                "action": trade.action.value,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "entry_value": trade.entry_value,
                "exit_value": trade.exit_value,
                "profit_loss": trade.profit_loss,
                "profit_percentage": trade.profit_percentage,
                "reason": trade.reason
            })
        
        return BacktestResponse(
            success=True,
            symbol=request.symbol,
            initial_capital=result.initial_capital,
            final_capital=result.final_capital,
            total_profit=result.total_profit,
            total_percentage=result.total_percentage,
            total_trades=result.total_trades,
            win_rate=result.win_rate,
            avg_profit_per_trade=result.avg_profit_per_trade,
            max_drawdown=result.max_drawdown,
            monthly_profit=monthly_profit,
            target_achievement=target_achievement,
            risk_level=risk_level,
            trades_summary=trades_summary
        )
        
    except Exception as e:
        return BacktestResponse(
            success=False,
            symbol=request.symbol,
            initial_capital=request.initial_capital,
            final_capital=request.initial_capital,
            total_profit=0,
            total_percentage=0,
            total_trades=0,
            win_rate=0,
            avg_profit_per_trade=0,
            max_drawdown=0,
            monthly_profit=0,
            target_achievement=0,
            risk_level="N/A",
            trades_summary=[],
            error=str(e)
        )

@backtest_router.post("/multi-pair", response_model=MultiPairBacktestResponse)
async def run_multi_pair_backtest(request: MultiPairBacktestRequest):
    """Run backtests for multiple trading pairs and compare results"""
    try:
        results = {}
        comparison = {}
        
        for symbol in request.symbols:
            # Run individual backtest
            backtest_request = BacktestRequest(
                symbol=symbol,
                timeframe=request.timeframe,
                days_back=request.days_back,
                initial_capital=request.initial_capital,
                risk_per_trade=request.risk_per_trade,
                monthly_target=request.monthly_target,
                xrp_hold_amount=request.xrp_hold_amount
            )
            
            result = await run_backtest(backtest_request)
            results[symbol] = result
            
            # Add to comparison
            if result.success:
                comparison[symbol] = {
                    "total_profit": result.total_profit,
                    "monthly_profit": result.monthly_profit,
                    "win_rate": result.win_rate,
                    "max_drawdown": result.max_drawdown,
                    "target_achievement": result.target_achievement
                }
        
        # Find best performer
        best_performer = "N/A"
        best_profit = -float('inf')
        
        for symbol, comp in comparison.items():
            if comp["total_profit"] > best_profit:
                best_profit = comp["total_profit"]
                best_performer = symbol
        
        # Calculate summary statistics
        if comparison:
            total_profits = [comp["total_profit"] for comp in comparison.values()]
            monthly_profits = [comp["monthly_profit"] for comp in comparison.values()]
            win_rates = [comp["win_rate"] for comp in comparison.values()]
            
            summary = {
                "avg_total_profit": sum(total_profits) / len(total_profits),
                "avg_monthly_profit": sum(monthly_profits) / len(monthly_profits),
                "avg_win_rate": sum(win_rates) / len(win_rates),
                "best_total_profit": max(total_profits),
                "worst_total_profit": min(total_profits),
                "pairs_tested": len(comparison)
            }
        else:
            summary = {
                "avg_total_profit": 0,
                "avg_monthly_profit": 0,
                "avg_win_rate": 0,
                "best_total_profit": 0,
                "worst_total_profit": 0,
                "pairs_tested": 0
            }
        
        return MultiPairBacktestResponse(
            success=True,
            results=results,
            comparison=comparison,
            best_performer=best_performer,
            summary=summary
        )
        
    except Exception as e:
        return MultiPairBacktestResponse(
            success=False,
            results={},
            comparison={},
            best_performer="N/A",
            summary={},
            error=str(e)
        )

@backtest_router.get("/strategies")
async def get_available_strategies():
    """Get list of available trading strategies"""
    return {
        "strategies": [
            {
                "name": "RSI + Bollinger Bands",
                "description": "Combined RSI and Bollinger Bands strategy with 4% risk management",
                "parameters": {
                    "rsi_period": 14,
                    "rsi_oversold": 30,
                    "rsi_overbought": 70,
                    "bb_period": 20,
                    "bb_std_dev": 2,
                    "stop_loss": "4%",
                    "position_sizing": "Risk-based"
                },
                "suitable_for": ["BTC/ZAR", "ETH/ZAR", "XRP/ZAR"],
                "recommended_timeframes": ["1h", "4h", "1d"]
            }
        ],
        "risk_management": {
            "max_risk_per_trade": "4%",
            "position_sizing": "Dynamic based on stop-loss distance",
            "stop_loss": "Trailing 4% or technical levels",
            "max_open_positions": "3",
            "capital_preservation": "Reserved funds for long-term holds (XRP)"
        },
        "user_requirements": {
            "monthly_target": "R8,000",
            "current_portfolio": "R154,273.71",
            "xrp_long_term_hold": "1,000 XRP",
            "risk_tolerance": "Conservative with 4% max risk",
            "preferred_pairs": ["BTC/ZAR", "ETH/ZAR", "XRP/ZAR"]
        }
    }

@backtest_router.get("/performance/{symbol}")
async def get_strategy_performance(symbol: str, days: int = 30):
    """Get recent performance analysis for a specific symbol"""
    try:
        # Get recent historical data
        data = await data_service.get_historical_data(symbol, "1h", days)
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
        
        # Quick performance analysis
        start_price = data['close'].iloc[0]
        end_price = data['close'].iloc[-1]
        price_change = ((end_price - start_price) / start_price) * 100
        
        volatility = data['close'].pct_change().std() * 100
        avg_volume = data['volume'].mean()
        
        # Calculate simple moving averages
        data['sma_20'] = data['close'].rolling(window=20).mean()
        data['sma_50'] = data['close'].rolling(window=50).mean() if len(data) >= 50 else None
        
        current_vs_sma20 = ((end_price - data['sma_20'].iloc[-1]) / data['sma_20'].iloc[-1]) * 100
        
        # Trend analysis
        trend = "BULLISH" if current_vs_sma20 > 2 else "BEARISH" if current_vs_sma20 < -2 else "NEUTRAL"
        
        return {
            "symbol": symbol,
            "period_days": days,
            "price_performance": {
                "start_price": float(start_price),
                "end_price": float(end_price),
                "price_change_percent": float(price_change)
            },
            "technical_analysis": {
                "current_vs_sma20": float(current_vs_sma20),
                "trend": trend,
                "volatility_percent": float(volatility)
            },
            "market_data": {
                "avg_daily_volume": float(avg_volume),
                "high": float(data['high'].max()),
                "low": float(data['low'].min())
            },
            "strategy_suitability": {
                "rsi_suitable": volatility > 1.5,  # Good volatility for RSI signals
                "bb_suitable": volatility > 1.0,   # Sufficient volatility for BB
                "overall_rating": "GOOD" if volatility > 1.5 and abs(price_change) > 5 else "MODERATE"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task for automated backtesting
async def scheduled_backtest():
    """Run scheduled backtests and update performance metrics"""
    try:
        # Run multi-pair backtest
        request = MultiPairBacktestRequest()
        results = await run_multi_pair_backtest(request)
        
        # Store results for dashboard (could be saved to MongoDB)
        timestamp = datetime.utcnow().isoformat()
        
        # Log results
        print(f"[{timestamp}] Scheduled backtest completed:")
        if results.success:
            print(f"  Best performer: {results.best_performer}")
            print(f"  Average monthly profit: R{results.summary['avg_monthly_profit']:,.2f}")
            print(f"  Pairs tested: {results.summary['pairs_tested']}")
        
        return results
        
    except Exception as e:
        print(f"Scheduled backtest error: {e}")
        return None

@backtest_router.post("/schedule")
async def schedule_backtest(background_tasks: BackgroundTasks):
    """Schedule a background backtest to run"""
    background_tasks.add_task(scheduled_backtest)
    
    return {
        "message": "Backtest scheduled to run in background",
        "timestamp": datetime.utcnow().isoformat(),
        "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    }

# Add router to main app (this would be added to server.py)
def add_backtest_routes(app):
    """Add backtesting routes to the main FastAPI app"""
    app.include_router(backtest_router)
    return app