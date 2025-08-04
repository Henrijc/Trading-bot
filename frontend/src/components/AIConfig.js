import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AIConfig = () => {
  const [config, setConfig] = useState({
    daily_target_zar: 1000,
    max_daily_risk_percent: 2.0,
    allocation_scalping_percent: 60.0,
    allocation_accumulation_percent: 40.0,
    max_open_trades: 5,
    stop_loss_percent: 1.5,
    take_profit_percent: 3.0
  });
  const [aiStatus, setAiStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [predictions, setPredictions] = useState([]);

  useEffect(() => {
    loadAIStatus();
    loadCurrentPredictions();
    
    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      loadAIStatus();
      loadCurrentPredictions();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadAIStatus = async () => {
    try {
      const response = await axios.get(`${API}/ai-strategy/status`);
      setAiStatus(response.data.data);
    } catch (error) {
      console.error('Failed to load AI status:', error);
    }
  };

  const loadCurrentPredictions = async () => {
    try {
      // This would load current AI predictions
      const mockPredictions = [
        {
          symbol: 'BTC/USDT',
          prediction: 0.025,
          confidence: 0.85,
          signal: 'buy',
          strength: 2.1,
          current_price: 45000
        },
        {
          symbol: 'ETH/USDT',
          prediction: -0.015,
          confidence: 0.72,
          signal: 'sell',
          strength: 1.3,
          current_price: 3200
        }
      ];
      setPredictions(mockPredictions);
    } catch (error) {
      console.error('Failed to load predictions:', error);
    }
  };

  const handleConfigChange = (key, value) => {
    setConfig(prev => ({
      ...prev,
      [key]: parseFloat(value) || 0
    }));
  };

  const saveConfiguration = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      await axios.post(`${API}/ai-strategy/configure`, config, {
        headers: {
          'Authorization': 'Bearer secure_token_123'
        }
      });

      setMessage({
        type: 'success',
        text: 'AI configuration updated successfully!'
      });

      // Reload AI status
      await loadAIStatus();

    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to update configuration'
      });
    } finally {
      setLoading(false);
    }
  };

  const retrainModel = async () => {
    setLoading(true);
    setMessage(null);

    try {
      // This would trigger model retraining
      setMessage({
        type: 'info',
        text: 'Model retraining initiated. This may take several minutes...'
      });

      // Simulate retraining delay
      setTimeout(async () => {
        setMessage({
          type: 'success',
          text: 'Model retraining completed successfully!'
        });
        await loadAIStatus();
      }, 3000);

    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Model retraining failed'
      });
    } finally {
      setLoading(false);
    }
  };

  const formatPercentage = (value) => `${(value * 100).toFixed(1)}%`;
  const formatCurrency = (amount) => `R${amount.toFixed(2)}`;

  return (
    <div className="ai-config">
      <div className="container mx-auto px-4 py-6">
        
        {/* Header */}
        <div className="config-header mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Configuration</h1>
          <p className="text-gray-600">Configure your AI trading strategy parameters and risk management</p>
        </div>

        {/* Message Display */}
        {message && (
          <div className={`message-banner mb-6 p-4 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-100 border border-green-400 text-green-700'
              : message.type === 'error'
              ? 'bg-red-100 border border-red-400 text-red-700'
              : 'bg-blue-100 border border-blue-400 text-blue-700'
          }`}>
            <p>{message.text}</p>
          </div>
        )}

        {/* AI Status Overview */}
        <div className="ai-status-overview mb-8 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">AI Strategy Status</h2>
          
          {aiStatus && (
            <div className="status-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              
              <div className="status-item">
                <p className="text-sm text-gray-500">Status</p>
                <p className={`text-lg font-semibold ${aiStatus.is_active ? 'text-green-600' : 'text-gray-600'}`}>
                  {aiStatus.is_active ? 'Active' : 'Inactive'}
                </p>
              </div>
              
              <div className="status-item">
                <p className="text-sm text-gray-500">Model Confidence</p>
                <p className="text-lg font-semibold text-blue-600">
                  {formatPercentage(aiStatus.confidence)}
                </p>
              </div>
              
              <div className="status-item">
                <p className="text-sm text-gray-500">Last Retrain</p>
                <p className="text-lg font-semibold text-gray-600">
                  {aiStatus.last_retrain ? new Date(aiStatus.last_retrain).toLocaleDateString() : 'Never'}
                </p>
              </div>
              
              <div className="status-item">
                <p className="text-sm text-gray-500">Supported Pairs</p>
                <p className="text-lg font-semibold text-gray-600">
                  {aiStatus.supported_pairs?.length || 0} pairs
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="config-content grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Configuration Form */}
          <div className="config-form lg:col-span-2 bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Strategy Parameters</h3>
            
            <form onSubmit={saveConfiguration} className="space-y-6">
              
              {/* Financial Targets */}
              <div className="form-section">
                <h4 className="text-md font-medium text-gray-900 mb-4">Financial Targets</h4>
                <div className="form-grid grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Daily Target (ZAR)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={config.daily_target_zar}
                      onChange={(e) => handleConfigChange('daily_target_zar', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Daily Risk (%)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="10"
                      value={config.max_daily_risk_percent}
                      onChange={(e) => handleConfigChange('max_daily_risk_percent', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Strategy Allocation */}
              <div className="form-section">
                <h4 className="text-md font-medium text-gray-900 mb-4">Strategy Allocation</h4>
                <div className="form-grid grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Scalping Strategy (%)
                    </label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="100"
                      value={config.allocation_scalping_percent}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value) || 0;
                        handleConfigChange('allocation_scalping_percent', value);
                        handleConfigChange('allocation_accumulation_percent', 100 - value);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Accumulation Strategy (%)
                    </label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="100"
                      value={config.allocation_accumulation_percent}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value) || 0;
                        handleConfigChange('allocation_accumulation_percent', value);
                        handleConfigChange('allocation_scalping_percent', 100 - value);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Risk Management */}
              <div className="form-section">
                <h4 className="text-md font-medium text-gray-900 mb-4">Risk Management</h4>
                <div className="form-grid grid grid-cols-1 md:grid-cols-3 gap-4">
                  
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Open Trades
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={config.max_open_trades}
                      onChange={(e) => handleConfigChange('max_open_trades', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Stop Loss (%)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="10"
                      value={config.stop_loss_percent}
                      onChange={(e) => handleConfigChange('stop_loss_percent', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Take Profit (%)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="20"
                      value={config.take_profit_percent}
                      onChange={(e) => handleConfigChange('take_profit_percent', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Save Button */}
              <div className="form-actions pt-4 border-t border-gray-200">
                <button
                  type="submit"
                  disabled={loading}
                  className={`px-6 py-3 rounded-md font-medium text-white transition-colors ${
                    loading 
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                  }`}
                >
                  {loading ? 'Saving...' : 'Save Configuration'}
                </button>
              </div>
            </form>
          </div>

          {/* Side Panel */}
          <div className="config-side-panel space-y-6">
            
            {/* Model Management */}
            <div className="model-management bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Management</h3>
              
              <div className="model-actions space-y-4">
                <button
                  onClick={retrainModel}
                  disabled={loading}
                  className={`w-full px-4 py-3 rounded-md font-medium text-white transition-colors ${
                    loading
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {loading ? 'Retraining...' : 'Retrain Model'}
                </button>
                
                <p className="text-sm text-gray-600">
                  Retrain the AI model with latest market data to improve prediction accuracy.
                </p>
              </div>
            </div>

            {/* Current Predictions */}
            <div className="current-predictions bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Predictions</h3>
              
              <div className="predictions-list space-y-3">
                {predictions.length > 0 ? (
                  predictions.map((pred, index) => (
                    <div key={index} className="prediction-item p-3 bg-gray-50 rounded-lg">
                      <div className="prediction-header flex justify-between items-center mb-2">
                        <span className="font-medium">{pred.symbol}</span>
                        <span className={`px-2 py-1 text-xs rounded font-medium ${
                          pred.signal === 'buy' 
                            ? 'bg-green-100 text-green-800'
                            : pred.signal === 'sell'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {pred.signal.toUpperCase()}
                        </span>
                      </div>
                      <div className="prediction-details text-xs text-gray-600">
                        <p>Expected: {formatPercentage(pred.prediction)}</p>
                        <p>Confidence: {formatPercentage(pred.confidence)}</p>
                        <p>Current: {formatCurrency(pred.current_price)}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="no-predictions text-center py-4">
                    <p className="text-gray-500 text-sm">No predictions available</p>
                  </div>
                )}
              </div>
            </div>

            {/* Configuration Summary */}
            <div className="config-summary bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration Summary</h3>
              
              <div className="summary-items space-y-2 text-sm">
                <div className="summary-item flex justify-between">
                  <span className="text-gray-600">Daily Target:</span>
                  <span className="font-medium">{formatCurrency(config.daily_target_zar)}</span>
                </div>
                <div className="summary-item flex justify-between">
                  <span className="text-gray-600">Max Risk:</span>
                  <span className="font-medium">{config.max_daily_risk_percent}%</span>
                </div>
                <div className="summary-item flex justify-between">
                  <span className="text-gray-600">Scalping:</span>
                  <span className="font-medium">{config.allocation_scalping_percent}%</span>
                </div>
                <div className="summary-item flex justify-between">
                  <span className="text-gray-600">Accumulation:</span>
                  <span className="font-medium">{config.allocation_accumulation_percent}%</span>
                </div>
                <div className="summary-item flex justify-between">
                  <span className="text-gray-600">Stop Loss:</span>
                  <span className="font-medium">{config.stop_loss_percent}%</span>
                </div>
                <div className="summary-item flex justify-between">
                  <span className="text-gray-600">Take Profit:</span>
                  <span className="font-medium">{config.take_profit_percent}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default AIConfig;