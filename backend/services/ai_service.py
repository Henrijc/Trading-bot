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
        # Note: Memory service will be imported dynamically to avoid circular import
        
        # Session management - maintain chat instances per session
        self.chat_sessions = {}
        
        # Load comprehensive training data from knowledge base
        training_data = self.knowledge_base.get_training_data()
        training_context = ""
        if training_data:
            # Use a portion of the training data to guide AI behavior
            training_context = f"\n\nCOMPREHENSIVE TRAINING DATA:\n{training_data[:5000]}\n\nUSE THIS TRAINING DATA TO GUIDE YOUR RESPONSES AND BEHAVIOR. YOU ARE A SEASONED SOUTH AFRICAN CRYPTO TRADER."
        
        self.system_message = f"""You are an expert South African cryptocurrency trading coach. Be concise and professional.

CRITICAL INSTRUCTIONS:
- ALWAYS use the portfolio data provided in the context when users ask about their holdings, assets, profile, or staking
- When portfolio data is provided, reference it directly in your response
- Be concise by default but include relevant portfolio details when asked

RESPONSE STYLE:
- Give brief, actionable responses unless detailed analysis is requested
- Focus on answering the specific question asked
- When users ask about their portfolio/profile/assets/staking, show them their actual data

DATA ACCESS:
You have access to real-time portfolio data, market prices, technical indicators, and market sentiment. When portfolio data is provided in context, USE IT in your response.

PORTFOLIO QUESTIONS:
- When users ask "show me my profile/portfolio/assets/staking" - display their actual holdings
- When users ask about their holdings - reference their specific assets and values
- When users ask about staking - show which of their assets are staked (if that data is available)

Be professional, direct, and use the actual data provided to answer their questions.{training_context}"""
    
    async def web_search(self, query: str) -> str:
        """Search the web for current crypto market information"""
        try:
            results = []
            
            # Method 1: Get global crypto market data from CoinGecko
            try:
                cg_url = "https://api.coingecko.com/api/v3/global"
                response = requests.get(cg_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    global_data = data.get('data', {})
                    if global_data:
                        market_cap = global_data.get('total_market_cap', {}).get('usd', 0)
                        volume = global_data.get('total_volume', {}).get('usd', 0)
                        btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
                        results.append(f"GLOBAL CRYPTO MARKET: Market cap ${market_cap:,.0f}. 24h volume ${volume:,.0f}. BTC dominance: {btc_dominance:.1f}%")
            except Exception as e:
                print(f"CoinGecko error: {e}")
            
            # Method 2: Get specific crypto prices from CoinGecko
            try:
                if any(crypto in query.lower() for crypto in ['bitcoin', 'btc', 'ethereum', 'eth']):
                    coins_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
                    response = requests.get(coins_url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'bitcoin' in data:
                            btc_price = data['bitcoin']['usd']
                            btc_change = data['bitcoin']['usd_24h_change']
                            results.append(f"BITCOIN: ${btc_price:,.0f} USD ({btc_change:+.2f}% 24h)")
                        
                        if 'ethereum' in data:
                            eth_price = data['ethereum']['usd']
                            eth_change = data['ethereum']['usd_24h_change']
                            results.append(f"ETHEREUM: ${eth_price:,.0f} USD ({eth_change:+.2f}% 24h)")
            except Exception as e:
                print(f"Crypto prices error: {e}")
            
            # Method 3: Get Fear & Greed Index
            try:
                fng_url = "https://api.alternative.me/fng/"
                response = requests.get(fng_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data') and len(data['data']) > 0:
                        fng_value = data['data'][0]['value']
                        fng_classification = data['data'][0]['value_classification']
                        results.append(f"MARKET SENTIMENT: Fear & Greed Index {fng_value}/100 ({fng_classification})")
            except Exception as e:
                print(f"Fear & Greed error: {e}")
            
            # Method 4: Crypto news headlines (alternative API)
            try:
                # Using a more reliable crypto news source
                news_url = "https://api.coindesk.com/v1/news.json"
                response = requests.get(news_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('articles'):
                        latest_article = data['articles'][0]
                        results.append(f"LATEST NEWS: {latest_article.get('title', '')}")
            except Exception as e:
                print(f"News error: {e}")
            
            # Method 5: DeFi and altcoin data
            try:
                if 'defi' in query.lower() or 'altcoin' in query.lower():
                    defi_url = "https://api.coingecko.com/api/v3/global/defi"
                    response = requests.get(defi_url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        defi_data = data.get('data', {})
                        if defi_data:
                            defi_cap = defi_data.get('defi_market_cap', 0)
                            defi_dominance = defi_data.get('defi_dominance', 0)
                            results.append(f"DEFI MARKET: ${defi_cap:,.0f} market cap, {defi_dominance:.2f}% of total crypto")
            except Exception as e:
                print(f"DeFi error: {e}")
            
            # Return comprehensive results
            if results:
                return ' | '.join(results)
            else:
                return f"Real-time market data search for '{query}' - Using live Luno and technical analysis data for current market conditions."
                
        except Exception as e:
            print(f"Error in web search: {e}")
            return f"Market analysis using real-time Luno data and technical indicators for: {query}"
    
    async def send_message(self, session_id: str, message: str, context: Dict[str, Any] = None) -> str:
        """Send a message to the AI coach and get a response with enhanced knowledge"""
        try:
            # Get or create chat instance for this session
            if session_id not in self.chat_sessions:
                self.chat_sessions[session_id] = LlmChat(
                    api_key=self.api_key,
                    session_id=session_id,
                    system_message=self.system_message
                ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(4000)
            
            chat = self.chat_sessions[session_id]
            
            # Build enhanced context - keep it focused and concise
            enhanced_context = ""
            
            # Add previous conversation summaries for continuity
            try:
                # Get recent conversation summaries (last 30 days)
                from motor.motor_asyncio import AsyncIOMotorClient
                import os
                client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
                db = client.ai_trading_coach
                
                # Get summaries for this user (we can expand this later for multi-user)
                summaries = await db.conversation_summaries.find().sort("timestamp", -1).limit(5).to_list(None)
                
                if summaries:
                    enhanced_context += "**PREVIOUS CONVERSATION CONTEXT:**\n"
                    for summary in reversed(summaries):  # Most recent first
                        enhanced_context += f"• {summary.get('summary', '')}\n"
                        
                        goals = summary.get('goals_discussed', [])
                        if goals:
                            enhanced_context += f"  Goals mentioned: {', '.join(goals)}\n"
                            
                        decisions = summary.get('key_decisions', [])
                        if decisions:
                            enhanced_context += f"  Decisions made: {', '.join(decisions)}\n"
                    
                    enhanced_context += "\n"
                    
            except Exception as e:
                print(f"Error loading conversation summaries: {e}")
                pass
            
            # Add web search for market-related queries
            web_research = ""
            market_keywords = ['market', 'analysis', 'price', 'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'trading', 'news', 'sentiment', 'trend']
            if any(keyword in message.lower() for keyword in market_keywords):
                try:
                    web_research = await self.web_search(message)
                    if web_research:
                        enhanced_context += f"**REAL-TIME MARKET DATA:**\n{web_research}\n\n"
                except Exception as e:
                    print(f"Web search error: {e}")
            
            # Check for semi-auto trade requests
            trade_keywords = ['execute trade', 'do that trade', 'make that trade', 'execute that', 'do it', 'go for it', 'execute all']
            has_trade_request = any(keyword in message.lower() for keyword in trade_keywords)
            
            if has_trade_request:
                try:
                    # Import to avoid circular import
                    from services.semi_auto_trade_service import SemiAutoTradeService
                    trade_service = SemiAutoTradeService()
                    
                    # Check if user wants to execute all pending trades
                    if 'execute all' in message.lower():
                        pending_trades = trade_service.get_pending_trades()
                        if pending_trades:
                            execution_results = []
                            for trade in pending_trades:
                                result = await trade_service.execute_approved_trade(trade['id'], message)
                                execution_results.append(result)
                            
                            success_count = sum(1 for r in execution_results if r.get('success'))
                            enhanced_context += f"**TRADE EXECUTION RESULTS:**\nExecuted {success_count}/{len(pending_trades)} trades successfully.\n\n"
                    
                    # Check for specific trade ID in message
                    elif 'execute trade' in message.lower():
                        import re
                        trade_id_match = re.search(r'execute trade ([a-zA-Z0-9]+)', message.lower())
                        if trade_id_match:
                            trade_id = trade_id_match.group(1)
                            result = await trade_service.execute_approved_trade(trade_id, message)
                            if result.get('success'):
                                enhanced_context += f"**TRADE EXECUTED:**\n{result['message']}\n\n"
                            else:
                                enhanced_context += f"**TRADE FAILED:**\n{result.get('error', 'Unknown error')}\n\n"
                    
                except Exception as e:
                    print(f"Trade execution error: {e}")
            
            # Check for trade suggestion requests
            suggest_keywords = ['suggest trades', 'trading opportunities', 'what should i trade', 'any trades', 'trading suggestions', 'analyze market']
            has_suggest_request = any(keyword in message.lower() for keyword in suggest_keywords)
            
            if has_suggest_request:
                try:
                    from services.semi_auto_trade_service import SemiAutoTradeService
                    trade_service = SemiAutoTradeService()
                    
                    portfolio_data = await self.luno_service.get_portfolio_data()
                    suggestions_result = await trade_service.analyze_and_suggest_trades(portfolio_data, message)
                    
                    if suggestions_result.get('success') and suggestions_result.get('suggestions'):
                        approval_message = await trade_service.generate_trade_approval_message(suggestions_result['suggestions'])
                        enhanced_context += f"**TRADE SUGGESTIONS:**\n{approval_message}\n\n"
                    
                except Exception as e:
                    print(f"Trade suggestion error: {e}")
            
            # Check if user is asking for portfolio-related information and add to existing context
            portfolio_keywords = ['portfolio', 'holdings', 'balance', 'value', 'allocation', 'assets', 'my coins', 'my crypto', 'profile', 'staking', 'stake', 'staked', 'examine', 'check', 'see', 'show me']
            requests_portfolio = any(keyword in message.lower() for keyword in portfolio_keywords)
            
            # Check if user is asking for market analysis
            market_keywords = ['market', 'analysis', 'overview', 'condition', 'sentiment']
            requests_market = any(keyword in message.lower() for keyword in market_keywords)
            
            # Check if user is asking for detailed information
            detail_keywords = ['detailed', 'full', 'breakdown', 'complete', 'comprehensive', 'analyze']
            requests_details = any(keyword in message.lower() for keyword in detail_keywords)
            
            # Add portfolio context only when requested (append to existing enhanced_context)
            if context and (requests_portfolio or requests_details):
                portfolio_value = context.get('portfolio', {}).get('total_value', 0)
                holdings = context.get('portfolio', {}).get('holdings', [])
                
                # Build concise portfolio context only when requested
                enhanced_context += f"""**CURRENT PORTFOLIO DATA:**
Portfolio Value: R{portfolio_value:,.2f}
Number of Holdings: {len(holdings)} assets

**HOLDINGS BREAKDOWN:**"""
                
                for holding in holdings:
                    symbol = holding.get('symbol', 'Unknown')
                    value = holding.get('value', 0)
                    allocation = holding.get('allocation', 0)
                    enhanced_context += f"\n- {symbol}: R{value:,.2f} ({allocation:.1f}%)"
                
                enhanced_context += f"\n\n"
            
            # Add technical analysis for relevant crypto discussions only when needed
            if any(keyword in message.lower() for keyword in ['btc', 'bitcoin', 'eth', 'ethereum', 'trade', 'buy', 'sell']) or requests_details:
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
                                    enhanced_context += f"\n**{symbol} TECHNICAL ANALYSIS:**\nRecommendation: {rec.get('action', 'HOLD')}, RSI: {rsi:.1f}, Trend: {trend}\n"
                            except:
                                continue
                except:
                    pass
            
            # Always add the user's message
            final_message = enhanced_context + f"**USER MESSAGE:** {message}"
            
            user_message = UserMessage(text=final_message)
            
            # Send message and get response
            response = await chat.send_message(user_message)
            
            # Clean up the response to ensure it's well-formatted
            return self._format_response(response)
            
        except Exception as e:
            print(f"Error in AI service: {e}")
            return """I'm having trouble accessing real-time data right now. Please try again in a moment.

With your current portfolio value, I'd suggest taking profits on any positions that are up 15-20% and consider reinvesting in underperforming assets with strong fundamentals. Happy to help you analyze specific positions once my connection is restored."""
    
    def clear_session(self, session_id: str):
        """Clear a specific chat session"""
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            
    def clear_all_sessions(self):
        """Clear all chat sessions"""
        self.chat_sessions.clear()
    
    async def summarize_conversation(self, messages: List[Dict]) -> Dict[str, Any]:
        """Generate intelligent summary of conversation"""
        try:
            if not messages or len(messages) < 3:
                return {
                    "summary": "Brief conversation with minimal context.",
                    "key_decisions": [],
                    "goals_discussed": [],
                    "portfolio_context": {}
                }
            
            # Build conversation text for summarization
            conversation_text = ""
            for msg in messages:
                role = msg.get('role', 'unknown')
                message = msg.get('message', '')
                conversation_text += f"{role.upper()}: {message}\n"
            
            # Create summarization prompt
            summary_prompt = f"""Analyze this crypto trading conversation and create a structured summary:

CONVERSATION:
{conversation_text}

Please provide a JSON response with:
1. "summary": Brief 2-3 sentence overview of the conversation
2. "key_decisions": List of specific decisions made (target changes, trading plans, etc.)
3. "goals_discussed": List of goals mentioned (monthly targets, portfolio objectives, etc.)  
4. "portfolio_context": Any important portfolio details discussed (asset holdings, staking, etc.)

Focus on actionable information and specific details that would be useful context for future conversations.
"""

            # Use a simple chat instance for summarization
            summary_chat = LlmChat(
                api_key=self.api_key,
                session_id="summary_session"
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1000)
            
            response = await summary_chat.send_message(summary_prompt)
            
            # Try to parse JSON response
            try:
                import json
                # Clean response - remove markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:-3]
                elif clean_response.startswith('```'):
                    clean_response = clean_response[3:-3]
                
                summary_data = json.loads(clean_response)
                return summary_data
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "summary": response[:200] + "..." if len(response) > 200 else response,
                    "key_decisions": [],
                    "goals_discussed": [],
                    "portfolio_context": {}
                }
                
        except Exception as e:
            print(f"Error creating conversation summary: {e}")
            return {
                "summary": f"Conversation about crypto trading strategy with {len(messages)} messages exchanged.",
                "key_decisions": [],
                "goals_discussed": [],
                "portfolio_context": {}
            }
    
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
        """Allow AI to analyze and adjust targets based on real performance and user requests"""
        try:
            current_value = context.get("current_portfolio", 0)
            current_target = context.get("current_monthly_target", 100000)
            reason = context.get("request", "")
            ai_suggestion = context.get("ai_suggestion", "")
            
            # Parse user request for specific target amounts
            import re
            user_target_match = re.search(r'[Rr]?\s?(\d{1,3}(?:,?\d{3})*(?:k|K)?)', reason)
            specific_target = None
            
            if user_target_match:
                target_str = user_target_match.group(1).replace(',', '').upper()
                if 'K' in target_str:
                    specific_target = int(target_str.replace('K', '')) * 1000
                else:
                    specific_target = int(target_str)
            
            # Get market conditions for context
            market_research = await self.web_search("cryptocurrency market outlook 2025")
            
            prompt = f"""You are analyzing a target adjustment request from a South African crypto trader.

**CURRENT SITUATION:**
- Portfolio Value: R{current_value:,.2f}
- Current Monthly Target: R{current_target:,.2f}
- Progress: {(current_value / current_target * 100):.1f}%
- User Request: "{reason}"
- Specific Target Requested: {f"R{specific_target:,.2f}" if specific_target else "Not specified"}

**MARKET CONTEXT:**
{market_research}

**YOUR TASK:**
Analyze this request and determine the optimal monthly target:

**DECISION RULES:**
1. If user specifies exact amount (e.g., "change to R150k"), use that if reasonable
2. If user says "adjust based on performance", analyze current progress
3. Consider market conditions and risk management
4. Ensure target is challenging but achievable

**RESPONSE FORMAT:**
If adjusting: "ADJUST: New monthly target should be R[amount] because [detailed reason]"
If maintaining: "MAINTAIN: Current target is appropriate because [reason]"

**FACTORS TO CONSIDER:**
- Current portfolio performance vs target
- Market volatility and conditions
- Risk management (target should be 50-200% of current portfolio value)
- User's trading experience and goals
- South African market conditions (ZAR volatility, Luno liquidity)

Provide a detailed explanation with specific reasoning."""
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id="target_adjustment",
                system_message=self.system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1500)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Parse AI response to extract new targets - try multiple patterns
            new_monthly_target = None
            
            # Pattern 1: ADJUST: ... R[amount]
            if "ADJUST:" in response:
                import re
                target_match = re.search(r'R([\d,]+)', response)
                if target_match:
                    new_monthly_target = int(target_match.group(1).replace(',', ''))
            
            # Pattern 2: If user specified a target, use it (if AI agreed)
            elif specific_target and ("reasonable" in response.lower() or "appropriate" in response.lower()):
                new_monthly_target = specific_target
            
            # Pattern 3: Look for "target should be" anywhere in response
            if not new_monthly_target:
                target_match = re.search(r'target should be R([\d,]+)', response.lower())
                if target_match:
                    new_monthly_target = int(target_match.group(1).replace(',', ''))
            
            if new_monthly_target and new_monthly_target != current_target:
                new_weekly_target = new_monthly_target / 4
                new_daily_target = new_weekly_target / 7
                
                return {
                    "new_targets": {
                        "monthly_target": new_monthly_target,
                        "weekly_target": new_weekly_target,
                        "daily_target": new_daily_target
                    },
                    "explanation": response,
                    "adjusted": True,
                    "user_requested": specific_target is not None
                }
            
            return {
                "explanation": response,
                "adjusted": False,
                "reason": "No adjustment needed or AI recommended maintaining current target"
            }
            
        except Exception as e:
            print(f"Error in target adjustment: {e}")
            return {
                "explanation": "I couldn't analyze the targets right now. Let's keep the current targets for now.",
                "adjusted": False,
                "error": str(e)
            }