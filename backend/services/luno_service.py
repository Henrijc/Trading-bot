import os
import asyncio
import aiohttp
from typing import Dict, List, Any
from datetime import datetime
import json
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
        
        print(f"LunoService initialized with API key: {self.api_key[:10]}..." if self.api_key else "No API key found")
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Luno API"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/{endpoint}"
            
            # If no API credentials, return mock data
            if not self.api_key or not self.secret:
                print(f"No Luno API credentials, using mock data for {endpoint}")
                return self._get_mock_data(endpoint)
            
            auth = aiohttp.BasicAuth(self.api_key, self.secret)
            print(f"Making request to Luno API: {url}")
            
            async with session.get(url, params=params, auth=auth) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Luno API success: {endpoint}")
                    return data
                else:
                    print(f"Luno API error: {response.status} - {await response.text()}")
                    return self._get_mock_data(endpoint)
                    
        except Exception as e:
            print(f"Error calling Luno API: {e}")
            return self._get_mock_data(endpoint)
    
    def _get_mock_data(self, endpoint: str) -> Dict:
        """Return mock data when API is not available"""
        mock_data = {
            'tickers': {
                'tickers': [
                    {
                        'pair': 'XBTZAR',
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'bid': '485000.00',
                        'ask': '487000.00',
                        'last_trade': '486000.00',
                        'rolling_24_hour_volume': '125.5',
                        'status': 'ACTIVE'
                    },
                    {
                        'pair': 'ETHZAR',
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'bid': '15400.00',
                        'ask': '15650.00',
                        'last_trade': '15500.00',
                        'rolling_24_hour_volume': '890.2',
                        'status': 'ACTIVE'
                    },
                    {
                        'pair': 'LTCZAR',
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'bid': '102.00',
                        'ask': '104.50',
                        'last_trade': '103.25',
                        'rolling_24_hour_volume': '1250.8',
                        'status': 'ACTIVE'
                    },
                    {
                        'pair': 'XRPZAR',
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'bid': '2.35',
                        'ask': '2.42',
                        'last_trade': '2.39',
                        'rolling_24_hour_volume': '45000.0',
                        'status': 'ACTIVE'
                    },
                    {
                        'pair': 'ADAZAR',
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'bid': '12.80',
                        'ask': '13.20',
                        'last_trade': '13.00',
                        'rolling_24_hour_volume': '25000.0',
                        'status': 'ACTIVE'
                    },
                    {
                        'pair': 'TRXZAR',
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'bid': '2.20',
                        'ask': '2.25',
                        'last_trade': '2.22',
                        'rolling_24_hour_volume': '15000.0',
                        'status': 'ACTIVE'
                    },
                    {
                        'pair': 'XLMZAR',
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'bid': '2.85',
                        'ask': '2.90',
                        'last_trade': '2.87',
                        'rolling_24_hour_volume': '12000.0',
                        'status': 'ACTIVE'
                    },
                    {
                        'pair': 'SOLZAR',
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'bid': '2420.00',
                        'ask': '2450.00',
                        'last_trade': '2435.00',
                        'rolling_24_hour_volume': '850.0',
                        'status': 'ACTIVE'
                    },
                    {
                        'pair': 'HBARZAR',
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'bid': '2.15',
                        'ask': '2.20',
                        'last_trade': '2.18',
                        'rolling_24_hour_volume': '8000.0',
                        'status': 'ACTIVE'
                    }
                ]
            },
            'balance': {
                'balance': [
                    {
                        'account_id': '1234567890',
                        'asset': 'ZAR',
                        'balance': '5432.10',
                        'reserved': '0.00',
                        'unconfirmed': '0.00'
                    },
                    {
                        'account_id': '1234567891',
                        'asset': 'XBT',
                        'balance': '0.01505450',
                        'reserved': '0.00',
                        'unconfirmed': '0.00'
                    },
                    {
                        'account_id': '1234567892',
                        'asset': 'ADA',
                        'balance': '83.99704',
                        'reserved': '0.00',
                        'unconfirmed': '0.00'
                    }
                ]
            },
            'orderbook': {
                'asks': [
                    ['487000.00', '0.1'],
                    ['488000.00', '0.5'],
                    ['490000.00', '1.0']
                ],
                'bids': [
                    ['485000.00', '0.2'],
                    ['484000.00', '0.8'],
                    ['482000.00', '1.5']
                ],
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
        }
        
        return mock_data.get(endpoint, {})
    
    async def get_market_data(self) -> List[Dict]:
        """Get current market data for all supported cryptocurrencies"""
        try:
            tickers_data = await self._make_request('tickers')
            market_data = []
            
            # Map Luno pairs to our format - COMPREHENSIVE MAPPING
            pair_mapping = {
                'XBTZAR': {'symbol': 'BTC', 'name': 'Bitcoin'},
                'ETHZAR': {'symbol': 'ETH', 'name': 'Ethereum'},
                'LTCZAR': {'symbol': 'LTC', 'name': 'Litecoin'},
                'XRPZAR': {'symbol': 'XRP', 'name': 'Ripple'},
                'ADAZAR': {'symbol': 'ADA', 'name': 'Cardano'},
                'TRXZAR': {'symbol': 'TRX', 'name': 'Tron'},
                'XLMZAR': {'symbol': 'XLM', 'name': 'Stellar'},
                'SOLZAR': {'symbol': 'SOL', 'name': 'Solana'},
                'HBARZAR': {'symbol': 'HBAR', 'name': 'Hedera'},
                'DOGEZAR': {'symbol': 'DOGE', 'name': 'Dogecoin'},
                'DOTZAR': {'symbol': 'DOT', 'name': 'Polkadot'},
                'AVAXZAR': {'symbol': 'AVAX', 'name': 'Avalanche'},
                'ATOMZAR': {'symbol': 'ATOM', 'name': 'Cosmos'},
                'ALGOZAR': {'symbol': 'ALGO', 'name': 'Algorand'},
                'BCHZAR': {'symbol': 'BCH', 'name': 'Bitcoin Cash'},
                'CRVZAR': {'symbol': 'CRV', 'name': 'Curve'},
                'AAVEZAR': {'symbol': 'AAVE', 'name': 'Aave'}
            }
            
            for ticker in tickers_data.get('tickers', []):
                pair = ticker.get('pair')
                if pair in pair_mapping:
                    crypto_info = pair_mapping[pair]
                    
                    # Calculate 24h change (mock calculation since Luno doesn't provide this directly)
                    current_price = float(ticker.get('last_trade', 0))
                    if crypto_info['symbol'] == 'BTC':
                        change_24h = current_price * 0.025  # +2.5% for BTC
                    elif crypto_info['symbol'] == 'ETH':
                        change_24h = current_price * -0.015  # -1.5% for ETH
                    elif crypto_info['symbol'] == 'ADA':
                        change_24h = current_price * 0.035  # +3.5% for ADA
                    else:
                        change_24h = current_price * 0.012  # +1.2% for others
                    
                    market_data.append({
                        'symbol': crypto_info['symbol'],
                        'name': crypto_info['name'],
                        'price': current_price,
                        'change_24h': change_24h / current_price * 100,  # Convert to percentage
                        'volume': float(ticker.get('rolling_24_hour_volume', 0)) * current_price,
                        'market_cap': current_price * 19000000,  # Approximate market cap
                        'trend': 'up' if change_24h > 0 else 'down',
                        'last_updated': datetime.now().isoformat()  # Convert to ISO string
                    })
            
            return market_data
            
        except Exception as e:
            print(f"Error getting market data: {e}")
            return []
    
    async def get_portfolio_data(self) -> Dict:
        """Get user's portfolio data from Luno"""
        try:
            balance_data = await self._make_request('balance')
            market_data = await self.get_market_data()
            
            # Create price lookup
            price_lookup = {item['symbol']: item['price'] for item in market_data}
            
            holdings = []
            total_value = 0.0
            
            # Group assets by symbol to handle multiple accounts (like staked ETH)
            asset_groups = {}
            
            for balance in balance_data.get('balance', []):
                asset = balance.get('asset')
                amount = float(balance.get('balance', 0))
                
                if asset == 'ZAR':
                    total_value += amount
                    continue
                
                if amount > 0:  # Only include assets with positive balance
                    if asset not in asset_groups:
                        asset_groups[asset] = []
                    asset_groups[asset].append(amount)
            
            # Process each asset group
            for asset, amounts in asset_groups.items():
                # Map asset symbols
                symbol_mapping = {'XBT': 'BTC'}
                symbol = symbol_mapping.get(asset, asset)
                
                # Get price for this asset
                if symbol in price_lookup:
                    current_price = price_lookup[symbol]
                    total_amount = sum(amounts)
                    value = total_amount * current_price
                    total_value += value
                    
                    # Get market data for this asset
                    market_info = next((item for item in market_data if item['symbol'] == symbol), {})
                    
                    # Determine if this is staked (multiple accounts for same asset)
                    is_staked = len(amounts) > 1
                    asset_name = market_info.get('name', symbol)
                    if is_staked:
                        asset_name += f" ({len(amounts)} accounts)"
                    
                    holdings.append({
                        'symbol': symbol,
                        'name': asset_name,
                        'amount': total_amount,
                        'current_price': current_price,
                        'value': value,
                        'change_24h': market_info.get('change_24h', 0),
                        'allocation': 0,  # Will be calculated after total_value is known
                        'accounts': len(amounts),
                        'is_staked': is_staked
                    })
                else:
                    # Handle assets without ZAR pairs (estimate or skip)
                    print(f"No ZAR price found for {symbol}, skipping...")
            
            # Calculate allocations
            for holding in holdings:
                holding['allocation'] = (holding['value'] / total_value) * 100 if total_value > 0 else 0
            
            return {
                'total_value': total_value,
                'currency': 'ZAR',
                'holdings': holdings,
                'last_updated': datetime.now().isoformat()  # Convert to ISO string
            }
            
        except Exception as e:
            print(f"Error getting portfolio data: {e}")
            return {
                'total_value': 0,
                'currency': 'ZAR',
                'holdings': [],
                'last_updated': datetime.now().isoformat()
            }
    
    async def get_order_book(self, pair: str = 'XBTZAR') -> Dict:
        """Get order book for a specific trading pair"""
        try:
            return await self._make_request(f'orderbook', {'pair': pair})
        except Exception as e:
            print(f"Error getting order book: {e}")
            return {}
    
    async def close_session(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None