from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
from datetime import datetime
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
from services.authentication_service import AuthenticationService
from services.backtest_api_service import backtest_router
from services.live_trading_service import live_trading_router
from services.freqtrade_service import FreqtradeService
from services.target_service import TargetService
from services.decision_engine import DecisionEngine

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
security_service = SecurityService()
auth_service = AuthenticationService()
freqtrade_service = FreqtradeService()
target_service = TargetService(db_client=client)
decision_engine = DecisionEngine()

# Security middleware
security = HTTPBearer()

# Create the main app with security headers
app = FastAPI(
    title="Crypto Trading Coach API",
    version="1.0.0",
    docs_url=None,  # Disable docs in production
    redoc_url=None,  # Disable redoc in production
)

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
        # Check for goal updates in user message and save them immediately
        user_message_lower = message_data.message.lower()
        if any(keyword in user_message_lower for keyword in ['goal', 'target', 'r8000', 'r8,000', '8000', 'monthly']):
            # Extract potential R8000 goal
            import re
            amounts = re.findall(r'r\s*(\d{1,3}(?:,?\d{3})*)', user_message_lower)
            monthly_amounts = [int(amount.replace(',', '')) for amount in amounts if '8' in amount and len(amount.replace(',', '')) >= 3]
            
            if monthly_amounts or '8000' in user_message_lower:
                target_amount = 8000 if '8000' in user_message_lower else (monthly_amounts[0] if monthly_amounts else None)
                if target_amount:
                    try:
                        # Save the updated goal immediately
                        target_settings = {
                            "monthly_target": target_amount,
                            "weekly_target": target_amount / 4,
                            "daily_target": target_amount / 30,
                            "user_id": "Henrijc",
                            "updated_at": datetime.utcnow().isoformat(),
                            "goal_notes": "Updated via chat: R8000/month, keep 1000 XRP long-term, 4% risk management"
                        }
                        await db.target_settings.replace_one(
                            {"user_id": "Henrijc"}, 
                            target_settings, 
                            upsert=True
                        )
                        print(f"Goal automatically saved: Monthly R{target_amount}")
                    except Exception as goal_save_error:
                        print(f"Error saving goal: {goal_save_error}")
        
        # Use context from frontend if provided, otherwise get fresh data
        if message_data.context:
            print(f"Using frontend context for chat message")
            context = message_data.context
            # Ensure we have timestamp (always use UTC for consistency)
            context["timestamp"] = datetime.utcnow().isoformat()
        else:
            print(f"Fetching fresh context for chat message")
            # Get portfolio and market context
            portfolio_data = await luno_service.get_portfolio_data()
            market_data = await luno_service.get_market_data()
            
            context = {
                "portfolio": portfolio_data,
                "market_data": market_data,
                "timestamp": datetime.utcnow().isoformat()
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

@api_router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Summarize conversation then clear chat history for session forking"""
    try:
        # Get existing messages for summarization
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(None)
        
        summary_result = None
        if messages and len(messages) > 2:  # Only summarize if meaningful conversation
            try:
                # Generate conversation summary
                message_dicts = [
                    {
                        "role": msg.get("role", "unknown"),
                        "message": msg.get("message", ""),
                        "timestamp": msg.get("timestamp")
                    } 
                    for msg in messages
                ]
                
                summary_data = await ai_service.summarize_conversation(message_dicts)
                
                # Save summary to database
                from models import ConversationSummary
                conversation_summary = ConversationSummary(
                    session_id=session_id,
                    summary=summary_data.get("summary", ""),
                    key_decisions=summary_data.get("key_decisions", []),
                    goals_discussed=summary_data.get("goals_discussed", []),
                    portfolio_context=summary_data.get("portfolio_context", {}),
                    message_count=len(messages)
                )
                
                await db.conversation_summaries.insert_one(conversation_summary.dict())
                summary_result = conversation_summary.dict()
                print(f"Created conversation summary for session {session_id}: {summary_data.get('summary', '')}")
                
            except Exception as e:
                print(f"Error creating summary: {e}")
        
        # Delete chat messages (clean slate)
        result = await db.chat_messages.delete_many(
            {"session_id": session_id}
        )
        
        # Clear AI session memory (fresh start)
        ai_service.clear_session(session_id)
        
        return {
            "success": True, 
            "message": f"Summarized and cleared {result.deleted_count} messages for session {session_id}",
            "deleted_count": result.deleted_count,
            "summary_created": summary_result is not None,
            "summary": summary_result
        }
        
    except Exception as e:
        print(f"Error in session forking: {e}")
        raise HTTPException(status_code=500, detail="Failed to fork session")

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
        # Input validation for target settings
        if not settings:
            raise HTTPException(status_code=400, detail="Settings data is required")
        
        # Validate known fields
        valid_fields = {"monthly_target", "weekly_target", "daily_target", "auto_adjust", "goal_notes"}
        provided_fields = set(settings.keys())
        
        # Check if at least one valid field is provided
        if not (provided_fields & valid_fields):
            raise HTTPException(status_code=400, detail="At least one valid target field is required")
        
        # Validate numeric fields
        numeric_fields = {"monthly_target", "weekly_target", "daily_target"}
        for field in numeric_fields:
            if field in settings:
                value = settings[field]
                if value is None:
                    raise HTTPException(status_code=400, detail=f"{field} cannot be None")
                try:
                    numeric_value = float(value)
                    if numeric_value < 0:
                        raise HTTPException(status_code=400, detail=f"{field} must be positive")
                    settings[field] = numeric_value
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail=f"{field} must be a valid number")
        
        # Validate boolean fields
        if "auto_adjust" in settings:
            if not isinstance(settings["auto_adjust"], bool):
                raise HTTPException(status_code=400, detail="auto_adjust must be a boolean")
        
        # Add system fields
        settings["updated_at"] = datetime.utcnow().isoformat()
        settings["user_id"] = "default_user"
        
        await db.target_settings.update_one(
            {"user_id": "default_user"},
            {"$set": settings},
            upsert=True
        )
        
        return {"success": True, "settings": settings}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating target settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update target settings")

@api_router.post("/targets/settings")
async def create_or_update_target_settings(settings: dict):
    """Create or update target settings (POST version)"""
    try:
        # Input validation for target settings
        if not settings:
            raise HTTPException(status_code=400, detail="Settings data is required")
        
        # Validate known fields
        valid_fields = {"monthly_target", "weekly_target", "daily_target", "auto_adjust", "goal_notes"}
        provided_fields = set(settings.keys())
        
        # Check if at least one valid field is provided
        if not (provided_fields & valid_fields):
            raise HTTPException(status_code=400, detail="At least one valid target field is required")
        
        # Validate numeric fields
        numeric_fields = {"monthly_target", "weekly_target", "daily_target"}
        for field in numeric_fields:
            if field in settings:
                value = settings[field]
                if value is None:
                    raise HTTPException(status_code=400, detail=f"{field} cannot be None")
                try:
                    numeric_value = float(value)
                    if numeric_value < 0:
                        raise HTTPException(status_code=400, detail=f"{field} must be positive")
                    settings[field] = numeric_value
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail=f"{field} must be a valid number")
        
        # Validate boolean fields
        if "auto_adjust" in settings:
            if not isinstance(settings["auto_adjust"], bool):
                raise HTTPException(status_code=400, detail="auto_adjust must be a boolean")
        
        # Add system fields
        settings["updated_at"] = datetime.utcnow().isoformat()
        settings["user_id"] = "default_user"
        
        await db.target_settings.update_one(
            {"user_id": "default_user"},
            {"$set": settings},
            upsert=True
        )
        
        return {"success": True, "settings": settings}
        
    except HTTPException:
        raise
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
            'timestamp': signals_data.get('timestamp', datetime.utcnow().isoformat())
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
            'timestamp': datetime.utcnow().isoformat(),
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

# Authentication dependency - MUST be defined before authentication endpoints
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token for protected endpoints"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = credentials.credentials
    payload = security_service.verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload

# Authentication endpoints - MUST be defined before router inclusion
@api_router.post("/auth/login")
async def login(credentials: dict):
    """Enhanced login with 2FA and AI analysis"""
    try:
        username = credentials.get("username")
        password = credentials.get("password")
        totp_code = credentials.get("totp_code")
        backup_code = credentials.get("backup_code")
        
        # Authenticate user
        result = await auth_service.authenticate_user(
            username=username,
            password=password,
            totp_code=totp_code,
            backup_code=backup_code
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Authentication error")

@api_router.post("/auth/setup-2fa")
async def setup_2fa(user_data: dict):
    """Set up 2FA for user"""
    try:
        username = user_data.get("username")
        result = auth_service.setup_2fa_for_existing_user(username)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/verify-2fa")
async def verify_2fa_setup(verification_data: dict):
    """Verify 2FA setup is working"""
    try:
        totp_secret = verification_data.get("totp_secret")
        test_code = verification_data.get("test_code")
        
        is_valid = auth_service.verify_2fa_setup(totp_secret, test_code)
        
        return {"success": is_valid, "message": "2FA verified successfully" if is_valid else "Invalid 2FA code"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/update-goals")
async def update_user_goals(goals_data: dict, user_data = Depends(get_current_user)):
    """Update user trading goals"""
    try:
        username = user_data.get("user_id", "admin")
        result = await auth_service.update_user_goals(username, goals_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/login-analysis")
async def get_login_analysis(user_data = Depends(get_current_user)):
    """Get fresh login analysis"""
    try:
        username = user_data.get("user_id", "admin")
        analysis = await auth_service._perform_login_analysis(username)
        return {"success": True, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bot Control endpoints - Enhanced with Mode Selection
@api_router.post("/bot/start")
async def start_trading_bot(request: dict = None):
    """
    Start the Freqtrade trading bot with specified mode
    
    Request body:
    {
        "mode": "dry" | "live"  // Default: "dry" for safety
    }
    """
    try:
        # Get mode from request (default to dry run for safety)
        mode = "dry"
        if request and isinstance(request, dict):
            mode = request.get("mode", "dry")
        
        # Validate mode
        if mode not in ["dry", "live"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid mode. Must be 'dry' or 'live'"
            )
        
        # Start bot with specified mode
        result = await freqtrade_service.start_bot(mode=mode)
        
        # Log the mode for transparency
        logger.info(f"Trading bot started in {mode.upper()} mode")
        
        return {
            **result,
            "mode": mode,
            "safety_notice": "Dry run mode" if mode == "dry" else "LIVE TRADING MODE - REAL MONEY AT RISK"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting trading bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/bot/stop")
async def stop_trading_bot():
    """Stop the Freqtrade trading bot"""
    try:
        result = await freqtrade_service.stop_bot()
        return result
    except Exception as e:
        logger.error(f"Error stopping trading bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/bot/status")
async def get_bot_status():
    """Get current status of the trading bot"""
    try:
        result = await freqtrade_service.get_status()
        return result
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/bot/trades")
async def get_bot_trades():
    """Get all trades from the trading bot"""
    try:
        result = await freqtrade_service.get_trades()
        return result
    except Exception as e:
        logger.error(f"Error getting bot trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/bot/profit")
async def get_bot_profit():
    """Get profit summary from the trading bot"""
    try:
        result = await freqtrade_service.get_profit()
        return result
    except Exception as e:
        logger.error(f"Error getting bot profit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/bot/health")
async def check_bot_health():
    """Check if the trading bot is healthy"""
    try:
        is_healthy = await freqtrade_service.health_check()
        return {
            "healthy": is_healthy,
            "status": "connected" if is_healthy else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking bot health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Target Management endpoints - NEW
@api_router.get("/targets/user")
async def get_user_targets():
    """Get user targets and performance goals"""
    try:
        targets = await target_service.get_user_targets()
        return targets
    except Exception as e:
        logger.error(f"Error getting user targets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/targets/user")
async def update_user_targets(targets: dict):
    """Update user targets"""
    try:
        result = await target_service.update_user_targets("default_user", targets)
        return {"success": True, "targets": result}
    except Exception as e:
        logger.error(f"Error updating user targets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/targets/progress")
async def get_target_progress():
    """Get progress towards targets"""
    try:
        progress = await target_service.calculate_progress()
        return progress
    except Exception as e:
        logger.error(f"Error getting target progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/targets/auto-adjust")
async def auto_adjust_targets():
    """Auto-adjust targets based on performance"""
    try:
        result = await target_service.adjust_targets_based_on_performance()
        return result
    except Exception as e:
        logger.error(f"Error auto-adjusting targets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# FreqAI endpoints - NEW
@api_router.post("/freqai/train")
async def train_freqai_models():
    """Train FreqAI models via trading bot"""
    try:
        result = await freqtrade_service._make_request("/api/v1/freqai/train", method="POST")
        return result
    except Exception as e:
        logger.error(f"Error training FreqAI models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/freqai/status")
async def get_freqai_status():
    """Get FreqAI model status via trading bot"""
    try:
        result = await freqtrade_service._make_request("/api/v1/freqai/status")
        return result
    except Exception as e:
        logger.error(f"Error getting FreqAI status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/freqai/predict")
async def get_freqai_prediction(pair: str):
    """Get FreqAI prediction via trading bot"""
    try:
        result = await freqtrade_service._make_request(f"/api/v1/freqai/predict?pair={pair}")
        return result
    except Exception as e:
        logger.error(f"Error getting FreqAI prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DECISION ENGINE ENDPOINTS - Phase 6: Final Intelligence Layer
# ============================================================================

@api_router.get("/decision/status")
async def get_decision_engine_status():
    """Get decision engine status and configuration"""
    try:
        status = await decision_engine.get_decision_engine_status()
        return status
    except Exception as e:
        logger.error(f"Error getting decision engine status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/decision/evaluate")
async def evaluate_trade_signal(signal_data: dict):
    """
    Evaluate a trade signal through the decision engine
    
    Expected format:
    {
        "pair": "BTC/ZAR",
        "action": "buy",
        "confidence": 0.75,
        "signal_strength": "strong",
        "direction": "bullish", 
        "amount": 0.01
    }
    """
    try:
        from services.decision_engine import TradeSignal
        
        # Create TradeSignal object
        signal = TradeSignal(
            pair=signal_data.get('pair'),
            action=signal_data.get('action'),
            confidence=signal_data.get('confidence', 0.5),
            signal_strength=signal_data.get('signal_strength', 'medium'),
            direction=signal_data.get('direction', 'neutral'),
            amount=signal_data.get('amount', 0.01),
            predicted_return=signal_data.get('predicted_return'),
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Evaluate through decision engine
        result = await decision_engine.evaluate_trade_signal(signal)
        
        return {
            "decision": result.decision.value,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "recommended_amount": result.recommended_amount,
            "risk_assessment": result.risk_assessment,
            "conditions": result.conditions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error evaluating trade signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/decision/simulate")
async def simulate_trade_decision(simulation_data: dict):
    """
    Simulate a trade decision without executing
    Useful for testing and analysis
    
    Expected format:
    {
        "pair": "ETH/ZAR",
        "action": "sell",
        "amount": 0.5,
        "confidence": 0.8
    }
    """
    try:
        pair = simulation_data.get('pair')
        action = simulation_data.get('action')
        amount = simulation_data.get('amount', 0.01)
        confidence = simulation_data.get('confidence', 0.5)
        
        if not pair or not action:
            raise HTTPException(status_code=400, detail="pair and action are required")
        
        result = await decision_engine.simulate_decision(pair, action, amount, confidence)
        
        return {
            "simulation": True,
            "input": {
                "pair": pair,
                "action": action,
                "amount": amount,
                "confidence": confidence
            },
            "result": {
                "decision": result.decision.value,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "recommended_amount": result.recommended_amount,
                "risk_assessment": result.risk_assessment,
                "conditions": result.conditions
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error simulating trade decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/decision/ai-integrated")
async def ai_integrated_trade_decision(trade_request: dict):
    """
    Complete AI-integrated trade decision pipeline:
    1. Get FreqAI signal
    2. Run through decision engine
    3. Return combined intelligence result
    
    Expected format:
    {
        "pair": "BTC/ZAR",
        "action": "buy" // optional - will get from FreqAI if not provided
    }
    """
    try:
        pair = trade_request.get('pair')
        requested_action = trade_request.get('action')
        
        if not pair:
            raise HTTPException(status_code=400, detail="trading pair is required")
        
        # Step 1: Get FreqAI prediction
        try:
            freqai_response = await freqtrade_service.get_freqai_prediction(pair)
            
            if not freqai_response.get('success', False):
                return {
                    "success": False,
                    "error": "FreqAI prediction unavailable",
                    "decision": "hold",
                    "reason": "Cannot evaluate without AI signal"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"FreqAI service error: {str(e)}",
                "decision": "hold",
                "reason": "AI service unavailable"
            }
        
        # Step 2: Parse FreqAI response into trade signal
        prediction_data = freqai_response.get('prediction', {})
        
        # Determine action from FreqAI or use requested action
        if requested_action:
            action = requested_action
        else:
            # Derive action from FreqAI direction and confidence
            direction = prediction_data.get('direction', 'neutral')
            confidence = prediction_data.get('confidence', 0.5)
            
            if direction == 'bullish' and confidence > 0.6:
                action = 'buy'
            elif direction == 'bearish' and confidence > 0.6:
                action = 'sell'
            else:
                action = 'hold'
        
        # Skip decision engine for hold signals
        if action == 'hold':
            return {
                "success": True,
                "freqai_signal": prediction_data,
                "decision": "hold",
                "reasoning": "FreqAI suggests neutral position",
                "confidence": prediction_data.get('confidence', 0.5),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Step 3: Create trade signal for decision engine
        from services.decision_engine import TradeSignal
        
        signal = TradeSignal(
            pair=pair,
            action=action,
            confidence=prediction_data.get('confidence', 0.5),
            signal_strength=prediction_data.get('signal_strength', 'medium'),
            direction=prediction_data.get('direction', 'neutral'),
            amount=0.01,  # Default amount - will be adjusted by decision engine
            predicted_return=prediction_data.get('prediction_roc_5'),
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Step 4: Evaluate through decision engine
        decision_result = await decision_engine.evaluate_trade_signal(signal)
        
        # Step 5: Return complete AI-integrated result
        return {
            "success": True,
            "freqai_signal": {
                "pair": pair,
                "confidence": prediction_data.get('confidence'),
                "signal_strength": prediction_data.get('signal_strength'),
                "direction": prediction_data.get('direction'),
                "predicted_return": prediction_data.get('prediction_roc_5')
            },
            "decision_engine": {
                "decision": decision_result.decision.value,
                "confidence": decision_result.confidence,
                "reasoning": decision_result.reasoning,
                "recommended_amount": decision_result.recommended_amount,
                "risk_assessment": decision_result.risk_assessment,
                "conditions": decision_result.conditions
            },
            "final_recommendation": {
                "action": decision_result.decision.value,
                "confidence": decision_result.confidence,
                "amount": decision_result.recommended_amount,
                "summary": decision_result.reasoning
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI-integrated trade decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/decision-log")
async def get_decision_log(limit: int = 50):
    """
    Get recent decision log entries for AI Decision Transparency
    
    This endpoint provides real-time transparency into the Decision Engine's
    reasoning process, showing how the AI evaluates each trade decision.
    
    Query Parameters:
    - limit: Number of recent entries to return (default: 50, max: 100)
    """
    try:
        # Validate limit
        if limit > 100:
            limit = 100
        elif limit < 1:
            limit = 10
            
        # Get decision log from Decision Engine
        decision_log = decision_engine.get_decision_log(limit)
        
        return {
            "success": True,
            "count": len(decision_log),
            "decisions": decision_log,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "This log provides transparency into AI decision-making process"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving decision log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include sub-routers in the api_router (they will inherit the /api prefix)
api_router.include_router(backtest_router)
api_router.include_router(live_trading_router)

# Include the main api_router in the app  
app.include_router(api_router)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # In production, specify exact hosts
)

# CORS with security restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://0cfbd3ed-dae1-446a-a9cf-a2c7cbb1213a.preview.emergentagent.com",
        "http://34.121.6.206:3000",  # Public frontend URL
        "http://34.121.6.206:8001",  # Public backend URL
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=300,
)

# Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    start_time = time.time()
    
    # Rate limiting check
    client_ip = request.client.host
    
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    # Log request time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log security event for sensitive endpoints
    if any(path in str(request.url) for path in ["/trade/", "/ai/", "/targets/"]):
        security_service.log_security_event(
            event_type="API_ACCESS",
            user_id="default_user",
            details={
                "endpoint": str(request.url.path),
                "method": request.method,
                "ip_address": client_ip,
                "process_time": process_time
            }
        )
    
    return response

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
    await freqtrade_service.close_session()
    client.close()
    logger.info("Crypto Trading Coach API stopped")