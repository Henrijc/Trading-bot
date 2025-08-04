import asyncio
import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pickle
import os
from pathlib import Path
import ccxt.async_support as ccxt

# Machine learning imports
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pandas_ta as ta

logger = logging.getLogger(__name__)

class FreqAITradingStrategy:
    """
    Advanced AI trading strategy using machine learning for cryptocurrency trading
    Integrates with multiple exchanges for data and uses ML models for predictions
    """
    
    def __init__(self):
        self.is_trading_active = False
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.last_retrain_time = None
        self.next_retrain_time = None
        self.model_confidence = 0.0
        self.models_path = Path(__file__).parent / "models"
        self.models_path.mkdir(exist_ok=True)
        
        # Trading parameters
        self.lookback_periods = 50
        self.prediction_horizon = 24  # Hours
        self.confidence_threshold = 0.7
        self.max_position_size = 0.05  # 5% of portfolio per position
        
        # Initialize exchange for data fetching (Binance for OHLCV data)
        self.exchange = None
        self.supported_pairs = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT']
        
        # Model ensemble
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression()
        }
        
        self.model_weights = {'random_forest': 0.4, 'gradient_boost': 0.4, 'linear_regression': 0.2}
        
    async def initialize_exchange(self):
        """Initialize exchange connection"""
        try:
            if self.exchange is None:
                self.exchange = ccxt.binance({
                    'apiKey': os.environ.get('BINANCE_API_KEY', ''),
                    'secret': os.environ.get('BINANCE_SECRET', ''),
                    'sandbox': True,  # Use sandbox for testing
                    'enableRateLimit': True,
                })
                await self.exchange.load_markets()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            return False
            
    async def get_market_data(self, symbol: str, timeframe: str = '5m', limit: int = 1000) -> pd.DataFrame:
        """Fetch OHLCV data from exchange"""
        try:
            await self.initialize_exchange()
            
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch market data for {symbol}: {e}")
            return pd.DataFrame()
            
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for feature engineering"""
        try:
            # Price-based indicators
            df['sma_10'] = ta.sma(df['close'], length=10)
            df['sma_20'] = ta.sma(df['close'], length=20)
            df['sma_50'] = ta.sma(df['close'], length=50)
            
            df['ema_10'] = ta.ema(df['close'], length=10)
            df['ema_20'] = ta.ema(df['close'], length=20)
            
            # RSI
            df['rsi'] = ta.rsi(df['close'], length=14)
            df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
            df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
            
            # MACD
            macd_data = ta.macd(df['close'])
            if isinstance(macd_data, pd.DataFrame):
                df['macd'] = macd_data['MACD_12_26_9']
                df['macd_signal'] = macd_data['MACDs_12_26_9']
                df['macd_histogram'] = macd_data['MACDh_12_26_9']
            
            # Bollinger Bands
            bb_data = ta.bbands(df['close'])
            if isinstance(bb_data, pd.DataFrame):
                df['bb_upper'] = bb_data['BBU_20_2.0']
                df['bb_middle'] = bb_data['BBM_20_2.0']
                df['bb_lower'] = bb_data['BBL_20_2.0']
                df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            
            # Volume indicators
            df['volume_sma'] = ta.sma(df['volume'], length=20)
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Price changes
            df['price_change_1h'] = df['close'].pct_change(periods=12)  # 5m * 12 = 1h
            df['price_change_4h'] = df['close'].pct_change(periods=48)  # 5m * 48 = 4h
            df['price_change_24h'] = df['close'].pct_change(periods=288)  # 5m * 288 = 24h
            
            # Volatility
            df['volatility'] = df['close'].rolling(window=20).std()
            
            # Support and resistance levels
            df['high_20'] = df['high'].rolling(window=20).max()
            df['low_20'] = df['low'].rolling(window=20).min()
            df['support_resistance_ratio'] = (df['close'] - df['low_20']) / (df['high_20'] - df['low_20'])
            
            # Momentum indicators
            df['momentum'] = df['close'] / df['close'].shift(10)
            df['roc'] = ta.roc(df['close'], length=10)  # Rate of Change
            
            # Time-based features
            df['hour'] = df.index.hour
            df['day_of_week'] = df.index.dayofweek
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to calculate technical indicators: {e}")
            return df
            
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Prepare feature matrix for machine learning"""
        try:
            # Calculate technical indicators
            df_features = self.calculate_technical_indicators(df.copy())
            
            # Define feature columns
            feature_columns = [
                'sma_10', 'sma_20', 'sma_50', 'ema_10', 'ema_20',
                'rsi', 'rsi_oversold', 'rsi_overbought',
                'macd', 'macd_signal', 'macd_histogram',
                'bb_width', 'volume_ratio',
                'price_change_1h', 'price_change_4h', 'price_change_24h',
                'volatility', 'support_resistance_ratio',
                'momentum', 'roc',
                'hour', 'day_of_week', 'is_weekend'
            ]
            
            # Filter existing columns
            existing_features = [col for col in feature_columns if col in df_features.columns]
            
            # Create feature matrix
            X = df_features[existing_features].copy()
            
            # Handle missing values
            X = X.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            return X, existing_features
            
        except Exception as e:
            logger.error(f"Failed to prepare features: {e}")
            return pd.DataFrame(), []
            
    def create_target_variable(self, df: pd.DataFrame, horizon: int = 24) -> pd.Series:
        """Create target variable for prediction (future price movement)"""
        try:
            # Predict price change over the next 'horizon' periods
            future_price = df['close'].shift(-horizon)
            current_price = df['close']
            
            # Calculate percentage change
            price_change_pct = (future_price - current_price) / current_price
            
            return price_change_pct
            
        except Exception as e:
            logger.error(f"Failed to create target variable: {e}")
            return pd.Series()
            
    async def train_models(self, symbol: str = 'BTC/USDT') -> Dict[str, Any]:
        """Train machine learning models"""
        try:
            logger.info(f"Starting model training for {symbol}")
            
            # Fetch historical data
            df = await self.get_market_data(symbol, timeframe='5m', limit=2000)
            if df.empty:
                return {"status": "error", "message": "No data available for training"}
                
            # Prepare features and target
            X, feature_columns = self.prepare_features(df)
            y = self.create_target_variable(df, horizon=self.prediction_horizon)
            
            if X.empty or y.empty:
                return {"status": "error", "message": "Failed to prepare training data"}
                
            # Align data (remove NaN values from target)
            valid_indices = ~(y.isna() | X.isna().any(axis=1))
            X_clean = X[valid_indices]
            y_clean = y[valid_indices]
            
            if len(X_clean) < 100:
                return {"status": "error", "message": "Insufficient clean data for training"}
                
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_clean, y_clean, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train ensemble of models
            model_scores = {}
            trained_models = {}
            
            for model_name, model in self.models.items():
                try:
                    # Train model
                    model.fit(X_train_scaled, y_train)
                    
                    # Make predictions
                    y_pred = model.predict(X_test_scaled)
                    
                    # Calculate metrics
                    mse = mean_squared_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    model_scores[model_name] = {
                        'mse': mse,
                        'r2': r2,
                        'rmse': np.sqrt(mse)
                    }
                    
                    trained_models[model_name] = model
                    
                    logger.info(f"{model_name} - R²: {r2:.4f}, RMSE: {np.sqrt(mse):.4f}")
                    
                except Exception as e:
                    logger.warning(f"Failed to train {model_name}: {e}")
                    continue
                    
            if not trained_models:
                return {"status": "error", "message": "Failed to train any models"}
                
            # Update instance variables
            self.models = trained_models
            self.feature_columns = feature_columns
            self.last_retrain_time = datetime.utcnow()
            self.next_retrain_time = self.last_retrain_time + timedelta(hours=24)
            
            # Calculate overall confidence based on best model performance
            best_r2 = max(score['r2'] for score in model_scores.values() if score['r2'] > 0)
            self.model_confidence = max(0.0, min(1.0, best_r2))
            
            # Save models
            await self.save_models()
            
            return {
                "status": "success",
                "message": "Models trained successfully",
                "model_scores": model_scores,
                "feature_count": len(feature_columns),
                "training_samples": len(X_train),
                "confidence": self.model_confidence
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {"status": "error", "message": str(e)}
            
    async def predict_price_movement(self, symbol: str) -> Dict[str, Any]:
        """Make price movement prediction"""
        try:
            if not self.models or not self.feature_columns:
                return {"error": "Models not trained"}
                
            # Get recent data
            df = await self.get_market_data(symbol, timeframe='5m', limit=100)
            if df.empty:
                return {"error": "No market data available"}
                
            # Prepare features
            X, _ = self.prepare_features(df)
            if X.empty:
                return {"error": "Failed to prepare features"}
                
            # Get the latest data point
            latest_features = X.iloc[-1:][self.feature_columns].fillna(0)
            
            if latest_features.empty:
                return {"error": "No valid features"}
                
            # Scale features
            features_scaled = self.scaler.transform(latest_features)
            
            # Make ensemble prediction
            predictions = {}
            weighted_prediction = 0
            total_weight = 0
            
            for model_name, model in self.models.items():
                try:
                    pred = model.predict(features_scaled)[0]
                    predictions[model_name] = pred
                    
                    weight = self.model_weights.get(model_name, 0.33)
                    weighted_prediction += pred * weight
                    total_weight += weight
                    
                except Exception as e:
                    logger.warning(f"Prediction failed for {model_name}: {e}")
                    continue
                    
            if total_weight == 0:
                return {"error": "All model predictions failed"}
                
            final_prediction = weighted_prediction / total_weight
            
            # Calculate prediction confidence
            prediction_std = np.std(list(predictions.values())) if len(predictions) > 1 else 0
            confidence = max(0.1, min(1.0, self.model_confidence * (1 - prediction_std)))
            
            # Determine trading signal
            signal_threshold = 0.005  # 0.5% price change threshold
            
            if final_prediction > signal_threshold:
                signal = "buy"
                strength = min(abs(final_prediction) / signal_threshold, 3.0)
            elif final_prediction < -signal_threshold:
                signal = "sell" 
                strength = min(abs(final_prediction) / signal_threshold, 3.0)
            else:
                signal = "hold"
                strength = 0.0
                
            return {
                "symbol": symbol,
                "prediction": final_prediction,
                "confidence": confidence,
                "signal": signal,
                "strength": strength,
                "individual_predictions": predictions,
                "timestamp": datetime.utcnow(),
                "current_price": float(df['close'].iloc[-1])
            }
            
        except Exception as e:
            logger.error(f"Price prediction failed: {e}")
            return {"error": str(e)}
            
    async def get_trading_signals(self) -> List[Dict[str, Any]]:
        """Generate trading signals for all supported pairs"""
        signals = []
        
        for pair in self.supported_pairs:
            try:
                prediction = await self.predict_price_movement(pair)
                
                if "error" not in prediction and prediction.get("confidence", 0) > self.confidence_threshold:
                    # Calculate position size based on confidence and risk management
                    position_size = self.calculate_position_size(
                        prediction["confidence"], 
                        prediction["strength"]
                    )
                    
                    if prediction["signal"] in ["buy", "sell"] and position_size > 0:
                        signal = {
                            "pair": pair.replace("/", ""),  # Convert to Luno format
                            "side": prediction["signal"],
                            "amount": position_size,
                            "confidence": prediction["confidence"],
                            "expected_return": prediction["prediction"],
                            "timestamp": prediction["timestamp"]
                        }
                        signals.append(signal)
                        
            except Exception as e:
                logger.warning(f"Failed to generate signal for {pair}: {e}")
                continue
                
        return signals
        
    def calculate_position_size(self, confidence: float, strength: float) -> float:
        """Calculate position size based on confidence and signal strength"""
        try:
            # Base position size scaled by confidence and strength
            base_size = self.max_position_size
            
            # Adjust for confidence (higher confidence = larger position)
            confidence_multiplier = confidence
            
            # Adjust for signal strength (stronger signal = larger position)
            strength_multiplier = min(strength / 2.0, 1.0)
            
            position_size = base_size * confidence_multiplier * strength_multiplier
            
            # Minimum position size threshold
            min_size = 0.001
            
            return max(position_size, min_size) if position_size >= min_size else 0.0
            
        except Exception as e:
            logger.error(f"Position size calculation failed: {e}")
            return 0.0
            
    async def start_trading(self):
        """Start automated trading"""
        self.is_trading_active = True
        logger.info("AI trading started")
        
    async def stop_trading(self):
        """Stop automated trading"""
        self.is_trading_active = False
        logger.info("AI trading stopped")
        
    async def get_status(self) -> Dict[str, Any]:
        """Get current strategy status"""
        return {
            "is_active": self.is_trading_active,
            "models_trained": len(self.models) > 0,
            "confidence": self.model_confidence,
            "last_retrain": self.last_retrain_time,
            "next_retrain": self.next_retrain_time,
            "supported_pairs": self.supported_pairs
        }
        
    async def get_current_predictions(self) -> List[Dict[str, Any]]:
        """Get current predictions for all pairs"""
        predictions = []
        
        for pair in self.supported_pairs:
            try:
                pred = await self.predict_price_movement(pair)
                if "error" not in pred:
                    predictions.append(pred)
            except Exception as e:
                logger.warning(f"Failed to get prediction for {pair}: {e}")
                
        return predictions
        
    def get_model_confidence(self) -> float:
        """Get current model confidence"""
        return self.model_confidence
        
    async def get_active_trades(self) -> List[Dict[str, Any]]:
        """Get active trading positions (placeholder for now)"""
        # This would integrate with actual position tracking
        return []
        
    async def update_config(self, config: Dict[str, Any]):
        """Update strategy configuration"""
        try:
            if "max_position_size" in config:
                self.max_position_size = config["max_position_size"] / 100  # Convert from percentage
                
            if "confidence_threshold" in config:
                self.confidence_threshold = config["confidence_threshold"]
                
            if "prediction_horizon" in config:
                self.prediction_horizon = config["prediction_horizon"]
                
            logger.info("AI strategy configuration updated")
            
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            raise
            
    async def save_models(self):
        """Save trained models to disk"""
        try:
            model_data = {
                "models": self.models,
                "scaler": self.scaler,
                "feature_columns": self.feature_columns,
                "model_confidence": self.model_confidence,
                "last_retrain_time": self.last_retrain_time
            }
            
            model_file = self.models_path / "ai_trading_models.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(model_data, f)
                
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
            
    async def load_models(self):
        """Load trained models from disk"""
        try:
            model_file = self.models_path / "ai_trading_models.pkl"
            
            if model_file.exists():
                with open(model_file, 'rb') as f:
                    model_data = pickle.load(f)
                    
                self.models = model_data.get("models", {})
                self.scaler = model_data.get("scaler", StandardScaler())
                self.feature_columns = model_data.get("feature_columns", [])
                self.model_confidence = model_data.get("model_confidence", 0.0)
                self.last_retrain_time = model_data.get("last_retrain_time")
                
                logger.info("Models loaded successfully")
                return True
            else:
                logger.info("No saved models found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
            
    async def close(self):
        """Close exchange connections"""
        try:
            if self.exchange:
                await self.exchange.close()
        except Exception as e:
            logger.error(f"Failed to close exchange: {e}")