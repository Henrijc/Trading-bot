import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class LunoClient:
    """
    Luno API client for cryptocurrency trading
    Uses the exact same pattern as the working implementation
    """
    
    def __init__(self, api_key: str, api_secret: str):
        """Initialize Luno API client"""
        self.api_key = api_key
        self.api_secret = api_secret  # This should be LUNO_SECRET
        self.base_url = "https://api.luno.com/api/1"
        self.session = None
        
        logger.info(f"LunoClient initialized with API key: {self.api_key[:10]}..." if self.api_key else "No API key found")
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, endpoint: str, params: Dict = None, method: str = 'GET', data: Dict = None) -> Dict:
        """Make authenticated request to Luno API - using working implementation"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/{endpoint}"
            
            if not self.api_key or not self.api_secret:
                raise Exception("No Luno API credentials available")
            
            auth = aiohttp.BasicAuth(self.api_key, self.api_secret)
            
            logger.info(f"Making request to: {url}")
            logger.info(f"Using API key: {self.api_key}")
            logger.info(f"Using API secret length: {len(self.api_secret)}")
            
            if method == 'GET':
                async with session.get(url, params=params, auth=auth) as response:
                    return await self._handle_response(response, endpoint)
            elif method == 'POST':
                async with session.post(url, data=data, auth=auth) as response:
                    return await self._handle_response(response, endpoint)
                    
        except Exception as e:
            logger.error(f"Error calling Luno API: {e}")
            raise e
    
    async def _handle_response(self, response, endpoint):
        """Handle API response - using working implementation"""
        if response.status == 200:
            data = await response.json()
            logger.info(f"Luno API success: {endpoint}")
            return data
        else:
            error_text = await response.text()
            logger.error(f"Luno API error: {response.status} - {error_text}")
            raise Exception(f"Luno API error: {response.status} - {error_text}")
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance - using working implementation pattern"""
        try:
            response = await self._make_request("balance")
            
            # Parse balance data like the working implementation
            balances = {}
            for asset in response.get('balance', []):
                currency = asset['asset']
                # Map XBT to BTC for consistency  
                if currency == 'XBT':
                    currency = 'BTC'
                    
                balances[f"{currency}_balance"] = float(asset['balance'])
                balances[f"{currency}_reserved"] = float(asset['reserved'])
                balances[f"{currency}_unconfirmed"] = float(asset['unconfirmed_balance'])
                
            logger.info(f"Balance retrieved: {balances}")
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise Exception(f"Luno API authentication failed: {e}")
    
    async def get_market_data(self, pair: str) -> Dict[str, Any]:
        """Get market data for a specific trading pair"""
        try:
            response = await self._make_request("ticker", {"pair": pair})
            return response
        except Exception as e:
            logger.error(f"Failed to get market data for {pair}: {e}")
            # For market data, we can fallback to public data
            # But return empty dict to indicate failure
            return {}
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None