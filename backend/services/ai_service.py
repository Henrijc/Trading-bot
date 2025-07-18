import os
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage
from typing import List, Dict, Any
import json
from datetime import datetime
import requests
from services.luno_service import LunoService

class AICoachService:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.luno_service = LunoService()
        self.system_message = """You are an expert cryptocurrency trading coach specializing in the South African market. 
        You have access to real-time market data, web research capabilities, and can execute trades on Luno.
        
        Your goal is to help users reach their monthly target of R100,000 through strategic crypto trading.
        
        COMMUNICATION STYLE:
        - Be direct and concise
        - No emojis or emoticons
        - Minimal formatting - avoid excessive bold text
        - Clear, structured responses
        - Professional tone
        - Get straight to the point
        - Only use formatting when absolutely necessary for clarity
        
        RESPONSE FORMAT:
        - Start with the key point immediately
        - Use simple bullet points if needed
        - Keep responses under 200 words unless specifically asked to elaborate
        - End with a clear recommendation or next step
        
        TRADING CAPABILITIES:
        - Research market conditions using web searches
        - Analyze real-time portfolio data
        - Suggest specific trades with exact amounts
        - Execute trades (with user confirmation)
        - Adjust targets when performance indicates it's needed
        - Always explain reasoning briefly
        
        TRADING FOCUS:
        - Practical, actionable trading advice
        - Risk management and sustainable strategies
        - ZAR market conditions and Luno exchange specifics
        - Responsible trading practices
        - Specific price levels and technical analysis
        
        User's Goal: R100,000 monthly earnings through crypto trading
        Exchange: Luno (South Africa)
        Base Currency: ZAR
        """
    
    async def web_search(self, query: str) -> str:
        """Search the web for current crypto market information"""
        try:
            # Use a simple web search API or scraping
            search_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Extract relevant information
                for result in data.get('RelatedTopics', [])[:3]:
                    if isinstance(result, dict) and 'Text' in result:
                        results.append(result['Text'])
                
                return ' '.join(results) if results else f"No specific results found for: {query}"
            else:
                return f"Unable to search for: {query}"
                
        except Exception as e:
            print(f"Error in web search: {e}")
            return f"Search unavailable for: {query}"
    
    async def send_message(self, session_id: str, message: str, context: Dict[str, Any] = None) -> str:
        """Send a message to the AI coach and get a response"""
        try:
            # Create a new chat instance for each session
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1200)
            
            # Enhance context with real-time data and web research
            enhanced_context = ""
            
            if context:
                portfolio_value = context.get('portfolio', {}).get('total_value', 0)
                holdings_count = len(context.get('portfolio', {}).get('holdings', []))
                
                enhanced_context = f"""
**Current Portfolio:**
- Value: R{portfolio_value:,.2f}
- Holdings: {holdings_count} assets
- Real-time market data available

**Market Context:**
- All prices are real-time from Luno and CoinGecko
- USD pairs converted to ZAR at current rates
- No mock data - everything is live

**User Question:** {message}
"""
            
            # If the message contains requests for market research, do web searches
            if any(keyword in message.lower() for keyword in ['news', 'market', 'trend', 'analysis', 'research']):
                search_query = f"cryptocurrency market news {datetime.now().strftime('%Y-%m-%d')}"
                web_results = await self.web_search(search_query)
                enhanced_context += f"\n**Latest Market Research:**\n{web_results}\n"
            
            # If asking about specific cryptos, get current prices
            crypto_keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'cardano', 'ada', 'solana', 'sol', 'xrp', 'ripple']
            if any(keyword in message.lower() for keyword in crypto_keywords):
                try:
                    market_data = await self.luno_service.get_market_data()
                    prices_info = "\n**Current Prices:**\n"
                    for crypto in market_data[:5]:  # Top 5 cryptos
                        prices_info += f"- {crypto['symbol']}: R{crypto['price']:,.2f} ({crypto['change_24h']:+.2f}%)\n"
                    enhanced_context += prices_info
                except Exception as e:
                    print(f"Error getting market data: {e}")
            
            user_message = UserMessage(text=enhanced_context if enhanced_context else message)
            
            # Send message and get response
            response = await chat.send_message(user_message)
            
            # Clean up the response to ensure it's well-formatted
            return self._format_response(response)
            
        except Exception as e:
            print(f"Error in AI service: {e}")
            return """I'm having trouble accessing real-time data right now. Please try again in a moment.

Current portfolio value suggests taking profits on positions up 15-20% and reinvesting in underperforming assets with strong fundamentals."""
    
    def _format_response(self, response: str) -> str:
        """Format the AI response to be more readable"""
        # Ensure the response is not too long and clean
        if len(response) > 600:
            # Truncate but end at a complete sentence
            truncated = response[:600]
            last_period = truncated.rfind('.')
            if last_period > 500:
                response = truncated[:last_period + 1]
            else:
                response = truncated + "..."
        
        # Clean up excessive formatting
        response = response.replace('**', '').replace('*', '')
        response = response.replace('📊', '').replace('💡', '').replace('🎯', '')
        response = response.replace('📈', '').replace('⚠️', '').replace('🔥', '')
        response = response.replace('💰', '').replace('🛡️', '').replace('🚀', '')
        
        return response
    
    async def execute_trade(self, trade_instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade on Luno"""
        try:
            action = trade_instruction.get('action', '').upper()
            symbol = trade_instruction.get('symbol', '')
            amount = float(trade_instruction.get('amount', 0))
            order_type = trade_instruction.get('order_type', 'market').lower()
            price = trade_instruction.get('price', 0)
            
            # Map symbol to Luno pair
            pair_mapping = {
                'BTC': 'XBTZAR',
                'ETH': 'ETHZAR',
                'ADA': 'ADAZAR',
                'XRP': 'XRPZAR',
                'SOL': 'SOLZAR',
                'TRX': 'TRXZAR',
                'XLM': 'XLMZAR',
                'LTC': 'LTCZAR'
            }
            
            pair = pair_mapping.get(symbol, f'{symbol}ZAR')
            
            if order_type == 'market':
                result = await self.luno_service.place_market_order(pair, action, amount)
            elif order_type == 'limit':
                result = await self.luno_service.place_limit_order(pair, action, amount, price)
            else:
                return {'error': 'Invalid order type'}
            
            return result
            
        except Exception as e:
            print(f"Error executing trade: {e}")
            return {'error': str(e)}
    
    async def generate_daily_strategy(self, market_data: List[Dict], portfolio_data: Dict) -> Dict[str, Any]:
        """Generate daily trading strategy based on real-time market data and portfolio"""
        try:
            # Get current market sentiment through web research
            market_research = await self.web_search(f"cryptocurrency market analysis {datetime.now().strftime('%Y-%m-%d')}")
            
            prompt = f"""Generate a comprehensive daily trading strategy using REAL-TIME data.

**Current Portfolio:** R{portfolio_data.get('total_value', 0):,.2f}
**Holdings:** {len(portfolio_data.get('holdings', []))} assets

**Real-Time Market Data:**
{json.dumps(market_data[:5], indent=2)}

**Latest Market Research:**
{market_research}

**Strategy Requirements:**
1. **Main Recommendation** (based on real data)
2. **Risk Level** (Low/Medium/High)
3. **Expected Return** (realistic percentage)
4. **Key Levels** (actual support/resistance from real prices)
5. **Specific Actions** (exact amounts and prices)

Focus on achieving R100,000 monthly target through practical, data-driven steps."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="daily_strategy",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1500)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return {"strategy": response, "generated_at": datetime.now().isoformat()}
            
        except Exception as e:
            print(f"Error generating daily strategy: {e}")
            return {"error": "Failed to generate daily strategy"}
    
    async def analyze_portfolio_risk(self, portfolio_data: Dict) -> Dict[str, Any]:
        """Analyze portfolio risk using real-time data"""
        try:
            # Get current market conditions
            market_research = await self.web_search("cryptocurrency market volatility risk analysis")
            
            prompt = f"""Analyze this REAL portfolio for risk management:

**Portfolio Value:** R{portfolio_data.get('total_value', 0):,.2f}
**Holdings:** {len(portfolio_data.get('holdings', []))} assets

**Real Holdings Data:**
{json.dumps(portfolio_data.get('holdings', []), indent=2)}

**Current Market Conditions:**
{market_research}

**Risk Analysis Requirements:**
1. **Risk Score** (0-10 based on real allocation)
2. **Portfolio Analysis** (actual diversification, concentration risk)
3. **Specific Recommendations** (actionable items with exact amounts)
4. **Risk Management** (stop-loss levels, position sizing)

Focus on real-world risk management for achieving R100,000 monthly target."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="risk_analysis",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1200)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return {"analysis": response, "generated_at": datetime.now().isoformat()}
            
        except Exception as e:
            print(f"Error analyzing portfolio risk: {e}")
            return {"error": "Failed to analyze portfolio risk"}
    
    async def adjust_targets(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Allow AI to analyze and adjust targets based on real performance"""
        try:
            current_value = context.get("current_portfolio", 0)
            current_target = context.get("current_monthly_target", 100000)
            reason = context.get("request", "")
            
            # Get market conditions for context
            market_research = await self.web_search("cryptocurrency market outlook 2025")
            
            prompt = f"""Analyze real trading performance and determine if target adjustments are needed.

**Current Situation:**
- Portfolio Value: R{current_value:,.2f}
- Monthly Target: R{current_target:,.2f}
- Progress: {(current_value / current_target * 100):.1f}%
- Reason for Review: {reason}

**Market Context:**
{market_research}

**Your Task:**
Based on REAL data, analyze if the monthly target should be adjusted:

1. **Should targets be adjusted?** (Yes/No)
2. **New Monthly Target** (if adjusting)
3. **Reasoning** (why this adjustment makes sense)
4. **Action Plan** (how to achieve the new target)

**Guidelines:**
- Be realistic based on current performance
- Consider actual market conditions
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
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1200)
            
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
            
            # Also check for specific target mentions in the response
            import re
            target_match = re.search(r'target should be R([\d,]+)', response.lower())
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