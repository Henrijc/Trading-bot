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
        
        Guidelines:
        - Provide practical, actionable trading advice
        - Focus on risk management and sustainable strategies
        - Consider ZAR market conditions and Luno exchange specifics
        - Be conversational but professional
        - Include specific price levels and technical analysis when relevant
        - Always emphasize responsible trading and risk management
        
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
                context_message = f"Current context: {json.dumps(context, indent=2)}\n\nUser question: {message}"
                user_message = UserMessage(text=context_message)
            else:
                user_message = UserMessage(text=message)
            
            # Send message and get response
            response = await chat.send_message(user_message)
            return response
            
        except Exception as e:
            print(f"Error in AI service: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
    
    async def generate_daily_strategy(self, market_data: List[Dict], portfolio_data: Dict) -> Dict[str, Any]:
        """Generate daily trading strategy based on market data and portfolio"""
        try:
            context = {
                "market_data": market_data,
                "portfolio": portfolio_data,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            prompt = """Based on the current market data and portfolio, generate a comprehensive daily trading strategy for today. 
            Include:
            1. Main recommendation (2-3 sentences)
            2. Risk level (Low/Medium/High)
            3. Expected return percentage
            4. Timeframe for trades
            5. Key support/resistance levels
            6. Specific trading actions (BUY/SELL/TAKE_PROFIT)
            
            Format your response as a structured analysis focusing on achieving the R100,000 monthly target."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="daily_strategy",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1500)
            
            context_message = f"Context: {json.dumps(context, indent=2)}\n\n{prompt}"
            user_message = UserMessage(text=context_message)
            
            response = await chat.send_message(user_message)
            return {"strategy": response, "generated_at": datetime.now().isoformat()}
            
        except Exception as e:
            print(f"Error generating daily strategy: {e}")
            return {"error": "Failed to generate daily strategy"}
    
    async def analyze_portfolio_risk(self, portfolio_data: Dict) -> Dict[str, Any]:
        """Analyze portfolio risk and provide recommendations"""
        try:
            prompt = """Analyze the following portfolio for risk management:
            
            Portfolio Data:
            {portfolio_data}
            
            Provide:
            1. Risk score (0-10)
            2. Portfolio diversification analysis
            3. Specific risk management recommendations
            4. Suggested stop-loss levels
            5. Position sizing recommendations
            
            Focus on achieving R100,000 monthly target while maintaining proper risk management."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="risk_analysis",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1200)
            
            context_message = prompt.format(portfolio_data=json.dumps(portfolio_data, indent=2))
            user_message = UserMessage(text=context_message)
            
            response = await chat.send_message(user_message)
            return {"analysis": response, "generated_at": datetime.now().isoformat()}
            
        except Exception as e:
            print(f"Error analyzing portfolio risk: {e}")
            return {"error": "Failed to analyze portfolio risk"}