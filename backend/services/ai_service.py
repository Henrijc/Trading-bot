import os
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage
from typing import List, Dict, Any
import json
from datetime import datetime

class AICoachService:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.system_message = """You are an expert cryptocurrency trading coach specializing in the South African market. 
        Your goal is to help users reach their monthly target of R100,000 through strategic crypto trading.
        
        COMMUNICATION STYLE:
        - Write like a professional but friendly trading coach
        - Use clear, structured responses with proper formatting
        - Break down complex information into digestible sections
        - Use bullet points, numbered lists, and clear headers
        - Keep responses conversational but informative
        - Always include specific actionable advice
        - Use South African Rand (ZAR) for all prices
        
        RESPONSE FORMAT:
        - Start with a brief summary/key point
        - Use headers like "📊 Market Analysis:" or "💡 My Recommendation:"
        - Use bullet points for multiple items
        - End with a clear next step or question
        
        TRADING FOCUS:
        - Provide practical, actionable trading advice
        - Focus on risk management and sustainable strategies
        - Consider ZAR market conditions and Luno exchange specifics
        - You can adjust targets when asked or when performance indicates it's needed
        - Use commands like "adjust my targets" or "I think I need a more realistic target"
        - Always explain your reasoning for target changes
        - Consider both current performance and market conditions when adjusting targets
        - Include specific price levels and technical analysis when relevant
        
        User's Goal: R100,000 monthly earnings through crypto trading
        Exchange: Luno (South Africa)
        Base Currency: ZAR
        """
    
    async def send_message(self, session_id: str, message: str, context: Dict[str, Any] = None) -> str:
        """Send a message to the AI coach and get a response"""
        try:
            # Create a new chat instance for each session
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1000)
            
            # Add context if provided
            if context:
                # Format context nicely
                context_summary = f"""
Current Portfolio Value: R{context.get('portfolio', {}).get('total_value', 0):,.2f}
Holdings: {len(context.get('portfolio', {}).get('holdings', []))} assets
Market Status: {len(context.get('market_data', []))} cryptocurrencies tracked

User question: {message}
"""
                user_message = UserMessage(text=context_summary)
            else:
                user_message = UserMessage(text=message)
            
            # Send message and get response
            response = await chat.send_message(user_message)
            
            # Clean up the response to ensure it's well-formatted
            return self._format_response(response)
            
        except Exception as e:
            print(f"Error in AI service: {e}")
            return """I apologize, but I'm having trouble processing your request right now. 

**Please try again in a moment.**

In the meantime, here's a quick tip: Focus on your current holdings and consider taking profits when you're up 10-15% on any position."""
    
    def _format_response(self, response: str) -> str:
        """Format the AI response to be more readable"""
        # Ensure the response is not too long
        if len(response) > 800:
            # Truncate but end at a complete sentence
            truncated = response[:800]
            last_period = truncated.rfind('.')
            if last_period > 600:
                response = truncated[:last_period + 1]
            else:
                response = truncated + "..."
        
        return response
    
    async def generate_daily_strategy(self, market_data: List[Dict], portfolio_data: Dict) -> Dict[str, Any]:
        """Generate daily trading strategy based on market data and portfolio"""
        try:
            context = {
                "market_data": market_data,
                "portfolio": portfolio_data,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            prompt = f"""Based on the current market data and portfolio, generate a comprehensive daily trading strategy for today.

Portfolio Value: R{portfolio_data.get('total_value', 0):,.2f}
Holdings: {len(portfolio_data.get('holdings', []))} assets

Format your response as a structured analysis with:
1. **Main Recommendation** (2-3 sentences)
2. **Risk Level** (Low/Medium/High)
3. **Expected Return** (percentage)
4. **Key Levels** (support/resistance)
5. **Specific Actions** (what to buy/sell)

Focus on achieving the R100,000 monthly target through practical steps."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="daily_strategy",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1200)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return {"strategy": response, "generated_at": datetime.now().isoformat()}
            
        except Exception as e:
            print(f"Error generating daily strategy: {e}")
            return {"error": "Failed to generate daily strategy"}
    
    async def analyze_portfolio_risk(self, portfolio_data: Dict) -> Dict[str, Any]:
        """Analyze portfolio risk and provide recommendations"""
        try:
            prompt = f"""Analyze the following portfolio for risk management:

Portfolio Value: R{portfolio_data.get('total_value', 0):,.2f}
Number of Holdings: {len(portfolio_data.get('holdings', []))}

Provide:
1. **Risk Score** (0-10)
2. **Portfolio Analysis** (diversification, concentration risk)
3. **Specific Recommendations** (3-4 actionable items)
4. **Risk Management** (stop-loss levels, position sizing)

Focus on achieving R100,000 monthly target while maintaining proper risk management.
Keep response clear and actionable."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="risk_analysis",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1000)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return {"analysis": response, "generated_at": datetime.now().isoformat()}
            
        except Exception as e:
            print(f"Error analyzing portfolio risk: {e}")
    async def adjust_targets(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Allow AI to analyze and adjust targets based on performance"""
        try:
            current_value = context.get("current_portfolio", 0)
            current_target = context.get("current_monthly_target", 100000)
            reason = context.get("request", "")
            
            prompt = f"""Analyze the current trading performance and determine if target adjustments are needed.

**Current Situation:**
- Portfolio Value: R{current_value:,.2f}
- Monthly Target: R{current_target:,.2f}
- Progress: {(current_value / current_target * 100):.1f}%
- Reason for Review: {reason}

**Your Task:**
Analyze if the monthly target should be adjusted and provide:

1. **Should targets be adjusted?** (Yes/No)
2. **New Monthly Target** (if adjusting)
3. **Reasoning** (why this adjustment makes sense)
4. **Action Plan** (how to achieve the new target)

**Guidelines:**
- Be realistic based on current performance
- Consider market conditions
- Ensure targets are achievable but challenging
- Factor in risk management

**Response Format:**
If adjusting: "ADJUST: New monthly target should be R[amount] because [reason]"
If not adjusting: "MAINTAIN: Current target is appropriate because [reason]"

Then provide detailed explanation and action plan."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="target_adjustment",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1000)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Parse AI response to extract new targets
            if "ADJUST:" in response:
                # Extract new target amount
                import re
                target_match = re.search(r'R([\d,]+)', response)
                if target_match:
                    new_monthly_target = int(target_match.group(1).replace(',', ''))
                    new_weekly_target = new_monthly_target / 4
                    new_daily_target = new_weekly_target / 7
                    
                    return {
                        "new_targets": {
                            "monthly_target": new_monthly_target,
                            "weekly_target": new_weekly_target,
                            "daily_target": new_daily_target
                        },
                        "explanation": response,
                        "adjusted": True
                    }
            
            return {
                "explanation": response,
                "adjusted": False
            }
            
        except Exception as e:
            print(f"Error in target adjustment: {e}")
            return {
                "explanation": "I couldn't analyze the targets right now. Let's keep the current targets for now.",
                "adjusted": False
            }