from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
from datetime import datetime, timedelta
import json

# Import our models and services
from models import *
from services.ai_service import AICoachService
from services.luno_service import LunoService
from services.technical_analysis_service import TechnicalAnalysisService
from services.ai_knowledge_base import AIKnowledgeBase
from services.trading_campaign_service import TradingCampaignService
from services.ai_memory_service import AIMemoryService
from services.semi_auto_trade_service import SemiAutoTradeService
from services.security_service import SecurityService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services AFTER loading environment variables
ai_service = AICoachService()
luno_service = LunoService()
ta_service = TechnicalAnalysisService()
knowledge_base = AIKnowledgeBase()
campaign_service = TradingCampaignService()
memory_service = AIMemoryService()
semi_auto_service = SemiAutoTradeService()

# Create the main app without a prefix
app = FastAPI(title="Crypto Trading Coach API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Basic health check
@api_router.get("/")
async def root():
    return {"message": "Crypto Trading Coach API is running"}

# Chat endpoints
@api_router.post("/chat/send", response_model=ChatMessage)
async def send_chat_message(message_data: ChatMessageCreate):
    """Send a message to the AI coach"""
    try:
        # Use context from frontend if provided, otherwise get fresh data
        if message_data.context:
            print(f"Using frontend context for chat message")
            context = message_data.context
            # Ensure we have timestamp
            context["timestamp"] = datetime.now().isoformat()
        else:
            print(f"Fetching fresh context for chat message")
            # Get portfolio and market context
            portfolio_data = await luno_service.get_portfolio_data()
            market_data = await luno_service.get_market_data()
            
            context = {
                "portfolio": portfolio_data,
                "market_data": market_data,
                "timestamp": datetime.now().isoformat()
            }
        
        print(f"Chat context: Portfolio value = {context.get('portfolio', {}).get('total_value', 'N/A')}")
        
        # Get AI response
        ai_response = await ai_service.send_message(
            session_id=message_data.session_id,
            message=message_data.message,
            context=context
        )
        
        # Save user message
        user_message = ChatMessage(
            session_id=message_data.session_id,
            role="user",
            message=message_data.message
        )
        await db.chat_messages.insert_one(user_message.dict())
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=message_data.session_id,
            role="assistant",
            message=ai_response
        )
        await db.chat_messages.insert_one(ai_message.dict())
        
        return ai_message
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50):
    """Get chat history for a session"""
    try:
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(limit).to_list(None)
        
        # Reverse to get chronological order
        messages.reverse()
        
        return [ChatMessage(**msg) for msg in messages]
        
    except Exception as e:
        print(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")

# Market Data endpoints
@api_router.get("/market/data")
async def get_market_data():
    """Get current market data for all cryptocurrencies"""
    try:
        market_data = await luno_service.get_market_data()
        return market_data
        
    except Exception as e:
        print(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get market data")

# Portfolio endpoints
@api_router.get("/portfolio")
async def get_portfolio():
    """Get user's portfolio data"""
    try:
        portfolio_data = await luno_service.get_portfolio_data()
        return portfolio_data
        
    except Exception as e:
        print(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio")

# Strategy endpoints
@api_router.get("/strategy/daily")
async def get_daily_strategy():
    """Get daily trading strategy"""
    try:
        # Check if we have a strategy for today
        today = datetime.now().strftime("%Y-%m-%d")
        existing_strategy = await db.daily_strategies.find_one({"date": today})
        
        if existing_strategy:
            return DailyStrategy(**existing_strategy)
        
        # Generate new strategy
        market_data = await luno_service.get_market_data()
        portfolio_data = await luno_service.get_portfolio_data()
        
        ai_strategy = await ai_service.generate_daily_strategy(market_data, portfolio_data)
        
        # Create structured strategy (for now, use mock structure)
        strategy = DailyStrategy(
            date=today,
            main_recommendation="BTC showing strong support at R480,000. Consider accumulating on dips below R475,000",
            risk_level="Medium",
            expected_return="5-8%",
            timeframe="1-3 days",
            key_levels=KeyLevels(
                support="R475,000",
                resistance="R520,000",
                target="R510,000"
            ),
            actions=[
                TradingAction(
                    type="BUY",
                    asset="BTC",
                    amount="R10,000",
                    price="R475,000 - R480,000",
                    reasoning="Strong support level with high volume"
                ),
                TradingAction(
                    type="TAKE_PROFIT",
                    asset="ETH",
                    amount="30%",
                    price="R16,200",
                    reasoning="Approaching resistance, secure profits"
                )
            ]
        )
        
        # Save strategy
        await db.daily_strategies.insert_one(strategy.dict())
        
        return strategy
        
    except Exception as e:
        print(f"Error getting daily strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to get daily strategy")

# Weekly targets endpoints
@api_router.get("/targets/weekly")
async def get_weekly_targets():
    """Get weekly cash-out targets"""
    try:
        # Get current week
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_of = week_start.strftime("%Y-%m-%d")
        
        # Check if we have targets for this week
        existing_targets = await db.weekly_targets.find_one({"week_of": week_of})
        
        if existing_targets:
            return WeeklyTargets(**existing_targets)
        
        # Create new weekly targets
        weekly_target = 25000  # R25,000 per week to reach R100,000/month
        
        # Mock milestones for demo
        milestones = [
            WeeklyMilestone(day="Monday", target=3571, achieved=4200, status="exceeded"),
            WeeklyMilestone(day="Tuesday", target=3571, achieved=2890, status="below"),
            WeeklyMilestone(day="Wednesday", target=3571, achieved=3950, status="exceeded"),
            WeeklyMilestone(day="Thursday", target=3571, achieved=4210, status="exceeded"),
            WeeklyMilestone(day="Friday", target=3571, achieved=3500, status="pending"),
            WeeklyMilestone(day="Saturday", target=3571, achieved=0, status="pending"),
            WeeklyMilestone(day="Sunday", target=3571, achieved=0, status="pending")
        ]
        
        achieved = sum(m.achieved for m in milestones)
        remaining = weekly_target - achieved
        days_left = 7 - today.weekday()
        daily_required = remaining / days_left if days_left > 0 else 0
        progress = (achieved / weekly_target) * 100 if weekly_target > 0 else 0
        
        targets = WeeklyTargets(
            week_of=week_of,
            target=weekly_target,
            achieved=achieved,
            remaining=remaining,
            days_left=days_left,
            daily_required=daily_required,
            progress=progress,
            milestones=milestones
        )
        
        # Save targets
        await db.weekly_targets.insert_one(targets.dict())
        
        return targets
        
    except Exception as e:
        print(f"Error getting weekly targets: {e}")
        raise HTTPException(status_code=500, detail="Failed to get weekly targets")

# Risk management endpoints
@api_router.get("/risk/metrics")
async def get_risk_metrics():
    """Get risk management metrics"""
    try:
        # Get portfolio data
        portfolio_data = await luno_service.get_portfolio_data()
        
        # Generate risk analysis
        risk_analysis = await ai_service.analyze_portfolio_risk(portfolio_data)
        
        # Create risk metrics (mock structure for now)
        risk_metrics = RiskMetrics(
            user_id="default_user",
            risk_score=6.2,
            portfolio_var=8.5,
            sharpe_ratio=1.8,
            max_drawdown=12.3,
            diversification_score=7.5,
            recommendations=[
                "Consider reducing BTC allocation to below 60%",
                "Add stablecoin allocation for better risk management",
                "Set stop-loss at 5% below current portfolio value"
            ]
        )
        
        # Save risk metrics
        await db.risk_metrics.insert_one(risk_metrics.dict())
        
        return risk_metrics
        
    except Exception as e:
        print(f"Error getting risk metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk metrics")

# Trading endpoints
@api_router.post("/trade/execute")
async def execute_trade(trade_request: dict):
    """Execute a trade on Luno"""
    try:
        result = await ai_service.execute_trade(trade_request)
        return result
    except Exception as e:
        print(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute trade")

@api_router.get("/trade/pairs")
async def get_trading_pairs():
    """Get all available trading pairs"""
    try:
        pairs = await luno_service.get_trading_pairs()
        return {"pairs": pairs}
    except Exception as e:
        print(f"Error getting trading pairs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trading pairs")

@api_router.get("/trade/orderbook/{pair}")
async def get_order_book(pair: str):
    """Get order book for a trading pair"""
    try:
        orderbook = await luno_service.get_order_book(pair)
        return orderbook
    except Exception as e:
        print(f"Error getting order book: {e}")
        raise HTTPException(status_code=500, detail="Failed to get order book")

@api_router.get("/trade/history")
async def get_trade_history(pair: str = None, limit: int = 100):
    """Get trading history"""
    try:
        history = await luno_service.get_order_history(pair, limit)
        return {"orders": history}
    except Exception as e:
        print(f"Error getting trade history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trade history")

@api_router.post("/ai/research")
async def ai_research(request: dict):
    """AI web research for market analysis"""
    try:
        query = request.get("query", "")
        results = await ai_service.web_search(query)
        return {"results": results}
    except Exception as e:
        print(f"Error in AI research: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform research")

# Trading Campaign endpoints
@api_router.post("/campaigns/create")
async def create_trading_campaign(request: dict):
    """Create a new targeted trading campaign"""
    try:
        allocated_capital = request.get("allocated_capital", 10000)
        profit_target = request.get("profit_target", 10000)
        timeframe_days = request.get("timeframe_days", 7)
        risk_level = request.get("risk_level", "aggressive")
        name = request.get("name")
        
        result = await campaign_service.create_campaign(
            allocated_capital=allocated_capital,
            profit_target=profit_target,
            timeframe_days=timeframe_days,
            risk_level=risk_level,
            name=name
        )
        return result
    except Exception as e:
        print(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/campaigns/{campaign_id}/progress")
async def get_campaign_progress(campaign_id: str):
    """Get real-time progress of a trading campaign"""
    try:
        result = await campaign_service.get_campaign_progress(campaign_id)
        return result
    except Exception as e:
        print(f"Error getting campaign progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/campaigns/{campaign_id}/execute")
async def execute_campaign_trades(campaign_id: str, max_trades: int = 3):
    """Execute trades for an active campaign"""
    try:
        result = await campaign_service.execute_campaign_trades(campaign_id, max_trades)
        return result
    except Exception as e:
        print(f"Error executing campaign trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: str):
    """Pause an active campaign"""
    try:
        result = await campaign_service.pause_campaign(campaign_id)
        return result
    except Exception as e:
        print(f"Error pausing campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/campaigns/{campaign_id}/resume")
async def resume_campaign(campaign_id: str):
    """Resume a paused campaign"""
    try:
        result = await campaign_service.resume_campaign(campaign_id)
        return result
    except Exception as e:
        print(f"Error resuming campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Auto Trading endpoints
@api_router.get("/autotrade/settings", response_model=AutoTradingSettings)
async def get_autotrade_settings():
    """Get auto trading settings"""
    try:
        settings = await db.autotrade_settings.find_one({"user_id": "default_user"})
        
        if not settings:
            # Create default settings
            default_settings = AutoTradingSettings(user_id="default_user")
            await db.autotrade_settings.insert_one(default_settings.dict())
            return default_settings
        
        return AutoTradingSettings(**settings)
        
    except Exception as e:
        print(f"Error getting autotrade settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get autotrade settings")

@api_router.put("/autotrade/settings")
async def update_autotrade_settings(settings: AutoTradingSettingsCreate):
    """Update auto trading settings"""
    try:
        settings_dict = settings.dict()
        settings_dict["user_id"] = "default_user"
        settings_dict["updated_at"] = datetime.utcnow()
        
        await db.autotrade_settings.update_one(
            {"user_id": "default_user"},
            {"$set": settings_dict},
            upsert=True
        )
        
        return {"success": True, "message": "Auto trading settings updated"}
        
    except Exception as e:
        print(f"Error updating autotrade settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update autotrade settings")

@api_router.get("/autotrade/logs")
async def get_autotrade_logs(limit: int = 50):
    """Get auto trading execution logs"""
    try:
        logs = await db.autotrade_logs.find(
            {"user_id": "default_user"}
        ).sort("executed_at", -1).limit(limit).to_list(None)
        
        return [AutoTradeLog(**log) for log in logs]
        
    except Exception as e:
        print(f"Error getting autotrade logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get autotrade logs")

@api_router.post("/autotrade/execute")
async def execute_autotrade():
    """Manually trigger auto trading analysis and execution"""
    try:
        # Get auto trading settings
        settings = await db.autotrade_settings.find_one({"user_id": "default_user"})
        if not settings or not settings.get("enabled", False):
            return {"success": False, "message": "Auto trading is not enabled"}
        
        # Get current portfolio and market data
        portfolio_data = await luno_service.get_portfolio_data()
        market_data = await luno_service.get_market_data()
        
        # Execute auto trading analysis
        results = await ai_service.execute_autotrade(settings, portfolio_data, market_data)
        
        return results
        
    except Exception as e:
        print(f"Error executing autotrade: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute autotrade")

@api_router.post("/autotrade/toggle")
async def toggle_autotrade(enabled: bool):
    """Enable or disable auto trading"""
    try:
        await db.autotrade_settings.update_one(
            {"user_id": "default_user"},
            {"$set": {"enabled": enabled, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        
        status = "enabled" if enabled else "disabled"
        return {"success": True, "message": f"Auto trading {status}"}
        
    except Exception as e:
        print(f"Error toggling autotrade: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle autotrade")

# AI Memory endpoints
@api_router.post("/ai/memory/consolidate")
async def consolidate_daily_memory():
    """Manually trigger daily memory consolidation"""
    try:
        result = await memory_service.consolidate_daily_memory()
        return result
    except Exception as e:
        print(f"Error consolidating memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/ai/memory/recent")
async def get_recent_memories(days: int = 7):
    """Get recent daily memories"""
    try:
        memories = await memory_service.get_recent_memories(days)
        return {"memories": memories, "days": days}
    except Exception as e:
        print(f"Error getting recent memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/memory/schedule")
async def schedule_memory_consolidation():
    """Schedule daily memory consolidation"""
    try:
        result = await memory_service.schedule_daily_consolidation()
        return result
    except Exception as e:
        print(f"Error scheduling memory consolidation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Semi-Auto Trading endpoints
@api_router.post("/trade/suggest")
async def suggest_trades():
    """Get AI trade suggestions for approval"""
    try:
        # Get current portfolio data
        portfolio_data = await luno_service.get_portfolio_data()
        
        # Get trade suggestions
        result = await semi_auto_service.analyze_and_suggest_trades(portfolio_data)
        
        if result.get("success") and result.get("suggestions"):
            # Generate user-friendly message
            approval_message = await semi_auto_service.generate_trade_approval_message(result["suggestions"])
            result["approval_message"] = approval_message
        
        return result
    except Exception as e:
        print(f"Error getting trade suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/trade/execute/{trade_id}")
async def execute_trade(trade_id: str, approval_data: dict):
    """Execute an approved trade"""
    try:
        user_approval = approval_data.get("approval", "User approved via API")
        result = await semi_auto_service.execute_approved_trade(trade_id, user_approval)
        return result
    except Exception as e:
        print(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/trade/pending")
async def get_pending_trades():
    """Get all pending trades awaiting approval"""
    try:
        pending_trades = semi_auto_service.get_pending_trades()
        return {"pending_trades": pending_trades, "count": len(pending_trades)}
    except Exception as e:
        print(f"Error getting pending trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/trade/cancel/{trade_id}")
async def cancel_trade(trade_id: str):
    """Cancel a pending trade"""
    try:
        success = semi_auto_service.cancel_pending_trade(trade_id)
        if success:
            return {"success": True, "message": f"Trade {trade_id} cancelled"}
        else:
            return {"success": False, "message": "Trade not found or already executed"}
    except Exception as e:
        print(f"Error cancelling trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Import the new models at the top
from models import AutoTradingSettings, AutoTradeLog, AutoTradingSettingsCreate

# Target management endpoints
@api_router.get("/targets/settings")
async def get_target_settings():
    """Get current target settings"""
    try:
        settings = await db.target_settings.find_one({"user_id": "default_user"})
        
        if not settings:
            # Create default settings
            default_settings = {
                "user_id": "default_user",
                "monthly_target": 100000,
                "weekly_target": 25000,
                "daily_target": 3571,
                "auto_adjust": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            await db.target_settings.insert_one(default_settings)
            return default_settings
        
        # Remove ObjectId and convert to JSON serializable format
        if '_id' in settings:
            del settings['_id']
        
        return settings
        
    except Exception as e:
        print(f"Error getting target settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get target settings")

@api_router.put("/targets/settings")
async def update_target_settings(settings: dict):
    """Update target settings"""
    try:
        settings["updated_at"] = datetime.utcnow().isoformat()
        settings["user_id"] = "default_user"
        
        await db.target_settings.update_one(
            {"user_id": "default_user"},
            {"$set": settings},
            upsert=True
        )
        
        return {"success": True, "settings": settings}
        
    except Exception as e:
        print(f"Error updating target settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update target settings")

@api_router.post("/targets/settings")
async def create_or_update_target_settings(settings: dict):
    """Create or update target settings (POST version)"""
    try:
        settings["updated_at"] = datetime.utcnow().isoformat()
        settings["user_id"] = "default_user"
        
        await db.target_settings.update_one(
            {"user_id": "default_user"},
            {"$set": settings},
            upsert=True
        )
        
        return {"success": True, "settings": settings}
        
    except Exception as e:
        print(f"Error updating target settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update target settings")

@api_router.post("/ai/adjust-targets")
async def ai_adjust_targets(request: dict):
    """Allow AI to adjust targets based on performance"""
    try:
        # Get current portfolio performance
        portfolio_data = await luno_service.get_portfolio_data()
        current_value = portfolio_data.get('total_value', 0)
        
        # Get current targets
        current_targets = await db.target_settings.find_one({"user_id": "default_user"})
        if not current_targets:
            current_targets = {"monthly_target": 100000}
        
        # Let AI analyze and suggest new targets
        context = {
            "current_portfolio": current_value,
            "current_monthly_target": current_targets.get("monthly_target", 100000),
            "request": request.get("reason", ""),
            "market_conditions": await luno_service.get_market_data()
        }
        
        ai_response = await ai_service.adjust_targets(context)
        
        # If AI suggests new targets, update them
        if "new_targets" in ai_response:
            new_targets = ai_response["new_targets"]
            new_targets["updated_at"] = datetime.utcnow().isoformat()
            new_targets["user_id"] = "default_user"
            new_targets["ai_adjusted"] = True
            new_targets["adjustment_reason"] = request.get("reason", "AI optimization")
            
            await db.target_settings.update_one(
                {"user_id": "default_user"},
                {"$set": new_targets},
                upsert=True
            )
            
            return {
                "success": True,
                "message": ai_response.get("explanation", "Targets updated successfully"),
                "new_targets": new_targets
            }
        
        return {
            "success": False,
            "message": ai_response.get("explanation", "No target adjustment needed")
        }
        
    except Exception as e:
        print(f"Error in AI target adjustment: {e}")
        raise HTTPException(status_code=500, detail="Failed to adjust targets")
@api_router.get("/settings")
async def get_user_settings():
    """Get user settings"""
    try:
        settings = await db.user_settings.find_one({"user_id": "default_user"})
        
        if not settings:
            # Create default settings
            default_settings = UserSettings(user_id="default_user")
            await db.user_settings.insert_one(default_settings.dict())
            return default_settings
        
        return UserSettings(**settings)
        
    except Exception as e:
        print(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get settings")

@api_router.put("/settings")
async def update_user_settings(settings: UserSettings):
    """Update user settings"""
    try:
        settings.updated_at = datetime.utcnow()
        await db.user_settings.update_one(
            {"user_id": settings.user_id},
            {"$set": settings.dict()},
            upsert=True
        )
        return settings
        
    except Exception as e:
        print(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")

# Technical Analysis endpoints
@api_router.get("/technical/signals/{symbol}")
async def get_technical_signals(symbol: str, days: int = 30):
    """Get technical analysis signals for a specific symbol"""
    try:
        signals = await ta_service.generate_trading_signals(symbol.upper(), days)
        return signals
        
    except Exception as e:
        print(f"Error getting technical signals for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get technical signals")

@api_router.get("/technical/portfolio")
async def get_portfolio_technical_analysis():
    """Get technical analysis for entire portfolio"""
    try:
        portfolio_data = await luno_service.get_portfolio_data()
        analysis = await ta_service.analyze_portfolio_technical(portfolio_data)
        return analysis
        
    except Exception as e:
        print(f"Error getting portfolio technical analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio technical analysis")

@api_router.get("/technical/indicators/{symbol}")
async def get_technical_indicators(symbol: str, days: int = 30):
    """Get detailed technical indicators for a symbol"""
    try:
        # Use the existing working signals endpoint which already handles serialization properly
        signals_data = await ta_service.generate_trading_signals(symbol.upper(), days)
        
        if 'error' in signals_data:
            raise HTTPException(status_code=404, detail=signals_data['error'])
        
        # Return the same data format as signals but focused on indicators
        return {
            'symbol': symbol.upper(),
            'indicators': signals_data.get('technical_indicators', {}),
            'current_price': signals_data.get('current_price', 0),
            'timestamp': signals_data.get('timestamp', datetime.now().isoformat())
        }
        
    except Exception as e:
        print(f"Error getting technical indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get technical indicators")

@api_router.get("/technical/strategy/{strategy_name}")
async def get_technical_strategy(strategy_name: str):
    """Get a specific technical analysis strategy"""
    try:
        # Define predefined strategies
        strategies = {
            'momentum': {
                'name': 'Momentum Strategy',
                'description': 'Uses RSI and MACD to identify momentum-based trading opportunities',
                'indicators': ['RSI', 'MACD', 'Moving Averages'],
                'rules': [
                    {'condition': 'RSI < 30', 'action': 'BUY', 'weight': 0.8},
                    {'condition': 'RSI > 70', 'action': 'SELL', 'weight': 0.8},
                    {'condition': 'MACD > Signal', 'action': 'BUY', 'weight': 0.6},
                    {'condition': 'MACD < Signal', 'action': 'SELL', 'weight': 0.6}
                ],
                'risk_parameters': {
                    'stop_loss': 0.05,
                    'take_profit': 0.10,
                    'position_size': 0.10
                }
            },
            'mean_reversion': {
                'name': 'Mean Reversion Strategy',
                'description': 'Uses Bollinger Bands to identify overbought/oversold conditions',
                'indicators': ['Bollinger Bands', 'RSI', 'Support/Resistance'],
                'rules': [
                    {'condition': 'Price < Lower BB', 'action': 'BUY', 'weight': 0.9},
                    {'condition': 'Price > Upper BB', 'action': 'SELL', 'weight': 0.9},
                    {'condition': 'Price near Support', 'action': 'BUY', 'weight': 0.7},
                    {'condition': 'Price near Resistance', 'action': 'SELL', 'weight': 0.7}
                ],
                'risk_parameters': {
                    'stop_loss': 0.03,
                    'take_profit': 0.06,
                    'position_size': 0.15
                }
            },
            'trend_following': {
                'name': 'Trend Following Strategy',
                'description': 'Uses moving averages to ride trends',
                'indicators': ['Moving Averages', 'MACD', 'Trend Analysis'],
                'rules': [
                    {'condition': 'MA(10) > MA(50)', 'action': 'BUY', 'weight': 0.7},
                    {'condition': 'MA(10) < MA(50)', 'action': 'SELL', 'weight': 0.7},
                    {'condition': 'Strong Uptrend', 'action': 'BUY', 'weight': 0.8},
                    {'condition': 'Strong Downtrend', 'action': 'SELL', 'weight': 0.8}
                ],
                'risk_parameters': {
                    'stop_loss': 0.08,
                    'take_profit': 0.15,
                    'position_size': 0.12
                }
            }
        }
        
        strategy = strategies.get(strategy_name.lower())
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
            
        return strategy
        
    except Exception as e:
        print(f"Error getting technical strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to get technical strategy")

@api_router.post("/technical/backtest")
async def backtest_strategy(request: dict):
    """Backtest a trading strategy"""
    try:
        symbol = request.get('symbol', 'BTC')
        strategy_name = request.get('strategy', 'momentum')
        days = request.get('days', 30)
        
        # Get historical data
        df = await ta_service.get_historical_data(symbol.upper(), days)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No historical data available")
        
        # Simple backtest simulation
        signals = await ta_service.generate_trading_signals(symbol.upper(), days)
        
        # Mock backtest results (would need more sophisticated implementation)
        backtest_results = {
            'symbol': symbol.upper(),
            'strategy': strategy_name,
            'period': f'{days} days',
            'total_trades': len(signals.get('trading_signals', [])),
            'winning_trades': len([s for s in signals.get('trading_signals', []) if s['type'] == 'BUY']),
            'losing_trades': len([s for s in signals.get('trading_signals', []) if s['type'] == 'SELL']),
            'win_rate': 0.65,  # Mock win rate
            'total_return': 0.12,  # Mock return
            'max_drawdown': 0.08,  # Mock drawdown
            'sharpe_ratio': 1.8,  # Mock Sharpe ratio
            'signals_analyzed': signals
        }
        
        return backtest_results
        
    except Exception as e:
        print(f"Error backtesting strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to backtest strategy")

@api_router.get("/technical/market-overview")
async def get_market_technical_overview():
    """Get technical analysis overview for major cryptocurrencies"""
    try:
        major_cryptos = ['BTC', 'ETH', 'ADA', 'XRP', 'SOL']
        overview = []
        
        for crypto in major_cryptos:
            try:
                signals = await ta_service.generate_trading_signals(crypto, 30)
                if 'error' not in signals:
                    overview.append({
                        'symbol': crypto,
                        'price': signals.get('current_price', 0),
                        'trend': signals.get('trend_analysis', {}).get('trend', 'neutral'),
                        'trend_strength': signals.get('trend_analysis', {}).get('strength', 0),
                        'recommendation': signals.get('recommendation', {}),
                        'rsi': signals.get('technical_indicators', {}).get('rsi'),
                        'signals_count': len(signals.get('trading_signals', []))
                    })
            except Exception as e:
                print(f"Error analyzing {crypto}: {e}")
                continue
        
        return {
            'market_overview': overview,
            'timestamp': datetime.now().isoformat(),
            'analyzed_assets': len(overview)
        }
        
    except Exception as e:
        print(f"Error getting market technical overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get market technical overview")

# Knowledge Base Management endpoints
@api_router.get("/knowledge/categories")
async def get_knowledge_categories():
    """Get all available knowledge categories and files"""
    try:
        categories = knowledge_base.list_knowledge_files()
        return categories
    except Exception as e:
        print(f"Error getting knowledge categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get knowledge categories")

@api_router.get("/knowledge/{category}")
async def get_knowledge_category(category: str):
    """Get all knowledge from a specific category"""
    try:
        knowledge = knowledge_base.load_category_knowledge(category)
        return knowledge
    except Exception as e:
        print(f"Error getting knowledge category {category}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge category: {category}")

@api_router.get("/knowledge/{category}/{filename}")
async def get_knowledge_file(category: str, filename: str):
    """Get a specific knowledge file"""
    try:
        content = knowledge_base.load_knowledge_file(category, filename)
        if not content:
            raise HTTPException(status_code=404, detail="Knowledge file not found")
        return {"category": category, "filename": filename, "content": content}
    except Exception as e:
        print(f"Error getting knowledge file {category}/{filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get knowledge file")

@api_router.post("/knowledge/{category}/{filename}")
async def add_knowledge_file(category: str, filename: str, request: dict):
    """Add or update a knowledge file"""
    try:
        content = request.get('content', '')
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        knowledge_base.add_knowledge_file(category, filename, content)
        return {"message": f"Knowledge file {category}/{filename} added successfully"}
    except Exception as e:
        print(f"Error adding knowledge file {category}/{filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add knowledge file")

@api_router.get("/knowledge/enhanced-context")
async def get_enhanced_context():
    """Get the full enhanced context that the AI uses"""
    try:
        context = knowledge_base.get_enhanced_context("default")
        return {"enhanced_context": context}
    except Exception as e:
        print(f"Error getting enhanced context: {e}")
        raise HTTPException(status_code=500, detail="Failed to get enhanced context")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Crypto Trading Coach API started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await luno_service.close_session()
    client.close()
    logger.info("Crypto Trading Coach API stopped")