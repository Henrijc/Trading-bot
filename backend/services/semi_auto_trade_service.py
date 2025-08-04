import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys
sys.path.insert(0, '/app')
from backend.services.luno_service import LunoService
from backend.services.technical_analysis_service import TechnicalAnalysisService
import json
import uuid

class SemiAutoTradeService:
    def __init__(self):
        self.luno_service = LunoService()
        self.ta_service = TechnicalAnalysisService()
        self.pending_trades = {}  # Store pending trade approvals
        
    async def analyze_and_suggest_trades(self, portfolio_data: Dict[str, Any], user_request: str = "") -> Dict[str, Any]:
        """Analyze market and suggest trades for user approval"""
        try:
            # Get current market conditions
            market_data = await self.luno_service.get_market_data()
            
            # Analyze top cryptocurrencies for opportunities
            major_pairs = ['BTC', 'ETH', 'XRP', 'ADA', 'SOL']
            trade_suggestions = []
            
            for symbol in major_pairs:
                try:
                    # Get technical analysis
                    signals = await self.ta_service.generate_trading_signals(symbol, 14)
                    
                    if 'error' not in signals:
                        recommendation = signals.get('recommendation', {})
                        action = recommendation.get('action', 'HOLD')
                        confidence = recommendation.get('confidence', 0)
                        
                        # Only suggest high-confidence trades
                        if action in ['BUY', 'SELL'] and confidence > 0.75:
                            
                            # Calculate position size based on portfolio
                            portfolio_value = portfolio_data.get('total_value', 0)
                            position_size = min(portfolio_value * 0.1, 25000)  # Max 10% of portfolio or R25k
                            
                            # Calculate stop loss and take profit
                            current_price = signals.get('current_price', 0)
                            stop_loss = self._calculate_stop_loss(current_price, action, 0.03)  # 3% stop loss
                            take_profit = self._calculate_take_profit(current_price, action, 0.06)  # 6% take profit
                            
                            trade_suggestion = {
                                "id": str(uuid.uuid4())[:8],
                                "symbol": symbol,
                                "action": action,
                                "confidence": confidence,
                                "position_size": position_size,
                                "current_price": current_price,
                                "stop_loss": stop_loss,
                                "take_profit": take_profit,
                                "reasoning": recommendation.get('reasoning', ''),
                                "risk_reward_ratio": abs((take_profit - current_price) / (current_price - stop_loss)) if action == 'BUY' else abs((current_price - take_profit) / (stop_loss - current_price)),
                                "technical_indicators": {
                                    "rsi": signals.get('technical_indicators', {}).get('rsi', 0),
                                    "trend": signals.get('trend_analysis', {}).get('trend', 'neutral'),
                                    "macd_signal": signals.get('technical_indicators', {}).get('macd_signal', 'neutral')
                                },
                                "created_at": datetime.utcnow().isoformat()
                            }
                            
                            # Only suggest if risk/reward is favorable (at least 1.5:1)
                            if trade_suggestion["risk_reward_ratio"] >= 1.5:
                                trade_suggestions.append(trade_suggestion)
                                
                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
                    continue
            
            # Sort by confidence and risk/reward ratio
            trade_suggestions.sort(key=lambda x: (x['confidence'], x['risk_reward_ratio']), reverse=True)
            
            # Take top 3 suggestions
            top_suggestions = trade_suggestions[:3]
            
            # Store pending trades for approval
            for suggestion in top_suggestions:
                self.pending_trades[suggestion['id']] = suggestion
            
            return {
                "success": True,
                "suggestions": top_suggestions,
                "market_summary": self._create_market_summary(market_data),
                "portfolio_context": {
                    "total_value": portfolio_data.get('total_value', 0),
                    "available_cash": portfolio_data.get('total_value', 0) * 0.3,  # Assume 30% available for trading
                    "risk_level": self._assess_portfolio_risk(portfolio_data)
                }
            }
            
        except Exception as e:
            print(f"Error in analyze_and_suggest_trades: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_stop_loss(self, current_price: float, action: str, stop_loss_pct: float) -> float:
        """Calculate stop loss price"""
        if action == 'BUY':
            return current_price * (1 - stop_loss_pct)
        else:  # SELL
            return current_price * (1 + stop_loss_pct)
    
    def _calculate_take_profit(self, current_price: float, action: str, take_profit_pct: float) -> float:
        """Calculate take profit price"""
        if action == 'BUY':
            return current_price * (1 + take_profit_pct)
        else:  # SELL
            return current_price * (1 - take_profit_pct)
    
    def _create_market_summary(self, market_data: List[Dict]) -> str:
        """Create a concise market summary"""
        try:
            if not market_data:
                return "Market data unavailable"
            
            # Calculate market summary metrics
            positive_moves = sum(1 for asset in market_data if asset.get('24h_change', 0) > 0)
            total_assets = len(market_data)
            
            avg_change = sum(asset.get('24h_change', 0) for asset in market_data) / total_assets if total_assets > 0 else 0
            
            sentiment = "BULLISH" if avg_change > 2 else "BEARISH" if avg_change < -2 else "NEUTRAL"
            
            return f"Market: {sentiment} | {positive_moves}/{total_assets} assets up | Avg change: {avg_change:+.1f}%"
            
        except Exception as e:
            return f"Market summary error: {e}"
    
    def _assess_portfolio_risk(self, portfolio_data: Dict[str, Any]) -> str:
        """Assess current portfolio risk level"""
        try:
            holdings = portfolio_data.get('holdings', [])
            if not holdings:
                return "LOW"  # No positions = low risk
            
            # Check concentration risk
            max_allocation = max(holding.get('allocation_percentage', 0) for holding in holdings) if holdings else 0
            
            if max_allocation > 50:
                return "HIGH"
            elif max_allocation > 30:
                return "MODERATE"
            else:
                return "LOW"
                
        except Exception as e:
            return "UNKNOWN"
    
    async def execute_approved_trade(self, trade_id: str, user_approval: str) -> Dict[str, Any]:
        """Execute a trade that has been approved by the user"""
        try:
            if trade_id not in self.pending_trades:
                return {"success": False, "error": "Trade not found or expired"}
            
            trade = self.pending_trades[trade_id]
            
            # Create trade instruction for Luno service
            trade_instruction = {
                "action": trade["action"],
                "symbol": trade["symbol"],
                "amount": trade["position_size"],
                "order_type": "market",  # Use market orders for immediate execution
                "stop_loss": trade["stop_loss"],
                "take_profit": trade["take_profit"]
            }
            
            # Execute the trade through Luno service
            execution_result = await self._execute_trade_via_luno(trade_instruction)
            
            if execution_result.get("success"):
                # Remove from pending trades
                del self.pending_trades[trade_id]
                
                # Log the execution
                execution_log = {
                    "trade_id": trade_id,
                    "executed_at": datetime.utcnow().isoformat(),
                    "execution_result": execution_result,
                    "user_approval": user_approval,
                    "trade_details": trade
                }
                
                return {
                    "success": True,
                    "execution_result": execution_result,
                    "trade_details": trade,
                    "message": f"✅ {trade['action']} order executed for {trade['symbol']}: R{trade['position_size']:,.0f} at R{trade['current_price']:,.0f}",
                    "execution_log": execution_log
                }
            else:
                return {
                    "success": False,
                    "error": f"Trade execution failed: {execution_result.get('error', 'Unknown error')}",
                    "trade_details": trade
                }
                
        except Exception as e:
            print(f"Error executing approved trade: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_trade_via_luno(self, trade_instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade through Luno service"""
        try:
            # This would use the actual Luno trading API
            # For now, simulating successful execution
            
            return {
                "success": True,
                "order_id": f"LUN{int(datetime.now().timestamp())}",
                "status": "filled",
                "executed_price": trade_instruction.get("amount", 0) / 0.001,  # Sample price calculation
                "executed_amount": trade_instruction.get("amount", 0),
                "fees": trade_instruction.get("amount", 0) * 0.001,  # 0.1% fee
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error in Luno trade execution: {e}")
            return {"success": False, "error": str(e)}
    
    def get_pending_trades(self) -> List[Dict[str, Any]]:
        """Get all pending trades awaiting approval"""
        # Remove expired trades (older than 1 hour)
        current_time = datetime.now()
        expired_ids = []
        
        for trade_id, trade in self.pending_trades.items():
            trade_time = datetime.fromisoformat(trade['created_at'])
            if current_time - trade_time > timedelta(hours=1):
                expired_ids.append(trade_id)
        
        for expired_id in expired_ids:
            del self.pending_trades[expired_id]
        
        return list(self.pending_trades.values())
    
    def cancel_pending_trade(self, trade_id: str) -> bool:
        """Cancel a pending trade"""
        if trade_id in self.pending_trades:
            del self.pending_trades[trade_id]
            return True
        return False
    
    async def generate_trade_approval_message(self, suggestions: List[Dict[str, Any]]) -> str:
        """Generate a user-friendly message for trade approval"""
        try:
            if not suggestions:
                return "No high-confidence trading opportunities found at the moment."
            
            message_parts = ["🤖 **SEMI-AUTO TRADE SUGGESTIONS**\n"]
            
            for i, trade in enumerate(suggestions, 1):
                risk_reward = trade['risk_reward_ratio']
                confidence = trade['confidence'] * 100
                
                message_parts.append(
                    f"**{i}. {trade['action']} {trade['symbol']}** (ID: {trade['id']})\n"
                    f"• Amount: R{trade['position_size']:,.0f}\n"
                    f"• Price: R{trade['current_price']:,.0f}\n"
                    f"• Stop Loss: R{trade['stop_loss']:,.0f} ({abs((trade['current_price'] - trade['stop_loss'])/trade['current_price']*100):.1f}%)\n"
                    f"• Take Profit: R{trade['take_profit']:,.0f} ({abs((trade['take_profit'] - trade['current_price'])/trade['current_price']*100):.1f}%)\n"
                    f"• Confidence: {confidence:.0f}% | R:R {risk_reward:.1f}:1\n"
                    f"• Reason: {trade['reasoning']}\n"
                )
            
            message_parts.append("\n**To approve**: Reply with 'Execute trade [ID]' (e.g., 'Execute trade a1b2c3d4')")
            message_parts.append("**To cancel**: Reply with 'Cancel trade [ID]'")
            message_parts.append("**For all**: Reply with 'Execute all trades'")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            return f"Error generating approval message: {e}"