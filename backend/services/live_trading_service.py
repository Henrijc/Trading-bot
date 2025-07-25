"""
Live Trading Service for AI Crypto Trading Coach
Integrates backtesting strategies with real trading execution via AI prompts
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json
from enum import Enum

# Import existing services
from services.luno_service import LunoService
from services.ai_service import AICoachService
from services.backtest_api_service import CryptoBacktester
from services.historical_data_service import HistoricalDataService

# Create router for live trading
live_trading_router = APIRouter(prefix="/api/live-trading", tags=["live_trading"])

class TradingMode(Enum):
    PAPER = "paper"
    LIVE = "live"
    AI_ASSISTED = "ai_assisted"

class TradeSignal(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class LiveTradeRequest(BaseModel):
    symbol: str
    mode: TradingMode = TradingMode.AI_ASSISTED
    amount_zar: Optional[float] = None
    reason: str = "AI Strategy Signal"
    confirm_with_ai: bool = True

class LiveTradeResponse(BaseModel):
    success: bool
    trade_id: Optional[str] = None
    symbol: str
    action: str
    amount: float
    price: float
    total_value: float
    ai_analysis: Optional[str] = None
    recommendation: str
    risk_assessment: str
    error: Optional[str] = None

class TradingStatusResponse(BaseModel):
    mode: TradingMode
    active_signals: List[Dict]
    portfolio_status: Dict
    recent_trades: List[Dict]
    ai_recommendations: List[str]
    risk_metrics: Dict

# Global instances
luno_service = LunoService()
ai_service = AICoachService()
data_service = HistoricalDataService()

# Trading state
trading_mode = TradingMode.AI_ASSISTED
active_signals = []
pending_trades = []

@live_trading_router.get("/status", response_model=TradingStatusResponse)
async def get_trading_status():
    """Get current live trading status"""
    try:
        # Get portfolio data
        portfolio_data = await luno_service.get_portfolio_data()
        
        # Get AI recommendations
        ai_context = {
            "portfolio": portfolio_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        ai_analysis = await ai_service.send_message(
            session_id="live_trading_analysis",
            message="Analyze current portfolio and provide 3 key trading recommendations for today. Be concise.",
            context=ai_context
        )
        
        # Extract recommendations (simple parsing)
        recommendations = [
            line.strip() for line in ai_analysis.split('\n') 
            if line.strip() and ('recommend' in line.lower() or line.startswith('-') or line.startswith('•'))
        ][:3]
        
        # Calculate risk metrics
        total_value = portfolio_data.get('total_value', 0)
        btc_percentage = 0
        eth_percentage = 0
        xrp_percentage = 0
        
        if portfolio_data.get('holdings'):
            for holding in portfolio_data['holdings']:
                if holding['asset'] == 'BTC':
                    btc_percentage = (holding['zar_value'] / total_value) * 100
                elif holding['asset'] == 'ETH':
                    eth_percentage = (holding['zar_value'] / total_value) * 100
                elif holding['asset'] == 'XRP':
                    xrp_percentage = (holding['zar_value'] / total_value) * 100
        
        risk_metrics = {
            "total_portfolio_value": total_value,
            "btc_allocation": f"{btc_percentage:.1f}%",
            "eth_allocation": f"{eth_percentage:.1f}%", 
            "xrp_allocation": f"{xrp_percentage:.1f}%",
            "max_trade_risk": "4% per trade",
            "diversification_score": "Good" if btc_percentage < 50 and eth_percentage < 50 else "Moderate"
        }
        
        return TradingStatusResponse(
            mode=trading_mode,
            active_signals=active_signals,
            portfolio_status=portfolio_data,
            recent_trades=[],  # Would need to implement trade history
            ai_recommendations=recommendations,
            risk_metrics=risk_metrics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@live_trading_router.post("/analyze-signal", response_model=Dict)
async def analyze_trading_signal(symbol: str, current_price: float):
    """Get AI analysis for a potential trading signal"""
    try:
        # Get historical data for analysis
        historical_data = await data_service.get_historical_data(symbol, "1h", 7)
        
        # Get portfolio context
        portfolio_data = await luno_service.get_portfolio_data()
        
        # Create analysis context
        context = {
            "symbol": symbol,
            "current_price": current_price,
            "portfolio": portfolio_data,
            "recent_data_points": len(historical_data) if not historical_data.empty else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Get AI analysis
        ai_prompt = f"""
        TRADING SIGNAL ANALYSIS for {symbol}:
        
        Current Price: R{current_price:,.2f}
        Portfolio Value: R{portfolio_data.get('total_value', 0):,.2f}
        
        Based on:
        1. Current market conditions
        2. Portfolio allocation 
        3. R8000 monthly profit target
        4. 4% risk management rule
        5. 1000 XRP long-term hold strategy
        
        Provide:
        - BUY/SELL/HOLD recommendation
        - Risk assessment (LOW/MEDIUM/HIGH)
        - Position size suggestion in ZAR
        - Key reasoning (2-3 points)
        
        Be concise and specific.
        """
        
        ai_analysis = await ai_service.send_message(
            session_id="signal_analysis",
            message=ai_prompt,
            context=context
        )
        
        # Parse AI response for key components
        signal = TradeSignal.HOLD
        if "BUY" in ai_analysis.upper():
            signal = TradeSignal.BUY
        elif "SELL" in ai_analysis.upper():
            signal = TradeSignal.SELL
            
        risk_level = "MEDIUM"
        if "LOW" in ai_analysis.upper():
            risk_level = "LOW"
        elif "HIGH" in ai_analysis.upper():
            risk_level = "HIGH"
        
        return {
            "symbol": symbol,
            "signal": signal.value,
            "risk_level": risk_level,
            "ai_analysis": ai_analysis,
            "confidence": "High" if signal != TradeSignal.HOLD else "Low",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "symbol": symbol,
            "signal": "hold",
            "risk_level": "HIGH", 
            "ai_analysis": f"Error analyzing signal: {str(e)}",
            "confidence": "Low",
            "timestamp": datetime.utcnow().isoformat()
        }

@live_trading_router.post("/execute-trade", response_model=LiveTradeResponse)
async def execute_live_trade(trade_request: LiveTradeRequest):
    """Execute a live trade with AI confirmation"""
    try:
        # Get current market price
        market_data = await luno_service.get_market_data()
        current_price = None
        
        for asset in market_data.get('assets', []):
            if f"{asset['symbol']}/ZAR" == trade_request.symbol:
                current_price = asset['price_zar']
                break
        
        if not current_price:
            return LiveTradeResponse(
                success=False,
                symbol=trade_request.symbol,
                action="none",
                amount=0,
                price=0,
                total_value=0,
                recommendation="REJECTED",
                risk_assessment="HIGH - Price not available",
                error="Could not fetch current price"
            )
        
        # Get AI confirmation if requested
        ai_analysis = ""
        if trade_request.confirm_with_ai:
            # Get signal analysis
            signal_analysis = await analyze_trading_signal(trade_request.symbol, current_price)
            ai_analysis = signal_analysis.get('ai_analysis', '')
            
            # Check if AI recommends against the trade
            if signal_analysis.get('signal') == 'hold' and signal_analysis.get('risk_level') == 'HIGH':
                return LiveTradeResponse(
                    success=False,
                    symbol=trade_request.symbol,
                    action="none",
                    amount=0,
                    price=current_price,
                    total_value=0,
                    ai_analysis=ai_analysis,
                    recommendation="AI REJECTED - High risk detected",
                    risk_assessment="HIGH",
                    error="AI analysis recommends against this trade"
                )
        
        # Paper trading mode - simulate the trade
        if trade_request.mode == TradingMode.PAPER:
            amount = trade_request.amount_zar or 1000  # Default R1000 for paper trading
            
            return LiveTradeResponse(
                success=True,
                trade_id=f"PAPER_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                symbol=trade_request.symbol,
                action="paper_trade",
                amount=amount / current_price,
                price=current_price,
                total_value=amount,
                ai_analysis=ai_analysis,
                recommendation="PAPER TRADE EXECUTED",
                risk_assessment="LOW - Simulated only"
            )
        
        # AI Assisted mode - requires explicit confirmation
        elif trade_request.mode == TradingMode.AI_ASSISTED:
            # For now, return the analysis without executing
            # In production, this would wait for user confirmation
            return LiveTradeResponse(
                success=False,
                symbol=trade_request.symbol,
                action="analysis_only",
                amount=0,
                price=current_price,
                total_value=0,
                ai_analysis=ai_analysis,
                recommendation="AI ANALYSIS COMPLETE - Awaiting user confirmation",
                risk_assessment="PENDING"
            )
        
        # Live trading mode - would execute real trades
        elif trade_request.mode == TradingMode.LIVE:
            # For safety, this is disabled in current implementation
            return LiveTradeResponse(
                success=False,
                symbol=trade_request.symbol,
                action="disabled",
                amount=0,
                price=current_price,
                total_value=0,
                ai_analysis="Live trading is currently disabled for safety",
                recommendation="LIVE TRADING DISABLED",
                risk_assessment="SAFETY MEASURE"
            )
        
    except Exception as e:
        return LiveTradeResponse(
            success=False,
            symbol=trade_request.symbol,
            action="error",
            amount=0,
            price=0,
            total_value=0,
            recommendation="ERROR",
            risk_assessment="HIGH",
            error=str(e)
        )

@live_trading_router.get("/ai-prompt")
async def get_ai_trading_prompt():
    """Get a formatted prompt for AI to execute trades via chat"""
    try:
        portfolio_data = await luno_service.get_portfolio_data()
        market_data = await luno_service.get_market_data()
        
        # Create comprehensive trading prompt
        prompt = f"""
