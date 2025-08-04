import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend.services.luno_service import LunoService
from backend.services.ai_service import AICoachService
import json

class AIMemoryService:
    def __init__(self):
        self.luno_service = LunoService()
        # Note: AI service will be imported dynamically to avoid circular import
        
    async def consolidate_daily_memory(self, user_id: str = "default") -> Dict[str, Any]:
        """Consolidate daily trading data into AI memory"""
        try:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # Collect daily data
            daily_data = await self._collect_daily_data(yesterday)
            
            # Generate AI memory summary
            memory_summary = await self._generate_memory_summary(daily_data)
            
            # Store in knowledge base
            await self._store_daily_memory(memory_summary, yesterday, user_id)
            
            return {
                "success": True,
                "date": yesterday.isoformat(),
                "memory_summary": memory_summary,
                "data_points": len(daily_data)
            }
            
        except Exception as e:
            print(f"Error consolidating daily memory: {e}")
            return {"success": False, "error": str(e)}
    
    async def _collect_daily_data(self, date) -> Dict[str, Any]:
        """Collect all relevant data for the specified date"""
        try:
            # Get portfolio performance data
            portfolio_data = await self.luno_service.get_portfolio_data()
            
            # Get market data and price changes
            market_data = await self.luno_service.get_market_data()
            
            # Simulate getting historical trade data for the date
            # In production, this would fetch actual trades from database
            trades_data = await self._get_trades_for_date(date)
            
            # Get chat conversation highlights
            chat_highlights = await self._get_chat_highlights_for_date(date)
            
            return {
                "date": date.isoformat(),
                "portfolio": {
                    "value": portfolio_data.get("total_value", 0),
                    "holdings": portfolio_data.get("holdings", []),
                    "currency": portfolio_data.get("currency", "ZAR")
                },
                "market": market_data,
                "trades": trades_data,
                "chat_highlights": chat_highlights,
                "performance_metrics": await self._calculate_performance_metrics(portfolio_data)
            }
            
        except Exception as e:
            print(f"Error collecting daily data: {e}")
            return {}
    
    async def _get_trades_for_date(self, date) -> List[Dict]:
        """Get trades executed on specific date"""
        # This would connect to database to get actual trades
        # For now, returning sample structure
        return [
            {
                "symbol": "BTC",
                "action": "BUY",
                "amount": 5000,
                "price": 2100000,
                "profit_loss": 0,
                "strategy": "momentum_scalping"
            }
        ]
    
    async def _get_chat_highlights_for_date(self, date) -> List[str]:
        """Get important chat conversations from the date"""
        # This would fetch from chat history database
        # For now, returning sample highlights
        return [
            "User requested target adjustment to R175k",
            "AI recommended BTC position based on RSI oversold condition",
            "Portfolio performance exceeded weekly target by 12%"
        ]
    
    async def _calculate_performance_metrics(self, portfolio_data) -> Dict[str, float]:
        """Calculate key performance metrics"""
        try:
            total_value = portfolio_data.get("total_value", 0)
            
            # These would be calculated from historical data
            return {
                "daily_return_pct": 2.3,  # Sample
                "weekly_return_pct": 8.7,
                "monthly_return_pct": 15.6,
                "portfolio_value": total_value,
                "largest_holding_pct": 25.4,
                "risk_score": 6.8  # 1-10 scale
            }
        except:
            return {}
    
    async def _generate_memory_summary(self, daily_data: Dict[str, Any]) -> str:
        """Generate AI summary of the day's events"""
        try:
            prompt = f"""Analyze this daily trading data and create a concise memory summary for future reference.

**DAILY DATA:**
{json.dumps(daily_data, indent=2, default=str)}

**CREATE A MEMORY SUMMARY:**
1. **Key Events**: What happened today (trades, market movements, portfolio changes)
2. **Performance**: How did the portfolio perform vs targets
3. **Market Context**: Important market conditions and sentiment
4. **Patterns**: Any trading patterns or user behavior to remember
5. **Lessons**: What worked well or didn't work
6. **Tomorrow**: Key things to watch for next trading day

**RESPONSE FORMAT:**
Concise, factual summary in 3-4 sentences that the AI can reference later to provide better advice.
"""
            
            # Dynamic import to avoid circular dependency
            from backend.services.ai_service import AICoachService
            ai_service = AICoachService()
            
            # Use AI to generate memory summary
            chat = ai_service._create_chat_session("memory_consolidation")
            user_message = ai_service._create_user_message(prompt)
            response = await chat.send_message(user_message)
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating memory summary: {e}")
            return f"Daily summary for {daily_data.get('date', 'unknown date')}: Portfolio value {daily_data.get('portfolio', {}).get('value', 0)}, market conditions analyzed."
    
    async def _store_daily_memory(self, memory_summary: str, date, user_id: str):
        """Store the daily memory summary in knowledge base"""
        try:
            memory_filename = f"daily_memory_{date.strftime('%Y_%m_%d')}.md"
            
            memory_content = f"""# Daily Memory - {date.strftime('%Y-%m-%d')}

## AI Memory Summary
{memory_summary}

## Generated: {datetime.now().isoformat()}
## User: {user_id}

---
*This is an automatically generated daily memory consolidation for AI reference.*
"""
            
            # Store in AI knowledge base directory
            memory_dir = "/app/backend/ai_knowledge_base/user_preferences"
            os.makedirs(memory_dir, exist_ok=True)
            
            memory_path = os.path.join(memory_dir, memory_filename)
            with open(memory_path, 'w', encoding='utf-8') as f:
                f.write(memory_content)
            
            print(f"✅ Daily memory stored: {memory_filename}")
            
        except Exception as e:
            print(f"Error storing daily memory: {e}")
    
    async def get_recent_memories(self, days: int = 7, user_id: str = "default") -> List[str]:
        """Get recent daily memories for AI context"""
        try:
            memories = []
            memory_dir = "/app/backend/ai_knowledge_base/user_preferences"
            
            for i in range(days):
                date = datetime.now().date() - timedelta(days=i+1)
                memory_filename = f"daily_memory_{date.strftime('%Y_%m_%d')}.md"
                memory_path = os.path.join(memory_dir, memory_filename)
                
                if os.path.exists(memory_path):
                    with open(memory_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract just the AI Memory Summary section
                        if "## AI Memory Summary" in content:
                            summary = content.split("## AI Memory Summary")[1].split("## Generated:")[0].strip()
                            memories.append(f"**{date}**: {summary}")
            
            return memories
            
        except Exception as e:
            print(f"Error getting recent memories: {e}")
            return []
    
    async def schedule_daily_consolidation(self):
        """Schedule daily memory consolidation (would be called by cron job)"""
        try:
            print("🧠 Starting daily AI memory consolidation...")
            result = await self.consolidate_daily_memory()
            
            if result.get("success"):
                print(f"✅ Daily memory consolidated: {result['data_points']} data points processed")
            else:
                print(f"❌ Memory consolidation failed: {result.get('error')}")
                
            return result
            
        except Exception as e:
            print(f"Error in scheduled consolidation: {e}")
            return {"success": False, "error": str(e)}