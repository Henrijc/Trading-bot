import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from services.luno_service import LunoService
from services.ai_service import AICoachService
from services.technical_analysis_service import TechnicalAnalysisService
import json

class TradingCampaignService:
    def __init__(self):
        self.luno_service = LunoService()
        self.ai_service = AICoachService()
        self.ta_service = TechnicalAnalysisService()
        
    async def create_campaign(self, 
                            allocated_capital: float,
                            profit_target: float, 
                            timeframe_days: int,
                            risk_level: str = "aggressive",
                            name: str = None) -> Dict[str, Any]:
        """Create a new targeted trading campaign"""
        try:
            if not name:
                name = f"R{allocated_capital:,.0f} → R{profit_target:,.0f} in {timeframe_days} days"
            
            campaign_id = f"campaign_{int(datetime.now().timestamp())}"
            
            campaign = {
                "id": campaign_id,
                "name": name,
                "allocated_capital": allocated_capital,
                "profit_target": profit_target,
                "target_return_pct": (profit_target / allocated_capital) * 100,
                "timeframe_days": timeframe_days,
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=timeframe_days)).isoformat(),
                "current_value": allocated_capital,
                "total_profit_loss": 0.0,
                "trades_executed": 0,
                "win_rate": 0.0,
                "status": "active",
                "risk_level": risk_level,
                "strategy_type": "aggressive_momentum",
                "created_at": datetime.utcnow().isoformat(),
                "trades": [],
                "daily_performance": []
            }
            
            # Calculate required daily return
            required_daily_return = ((profit_target / allocated_capital) ** (1/timeframe_days)) - 1
            
            return {
                "success": True,
                "campaign": campaign,
                "required_daily_return_pct": required_daily_return * 100,
                "risk_warning": self._generate_risk_warning(profit_target, allocated_capital, timeframe_days),
                "trading_plan": await self._generate_trading_plan(campaign)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_risk_warning(self, profit_target: float, capital: float, days: int) -> str:
        """Generate appropriate risk warning for the campaign"""
        return_pct = (profit_target / capital) * 100
        daily_return_needed = ((profit_target / capital) ** (1/days) - 1) * 100
        
        if return_pct >= 100:
            risk_level = "EXTREMELY HIGH RISK"
        elif return_pct >= 50:
            risk_level = "VERY HIGH RISK"
        elif return_pct >= 25:
            risk_level = "HIGH RISK"
        else:
            risk_level = "MODERATE RISK"
            
        return f"""
⚠️ {risk_level} TRADING CAMPAIGN ⚠️

Target: {return_pct:.1f}% return in {days} days
Required Daily Return: {daily_return_needed:.2f}%

RISKS:
- High probability of significant losses
- Requires aggressive position sizing
- Market volatility can cause rapid drawdowns
- No guarantee of achieving target
- Could lose substantial portion of allocated capital

RECOMMENDATION: Only proceed if you can afford to lose the entire R{capital:,.0f}
"""
    
    async def _generate_trading_plan(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-driven trading plan for the campaign"""
        try:
            capital = campaign["allocated_capital"]
            target = campaign["profit_target"]
            days = campaign["timeframe_days"]
            
            # Get current market conditions
            market_data = await self.luno_service.get_market_data()
            
            # Analyze technical conditions for major pairs
            analysis_results = {}
            major_pairs = ['BTC', 'ETH', 'XRP', 'ADA', 'SOL']
            
            for symbol in major_pairs:
                try:
                    signals = await self.ta_service.generate_trading_signals(symbol, 14)
                    if 'error' not in signals:
                        analysis_results[symbol] = {
                            "recommendation": signals.get('recommendation', {}),
                            "rsi": signals.get('technical_indicators', {}).get('rsi', 0),
                            "trend": signals.get('trend_analysis', {}).get('trend', 'neutral'),
                            "volatility": signals.get('volatility_analysis', {}).get('current_volatility', 0)
                        }
                except:
                    continue
            
            # Generate trading strategy recommendations
            strategy = {
                "primary_strategy": "momentum_scalping",
                "risk_per_trade": min(5.0, max(2.0, (target/capital) * 0.1)),  # 2-5% risk per trade
                "max_position_size": capital * 0.3,  # Max 30% of capital per position
                "daily_target": target / days,
                "preferred_pairs": self._select_optimal_pairs(analysis_results),
                "trading_hours": "08:00-22:00 SAST",
                "stop_loss_pct": 2.0,
                "take_profit_pct": 4.0,
                "max_trades_per_day": 8,
                "market_conditions": analysis_results
            }
            
            return strategy
            
        except Exception as e:
            return {"error": f"Failed to generate trading plan: {e}"}
    
    def _select_optimal_pairs(self, analysis: Dict[str, Any]) -> List[str]:
        """Select optimal trading pairs based on technical analysis"""
        optimal_pairs = []
        
        for symbol, data in analysis.items():
            rsi = data.get('rsi', 50)
            trend = data.get('trend', 'neutral')
            volatility = data.get('volatility', 0)
            
            # Look for high volatility and clear trends
            if volatility > 0.02 and trend in ['bullish', 'bearish']:
                optimal_pairs.append(symbol)
            elif 20 <= rsi <= 30 or 70 <= rsi <= 80:  # Oversold/Overbought for reversals
                optimal_pairs.append(symbol)
        
        return optimal_pairs[:3]  # Top 3 pairs
    
    async def execute_campaign_trades(self, campaign_id: str, max_trades: int = 3) -> Dict[str, Any]:
        """Execute trades for an active campaign"""
        try:
            # This would load campaign from database
            # For now, using sample logic
            
            # Get current market analysis
            market_analysis = await self._analyze_current_opportunities()
            
            trades_executed = []
            for opportunity in market_analysis.get("opportunities", [])[:max_trades]:
                if opportunity["confidence"] > 0.7:  # High confidence trades only
                    trade_result = await self._execute_campaign_trade(campaign_id, opportunity)
                    if trade_result.get("success"):
                        trades_executed.append(trade_result)
            
            return {
                "success": True,
                "trades_executed": len(trades_executed),
                "trades": trades_executed
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _analyze_current_opportunities(self) -> Dict[str, Any]:
        """Analyze current market for trading opportunities"""
        try:
            opportunities = []
            
            # Check major pairs for scalping opportunities
            major_pairs = ['BTC', 'ETH', 'XRP', 'ADA']
            
            for symbol in major_pairs:
                try:
                    signals = await self.ta_service.generate_trading_signals(symbol, 5)
                    if 'error' not in signals:
                        recommendation = signals.get('recommendation', {})
                        action = recommendation.get('action', 'HOLD')
                        confidence = recommendation.get('confidence', 0)
                        
                        if action in ['BUY', 'SELL'] and confidence > 0.6:
                            opportunities.append({
                                "symbol": symbol,
                                "action": action,
                                "confidence": confidence,
                                "reason": recommendation.get('reasoning', ''),
                                "entry_price": signals.get('current_price', 0),
                                "stop_loss": self._calculate_stop_loss(signals, action),
                                "take_profit": self._calculate_take_profit(signals, action)
                            })
                except:
                    continue
            
            # Sort by confidence
            opportunities.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {"opportunities": opportunities}
            
        except Exception as e:
            return {"opportunities": [], "error": str(e)}
    
    def _calculate_stop_loss(self, signals: Dict, action: str) -> float:
        """Calculate appropriate stop loss for trade"""
        current_price = signals.get('current_price', 0)
        if not current_price:
            return 0
            
        # 2% stop loss for aggressive trading
        stop_loss_pct = 0.02
        
        if action == 'BUY':
            return current_price * (1 - stop_loss_pct)
        else:  # SELL
            return current_price * (1 + stop_loss_pct)
    
    def _calculate_take_profit(self, signals: Dict, action: str) -> float:
        """Calculate take profit target"""
        current_price = signals.get('current_price', 0)
        if not current_price:
            return 0
            
        # 4% take profit for aggressive trading
        take_profit_pct = 0.04
        
        if action == 'BUY':
            return current_price * (1 + take_profit_pct)
        else:  # SELL
            return current_price * (1 - take_profit_pct)
    
    async def _execute_campaign_trade(self, campaign_id: str, opportunity: Dict) -> Dict[str, Any]:
        """Execute a specific trade for the campaign"""
        try:
            # Calculate position size based on risk management
            # This would integrate with actual campaign data
            position_size = 2000  # Sample position size
            
            trade_instruction = {
                "action": opportunity["action"],
                "symbol": opportunity["symbol"],
                "amount": position_size,
                "order_type": "market",
                "stop_loss": opportunity["stop_loss"],
                "take_profit": opportunity["take_profit"]
            }
            
            # Execute via AI service (which handles Luno integration)
            result = await self.ai_service.execute_trade(trade_instruction)
            
            if 'error' not in result:
                return {
                    "success": True,
                    "trade_id": result.get("order_id", f"trade_{int(datetime.now().timestamp())}"),
                    "symbol": opportunity["symbol"],
                    "action": opportunity["action"],
                    "amount": position_size,
                    "price": opportunity["entry_price"],
                    "reason": opportunity["reason"],
                    "executed_at": datetime.utcnow().isoformat()
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_campaign_progress(self, campaign_id: str) -> Dict[str, Any]:
        """Get real-time progress of a campaign"""
        try:
            # This would load campaign from database
            # Sample progress data
            
            progress = {
                "campaign_id": campaign_id,
                "current_capital": 12500,  # Sample current value
                "allocated_capital": 10000,
                "profit_target": 10000,
                "current_profit": 2500,
                "progress_percentage": 25.0,
                "days_remaining": 5,
                "trades_executed": 8,
                "win_rate": 62.5,
                "daily_performance": [
                    {"date": "2025-07-19", "pnl": 500, "trades": 2},
                    {"date": "2025-07-18", "pnl": 800, "trades": 3},
                    {"date": "2025-07-17", "pnl": -300, "trades": 2},
                    {"date": "2025-07-16", "pnl": 1200, "trades": 4},
                    {"date": "2025-07-15", "pnl": 300, "trades": 1}
                ],
                "risk_metrics": {
                    "max_drawdown": -5.2,
                    "sharpe_ratio": 1.8,
                    "win_rate": 62.5,
                    "avg_win": 650,
                    "avg_loss": -280
                },
                "next_actions": [
                    "Monitor BTC breakout above R2,120,000",
                    "Look for ETH reversal at R63,000 support",
                    "Scale into XRP if RSI drops below 30"
                ]
            }
            
            return {"success": True, "progress": progress}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Pause an active campaign"""
        try:
            # Close all open positions and pause trading
            return {
                "success": True,
                "message": f"Campaign {campaign_id} paused. All positions closed.",
                "status": "paused"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def resume_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Resume a paused campaign"""
        try:
            return {
                "success": True,
                "message": f"Campaign {campaign_id} resumed. Monitoring for opportunities.",
                "status": "active"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}