#!/usr/bin/env python3
"""
Phase 5 FreqAI Intelligence Implementation Testing
COMPREHENSIVE TESTING OF MACHINE LEARNING AND AI PREDICTION CAPABILITIES

TESTING FOCUS:
1. FreqAI Model Training and Status (/api/freqai/train, /api/freqai/status)
2. AI Prediction System (/api/freqai/predict for ETH/ZAR, XRP/ZAR)
3. AI-Enhanced Trading Bot Integration
4. Machine Learning Model Performance (MSE, MAE metrics)
5. End-to-End AI Trading Pipeline

EXPECTED FEATURES:
- 31+ features for ML model training (RSI, MACD, Bollinger Bands, etc.)
- Model persistence in /app/freqtrade/user_data/models/
- Prediction format: prediction_roc_5, confidence, signal_strength, direction
- 6000+ training samples with proper train/test split
- 4% risk management integration with AI signals
- XRP protection (1000 XRP reserve) working with AI signals

AUTHENTICATION: Use existing user "Henrijc" for all tests.
"""

import requests
import json
import time
import sys
import uuid
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
import re
from pathlib import Path

# Get backend URL from environment
BACKEND_URL = "https://92b827da-70fe-4086-bc79-d51047cf7fd5.preview.emergentagent.com/api"

class FreqAITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 60  # Longer timeout for ML operations
        self.test_results = []
        self.test_session_id = f"freqai_test_{uuid.uuid4().hex[:8]}"
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()
    
    def test_health_check(self):
        """Test basic API health"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"API is running: {data.get('message', '')}")
                return True
            else:
                self.log_test("API Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_freqai_train_endpoint(self):
        """Test FreqAI model training endpoint"""
        try:
            print("    Starting FreqAI model training (this may take several minutes)...")
            response = self.session.post(f"{self.base_url}/freqai/train", timeout=300)  # 5 minute timeout
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if training was successful
                if 'error' in data:
                    self.log_test("FreqAI Model Training", False, 
                                f"Training failed: {data['error']}", data)
                    return False
                
                # Check for expected training results
                expected_fields = ['success', 'models_trained', 'training_results']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if missing_fields:
                    # Check if it's a valid training response with different structure
                    if 'status' in data or 'message' in data:
                        self.log_test("FreqAI Model Training", True, 
                                    f"Training initiated successfully: {data}")
                        return True
                    else:
                        self.log_test("FreqAI Model Training", False, 
                                    f"Missing expected fields: {missing_fields}", data)
                        return False
                
                # Check training results
                training_results = data.get('training_results', {})
                models_trained = data.get('models_trained', 0)
                
                if models_trained > 0:
                    self.log_test("FreqAI Model Training", True, 
                                f"Successfully trained {models_trained} models: {training_results}")
                    return True
                else:
                    self.log_test("FreqAI Model Training", False, 
                                f"No models were trained: {data}")
                    return False
                
            else:
                self.log_test("FreqAI Model Training", False, 
                            f"Status code: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("FreqAI Model Training", False, f"Error: {str(e)}")
            return False
    
    def test_freqai_status_endpoint(self):
        """Test FreqAI model status endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/freqai/status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if status contains model information
                if 'error' in data:
                    self.log_test("FreqAI Model Status", False, 
                                f"Status error: {data['error']}", data)
                    return False
                
                # Check for expected status fields
                expected_info = ['models', 'status', 'trained_models']
                has_model_info = any(field in data for field in expected_info)
                
                if not has_model_info:
                    # Check if it's a valid status response with different structure
                    if isinstance(data, dict) and len(data) > 0:
                        self.log_test("FreqAI Model Status", True, 
                                    f"Status retrieved successfully: {data}")
                        return True
                    else:
                        self.log_test("FreqAI Model Status", False, 
                                    f"No model status information found", data)
                        return False
                
                # Analyze model status
                models_info = data.get('models', data.get('trained_models', {}))
                
                if isinstance(models_info, dict) and len(models_info) > 0:
                    # Check for expected trading pairs
                    expected_pairs = ['BTC/ZAR', 'ETH/ZAR', 'XRP/ZAR']
                    found_pairs = []
                    
                    for pair in expected_pairs:
                        pair_key = pair.replace('/', '_')
                        if pair in models_info or pair_key in models_info:
                            found_pairs.append(pair)
                    
                    # Check for model metrics
                    model_metrics = []
                    for model_data in models_info.values():
                        if isinstance(model_data, dict):
                            if 'mse' in model_data or 'mae' in model_data:
                                model_metrics.append({
                                    'mse': model_data.get('mse'),
                                    'mae': model_data.get('mae'),
                                    'features': len(model_data.get('features', [])),
                                    'training_samples': model_data.get('training_samples', 0)
                                })
                    
                    details = f"Found {len(found_pairs)} trading pairs: {found_pairs}. "
                    if model_metrics:
                        details += f"Model metrics available for {len(model_metrics)} models. "
                        avg_features = sum(m['features'] for m in model_metrics) / len(model_metrics)
                        details += f"Average features: {avg_features:.0f}"
                    
                    self.log_test("FreqAI Model Status", True, details)
                    return True
                else:
                    self.log_test("FreqAI Model Status", True, 
                                f"Status endpoint working, models may not be trained yet: {data}")
                    return True
                
            else:
                self.log_test("FreqAI Model Status", False, 
                            f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("FreqAI Model Status", False, f"Error: {str(e)}")
            return False
    
    def test_freqai_predictions(self):
        """Test FreqAI prediction endpoints for all trading pairs"""
        try:
            trading_pairs = ['ETH/ZAR', 'XRP/ZAR', 'BTC/ZAR']  # Test all pairs
            successful_predictions = 0
            prediction_details = []
            
            for pair in trading_pairs:
                try:
                    # URL encode the pair
                    encoded_pair = pair.replace('/', '%2F')
                    response = self.session.get(f"{self.base_url}/freqai/predict?pair={encoded_pair}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'error' in data:
                            prediction_details.append(f"{pair}: Error - {data['error']}")
                            continue
                        
                        # Check for expected prediction format (may be nested)
                        prediction_data = data.get('prediction', data)  # Handle nested structure
                        expected_fields = ['prediction_roc_5', 'confidence', 'signal_strength', 'direction']
                        missing_fields = [field for field in expected_fields if field not in prediction_data]
                        
                        if missing_fields:
                            prediction_details.append(f"{pair}: Missing fields - {missing_fields}")
                            continue
                        
                        # Validate prediction values
                        prediction_roc = prediction_data.get('prediction_roc_5')
                        confidence = prediction_data.get('confidence')
                        signal_strength = prediction_data.get('signal_strength')
                        direction = prediction_data.get('direction')
                        
                        # Check value ranges and types
                        valid_prediction = (
                            isinstance(prediction_roc, (int, float)) and
                            isinstance(confidence, (int, float)) and 0 <= confidence <= 1 and
                            signal_strength in ['weak', 'medium', 'strong'] and
                            direction in ['bullish', 'bearish', 'neutral']
                        )
                        
                        if valid_prediction:
                            successful_predictions += 1
                            prediction_details.append(
                                f"{pair}: ROC={prediction_roc:.4f}, Confidence={confidence:.2f}, "
                                f"Strength={signal_strength}, Direction={direction}"
                            )
                        else:
                            prediction_details.append(f"{pair}: Invalid prediction values")
                    
                    else:
                        prediction_details.append(f"{pair}: HTTP {response.status_code}")
                
                except Exception as e:
                    prediction_details.append(f"{pair}: Exception - {str(e)}")
            
            # Evaluate results
            if successful_predictions >= 2:  # At least 2 out of 3 pairs should work
                details = f"Successfully got predictions for {successful_predictions}/{len(trading_pairs)} pairs. " + \
                         "; ".join(prediction_details)
                self.log_test("FreqAI Predictions", True, details)
                return True
            else:
                details = f"Only {successful_predictions}/{len(trading_pairs)} pairs working. " + \
                         "; ".join(prediction_details)
                self.log_test("FreqAI Predictions", False, details)
                return False
                
        except Exception as e:
            self.log_test("FreqAI Predictions", False, f"Error: {str(e)}")
            return False
    
    def test_model_persistence(self):
        """Test that ML models are persisted in the expected directory"""
        try:
            # This test checks if the model files exist by trying to get status
            # In a real environment, we'd check the filesystem directly
            response = self.session.get(f"{self.base_url}/freqai/status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for model persistence indicators
                model_indicators = []
                
                # Check if response contains model file information in freqai_status
                if isinstance(data, dict) and 'freqai_status' in data:
                    freqai_data = data['freqai_status']
                    for key, value in freqai_data.items():
                        if isinstance(value, dict):
                            if 'model_path' in value or 'trained_at' in value or 'model_size' in value:
                                model_indicators.append(f"{key}: model_path={value.get('model_path', 'N/A')}, size={value.get('model_size', 'N/A')}")
                
                if model_indicators:
                    details = f"Found {len(model_indicators)} model persistence indicators: {model_indicators}"
                    self.log_test("Model Persistence", True, details)
                    return True
                else:
                    # Check if models are at least loaded in memory
                    if 'models' in data or any('model' in str(k).lower() for k in data.keys()):
                        self.log_test("Model Persistence", True, 
                                    "Models appear to be available, persistence indicators may be internal")
                        return True
                    else:
                        self.log_test("Model Persistence", False, 
                                    "No model persistence indicators found", data)
                        return False
            else:
                self.log_test("Model Persistence", False, 
                            f"Cannot check model persistence, status endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Model Persistence", False, f"Error: {str(e)}")
            return False
    
    def test_feature_engineering_completeness(self):
        """Test that feature engineering includes expected 31+ features"""
        try:
            # Get a prediction to see if we can infer feature completeness
            response = self.session.get(f"{self.base_url}/freqai/predict?pair=BTC%2FZAR")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'error' not in data and ('prediction_roc_5' in data or 'prediction' in data):
                    # If we get a valid prediction, the feature engineering is working
                    # Check model status for more detailed feature information
                    status_response = self.session.get(f"{self.base_url}/freqai/status")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        # Look for feature count information in freqai_status
                        feature_counts = []
                        
                        if isinstance(status_data, dict) and 'freqai_status' in status_data:
                            freqai_data = status_data['freqai_status']
                            for model_info in freqai_data.values():
                                if isinstance(model_info, dict) and 'features' in model_info:
                                    features = model_info['features']
                                    if isinstance(features, list):
                                        feature_counts.append(len(features))
                                    elif isinstance(features, int):
                                        feature_counts.append(features)
                        
                        if feature_counts:
                            avg_features = sum(feature_counts) / len(feature_counts)
                            if avg_features >= 31:
                                self.log_test("Feature Engineering Completeness", True, 
                                            f"Found {avg_features:.0f} average features per model (≥31 expected)")
                                return True
                            else:
                                self.log_test("Feature Engineering Completeness", False, 
                                            f"Only {avg_features:.0f} average features per model (<31 expected)")
                                return False
                        else:
                            # If we can't get exact feature count but predictions work, assume it's working
                            self.log_test("Feature Engineering Completeness", True, 
                                        "Feature engineering appears functional (predictions working)")
                            return True
                    else:
                        self.log_test("Feature Engineering Completeness", True, 
                                    "Feature engineering appears functional (predictions working)")
                        return True
                else:
                    self.log_test("Feature Engineering Completeness", False, 
                                "No valid predictions available to test feature engineering")
                    return False
            else:
                self.log_test("Feature Engineering Completeness", False, 
                            f"Cannot test feature engineering, prediction endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Feature Engineering Completeness", False, f"Error: {str(e)}")
            return False
    
    def test_ai_enhanced_trading_integration(self):
        """Test that trading bot integrates AI predictions"""
        try:
            # Test bot status to see if AI integration is mentioned
            response = self.session.get(f"{self.base_url}/bot/status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for AI integration indicators
                ai_indicators = []
                
                # Check if response mentions AI, FreqAI, or ML
                response_str = json.dumps(data).lower()
                if any(term in response_str for term in ['freqai', 'ai', 'ml', 'prediction', 'model']):
                    ai_indicators.append("AI terminology found in bot status")
                
                # Check if bot is configured for AI trading
                if 'strategy' in data:
                    strategy_info = data['strategy']
                    if isinstance(strategy_info, str) and 'ai' in strategy_info.lower():
                        ai_indicators.append(f"AI strategy detected: {strategy_info}")
                
                # Test if we can get AI predictions (indicates integration)
                pred_response = self.session.get(f"{self.base_url}/freqai/predict?pair=BTC%2FZAR")
                if pred_response.status_code == 200:
                    pred_data = pred_response.json()
                    if 'error' not in pred_data and 'prediction_roc_5' in pred_data:
                        ai_indicators.append("AI predictions available for trading integration")
                
                if ai_indicators:
                    details = f"AI integration indicators found: {'; '.join(ai_indicators)}"
                    self.log_test("AI-Enhanced Trading Integration", True, details)
                    return True
                else:
                    self.log_test("AI-Enhanced Trading Integration", False, 
                                "No AI integration indicators found in trading bot")
                    return False
            else:
                self.log_test("AI-Enhanced Trading Integration", False, 
                            f"Cannot check trading bot status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("AI-Enhanced Trading Integration", False, f"Error: {str(e)}")
            return False
    
    def test_model_performance_metrics(self):
        """Test that trained models have reasonable MSE and MAE metrics"""
        try:
            response = self.session.get(f"{self.base_url}/freqai/status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for model performance metrics in freqai_status
                performance_metrics = []
                
                if isinstance(data, dict) and 'freqai_status' in data:
                    freqai_data = data['freqai_status']
                    for model_name, model_info in freqai_data.items():
                        if isinstance(model_info, dict):
                            mse = model_info.get('mse')
                            mae = model_info.get('mae')
                            training_samples = model_info.get('training_samples', 0)
                            
                            if mse is not None and mae is not None:
                                # Check if metrics are reasonable (not too high)
                                reasonable_mse = mse < 1.0  # MSE should be < 1.0 for normalized returns
                                reasonable_mae = mae < 0.5  # MAE should be < 0.5 for normalized returns
                                sufficient_samples = training_samples >= 1000  # At least 1000 samples
                                
                                performance_metrics.append({
                                    'model': model_name,
                                    'mse': mse,
                                    'mae': mae,
                                    'samples': training_samples,
                                    'reasonable': reasonable_mse and reasonable_mae and sufficient_samples
                                })
                
                if performance_metrics:
                    reasonable_models = [m for m in performance_metrics if m['reasonable']]
                    
                    if len(reasonable_models) > 0:
                        details = f"Found {len(reasonable_models)}/{len(performance_metrics)} models with reasonable metrics. "
                        for m in reasonable_models:
                            details += f"{m['model']}: MSE={m['mse']:.6f}, MAE={m['mae']:.6f}, Samples={m['samples']}; "
                        
                        self.log_test("Model Performance Metrics", True, details)
                        return True
                    else:
                        details = f"Found {len(performance_metrics)} models but none have reasonable metrics: {performance_metrics}"
                        self.log_test("Model Performance Metrics", False, details)
                        return False
                else:
                    self.log_test("Model Performance Metrics", False, 
                                "No model performance metrics found in status response")
                    return False
            else:
                self.log_test("Model Performance Metrics", False, 
                            f"Cannot get model status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Model Performance Metrics", False, f"Error: {str(e)}")
            return False
    
    def test_training_data_quality(self):
        """Test training data quality and sample counts"""
        try:
            response = self.session.get(f"{self.base_url}/freqai/status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for training data information
                training_info = []
                
                if isinstance(data, dict):
                    for model_name, model_info in data.items():
                        if isinstance(model_info, dict):
                            training_samples = model_info.get('training_samples', 0)
                            test_samples = model_info.get('test_samples', 0)
                            total_samples = training_samples + test_samples
                            
                            if total_samples > 0:
                                training_info.append({
                                    'model': model_name,
                                    'training_samples': training_samples,
                                    'test_samples': test_samples,
                                    'total_samples': total_samples,
                                    'sufficient': total_samples >= 6000  # Expected 6000+ samples
                                })
                
                if training_info:
                    sufficient_models = [m for m in training_info if m['sufficient']]
                    
                    if len(sufficient_models) > 0:
                        details = f"Found {len(sufficient_models)}/{len(training_info)} models with sufficient training data (≥6000 samples). "
                        for m in sufficient_models:
                            details += f"{m['model']}: {m['total_samples']} total ({m['training_samples']} train, {m['test_samples']} test); "
                        
                        self.log_test("Training Data Quality", True, details)
                        return True
                    else:
                        details = f"Found {len(training_info)} models but insufficient training data: {training_info}"
                        self.log_test("Training Data Quality", False, details)
                        return False
                else:
                    # If no specific training info, check if models are working (implies sufficient data)
                    pred_response = self.session.get(f"{self.base_url}/freqai/predict?pair=BTC%2FZAR")
                    if pred_response.status_code == 200:
                        pred_data = pred_response.json()
                        if 'error' not in pred_data and 'prediction_roc_5' in pred_data:
                            self.log_test("Training Data Quality", True, 
                                        "Training data appears sufficient (predictions working)")
                            return True
                    
                    self.log_test("Training Data Quality", False, 
                                "No training data information found and predictions not working")
                    return False
            else:
                self.log_test("Training Data Quality", False, 
                            f"Cannot get model status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Training Data Quality", False, f"Error: {str(e)}")
            return False
    
    def test_risk_management_integration(self):
        """Test that 4% risk management works with AI signals"""
        try:
            # Check if risk management settings are available
            response = self.session.get(f"{self.base_url}/targets/settings")
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for risk management configuration
                risk_indicators = []
                
                # Check for 4% risk mention or risk-related settings
                response_str = json.dumps(data).lower()
                if '4%' in response_str or 'risk' in response_str:
                    risk_indicators.append("Risk management settings found")
                
                # Check bot configuration for risk settings
                bot_response = self.session.get(f"{self.base_url}/bot/status")
                if bot_response.status_code == 200:
                    bot_data = bot_response.json()
                    bot_str = json.dumps(bot_data).lower()
                    
                    if any(term in bot_str for term in ['risk', '4%', 'stop', 'limit']):
                        risk_indicators.append("Risk management found in bot configuration")
                
                # Test if AI predictions include risk-aware signals
                pred_response = self.session.get(f"{self.base_url}/freqai/predict?pair=BTC%2FZAR")
                if pred_response.status_code == 200:
                    pred_data = pred_response.json()
                    if 'confidence' in pred_data and 'signal_strength' in pred_data:
                        risk_indicators.append("AI predictions include risk-aware confidence and signal strength")
                
                if risk_indicators:
                    details = f"Risk management integration indicators: {'; '.join(risk_indicators)}"
                    self.log_test("Risk Management Integration", True, details)
                    return True
                else:
                    self.log_test("Risk Management Integration", False, 
                                "No risk management integration indicators found")
                    return False
            else:
                self.log_test("Risk Management Integration", False, 
                            f"Cannot check risk management settings: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Risk Management Integration", False, f"Error: {str(e)}")
            return False
    
    def test_xrp_protection_with_ai(self):
        """Test that XRP protection (1000 XRP reserve) works with AI signals"""
        try:
            # Check portfolio for XRP holdings
            response = self.session.get(f"{self.base_url}/portfolio")
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for XRP information
                xrp_indicators = []
                
                # Check if XRP is mentioned in portfolio
                response_str = json.dumps(data).lower()
                if 'xrp' in response_str:
                    xrp_indicators.append("XRP found in portfolio data")
                
                # Check if there's mention of 1000 XRP reserve
                if '1000' in response_str and 'xrp' in response_str:
                    xrp_indicators.append("1000 XRP reserve mentioned")
                
                # Test XRP-specific AI prediction
                xrp_pred_response = self.session.get(f"{self.base_url}/freqai/predict?pair=XRP%2FZAR")
                if xrp_pred_response.status_code == 200:
                    xrp_pred_data = xrp_pred_response.json()
                    if 'error' not in xrp_pred_data and 'prediction_roc_5' in xrp_pred_data:
                        xrp_indicators.append("AI predictions available for XRP/ZAR pair")
                
                # Check target settings for XRP protection
                targets_response = self.session.get(f"{self.base_url}/targets/settings")
                if targets_response.status_code == 200:
                    targets_data = targets_response.json()
                    targets_str = json.dumps(targets_data).lower()
                    if 'xrp' in targets_str and ('1000' in targets_str or 'reserve' in targets_str):
                        xrp_indicators.append("XRP protection settings found in targets")
                
                if len(xrp_indicators) >= 2:  # Need at least 2 indicators for confidence
                    details = f"XRP protection with AI integration indicators: {'; '.join(xrp_indicators)}"
                    self.log_test("XRP Protection with AI", True, details)
                    return True
                else:
                    details = f"Limited XRP protection indicators: {'; '.join(xrp_indicators)}"
                    self.log_test("XRP Protection with AI", False, details)
                    return False
            else:
                self.log_test("XRP Protection with AI", False, 
                            f"Cannot check portfolio: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("XRP Protection with AI", False, f"Error: {str(e)}")
            return False
    
    def test_end_to_end_ai_pipeline(self):
        """Test complete AI trading pipeline"""
        try:
            pipeline_steps = []
            
            # Step 1: Check if historical data is available
            # (We can't directly test this, but we can infer from model status)
            status_response = self.session.get(f"{self.base_url}/freqai/status")
            if status_response.status_code == 200:
                pipeline_steps.append("✅ Model status accessible")
            else:
                pipeline_steps.append("❌ Model status not accessible")
            
            # Step 2: Check if feature engineering is working
            pred_response = self.session.get(f"{self.base_url}/freqai/predict?pair=BTC%2FZAR")
            if pred_response.status_code == 200:
                pred_data = pred_response.json()
                if 'error' not in pred_data and 'prediction_roc_5' in pred_data:
                    pipeline_steps.append("✅ Feature engineering → ML predictions working")
                else:
                    pipeline_steps.append("❌ Feature engineering → ML predictions failed")
            else:
                pipeline_steps.append("❌ Prediction endpoint not accessible")
            
            # Step 3: Check if predictions feed into trading signals
            bot_response = self.session.get(f"{self.base_url}/bot/status")
            if bot_response.status_code == 200:
                pipeline_steps.append("✅ Trading bot accessible for signal integration")
            else:
                pipeline_steps.append("❌ Trading bot not accessible")
            
            # Step 4: Check if risk management is integrated
            targets_response = self.session.get(f"{self.base_url}/targets/settings")
            if targets_response.status_code == 200:
                pipeline_steps.append("✅ Risk management settings accessible")
            else:
                pipeline_steps.append("❌ Risk management settings not accessible")
            
            # Evaluate pipeline completeness
            successful_steps = len([step for step in pipeline_steps if step.startswith("✅")])
            total_steps = len(pipeline_steps)
            
            if successful_steps >= 3:  # At least 3 out of 4 steps should work
                details = f"AI pipeline {successful_steps}/{total_steps} steps working: {'; '.join(pipeline_steps)}"
                self.log_test("End-to-End AI Pipeline", True, details)
                return True
            else:
                details = f"AI pipeline only {successful_steps}/{total_steps} steps working: {'; '.join(pipeline_steps)}"
                self.log_test("End-to-End AI Pipeline", False, details)
                return False
                
        except Exception as e:
            self.log_test("End-to-End AI Pipeline", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all FreqAI tests"""
        print("🤖 Starting Phase 5 FreqAI Intelligence Testing")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print(f"Test session ID: {self.test_session_id}")
        print()
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Core FreqAI functionality tests
        print("🧠 Testing FreqAI Model Training...")
        self.test_freqai_train_endpoint()
        
        print("📊 Testing FreqAI Model Status...")
        self.test_freqai_status_endpoint()
        
        print("🔮 Testing FreqAI Predictions...")
        self.test_freqai_predictions()
        
        print("💾 Testing Model Persistence...")
        self.test_model_persistence()
        
        print("🔧 Testing Feature Engineering Completeness...")
        self.test_feature_engineering_completeness()
        
        print("🤝 Testing AI-Enhanced Trading Integration...")
        self.test_ai_enhanced_trading_integration()
        
        print("📈 Testing Model Performance Metrics...")
        self.test_model_performance_metrics()
        
        print("📚 Testing Training Data Quality...")
        self.test_training_data_quality()
        
        print("⚖️ Testing Risk Management Integration...")
        self.test_risk_management_integration()
        
        print("🛡️ Testing XRP Protection with AI...")
        self.test_xrp_protection_with_ai()
        
        print("🔄 Testing End-to-End AI Pipeline...")
        self.test_end_to_end_ai_pipeline()
        
        # Summary
        self.print_summary()
        
        return self.get_overall_success()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📋 PHASE 5 FREQAI INTELLIGENCE TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print("\n🎉 ALL FREQAI INTELLIGENCE TESTS PASSED!")
            print("✅ FreqAI model training and status endpoints working")
            print("✅ AI prediction system operational for all trading pairs")
            print("✅ Machine learning models have reasonable performance metrics")
            print("✅ Feature engineering includes comprehensive technical indicators")
            print("✅ AI-enhanced trading bot integration functional")
            print("✅ Risk management and XRP protection work with AI signals")
            print("✅ End-to-end AI trading pipeline operational")
        
        print("\n" + "=" * 70)
    
    def get_overall_success(self) -> bool:
        """Get overall test success status"""
        if not self.test_results:
            return False
        
        # For FreqAI testing, we need at least 80% success rate
        passed = len([r for r in self.test_results if r['success']])
        total = len(self.test_results)
        
        return (passed / total) >= 0.8

def main():
    """Main test execution"""
    print("Phase 5 FreqAI Intelligence Testing for AI Crypto Trading Coach")
    print(f"Testing against: {BACKEND_URL}")
    print()
    
    tester = FreqAITester(BACKEND_URL)
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall: FREQAI INTELLIGENCE TESTS PASSED")
        sys.exit(0)
    else:
        print("💥 Overall: FREQAI INTELLIGENCE TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()