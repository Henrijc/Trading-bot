import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
import httpx
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class FreqTradeController:
    """
    Controller for FreqTrade integration
    Manages FreqTrade bot lifecycle and API communication
    """
    
    def __init__(self):
        self.base_url = "http://localhost:8080"  # FreqTrade API endpoint
        self.jwt_secret = os.environ.get('FREQTRADE_JWT_SECRET', 'freqtrade_jwt_secret_key')
        self.is_running = False
        self.config_path = Path(__file__).parent / "config.json"
        self.strategy_path = Path(__file__).parent / "strategies"
        
    async def start(self) -> Dict[str, Any]:
        """Start FreqTrade bot"""
        try:
            # Check if already running
            status = await self.get_status()
            if status and status.get('runmode') == 'live':
                self.is_running = True
                return {"status": "success", "message": "FreqTrade already running"}
                
            # Start FreqTrade process (this would be handled by supervisor in production)
            # For now, we'll mark it as running and assume external process management
            self.is_running = True
            
            logger.info("FreqTrade started")
            return {"status": "success", "message": "FreqTrade started successfully"}
            
        except Exception as e:
            logger.error(f"Failed to start FreqTrade: {e}")
            return {"status": "error", "message": str(e)}
            
    async def stop(self) -> Dict[str, Any]:
        """Stop FreqTrade bot"""
        try:
            # Send stop command to FreqTrade
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.jwt_secret}"}
                async with session.post(f"{self.base_url}/api/v1/stop", headers=headers) as response:
                    if response.status == 200:
                        self.is_running = False
                        return {"status": "success", "message": "FreqTrade stopped"}
                    else:
                        return {"status": "error", "message": f"Failed to stop FreqTrade: {response.status}"}
                        
        except Exception as e:
            logger.error(f"Failed to stop FreqTrade: {e}")
            self.is_running = False  # Assume stopped if we can't communicate
            return {"status": "error", "message": str(e)}
            
    async def get_status(self) -> Optional[Dict[str, Any]]:
        """Get FreqTrade status"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.jwt_secret}"}
                async with session.get(f"{self.base_url}/api/v1/status", headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to get FreqTrade status: {e}")
            return None
            
    async def get_performance(self) -> Dict[str, Any]:
        """Get performance metrics from FreqTrade"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.jwt_secret}"}
                
                # Get multiple endpoints
                endpoints = {
                    "profit": "/api/v1/profit",
                    "performance": "/api/v1/performance",
                    "trades": "/api/v1/trades",
                    "balance": "/api/v1/balance"
                }
                
                results = {}
                for key, endpoint in endpoints.items():
                    try:
                        async with session.get(f"{self.base_url}{endpoint}", headers=headers) as response:
                            if response.status == 200:
                                results[key] = await response.json()
                    except Exception as e:
                        logger.warning(f"Failed to get {key}: {e}")
                        results[key] = None
                        
                return results
                
        except Exception as e:
            logger.error(f"Failed to get FreqTrade performance: {e}")
            return {}
            
    async def force_entry(self, pair: str, side: str, price: float = None) -> Dict[str, Any]:
        """Force entry into a trade"""
        try:
            data = {
                "pair": pair,
                "side": side
            }
            if price:
                data["price"] = price
                
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.jwt_secret}"}
                async with session.post(
                    f"{self.base_url}/api/v1/forceenter",
                    json=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {"status": "error", "message": error_text}
                        
        except Exception as e:
            logger.error(f"Failed to force entry: {e}")
            return {"status": "error", "message": str(e)}
            
    async def force_exit(self, trade_id: int) -> Dict[str, Any]:
        """Force exit from a trade"""
        try:
            data = {"tradeid": trade_id}
            
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.jwt_secret}"}
                async with session.post(
                    f"{self.base_url}/api/v1/forceexit",
                    json=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {"status": "error", "message": error_text}
                        
        except Exception as e:
            logger.error(f"Failed to force exit: {e}")
            return {"status": "error", "message": str(e)}
            
    async def get_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trades"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.jwt_secret}"}
                params = {"limit": limit}
                
                async with session.get(
                    f"{self.base_url}/api/v1/trades",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('trades', [])
                    else:
                        return []
                        
        except Exception as e:
            logger.error(f"Failed to get trades: {e}")
            return []
            
    async def get_strategies(self) -> List[str]:
        """Get available strategies"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.jwt_secret}"}
                
                async with session.get(f"{self.base_url}/api/v1/strategies", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('strategies', [])
                    else:
                        return []
                        
        except Exception as e:
            logger.error(f"Failed to get strategies: {e}")
            return []
            
    async def backtest(self, strategy: str, timerange: str = None) -> Dict[str, Any]:
        """Run backtest"""
        try:
            data = {
                "strategy": strategy,
                "timerange": timerange or "20240101-20241201"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                headers = {"Authorization": f"Bearer {self.jwt_secret}"}
                
                async with session.post(
                    f"{self.base_url}/api/v1/backtest",
                    json=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {"status": "error", "message": error_text}
                        
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return {"status": "error", "message": str(e)}
            
    def generate_config(self, config_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate FreqTrade configuration"""
        default_config = {
            "max_open_trades": config_params.get("max_open_trades", 3),
            "stake_currency": "ZAR",
            "stake_amount": config_params.get("stake_amount", 1000),
            "tradable_balance_ratio": 0.99,
            "fiat_display_currency": "ZAR",
            "timeframe": "5m",
            "dry_run": config_params.get("dry_run", True),
            "cancel_open_orders_on_exit": True,
            "process_only_new_candles": True,
            "minimal_roi": {
                "60": 0.01,
                "30": 0.02,
                "0": config_params.get("take_profit_percent", 3.0) / 100
            },
            "stoploss": -(config_params.get("stop_loss_percent", 1.5) / 100),
            "trailing_stop": False,
            "exchange": {
                "name": "binance",  # For data feed
                "key": "",
                "secret": "",
                "ccxt_config": {"enableRateLimit": True, "rateLimit": 200},
                "ccxt_async_config": {"enableRateLimit": True, "rateLimit": 200},
                "pair_whitelist": ["BTC/USDT", "ETH/USDT", "ADA/USDT", "DOT/USDT", "LINK/USDT"],
                "pair_blacklist": [".*UP/.*", ".*DOWN/.*", ".*BEAR/.*", ".*BULL/.*"]
            },
            "api_server": {
                "enabled": True,
                "listen_ip_address": "127.0.0.1",
                "listen_port": 8080,
                "verbosity": "info",
                "enable_openapi": False,
                "jwt_secret_key": self.jwt_secret,
                "CORS_origins": []
            },
            "bot_name": "AI_Crypto_Bot",
            "initial_state": "running",
            "force_entry_enable": True,
            "internals": {
                "process_throttle_secs": 5
            }
        }
        
        # Add FreqAI configuration if enabled
        if config_params.get("enable_freqai", True):
            default_config["freqai"] = {
                "enabled": True,
                "identifier": "ai_crypto_bot",
                "feature_parameters": {
                    "include_timeframes": ["5m", "15m", "1h"],
                    "include_corr_pairlist": ["ETH/USDT", "ADA/USDT", "DOT/USDT"],
                    "label_period_candles": 24,
                    "include_shifted_candles": 2,
                    "DI_threshold": 0.9,
                    "weight_factor": 0.9,
                    "principal_component_analysis": False,
                    "use_SVM_to_remove_outliers": True,
                    "svm_params": {"shuffle": True, "nu": 0.1},
                    "indicator_max_period_candles": 20,
                    "indicator_periods_candles": [10, 20]
                },
                "data_split_parameters": {
                    "test_size": 0.33,
                    "shuffle": False,
                    "random_state": 1
                },
                "model_training_parameters": {
                    "n_estimators": 800
                }
            }
            
        return default_config
        
    async def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
            
    async def reload_config(self) -> Dict[str, Any]:
        """Reload FreqTrade configuration"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.jwt_secret}"}
                
                async with session.post(f"{self.base_url}/api/v1/reload_config", headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {"status": "error", "message": error_text}
                        
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")
            return {"status": "error", "message": str(e)}