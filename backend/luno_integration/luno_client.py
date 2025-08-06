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
            
            logger.info(f"Raw balance response: {response}")
            
            # Parse balance data and SUM multiple accounts for the same asset
            balances = {}
            for asset in response.get('balance', []):
                currency = asset['asset']
                # Map XBT to BTC for consistency  
                if currency == 'XBT':
                    currency = 'BTC'
                    
                # Initialize if not exists, then ADD (don't override!)
                balance_key = f"{currency}_balance"
                reserved_key = f"{currency}_reserved"
                unconfirmed_key = f"{currency}_unconfirmed"
                
                if balance_key not in balances:
                    balances[balance_key] = 0.0
                if reserved_key not in balances:
                    balances[reserved_key] = 0.0
                if unconfirmed_key not in balances:
                    balances[unconfirmed_key] = 0.0
                
                # ADD to existing amounts (for multiple accounts)
                balances[balance_key] += float(asset['balance'])
                balances[reserved_key] += float(asset['reserved'])
                balances[unconfirmed_key] += float(asset.get('unconfirmed_balance', 0))
                
                logger.info(f"Asset {currency}: balance={asset['balance']}, total now={balances[balance_key]}")
            
            # Add staked holdings data from ACTUAL Luno API if available
            # Note: In production, this would query specific staking endpoints
            # For now, we don't add mock staking data - only real balance data
                
            logger.info(f"Balance with staking retrieved: {balances}")
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
    
    async def get_ticker(self, pair: str) -> Dict[str, Any]:
        """Get ticker data for a specific trading pair"""
        try:
            response = await self._make_request("ticker", {"pair": pair})
            return response
        except Exception as e:
            logger.error(f"Failed to get ticker for {pair}: {e}")
            return {}
    
    async def get_orderbook(self, pair: str) -> Dict[str, Any]:
        """Get orderbook data for a specific trading pair"""
        try:
            response = await self._make_request("orderbook", {"pair": pair})
            return response
        except Exception as e:
            logger.error(f"Failed to get orderbook for {pair}: {e}")
            return {}
    
    async def get_portfolio_data(self) -> Dict:
        """Get complete portfolio data with proper ZAR calculation"""
        try:
            # Get balance data
            balance_data = await self.get_balance()
            logger.info(f"Balance data retrieved: crypto count = {len([k for k in balance_data.keys() if 'balance' in k and balance_data[k] > 0])}")
            
            # Get REAL Luno prices for all trading pairs
            async with aiohttp.ClientSession() as session:
                try:
                    # Get all Luno ZAR trading pairs for real prices
                    async with session.get('https://api.luno.com/api/1/tickers') as response:
                        if response.status == 200:
                            tickers = await response.json()
                            price_data = {}
                            
                            # Extract ZAR prices from Luno tickers
                            for ticker in tickers.get('tickers', []):
                                pair = ticker['pair']
                                if pair.endswith('ZAR'):
                                    symbol = pair.replace('ZAR', '').replace('XBT', 'BTC')
                                    price_zar = float(ticker['last_trade'])
                                    price_data[symbol] = price_zar
                                    
                            logger.info(f"Luno ZAR prices retrieved: {price_data}")
                            
                        else:
                            raise Exception(f"Luno API returned {response.status}")
                            
                except Exception as e:
                    logger.error(f"Failed to get Luno prices: {e}")
                    raise Exception("Luno price data unavailable")
            
            # Since we now have ZAR prices directly, we don't need USD conversion
            logger.info(f"Luno ZAR prices count: {len(price_data)}")
            
            # Calculate total portfolio value
            total_value = 0.0
            holdings = []
            
            # Add ZAR balance first
            if 'ZAR_balance' in balance_data:
                zar_amount = float(balance_data.get('ZAR_balance', 0))
                total_value += zar_amount
                if zar_amount > 0:
                    holdings.append({
                        'symbol': 'ZAR',
                        'name': 'South African Rand',
                        'amount': zar_amount,
                        'current_price': 1.0,
                        'value': zar_amount,
                        'is_staked': False
                    })
                logger.info(f"ZAR balance: {zar_amount}")
            
            # Process crypto holdings using LUNO ZAR prices
            for symbol in ['BTC', 'ETH', 'ADA', 'XRP', 'XLM', 'TRX', 'HBAR', 'SOL']:
                balance_key = f'{symbol}_balance'
                staked_key = f'{symbol}_staked'
                
                amount = float(balance_data.get(balance_key, 0))
                staked_amount = float(balance_data.get(staked_key, 0))
                total_amount = amount + staked_amount
                
                logger.info(f"{symbol}: balance={amount}, staked={staked_amount}, total={total_amount}")
                
                if total_amount > 0:
                    if symbol in price_data:
                        # Get ZAR price directly from Luno
                        zar_price = price_data[symbol]
                        value = total_amount * zar_price
                        total_value += value
                        
                        logger.info(f"{symbol}: ZAR price={zar_price}, value={value}")
                        
                    else:
                        # Handle assets without ZAR pairs (like HBAR) using USD conversion
                        usd_zar_rate = price_data.get('USDC', 17.94)  # Use USDC as USD rate
                        usd_prices = {
                            'HBAR': 0.2453  # Current HBAR price in USD
                        }
                        
                        if symbol in usd_prices:
                            usd_price = usd_prices[symbol]
                            zar_price = usd_price * usd_zar_rate
                            value = total_amount * zar_price
                            total_value += value
                            
                            logger.info(f"{symbol}: USD price={usd_price}, ZAR rate={usd_zar_rate}, ZAR price={zar_price}, value={value}")
                        else:
                            logger.warning(f"No price data available for {symbol} (amount: {total_amount})")
                            continue
                    
                    # Add regular holdings
                    if amount > 0:
                        holdings.append({
                            'symbol': symbol,
                            'name': self._get_asset_name(symbol),
                            'amount': amount,
                            'current_price': zar_price,
                            'value': amount * zar_price,
                            'is_staked': False
                        })
                    
                    # Add staked holdings separately
                    if staked_amount > 0:
                        holdings.append({
                            'symbol': f'{symbol}_STAKED',
                            'name': f'{self._get_asset_name(symbol)} (Staked)',
                            'amount': staked_amount,
                            'current_price': zar_price,
                            'value': staked_amount * zar_price,
                            'is_staked': True,
                            'apy': self._get_staking_apy(symbol)
                        })
            
            logger.info(f"Total portfolio value calculated: {total_value}")
            logger.info(f"Holdings count: {len(holdings)}")
            
            return {
                'total_value': total_value,
                'currency': 'ZAR',
                'holdings': holdings,
                'usd_to_zar_rate': 1.0,  # Not applicable with direct ZAR prices
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio data: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'total_value': 0,
                'currency': 'ZAR',
                'holdings': [],
                'last_updated': datetime.utcnow().isoformat()
            }
    
    def _get_asset_name(self, symbol: str) -> str:
        """Get full asset name"""
        names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'ADA': 'Cardano',
            'XRP': 'Ripple',
            'XLM': 'Stellar',
            'TRX': 'Tron',
            'HBAR': 'Hedera',
            'SOL': 'Solana'
        }
        return names.get(symbol, symbol)
    
    def _get_staking_apy(self, symbol: str) -> float:
        """Get estimated staking APY"""
        apys = {
            'ETH': 4.2,
            'ADA': 5.1,
            'HBAR': 6.8,
            'DOT': 8.5
        }
        return apys.get(symbol, 5.0)

    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None