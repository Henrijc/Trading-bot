"""
Real FreqAI Integration Service
This implements core FreqAI concepts using the actual machine learning approach
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import joblib
import json

# Machine learning imports (FreqAI uses these)
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

logger = logging.getLogger(__name__)

class RealFreqAIService:
    """
    Real FreqAI implementation using actual ML concepts from FreqTrade
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_dir = Path("/app/freqtrade/user_data/models")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Real FreqAI Service initialized")
    
    def feature_engineering(self, df: pd.DataFrame, pair: str) -> pd.DataFrame:
        """
        FreqAI-style feature engineering
        Features are prefixed with '%-' as per FreqAI convention
        """
        try:
            coin = pair.split('/')[0]
            features = df.copy()
            
            # Technical Analysis Features (FreqAI style)
            # RSI variations (fixed parameter)
            for period in [10, 14, 20]:
                delta = features['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()  
                rs = gain / loss
                features[f"%-{coin}rsi-period-{period}"] = 100 - (100 / (1 + rs))
            
            # EMA variations
            for period in [10, 21, 50]:
                features[f"%-{coin}ema-period-{period}"] = features['close'].ewm(span=period).mean()
            
            # SMA variations
            for period in [10, 20, 50]:
                features[f"%-{coin}sma-period-{period}"] = features['close'].rolling(window=period).mean()
            
            # MACD
            ema12 = features['close'].ewm(span=12).mean()
            ema26 = features['close'].ewm(span=26).mean()
            features[f"%-{coin}macd"] = ema12 - ema26
            features[f"%-{coin}macd_signal"] = features[f"%-{coin}macd"].ewm(span=9).mean()
            features[f"%-{coin}macd_hist"] = features[f"%-{coin}macd"] - features[f"%-{coin}macd_signal"]
            
            # Bollinger Bands
            sma20 = features['close'].rolling(window=20).mean()
            std20 = features['close'].rolling(window=20).std()
            features[f"%-{coin}bb_upperband"] = sma20 + (std20 * 2)
            features[f"%-{coin}bb_lowerband"] = sma20 - (std20 * 2)
            features[f"%-{coin}bb_percent"] = (features['close'] - features[f"%-{coin}bb_lowerband"]) / (features[f"%-{coin}bb_upperband"] - features[f"%-{coin}bb_lowerband"])
            
            # Volume features
            features[f"%-{coin}volume_sma"] = features['volume'].rolling(window=20).mean()
            features[f"%-{coin}volume_ratio"] = features['volume'] / features[f"%-{coin}volume_sma"]
            
            # Price action features
            features[f"%-{coin}price_change"] = features['close'].pct_change()
            features[f"%-{coin}high_low_ratio"] = features['high'] / features['low']
            
            # Momentum features
            for period in [10, 14, 20]:
                features[f"%-{coin}momentum-period-{period}"] = features['close'] / features['close'].shift(period) - 1
            
            # Volatility features
            for period in [5, 10, 20]:
                features[f"%-{coin}volatility-period-{period}"] = features['close'].pct_change().rolling(window=period).std()
            
            # Create targets (FreqAI style with '&-' prefix)
            # Classification target: up/down/sideways
            future_return = (features['close'].shift(-5) / features['close'] - 1)
            features[f"&-{coin}up_or_down"] = (future_return > 0.01).astype(int)
            
            # Regression target: future price
            features[f"&-{coin}close_price_5"] = features['close'].shift(-5)
            
            return features
            
        except Exception as e:
            logger.error(f"Error in feature engineering: {e}")
            return df
    
    def train_freqai_model(self, df: pd.DataFrame, pair: str) -> bool:
        """
        Train FreqAI model using actual ML approach
        """
        try:
            logger.info(f"Training FreqAI model for {pair}")
            
            # Feature engineering
            features_df = self.feature_engineering(df, pair)
            
            # Get feature columns (those starting with '%-')
            feature_cols = [col for col in features_df.columns if col.startswith('%-')]
            target_col = [col for col in features_df.columns if col.startswith('&-') and 'up_or_down' in col][0]
            
            if not feature_cols:
                logger.error(f"No features found for {pair}")
                return False
            
            # Prepare data
            X = features_df[feature_cols].fillna(0)
            y = features_df[target_col].fillna(0)
            
            # Remove rows where target is NaN
            mask = ~(X.isna().any(axis=1) | y.isna())
            X = X[mask]
            y = y[mask]
            
            if len(X) < 100:
                logger.error(f"Insufficient data for {pair}: {len(X)} samples")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42, shuffle=False
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train RandomForest (like FreqAI uses)
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, (y_pred > 0.5).astype(int))
            
            logger.info(f"FreqAI model trained for {pair}: Accuracy={accuracy:.3f}")
            
            # Save model and scaler
            model_path = self.model_dir / f"{pair.replace('/', '_')}_freqai_model.joblib"
            scaler_path = self.model_dir / f"{pair.replace('/', '_')}_freqai_scaler.joblib"
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            # Store in memory
            self.models[pair] = model
            self.scalers[pair] = scaler
            
            # Save metadata
            metadata = {
                'pair': pair,
                'features': feature_cols,
                'accuracy': accuracy,
                'trained_at': datetime.utcnow().isoformat(),
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            metadata_path = self.model_dir / f"{pair.replace('/', '_')}_freqai_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error training FreqAI model for {pair}: {e}")
            return False
    
    def get_freqai_prediction(self, df: pd.DataFrame, pair: str) -> Dict:
        """
        Get FreqAI prediction for trading decision
        """
        try:
            # Load model if not in memory
            if pair not in self.models:
                model_path = self.model_dir / f"{pair.replace('/', '_')}_freqai_model.joblib"
                scaler_path = self.model_dir / f"{pair.replace('/', '_')}_freqai_scaler.joblib"
                
                if not (model_path.exists() and scaler_path.exists()):
                    return {'error': 'Model not trained'}
                
                self.models[pair] = joblib.load(model_path)
                self.scalers[pair] = joblib.load(scaler_path)
            
            # Feature engineering
            features_df = self.feature_engineering(df, pair)
            
            # Get latest features
            feature_cols = [col for col in features_df.columns if col.startswith('%-')]
            latest_features = features_df[feature_cols].iloc[-1:]
            
            # Scale and predict
            latest_scaled = self.scalers[pair].transform(latest_features.fillna(0))
            prediction = self.models[pair].predict(latest_scaled)[0]
            
            # FreqAI-style prediction format
            result = {
                'do_predict_up_or_down': prediction,
                'prediction_confidence': min(abs(prediction - 0.5) * 2, 1.0),  # Confidence based on distance from 0.5
                'prediction_signal': 'buy' if prediction > 0.6 else 'sell' if prediction < 0.4 else 'neutral',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting FreqAI prediction for {pair}: {e}")
            return {'error': str(e)}
    
    def get_model_status(self) -> Dict:
        """Get status of all FreqAI models"""
        status = {}
        pairs = ["BTC/ZAR", "ETH/ZAR", "XRP/ZAR"]
        
        for pair in pairs:
            model_path = self.model_dir / f"{pair.replace('/', '_')}_freqai_model.joblib"
            metadata_path = self.model_dir / f"{pair.replace('/', '_')}_freqai_metadata.json"
            
            if model_path.exists():
                status[pair] = {
                    'trained': True,
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
                status[pair] = {'trained': False, 'loaded_in_memory': False}
        
        return status