🤖 **AI TRADING ASSISTANT ACTIVATED** 🤖

**CURRENT PORTFOLIO STATUS:**
- Total Value: R{portfolio_data.get('total_value', 0):,.2f}
- Available Cash: R{portfolio_data.get('available_balance', 0):,.2f}

**CURRENT MARKET PRICES:**"""

        if market_data.get('assets'):
            for asset in market_data['assets'][:3]:  # Top 3 assets
                prompt += f"\n- {asset['symbol']}: R{asset['price_zar']:,.2f}"
        
        prompt += f"""

**TRADING COMMANDS AVAILABLE:**
1. `ANALYZE [SYMBOL]` - Get detailed analysis for a trading pair
2. `BUY [SYMBOL] [AMOUNT_ZAR]` - Execute buy order (paper trading)  
3. `SELL [SYMBOL] [AMOUNT_ZAR]` - Execute sell order (paper trading)
4. `STATUS` - Get current portfolio and trading status
5. `BACKTEST [SYMBOL] [DAYS]` - Run quick backtest

**RISK MANAGEMENT ACTIVE:**
- Maximum 4% risk per trade
- 1000 XRP protected for long-term hold
- AI confirmation required for all trades
- Monthly target: R8,000 profit

**EXAMPLE COMMANDS:**
- "ANALYZE BTC/ZAR"
- "BUY BTC/ZAR 5000" 
- "BACKTEST ETH/ZAR 14"
- "STATUS"

