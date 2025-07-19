import os
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import requests_cache
from dotenv import load_dotenv
from pathlib import Path

class LunoService:
    def __init__(self):
        # Ensure environment variables are loaded
        ROOT_DIR = Path(__file__).parent.parent
        load_dotenv(ROOT_DIR / '.env')
        
        self.api_key = os.environ.get('LUNO_API_KEY', '')
        self.secret = os.environ.get('LUNO_SECRET', '')
        self.base_url = 'https://api.luno.com/api/1'
        self.session = None
        
        # Setup caching for external price data
        self.cache = requests_cache.CachedSession('crypto_cache', expire_after=60)
        
        print(f"LunoService initialized with API key: {self.api_key[:10]}..." if self.api_key else "No API key found")
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, endpoint: str, params: Dict = None, method: str = 'GET', data: Dict = None) -> Dict:
        """Make authenticated request to Luno API"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/{endpoint}"
            
            if not self.api_key or not self.secret:
                raise Exception("No Luno API credentials available")
            
            auth = aiohttp.BasicAuth(self.api_key, self.secret)
            
            if method == 'GET':
                async with session.get(url, params=params, auth=auth) as response:
                    return await self._handle_response(response, endpoint)
            elif method == 'POST':
                async with session.post(url, data=data, auth=auth) as response:
                    return await self._handle_response(response, endpoint)
                    
        except Exception as e:
            print(f"Error calling Luno API: {e}")
            raise e
    
    async def _handle_response(self, response, endpoint):
        """Handle API response"""
        if response.status == 200:
            data = await response.json()
            print(f"Luno API success: {endpoint}")
            return data
        else:
            error_text = await response.text()
            print(f"Luno API error: {response.status} - {error_text}")
            raise Exception(f"Luno API error: {response.status} - {error_text}")
    
    def get_usd_to_zar_rate(self) -> float:
        """Get current USD to ZAR exchange rate"""
        try:
            response = self.cache.get('https://api.exchangerate-api.com/v4/latest/USD')
            if response.status_code == 200:
                data = response.json()
                return data['rates']['ZAR']
            else:
                print("Failed to get USD/ZAR rate, using fallback")
                return 18.50  # Fallback rate
        except Exception as e:
            print(f"Error getting USD/ZAR rate: {e}")
            return 18.50  # Fallback rate
    
    def get_crypto_usd_prices(self) -> Dict[str, float]:
        """Get cryptocurrency prices in USD from CoinGecko"""
        try:
            # Get prices for all major cryptocurrencies
            crypto_ids = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'ADA': 'cardano',
                'XRP': 'ripple',
                'SOL': 'solana',
                'TRX': 'tron',
                'XLM': 'stellar',
                'HBAR': 'hedera-hashgraph',
                'LTC': 'litecoin',
                'DOGE': 'dogecoin',
                'DOT': 'polkadot',
                'AVAX': 'avalanche-2',
                'ATOM': 'cosmos',
                'ALGO': 'algorand',
                'BCH': 'bitcoin-cash',
                'CRV': 'curve-dao-token',
                'AAVE': 'aave'
            }
            
            ids_string = ','.join(crypto_ids.values())
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd&include_24hr_change=true'
            
            response = self.cache.get(url)
            if response.status_code == 200:
                data = response.json()
                prices = {}
                for symbol, coin_id in crypto_ids.items():
                    if coin_id in data:
                        prices[symbol] = {
                            'usd': data[coin_id]['usd'],
                            'change_24h': data[coin_id].get('usd_24h_change', 0)
                        }
                return prices
            else:
                print("Failed to get crypto prices from CoinGecko")
                return {}
        except Exception as e:
            print(f"Error getting crypto USD prices: {e}")
            return {}
    
    async def get_market_data(self) -> List[Dict]:
        """Get current market data for all supported cryptocurrencies"""
        try:
            # Get real-time data from both Luno and external sources
            luno_tickers = await self._make_request('tickers')
            usd_prices = self.get_crypto_usd_prices()
            usd_to_zar = self.get_usd_to_zar_rate()
            
            market_data = []
            
            # Comprehensive mapping of all cryptocurrencies
            crypto_info = {
                'BTC': {'name': 'Bitcoin', 'luno_pair': 'XBTZAR'},
                'ETH': {'name': 'Ethereum', 'luno_pair': 'ETHZAR'},
                'ADA': {'name': 'Cardano', 'luno_pair': 'ADAZAR'},
                'XRP': {'name': 'Ripple', 'luno_pair': 'XRPZAR'},
                'SOL': {'name': 'Solana', 'luno_pair': 'SOLZAR'},
                'TRX': {'name': 'Tron', 'luno_pair': 'TRXZAR'},
                'XLM': {'name': 'Stellar', 'luno_pair': 'XLMZAR'},
                'HBAR': {'name': 'Hedera', 'luno_pair': 'HBARZAR'},
                'LTC': {'name': 'Litecoin', 'luno_pair': 'LTCZAR'},
                'DOGE': {'name': 'Dogecoin', 'luno_pair': 'DOGEZAR'},
                'DOT': {'name': 'Polkadot', 'luno_pair': 'DOTZAR'},
                'AVAX': {'name': 'Avalanche', 'luno_pair': 'AVAXZAR'},
                'ATOM': {'name': 'Cosmos', 'luno_pair': 'ATOMZAR'},
                'ALGO': {'name': 'Algorand', 'luno_pair': 'ALGOZAR'},
                'BCH': {'name': 'Bitcoin Cash', 'luno_pair': 'BCHZAR'},
                'CRV': {'name': 'Curve', 'luno_pair': 'CRVZAR'},
                'AAVE': {'name': 'Aave', 'luno_pair': 'AAVEZAR'}
            }
            
            # Create a lookup for Luno prices
            luno_lookup = {}
            for ticker in luno_tickers.get('tickers', []):
                luno_lookup[ticker['pair']] = ticker
            
            # Process each cryptocurrency
            for symbol, info in crypto_info.items():
                price_zar = None
                change_24h = 0
                source = "USD"
                
                # Try to get ZAR price from Luno first
                if info['luno_pair'] in luno_lookup:
                    ticker = luno_lookup[info['luno_pair']]
                    price_zar = float(ticker['last_trade'])
                    source = "Luno"
                    # Estimate 24h change (Luno doesn't provide this)
                    if symbol in usd_prices:
                        change_24h = usd_prices[symbol]['change_24h']
                
                # Fallback to USD price converted to ZAR
                elif symbol in usd_prices:
                    price_usd = usd_prices[symbol]['usd']
                    price_zar = price_usd * usd_to_zar
                    change_24h = usd_prices[symbol]['change_24h']
                
                if price_zar:
                    market_data.append({
                        'symbol': symbol,
                        'name': info['name'],
                        'price': price_zar,
                        'change_24h': change_24h,
                        'volume': 0,  # Volume not critical for display
                        'market_cap': 0,  # Market cap not critical for display
                        'trend': 'up' if change_24h > 0 else 'down',
                        'source': source,
                        'last_updated': datetime.now().isoformat()
                    })
            
            return market_data
            
        except Exception as e:
            print(f"Error getting market data: {e}")
            return []
    
    async def _get_cross_conversion_price(self, from_symbol: str, to_symbol: str = 'BTC') -> float:
        """Get cross-conversion price (e.g., HBAR/BTC)"""
        try:
            # Use CoinGecko for cross-conversion
            from_id_mapping = {
                'HBAR': 'hedera-hashgraph',
                'BTC': 'bitcoin',
                'ETH': 'ethereum'
            }
            
            to_id_mapping = {
                'HBAR': 'hedera-hashgraph', 
                'BTC': 'bitcoin',
                'ETH': 'ethereum'
            }
            
            from_id = from_id_mapping.get(from_symbol)
            to_id = to_id_mapping.get(to_symbol)
            
            if not from_id or not to_id:
                return None
                
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={from_id}&vs_currencies={to_id}"
            response = self.cache.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data[from_id][to_id]
                
        except Exception as e:
            print(f"Cross-conversion error for {from_symbol}/{to_symbol}: {e}")
            
        return None

    async def get_portfolio_data(self) -> Dict:
        """Get user's portfolio data from Luno"""
        try:
            balance_data = await self._make_request('balance')
            market_data = await self.get_market_data()
            
            # Create price lookup
            price_lookup = {item['symbol']: item['price'] for item in market_data}
            
            holdings = []
            total_value = 0.0
            
            # Group assets by symbol to handle multiple accounts (staking)
            asset_groups = {}
            
            for balance in balance_data.get('balance', []):
                asset = balance.get('asset')
                amount = float(balance.get('balance', 0))
                account_id = balance.get('account_id')
                
                if asset == 'ZAR':
                    total_value += amount
                    continue
                
                if amount > 0:
                    if asset not in asset_groups:
                        asset_groups[asset] = []
                    asset_groups[asset].append({
                        'amount': amount,
                        'account_id': account_id
                    })
            
            # First pass: collect all assets regardless of price availability
            all_assets = {}
            for asset, accounts in asset_groups.items():
                # Map asset symbols
                symbol_mapping = {'XBT': 'BTC'}
                symbol = symbol_mapping.get(asset, asset)
                total_amount = sum(acc['amount'] for acc in accounts)
                
                all_assets[symbol] = {
                    'accounts': accounts,
                    'total_amount': total_amount,
                    'symbol': symbol
                }
            
            # Second pass: get prices (including cross-conversion)
            enhanced_price_lookup = price_lookup.copy()
            
            # Add cross-conversion for missing assets (like HBAR)
            missing_assets = [symbol for symbol in all_assets.keys() if symbol not in enhanced_price_lookup]
            
            for missing_symbol in missing_assets:
                try:
                    # Get cross-conversion price via BTC
                    cross_price = await self._get_cross_conversion_price(missing_symbol, 'BTC')
                    if cross_price and 'BTC' in enhanced_price_lookup:
                        btc_zar_price = enhanced_price_lookup['BTC']
                        enhanced_price_lookup[missing_symbol] = cross_price * btc_zar_price
                        print(f"Cross-converted {missing_symbol}: {cross_price} BTC × R{btc_zar_price:.2f} = R{enhanced_price_lookup[missing_symbol]:.2f}")
                except Exception as e:
                    print(f"Cross-conversion failed for {missing_symbol}: {e}")
                    # Try direct USD conversion as fallback
                    try:
                        usd_prices = self.get_crypto_usd_prices()
                        usd_to_zar = self.get_usd_to_zar_rate()
                        if missing_symbol in usd_prices:
                            enhanced_price_lookup[missing_symbol] = usd_prices[missing_symbol]['usd'] * usd_to_zar
                            print(f"USD fallback for {missing_symbol}: ${usd_prices[missing_symbol]['usd']} × {usd_to_zar:.2f} = R{enhanced_price_lookup[missing_symbol]:.2f}")
                    except Exception as fallback_error:
                        print(f"USD fallback also failed for {missing_symbol}: {fallback_error}")
            
            # Third pass: process all assets with enhanced price lookup
            for symbol, asset_data in all_assets.items():
                accounts = asset_data['accounts']
                total_amount = asset_data['total_amount']
                
                # Get price (now includes cross-converted prices)
                if symbol in enhanced_price_lookup:
                    current_price = enhanced_price_lookup[symbol]
                    value = total_amount * current_price
                    total_value += value
                    
                    # Get market data for this asset
                    market_info = next((item for item in market_data if item['symbol'] == symbol), {})
                    
                    # Determine staking status
                    is_staked = len(accounts) > 1
                    
                    # Enhanced staking detection
                    staking_keywords = ['staking', 'stake', 'staked', 'earn', 'savings', 'rewards']
                    account_ids = [str(acc.get('account_id', '')) for acc in accounts]
                    staking_patterns = any(keyword in account_id.lower() for account_id in account_ids for keyword in staking_keywords)
                    
                    # Special handling for known staked assets
                    if symbol in ['SOL', 'ADA', 'ETH', 'HBAR']:
                        # Multiple accounts usually means staking
                        if len(accounts) > 1:
                            is_staked = True
                        # Single account but could still be staked based on patterns
                        elif staking_patterns or total_amount > 0.1:
                            is_staked = True
                    else:
                        is_staked = len(accounts) > 1 or staking_patterns
                    
                    # Get asset name
                    asset_name = market_info.get('name', symbol)
                    if not asset_name or asset_name == symbol:
                        # Fallback names for assets not in market data
                        name_mapping = {
                            'HBAR': 'Hedera',
                            'BTC': 'Bitcoin',
                            'ETH': 'Ethereum'
                        }
                        asset_name = name_mapping.get(symbol, symbol)
                    
                    if is_staked:
                        asset_name += f" (Staked)"
                    
                    # Add to holdings
                    holdings.append({
                        'symbol': symbol,
                        'name': asset_name,
                        'amount': total_amount,
                        'current_price': current_price,
                        'value': value,
                        'change_24h': market_info.get('change_24h', 0),
                        'allocation': 0,  # Will be calculated after total_value is known
                        'accounts': len(accounts),
                        'is_staked': is_staked,
                        'source': market_info.get('source', 'Cross-converted' if symbol in missing_assets else 'Luno')
                    })
                else:
                    print(f"Warning: Could not get price for {symbol} with balance {total_amount}")
            
                    
                    holdings.append({
                        'symbol': symbol,
                        'name': asset_name,
                        'amount': total_amount,
                        'current_price': current_price,
                        'value': value,
                        'change_24h': market_info.get('change_24h', 0),
                        'allocation': 0,  # Will be calculated after total_value is known
                        'accounts': len(accounts),
                        'is_staked': is_staked,
                        'source': market_info.get('source', 'Unknown')
                    })
            
            # Calculate allocations
            for holding in holdings:
                holding['allocation'] = (holding['value'] / total_value) * 100 if total_value > 0 else 0
            
            return {
                'total_value': total_value,
                'currency': 'ZAR',
                'holdings': holdings,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting portfolio data: {e}")
            return {
                'total_value': 0,
                'currency': 'ZAR',
                'holdings': [],
                'last_updated': datetime.now().isoformat()
            }
    
    async def place_market_order(self, pair: str, order_type: str, amount: float) -> Dict:
        """Place a market order (buy/sell immediately at current price)"""
        try:
            data = {
                'pair': pair,
                'type': order_type.upper(),
            }
            
            if order_type.upper() == 'BUY':
                data['counter_volume'] = str(amount)  # Amount in ZAR to spend
            else:
                data['base_volume'] = str(amount)    # Amount of crypto to sell
            
            result = await self._make_request('marketorder', method='POST', data=data)
            return result
            
        except Exception as e:
            print(f"Error placing market order: {e}")
            return {'error': str(e)}
    
    async def place_limit_order(self, pair: str, order_type: str, volume: float, price: float) -> Dict:
        """Place a limit order (buy/sell at specific price)"""
        try:
            data = {
                'pair': pair,
                'type': 'BID' if order_type.upper() == 'BUY' else 'ASK',
                'volume': str(volume),
                'price': str(price)
            }
            
            result = await self._make_request('postorder', method='POST', data=data)
            return result
            
        except Exception as e:
            print(f"Error placing limit order: {e}")
            return {'error': str(e)}
    
    async def get_order_book(self, pair: str) -> Dict:
        """Get order book for a specific trading pair"""
        try:
            return await self._make_request('orderbook', {'pair': pair})
        except Exception as e:
            print(f"Error getting order book: {e}")
            return {'error': str(e)}
    
    async def get_trading_pairs(self) -> List[str]:
        """Get all available trading pairs"""
        try:
            tickers = await self._make_request('tickers')
            pairs = [ticker['pair'] for ticker in tickers.get('tickers', [])]
            return sorted(pairs)
        except Exception as e:
            print(f"Error getting trading pairs: {e}")
            return []
    
    async def get_order_history(self, pair: str = None, limit: int = 100) -> List[Dict]:
        """Get order history"""
        try:
            params = {'limit': limit}
            if pair:
                params['pair'] = pair
            
            orders = await self._make_request('listorders', params)
            return orders.get('orders', [])
        except Exception as e:
            print(f"Error getting order history: {e}")
            return []
    
    async def close_session(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None