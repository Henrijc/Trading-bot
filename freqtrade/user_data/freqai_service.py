"""
FreqAI Integration Service
Machine Learning predictions for Luno trading using Google Gemini API
"""

import asyncio
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pickle
from pathlib import Path
import sys
import os

# Add backend services to path
sys.path.append('/app/backend')
from services.historical_data_service import HistoricalDataService

# Machine learning imports
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib

logger = logging.getLogger(__name__)

class FreqAIService:
    """
    FreqAI-inspired service for AI-driven trading predictions
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.historical_service = HistoricalDataService()
        self.model_dir = Path("/app/freqtrade/user_data/models")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Model parameters
        self.feature_columns = []
        self.target_periods = [2, 5, 10, 20]  # Prediction horizons in candles
        self.pairs = ["BTC/ZAR", "ETH/ZAR", "XRP/ZAR"]
        
        logger.info("FreqAI Service initialized")
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive features for machine learning
        """
        try:
            features_df = df.copy()
            
            # Technical indicators as features
            # RSI
            delta = features_df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            features_df['rsi'] = 100 - (100 / (1 + rs))
            
            # Moving averages
            for period in [10, 20, 50]:
                features_df[f'sma_{period}'] = features_df['close'].rolling(window=period).mean()
                features_df[f'ema_{period}'] = features_df['close'].ewm(span=period).mean()
            
            # MACD
            ema12 = features_df['close'].ewm(span=12).mean()
            ema26 = features_df['close'].ewm(span=26).mean()
            features_df['macd'] = ema12 - ema26
            features_df['macd_signal'] = features_df['macd'].ewm(span=9).mean()
            features_df['macd_hist'] = features_df['macd'] - features_df['macd_signal']
            
            # Bollinger Bands
            sma20 = features_df['close'].rolling(window=20).mean()
            std20 = features_df['close'].rolling(window=20).std()
            features_df['bb_upper'] = sma20 + (std20 * 2)
            features_df['bb_lower'] = sma20 - (std20 * 2)
            features_df['bb_percent'] = (features_df['close'] - features_df['bb_lower']) / (features_df['bb_upper'] - features_df['bb_lower'])
            features_df['bb_width'] = (features_df['bb_upper'] - features_df['bb_lower']) / sma20
            
            # Price-based features
            features_df['price_change'] = features_df['close'].pct_change()
            features_df['high_low_ratio'] = features_df['high'] / features_df['low']
            features_df['close_open_ratio'] = features_df['close'] / features_df['open']
            
            # Volume features
            features_df['volume_sma'] = features_df['volume'].rolling(window=20).mean()
            features_df['volume_ratio'] = features_df['volume'] / features_df['volume_sma']
            
            # Momentum features
            for period in [5, 10, 20]:
                features_df[f'momentum_{period}'] = features_df['close'] / features_df['close'].shift(period) - 1
            
            # Volatility features
            for period in [5, 10, 20]:
                features_df[f'volatility_{period}'] = features_df['price_change'].rolling(window=period).std()
            
            # Support/Resistance approximation
            features_df['resistance'] = features_df['high'].rolling(window=20).max()
            features_df['support'] = features_df['low'].rolling(window=20).min()
            features_df['price_to_resistance'] = features_df['close'] / features_df['resistance']
            features_df['price_to_support'] = features_df['close'] / features_df['support']
            
            # Time-based features
            features_df['hour'] = pd.to_datetime(features_df.index).hour if hasattr(features_df.index, 'hour') else 0
            features_df['day_of_week'] = pd.to_datetime(features_df.index).dayofweek if hasattr(features_df.index, 'dayofweek') else 0
            
            # Drop non-feature columns and handle NaN values
            feature_columns = [col for col in features_df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
            features_df = features_df[feature_columns].fillna(method='ffill').fillna(0)
            
            self.feature_columns = feature_columns
            
            logger.info(f"Created {len(feature_columns)} features for ML model")
            return features_df
            
        except Exception as e:
            logger.error(f"Error creating features: {e}")
            return pd.DataFrame()
    
    def create_targets(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Create target variables for different prediction horizons
        """
        targets = {}
        
        for period in self.target_periods:
            # Calculate future return over 'period' candles
            targets[f'target_roc_{period}'] = (
                df['close'].shift(-period) / df['close'] - 1
            )
        
        return targets
    
    async def prepare_training_data(self, pair: str, days: int = 365) -> Tuple[pd.DataFrame, Dict[str, pd.Series]]:
        """
        Prepare comprehensive training data for a specific pair
        """
        try:
            logger.info(f"Preparing training data for {pair}")
            
            # Get historical data using the correct method
            symbol = pair.replace("/", "")  # BTC/ZAR -> BTCZAR
            df = await self.historical_service.fetch_historical_data(symbol, timeframe='1h', days_back=days)
            
            if df.empty:
                logger.error(f"No historical data available for {pair}")
                return pd.DataFrame(), {}
            
            # Create features
            features_df = self.create_features(df)
            
            # Create targets
            targets = self.create_targets(df)
            
            logger.info(f"Training data prepared for {pair}: {len(features_df)} samples, {len(self.feature_columns)} features")
            
            return features_df, targets
            
        except Exception as e:
            logger.error(f"Error preparing training data for {pair}: {e}")
            return pd.DataFrame(), {}
    
    async def train_model(self, pair: str, retrain: bool = False) -> bool:
        """
        Train machine learning model for a specific pair
        """
        try:
            model_path = self.model_dir / f"{pair.replace('/', '_')}_model.pkl"
            scaler_path = self.model_dir / f"{pair.replace('/', '_')}_scaler.pkl"
            
            # Check if model exists and retrain is False
            if model_path.exists() and not retrain:
                logger.info(f"Model for {pair} already exists, loading existing model")
                self.models[pair] = joblib.load(model_path)
                self.scalers[pair] = joblib.load(scaler_path)
                return True
            
            logger.info(f"Training model for {pair}")
            
            # Prepare training data
            features_df, targets = await self.prepare_training_data(pair, days=365)
            
            if features_df.empty or not targets:
                logger.error(f"No training data available for {pair}")
                return False
            
            # Focus on mid-term prediction (5 candles ahead)
            target_col = 'target_roc_5'
            if target_col not in targets:
                logger.error(f"Target column {target_col} not found")
                return False
            
            # Prepare final training dataset
            y = targets[target_col].dropna()
            X = features_df.loc[y.index]
            
            # Remove any remaining NaN values
            mask = ~(X.isna().any(axis=1) | y.isna())
            X = X[mask]
            y = y[mask]
            
            if len(X) < 100:
                logger.error(f"Insufficient training data for {pair}: {len(X)} samples")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, shuffle=False  # Don't shuffle time series data
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model (using Gradient Boosting which works well for financial data)
            model = GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            logger.info(f"Model trained for {pair}: MSE={mse:.6f}, MAE={mae:.6f}")
            
            # Save model and scaler
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            # Store in memory
            self.models[pair] = model
            self.scalers[pair] = scaler
            
            # Save training metadata
            metadata = {
                'pair': pair,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'features': self.feature_columns,
                'mse': mse,
                'mae': mae,
                'trained_at': datetime.utcnow().isoformat()
            }
            
            metadata_path = self.model_dir / f"{pair.replace('/', '_')}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Model successfully trained and saved for {pair}")
            return True
            
        except Exception as e:
            logger.error(f"Error training model for {pair}: {e}")
            return False
    
    async def get_prediction(self, pair: str, current_data: pd.DataFrame) -> Dict[str, float]:
        """
        Get AI prediction for a specific pair
        """
        try:
            if pair not in self.models:
                # Try to load existing model
                model_path = self.model_dir / f"{pair.replace('/', '_')}_model.pkl"
                scaler_path = self.model_dir / f"{pair.replace('/', '_')}_scaler.pkl"
                
                if model_path.exists() and scaler_path.exists():
                    self.models[pair] = joblib.load(model_path)
                    self.scalers[pair] = joblib.load(scaler_path)
                else:
                    # Train model if it doesn't exist
                    if not await self.train_model(pair):
                        return {'error': 'Failed to train model'}
            
            # Create features for current data
            features_df = self.create_features(current_data)
            
            if features_df.empty:
                return {'error': 'Failed to create features'}
            
            # Get latest features
            latest_features = features_df.iloc[-1:][self.feature_columns]
            
            # Handle missing columns
            for col in self.feature_columns:
                if col not in latest_features.columns:
                    latest_features[col] = 0
            
            # Scale features
            latest_features_scaled = self.scalers[pair].transform(latest_features[self.feature_columns])
            
            # Make prediction
            prediction = self.models[pair].predict(latest_features_scaled)[0]
            
            # Calculate confidence (simplified approach)
            # In production, this would use more sophisticated confidence estimation
            confidence = min(abs(prediction) * 10, 1.0)  # Simple confidence based on prediction magnitude
            
            result = {
                'prediction_roc_5': prediction,
                'confidence': confidence,
                'signal_strength': 'strong' if confidence > 0.7 else 'medium' if confidence > 0.4 else 'weak',
                'direction': 'bullish' if prediction > 0.01 else 'bearish' if prediction < -0.01 else 'neutral',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Prediction for {pair}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting prediction for {pair}: {e}")
            return {'error': str(e)}
    
    async def train_all_models(self) -> Dict[str, bool]:
        """
        Train models for all trading pairs
        """
        results = {}
        
        for pair in self.pairs:
            logger.info(f"Training model for {pair}")
            results[pair] = await self.train_model(pair, retrain=True)
        
        return results
    
    def get_model_status(self) -> Dict[str, Dict]:
        """
        Get status of all trained models
        """
        status = {}
        
        for pair in self.pairs:
            model_path = self.model_dir / f"{pair.replace('/', '_')}_model.pkl"
            metadata_path = self.model_dir / f"{pair.replace('/', '_')}_metadata.json"
            
            if model_path.exists():
                status[pair] = {
                    'trained': True,
                    'model_path': str(model_path),
                    'model_size': model_path.stat().st_size,
                    'loaded_in_memory': pair in self.models
                }
                
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        status[pair].update(metadata)
                    except Exception as e:
                        logger.error(f"Error reading metadata for {pair}: {e}")
            else:
                status[pair] = {
                    'trained': False,
                    'loaded_in_memory': False
                }
        
        return status