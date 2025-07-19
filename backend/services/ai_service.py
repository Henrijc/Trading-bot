import os
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage
from typing import List, Dict, Any
import json
from datetime import datetime
import requests
from services.luno_service import LunoService
from services.ai_knowledge_base import AIKnowledgeBase

class AICoachService:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.luno_service = LunoService()
        self.knowledge_base = AIKnowledgeBase()
        # Import technical analysis service to avoid circular import
        from services.technical_analysis_service import TechnicalAnalysisService
        self.ta_service = TechnicalAnalysisService()
        self.system_message = """You are an expert South African cryptocurrency trading coach with real-time access to the user's portfolio and market data.

CRITICAL: You have complete access to:
- User's current portfolio (exact holdings, values, allocation percentages)
- Real-time market prices and 24h changes for all cryptocurrencies
- Technical analysis indicators (RSI, MACD, Bollinger Bands, trends)
- South African market conditions and Luno exchange data

NEVER ask users for information you already have access to. Always reference their actual data.

YOUR GOAL: Help the user reach R100,000 monthly earnings through strategic crypto trading.

RESPONSE STYLE:
- Give complete, actionable responses (never truncated)
- Reference specific portfolio values and holdings
- Provide concrete trading recommendations with reasoning
- Use actual market data and technical indicators
- Be direct and professional
- Include specific entry/exit prices and position sizes

TRADING FOCUS:
- Analyze their actual R155,953+ portfolio
- Identify which of their 8 assets to trade
- Use real technical analysis data for decisions
- Consider South African market conditions (Luno exchange, ZAR volatility)
- Apply risk management (max 20% per asset, 2% risk per trade)

Always start by acknowledging their current portfolio state and provide specific, data-driven analysis."""
    
    async def web_search(self, query: str) -> str:
        """Search the web for current crypto market information"""
        try:
            # Use multiple search methods for better results
            results = []
            
            # Method 1: Try DuckDuckGo API
            try:
                search_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
                response = requests.get(search_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract abstract if available
                    if data.get('Abstract'):
                        results.append(data['Abstract'])
                    
                    # Extract related topics
                    for result in data.get('RelatedTopics', [])[:3]:
                        if isinstance(result, dict) and 'Text' in result:
                            results.append(result['Text'])
            except:
                pass
            
            # Method 2: Try a simple news API or web scraping
            try:
                # Use a crypto news API
                crypto_news_url = f"https://newsapi.org/v2/everything?q={query}&apiKey=demo&pageSize=3"
                response = requests.get(crypto_news_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', [])[:2]:
                        if article.get('description'):
                            results.append(f"{article['title']}: {article['description']}")
            except:
                pass
            
            # Method 3: Use CoinGecko for crypto-specific data
            try:
                if any(crypto in query.lower() for crypto in ['bitcoin', 'ethereum', 'crypto', 'btc', 'eth']):
                    cg_url = "https://api.coingecko.com/api/v3/global"
                    response = requests.get(cg_url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        global_data = data.get('data', {})
                        if global_data:
                            market_cap = global_data.get('total_market_cap', {}).get('usd', 0)
                            volume = global_data.get('total_volume', {}).get('usd', 0)
                            results.append(f"Global crypto market cap: ${market_cap:,.0f}. 24h volume: ${volume:,.0f}")
            except:
                pass
            
            # Return results or fallback
            if results:
                return ' '.join(results[:3])  # Limit to 3 results
            else:
                return f"Current search for '{query}' - Market data available through real-time feeds. Consider checking specific crypto prices and market sentiment."
                
        except Exception as e:
            print(f"Error in web search: {e}")
            return f"Web search temporarily unavailable. Using real-time market data for analysis of: {query}"
    
    async def send_message(self, session_id: str, message: str, context: Dict[str, Any] = None) -> str:
        """Send a message to the AI coach and get a response with enhanced knowledge"""
        try:
            # Create a new chat instance for each session
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(2500)
            
            # Build enhanced context - keep it focused and concise
            enhanced_context = ""
            
            if context:
                portfolio_value = context.get('portfolio', {}).get('total_value', 0)
                holdings = context.get('portfolio', {}).get('holdings', [])
                
                # Build concise portfolio context
                enhanced_context = f"""**CURRENT PORTFOLIO DATA:**
Portfolio Value: R{portfolio_value:,.2f}
Number of Holdings: {len(holdings)} assets

**HOLDINGS BREAKDOWN:**"""
                
                for holding in holdings:
                    symbol = holding.get('symbol', 'Unknown')
                    value = holding.get('value', 0)
                    allocation = holding.get('allocation', 0)
                    enhanced_context += f"\n- {symbol}: R{value:,.2f} ({allocation:.1f}%)"
                
                enhanced_context += f"\n\n**USER QUESTION:** {message}\n"
            
            # Add technical analysis for relevant crypto discussions
            if any(keyword in message.lower() for keyword in ['btc', 'bitcoin', 'eth', 'ethereum', 'trade', 'buy', 'sell', 'market']):
                try:
                    if context and context.get('portfolio', {}).get('holdings'):
                        holdings = context['portfolio']['holdings']
                        # Get TA for top 2 holdings only to keep context manageable
                        for holding in holdings[:2]:
                            symbol = holding['symbol']
                            try:
                                signals = await self.ta_service.generate_trading_signals(symbol, 30)
                                if 'error' not in signals:
                                    rec = signals.get('recommendation', {})
                                    rsi = signals.get('technical_indicators', {}).get('rsi', 0)
                                    trend = signals.get('trend_analysis', {}).get('trend', 'neutral')
                                    enhanced_context += f"\n**{symbol} TECHNICAL ANALYSIS:**\nRecommendation: {rec.get('action', 'HOLD')}, RSI: {rsi:.1f}, Trend: {trend}"
                            except:
                                continue
                except:
                    pass
            
            user_message = UserMessage(text=enhanced_context if enhanced_context else message)
            
            # Send message and get response
            response = await chat.send_message(user_message)
            
            # Clean up the response to ensure it's well-formatted
            return self._format_response(response)
            
        except Exception as e:
            print(f"Error in AI service: {e}")
            return """I'm having trouble accessing real-time data right now. Please try again in a moment.

With your current portfolio value, I'd suggest taking profits on any positions that are up 15-20% and consider reinvesting in underperforming assets with strong fundamentals. Happy to help you analyze specific positions once my connection is restored."""
    
    def _format_response(self, response: str) -> str:
        """Format the AI response to be more readable"""
        # Remove the character limit truncation to allow full AI responses
        # Only clean up excessive formatting but keep it readable
        response = response.replace('**', '')
        
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
        """Generate daily trading strategy based on real-time market data, portfolio, and technical analysis"""
        try:
            # Get current market sentiment through web research
            market_research = await self.web_search(f"cryptocurrency market analysis {datetime.now().strftime('%Y-%m-%d')}")
            
            # Get technical analysis for major assets
            technical_insights = []
            major_assets = ['BTC', 'ETH', 'ADA', 'XRP', 'SOL']
            
            for asset in major_assets:
                try:
                    signals = await self.ta_service.generate_trading_signals(asset, 30)
                    if 'error' not in signals:
                        recommendation = signals.get('recommendation', {})
                        trend = signals.get('trend_analysis', {})
                        rsi = signals.get('technical_indicators', {}).get('rsi')
                        
                        insight = f"{asset}: {recommendation.get('action', 'HOLD')} "
                        if rsi:
                            insight += f"(RSI: {rsi:.1f}) "
                        insight += f"Trend: {trend.get('trend', 'neutral')}"
                        technical_insights.append(insight)
                except Exception as e:
                    print(f"Error getting TA for {asset}: {e}")
                    continue
            
            technical_summary = "\n".join(technical_insights) if technical_insights else "Technical analysis unavailable"
            
            prompt = f"""Generate a comprehensive daily trading strategy using REAL-TIME data and technical analysis.

**Current Portfolio:** R{portfolio_data.get('total_value', 0):,.2f}
**Holdings:** {len(portfolio_data.get('holdings', []))} assets

**Real-Time Market Data:**
{json.dumps(market_data[:5], indent=2)}

**Technical Analysis Insights:**
{technical_summary}

**Latest Market Research:**
{market_research}

**Strategy Requirements:**
1. **Main Recommendation** (based on real data and technical analysis)
2. **Risk Level** (Low/Medium/High)
3. **Expected Return** (realistic percentage)
4. **Key Levels** (actual support/resistance from technical analysis)
5. **Specific Actions** (exact amounts and prices with technical rationale)

Focus on achieving R100,000 monthly target through practical, data-driven steps supported by technical indicators."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="daily_strategy",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1500)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return {"strategy": response, "technical_analysis": technical_insights, "generated_at": datetime.now().isoformat()}
            
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
    
    async def execute_autotrade(self, settings: Dict[str, Any], portfolio_data: Dict, market_data: List[Dict]) -> Dict[str, Any]:
        """Execute auto trading based on settings and market analysis"""
        try:
            # Check if auto trading is enabled
            if not settings.get("enabled", False):
                return {"success": False, "message": "Auto trading is disabled"}
            
            # Check trading hours
            from datetime import datetime, time
            import pytz
            
            tz = pytz.timezone(settings.get("trading_hours", {}).get("timezone", "Africa/Johannesburg"))
            current_time = datetime.now(tz).time()
            start_time = time.fromisoformat(settings.get("trading_hours", {}).get("start", "08:00"))
            end_time = time.fromisoformat(settings.get("trading_hours", {}).get("end", "22:00"))
            
            if not (start_time <= current_time <= end_time):
                return {"success": False, "message": "Outside trading hours"}
            
            # Check daily limit
            daily_traded = await self._get_daily_traded_amount(settings.get("user_id"))
            if daily_traded >= settings.get("daily_limit", 5000):
                return {"success": False, "message": "Daily trading limit reached"}
            
            # Analyze market and portfolio for trading opportunities
            analysis = await self._analyze_trading_opportunities(settings, portfolio_data, market_data)
            
            executed_trades = []
            
            for opportunity in analysis.get("opportunities", []):
                # Check if we can execute this trade
                if self._can_execute_trade(opportunity, settings, daily_traded):
                    # Execute the trade
                    trade_result = await self._execute_auto_trade(opportunity, settings)
                    executed_trades.append(trade_result)
                    
                    if trade_result.get("success"):
                        daily_traded += trade_result.get("value", 0)
            
            return {
                "success": True,
                "executed_trades": executed_trades,
                "daily_traded": daily_traded,
                "opportunities_found": len(analysis.get("opportunities", [])),
                "message": f"Executed {len(executed_trades)} trades"
            }
            
        except Exception as e:
            print(f"Error in auto trading execution: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_daily_traded_amount(self, user_id: str) -> float:
        """Get the total amount traded today"""
        try:
            # This would query the database for today's trades
            # For now, return 0 as a placeholder
            return 0.0
        except Exception as e:
            print(f"Error getting daily traded amount: {e}")
            return 0.0
    
    async def _analyze_trading_opportunities(self, settings: Dict, portfolio_data: Dict, market_data: List[Dict]) -> Dict:
        """Analyze current market conditions for trading opportunities"""
        try:
            # Get current portfolio value and holdings
            current_value = portfolio_data.get("total_value", 0)
            holdings = portfolio_data.get("holdings", [])
            
            # Create analysis prompt
            prompt = f"""Analyze current market conditions for auto trading opportunities.

Portfolio Value: R{current_value:,.2f}
Holdings: {len(holdings)} assets

Auto Trading Settings:
- Max trade amount: R{settings.get('max_trade_amount', 1000):,.2f}
- Risk level: {settings.get('risk_level', 'medium')}
- Stop loss: {settings.get('stop_loss_percent', 5)}%
- Take profit: {settings.get('take_profit_percent', 10)}%
- Allowed assets: {', '.join(settings.get('allowed_assets', []))}

Current Market Data:
{json.dumps(market_data[:5], indent=2)}

Identify specific trading opportunities:
1. Assets showing strong momentum (consider buying)
2. Assets at profit targets (consider selling)
3. Assets hitting stop losses (consider selling)
4. Rebalancing opportunities

For each opportunity, specify:
- Action: BUY/SELL
- Asset: Symbol
- Amount: ZAR value
- Reason: Brief explanation
- Priority: 1-5 (1 = highest)

Keep recommendations under R{settings.get('max_trade_amount', 1000):,.2f} per trade."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="autotrade_analysis",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1000)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Parse the response to extract trading opportunities
            opportunities = self._parse_trading_opportunities(response)
            
            return {
                "opportunities": opportunities,
                "analysis": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing trading opportunities: {e}")
            return {"opportunities": [], "error": str(e)}
    
    def _parse_trading_opportunities(self, analysis: str) -> List[Dict]:
        """Parse AI analysis to extract specific trading opportunities"""
        opportunities = []
        
        # Simple parsing - look for BUY/SELL mentions
        lines = analysis.split('\n')
        for line in lines:
            if 'BUY' in line.upper() or 'SELL' in line.upper():
                try:
                    # Extract basic information
                    action = 'BUY' if 'BUY' in line.upper() else 'SELL'
                    
                    # Look for asset symbols
                    assets = ['BTC', 'ETH', 'ADA', 'XRP', 'SOL', 'TRX', 'XLM', 'HBAR']
                    asset = None
                    for a in assets:
                        if a in line.upper():
                            asset = a
                            break
                    
                    # Look for amount (R followed by numbers)
                    import re
                    amount_match = re.search(r'R([\d,]+)', line)
                    amount = 1000  # Default amount
                    if amount_match:
                        amount = float(amount_match.group(1).replace(',', ''))
                    
                    if asset:
                        opportunities.append({
                            'action': action,
                            'asset': asset,
                            'amount': amount,
                            'reason': line.strip(),
                            'priority': 3  # Default priority
                        })
                        
                except Exception as e:
                    print(f"Error parsing opportunity: {e}")
                    continue
        
        return opportunities
    
    def _can_execute_trade(self, opportunity: Dict, settings: Dict, daily_traded: float) -> bool:
        """Check if a trade can be executed based on settings and limits"""
        try:
            # Check if asset is allowed
            if opportunity['asset'] not in settings.get('allowed_assets', []):
                return False
            
            # Check trade amount limits
            if opportunity['amount'] > settings.get('max_trade_amount', 1000):
                return False
            
            # Check daily limit
            if daily_traded + opportunity['amount'] > settings.get('daily_limit', 5000):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error checking trade execution: {e}")
            return False
    
    async def _execute_auto_trade(self, opportunity: Dict, settings: Dict) -> Dict:
        """Execute a specific trade"""
        try:
            # Execute the trade using the existing trade execution function
            trade_result = await self.execute_trade({
                'action': opportunity['action'],
                'symbol': opportunity['asset'],
                'amount': opportunity['amount'],
                'order_type': 'market'
            })
            
            # Log the trade
            log_entry = {
                'user_id': settings.get('user_id'),
                'trade_type': opportunity['action'].lower(),
                'asset': opportunity['asset'],
                'amount': opportunity['amount'],
                'price': 0,  # Will be filled from trade result
                'value': opportunity['amount'],
                'reason': opportunity['reason'],
                'success': 'error' not in trade_result,
                'luno_order_id': trade_result.get('order_id'),
                'executed_at': datetime.now()
            }
            
            return {
                'success': 'error' not in trade_result,
                'trade': opportunity,
                'result': trade_result,
                'log': log_entry
            }
            
        except Exception as e:
            print(f"Error executing auto trade: {e}")
            return {
                'success': False,
                'error': str(e),
                'trade': opportunity
            }

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