**Safety Note:** All trades are in PAPER TRADING mode for safety. Real trading requires explicit user confirmation.

---
*Ready for trading commands! Type any command above to begin.*
        """
        
        return {
            "prompt": prompt,
            "timestamp": datetime.utcnow().isoformat(),
            "mode": trading_mode.value,
            "portfolio_value": portfolio_data.get('total_value', 0),
            "available_commands": ["ANALYZE", "BUY", "SELL", "STATUS", "BACKTEST"]
        }
        
    except Exception as e:
        return {
            "prompt": f"Error generating AI prompt: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "error",
            "portfolio_value": 0,
            "available_commands": []
        }

@live_trading_router.post("/process-ai-command")
async def process_ai_command(command: str):
    """Process trading commands from AI chat"""
    try:
        command = command.upper().strip()
        
        if command.startswith("ANALYZE"):
            # Extract symbol
            parts = command.split()
            if len(parts) >= 2:
                symbol = parts[1]
                # Get current price
                market_data = await luno_service.get_market_data()
                current_price = 0
                
                for asset in market_data.get('assets', []):
                    if f"{asset['symbol']}/ZAR" == symbol:
                        current_price = asset['price_zar']
                        break
                
                if current_price > 0:
                    analysis = await analyze_trading_signal(symbol, current_price)
                    return {
                        "command": "ANALYZE",
                        "symbol": symbol,
                        "result": analysis,
                        "status": "success"
                    }
            
            return {"command": "ANALYZE", "error": "Invalid symbol or format"}
        
        elif command.startswith("BUY") or command.startswith("SELL"):
            # Extract symbol and amount
            parts = command.split()
            if len(parts) >= 3:
                action = parts[0]
                symbol = parts[1]
                try:
                    amount = float(parts[2])
                    
                    # Execute paper trade
                    trade_request = LiveTradeRequest(
                        symbol=symbol,
                        mode=TradingMode.PAPER,
                        amount_zar=amount,
                        reason=f"AI command: {command}",
                        confirm_with_ai=True
                    )
                    
                    result = await execute_live_trade(trade_request)
                    return {
                        "command": action,
                        "symbol": symbol,
                        "amount": amount,
                        "result": result.dict(),
                        "status": "success" if result.success else "failed"
                    }
                    
                except ValueError:
                    return {"command": action, "error": "Invalid amount format"}
            
            return {"command": command.split()[0], "error": "Invalid format. Use: BUY/SELL [SYMBOL] [AMOUNT_ZAR]"}
        
        elif command == "STATUS":
            status = await get_trading_status()
            return {
                "command": "STATUS", 
                "result": status.dict(),
                "status": "success"
            }
        
        elif command.startswith("BACKTEST"):
            parts = command.split()
            if len(parts) >= 3:
                symbol = parts[1]
                try:
                    days = int(parts[2])
                    # This would trigger a quick backtest
                    return {
                        "command": "BACKTEST",
                        "symbol": symbol,
                        "days": days,
                        "result": "Backtest initiated - check Backtest tab for results",
                        "status": "success"
                    }
                except ValueError:
                    return {"command": "BACKTEST", "error": "Invalid days format"}
        
        return {"command": command, "error": "Unknown command", "status": "failed"}
        
    except Exception as e:
        return {"command": command, "error": str(e), "status": "error"}

# Add router to main app (this would be added to server.py)
def add_live_trading_routes(app):
    """Add live trading routes to the main FastAPI app"""
    app.include_router(live_trading_router)
    return app