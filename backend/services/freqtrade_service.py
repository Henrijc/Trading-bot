"""
FreqtradeService - Communication layer between Backend Orchestrator and Freqtrade Bot
This service handles all communication with the standalone Freqtrade trading bot
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FreqtradeService:
    """
    Service to communicate with the Freqtrade trading bot via its REST API
    """
    
    def __init__(self, bot_url: str = "http://localhost:8082"):
        self.bot_url = bot_url
        self.session = None
        logger.info(f"FreqtradeService initialized with bot URL: {bot_url}")
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict:
        """Make request to Freqtrade bot API"""
        try:
            session = await self._get_session()
            url = f"{self.bot_url}{endpoint}"
            
            if method == 'GET':
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Bot API error {response.status}: {await response.text()}")
                        return {"error": f"API error: {response.status}"}
            
            elif method == 'POST':
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Bot API error {response.status}: {await response.text()}")
                        return {"error": f"API error: {response.status}"}
        
        except Exception as e:
            logger.error(f"Error communicating with bot API: {e}")
            return {"error": str(e)}
    
    async def start_bot(self) -> Dict:
        """Start the Freqtrade trading bot"""
        try:
            result = await self._make_request("/api/v1/start", method="POST")
            logger.info(f"Bot start result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            return {"error": str(e), "success": False}
    
    async def stop_bot(self) -> Dict:
        """Stop the Freqtrade trading bot"""
        try:
            result = await self._make_request("/api/v1/stop", method="POST")
            logger.info(f"Bot stop result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            return {"error": str(e), "success": False}
    
    async def get_status(self) -> Dict:
        """Get the current status of the Freqtrade trading bot"""
        try:
            result = await self._make_request("/api/v1/status")
            return result
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return {
                "error": str(e),
                "status": "disconnected",
                "message": "Unable to connect to trading bot"
            }
    
    async def get_trades(self) -> Dict:
        """Get all trades from the Freqtrade bot"""
        try:
            result = await self._make_request("/api/v1/trades")
            return result
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return {"error": str(e), "trades": [], "count": 0}
    
    async def get_profit(self) -> Dict:
        """Get profit summary from the Freqtrade bot"""
        try:
            result = await self._make_request("/api/v1/profit")
            return result
        except Exception as e:
            logger.error(f"Error getting profit data: {e}")
            return {
                "error": str(e),
                "total_profit": 0,
                "total_trades": 0,
                "winning_trades": 0,
                "win_rate": 0,
                "avg_profit": 0
            }
    
    async def get_signals(self, pair: str = None) -> Dict:
        """Get trading signals from the bot"""
        try:
            # This would be implemented once the bot supports signal endpoints
            endpoint = f"/api/v1/signals"
            if pair:
                endpoint += f"?pair={pair}"
            
            result = await self._make_request(endpoint)
            return result
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return {"error": str(e), "signals": []}
    
    async def health_check(self) -> bool:
        """Check if the Freqtrade bot is healthy and responding"""
        try:
            result = await self._make_request("/")
            return "healthy" in result.get("status", "").lower()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def close_session(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None