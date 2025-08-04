import asyncio
import httpx
import hashlib
import hmac
import time
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class LunoClient:
    """
    Async Luno API client for cryptocurrency trading
    """
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.luno.com/api/1"
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    def _generate_signature(self, method: str, path: str, params: str = "", timestamp: int = None) -> str:
        """Generate HMAC signature for Luno API authentication"""
        if timestamp is None:
            timestamp = int(time.time() * 1000)
            
        message = f"{timestamp}{method.upper()}{path}{params}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return signature, timestamp
        
    def _get_auth_headers(self, method: str, path: str, params: str = "") -> Dict[str, str]:
        """Get authentication headers for API requests"""
        signature, timestamp = self._generate_signature(method, path, params)
        
        return {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "X-API-TIMESTAMP": str(timestamp),
            "X-API-SIGNATURE": signature
        }
        
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Make authenticated API request"""
        url = f"{self.base_url}{endpoint}"
        
        # Prepare request parameters
        query_params = params or {}
        request_body = json.dumps(data) if data else ""
        
        # Generate auth headers
        headers = self._get_auth_headers(method, endpoint, request_body)
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, params=query_params, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, params=query_params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Luno API error {e.response.status_code}: {e.response.text}")
            raise Exception(f"Luno API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Luno API request failed: {e}")
            raise
            
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        try:
            response = await self._make_request("GET", "/balance")
            
            # Parse balance data
            balances = {}
            for asset in response.get('balance', []):
                currency = asset['asset']
                balances[f"{currency}_balance"] = float(asset['balance'])
                balances[f"{currency}_reserved"] = float(asset['reserved'])
                balances[f"{currency}_unconfirmed"] = float(asset['unconfirmed_balance'])
                
            logger.info(f"Balance retrieved: {balances}")
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise
            
    async def get_ticker(self, pair: str) -> Dict[str, Any]:
        """Get ticker information for a trading pair"""
        try:
            response = await self._make_request("GET", "/ticker", params={"pair": pair})
            
            ticker_data = {
                "pair": pair,
                "ask": float(response.get('ask', 0)),
                "bid": float(response.get('bid', 0)),
                "last_trade": float(response.get('last_trade', 0)),
                "rolling_24_hour_volume": float(response.get('rolling_24_hour_volume', 0)),
                "status": response.get('status', ''),
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"Ticker for {pair}: {ticker_data}")
            return ticker_data
            
        except Exception as e:
            logger.error(f"Failed to get ticker for {pair}: {e}")
            raise
            
    async def get_orderbook(self, pair: str) -> Dict[str, Any]:
        """Get orderbook for a trading pair"""
        try:
            response = await self._make_request("GET", "/orderbook_top", params={"pair": pair})
            
            orderbook = {
                "pair": pair,
                "asks": [{"price": float(ask['price']), "volume": float(ask['volume'])} 
                        for ask in response.get('asks', [])],
                "bids": [{"price": float(bid['price']), "volume": float(bid['volume'])} 
                        for bid in response.get('bids', [])],
                "timestamp": datetime.utcnow()
            }
            
            return orderbook
            
        except Exception as e:
            logger.error(f"Failed to get orderbook for {pair}: {e}")
            raise
            
    async def place_order(self, pair: str, order_type: str, side: str, volume: float, price: float = None) -> Dict[str, Any]:
        """
        Place a trading order
        
        Args:
            pair: Trading pair (e.g., "XBTZAR", "ETHZAR")
            order_type: "market" or "limit"
            side: "buy" or "sell"
            volume: Amount to trade
            price: Price for limit orders
        """
        try:
            if order_type.lower() == "market":
                return await self._place_market_order(pair, side, volume)
            elif order_type.lower() == "limit":
                if price is None:
                    raise ValueError("Price is required for limit orders")
                return await self._place_limit_order(pair, side, volume, price)
            else:
                raise ValueError(f"Invalid order type: {order_type}")
                
        except Exception as e:
            logger.error(f"Failed to place {order_type} {side} order for {pair}: {e}")
            raise
            
    async def _place_market_order(self, pair: str, side: str, volume: float) -> Dict[str, Any]:
        """Place market order (instant buy/sell)"""
        try:
            if side.lower() == "buy":
                endpoint = "/marketorder"
                data = {
                    "pair": pair,
                    "type": "BUY",
                    "counter_volume": str(volume)  # ZAR amount for buying
                }
            else:  # sell
                endpoint = "/marketorder"
                data = {
                    "pair": pair,
                    "type": "SELL",
                    "base_volume": str(volume)  # Crypto amount for selling
                }
                
            response = await self._make_request("POST", endpoint, data=data)
            
            order_result = {
                "order_id": response.get('order_id'),
                "order_type": "market",
                "side": side,
                "pair": pair,
                "volume": volume,
                "price": float(response.get('base', 0)) / float(response.get('counter', 1)) if response.get('counter') and float(response.get('counter')) != 0 else 0,
                "fee": float(response.get('fee_base', 0)),
                "timestamp": datetime.utcnow(),
                "status": "completed"
            }
            
            logger.info(f"Market order executed: {order_result}")
            return order_result
            
        except Exception as e:
            logger.error(f"Market order failed: {e}")
            raise
            
    async def _place_limit_order(self, pair: str, side: str, volume: float, price: float) -> Dict[str, Any]:
        """Place limit order"""
        try:
            data = {
                "pair": pair,
                "type": "BID" if side.lower() == "buy" else "ASK",
                "volume": str(volume),
                "price": str(price)
            }
            
            response = await self._make_request("POST", "/postorder", data=data)
            
            order_result = {
                "order_id": response.get('order_id'),
                "order_type": "limit",
                "side": side,
                "pair": pair,
                "volume": volume,
                "price": price,
                "timestamp": datetime.utcnow(),
                "status": "pending"
            }
            
            logger.info(f"Limit order placed: {order_result}")
            return order_result
            
        except Exception as e:
            logger.error(f"Limit order failed: {e}")
            raise
            
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get status of a specific order"""
        try:
            response = await self._make_request("GET", f"/orders/{order_id}")
            
            order_status = {
                "order_id": order_id,
                "status": response.get('state', '').lower(),
                "pair": response.get('pair', ''),
                "type": response.get('type', ''),
                "volume": float(response.get('volume', 0)),
                "price": float(response.get('price', 0)),
                "filled_volume": float(response.get('base', 0)),
                "remaining_volume": float(response.get('volume', 0)) - float(response.get('base', 0)),
                "fee": float(response.get('fee_base', 0)),
                "creation_timestamp": response.get('creation_timestamp'),
                "expiration_timestamp": response.get('expiration_timestamp')
            }
            
            return order_status
            
        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            raise
            
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a pending order"""
        try:
            response = await self._make_request("POST", "/stoporder", data={"order_id": order_id})
            
            result = {
                "order_id": order_id,
                "status": "cancelled",
                "success": response.get('success', False),
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"Order cancelled: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
            
    async def get_trades_history(self, pair: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trading history"""
        try:
            params = {"limit": limit}
            if pair:
                params["pair"] = pair
                
            response = await self._make_request("GET", "/listtrades", params=params)
            
            trades = []
            for trade in response.get('trades', []):
                trade_data = {
                    "trade_id": trade.get('sequence'),
                    "order_id": trade.get('order_id'),
                    "pair": trade.get('pair'),
                    "price": float(trade.get('price', 0)),
                    "volume": float(trade.get('volume', 0)),
                    "value": float(trade.get('counter', 0)),
                    "fee": float(trade.get('fee_base', 0)),
                    "is_buy": trade.get('is_buy', False),
                    "timestamp": trade.get('timestamp')
                }
                trades.append(trade_data)
                
            logger.info(f"Retrieved {len(trades)} trades")
            return trades
            
        except Exception as e:
            logger.error(f"Failed to get trades history: {e}")
            raise
            
    async def get_account_transactions(self, min_row: int = 1, max_row: int = 100) -> List[Dict[str, Any]]:
        """Get account transactions"""
        try:
            params = {
                "min_row": min_row,
                "max_row": max_row
            }
            
            response = await self._make_request("GET", "/accounts", params=params)
            
            transactions = []
            for account in response.get('accounts', []):
                for transaction in account.get('transactions', []):
                    transaction_data = {
                        "transaction_id": transaction.get('row_index'),
                        "timestamp": transaction.get('timestamp'),
                        "balance": float(transaction.get('balance', 0)),
                        "available": float(transaction.get('available', 0)),
                        "balance_delta": float(transaction.get('balance_delta', 0)),
                        "available_delta": float(transaction.get('available_delta', 0)),
                        "currency": transaction.get('currency'),
                        "description": transaction.get('description')
                    }
                    transactions.append(transaction_data)
                    
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get account transactions: {e}")
            raise
            
    async def get_supported_pairs(self) -> List[str]:
        """Get list of supported trading pairs"""
        try:
            response = await self._make_request("GET", "/tickers")
            
            pairs = [ticker.get('pair') for ticker in response.get('tickers', [])]
            
            logger.info(f"Supported pairs: {pairs}")
            return pairs
            
        except Exception as e:
            logger.error(f"Failed to get supported pairs: {e}")
            raise
            
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()