import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TradingView = () => {
  const [marketData, setMarketData] = useState({});
  const [activeTab, setActiveTab] = useState('manual');
  const [tradingStatus, setTradingStatus] = useState({
    manual: false,
    ai: false
  });
  const [manualTradeForm, setManualTradeForm] = useState({
    pair: 'XBTZAR',
    side: 'buy',
    amount: '',
    orderType: 'market',
    price: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const tradingPairs = [
    { value: 'XBTZAR', label: 'BTC/ZAR' },
    { value: 'ETHZAR', label: 'ETH/ZAR' },
    { value: 'ADAZAR', label: 'ADA/ZAR' },
    { value: 'DOTZAR', label: 'DOT/ZAR' },
    { value: 'LINKZAR', label: 'LINK/ZAR' }
  ];

  useEffect(() => {
    loadMarketData();
    loadTradingStatus();
    
    // Update market data every 10 seconds
    const interval = setInterval(loadMarketData, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadMarketData = async () => {
    try {
      const promises = tradingPairs.map(pair => 
        axios.get(`${API}/market-data/${pair.value}`).catch(err => ({
          data: { data: null, error: err.message }
        }))
      );
      
      const responses = await Promise.all(promises);
      const newMarketData = {};
      
      responses.forEach((response, index) => {
        const pair = tradingPairs[index].value;
        newMarketData[pair] = response.data.data;
      });
      
      setMarketData(newMarketData);
    } catch (error) {
      console.error('Failed to load market data:', error);
    }
  };

  const loadTradingStatus = async () => {
    try {
      const aiStatus = await axios.get(`${API}/ai-strategy/status`);
      setTradingStatus({
        manual: true, // Manual trading is always available
        ai: aiStatus.data.data?.is_active || false
      });
    } catch (error) {
      console.error('Failed to load trading status:', error);
    }
  };

  const handleManualTrade = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const tradeData = {
        pair: manualTradeForm.pair,
        side: manualTradeForm.side,
        amount: parseFloat(manualTradeForm.amount),
        order_type: manualTradeForm.orderType,
        price: manualTradeForm.price ? parseFloat(manualTradeForm.price) : null
      };

      const response = await axios.post(`${API}/trade`, tradeData, {
        headers: {
          'Authorization': 'Bearer secure_token_123' // In production, use proper JWT
        }
      });

      setMessage({
        type: 'success',
        text: 'Trade executed successfully!'
      });

      // Reset form
      setManualTradeForm({
        ...manualTradeForm,
        amount: '',
        price: ''
      });

      // Refresh market data
      await loadMarketData();

    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Trade execution failed'
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleAITrading = async () => {
    setLoading(true);
    try {
      const endpoint = tradingStatus.ai ? '/trading/stop' : '/trading/start';
      await axios.post(`${API}${endpoint}`, {}, {
        headers: {
          'Authorization': 'Bearer secure_token_123'
        }
      });

      setTradingStatus({
        ...tradingStatus,
        ai: !tradingStatus.ai
      });

      setMessage({
        type: 'success',
        text: `AI trading ${tradingStatus.ai ? 'stopped' : 'started'} successfully`
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Failed to ${tradingStatus.ai ? 'stop' : 'start'} AI trading`
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount, currency = 'ZAR') => {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  return (
    <div className="trading-view">
      <div className="container mx-auto px-4 py-6">
        
        {/* Header */}
        <div className="trading-header mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Center</h1>
          <p className="text-gray-600">Execute trades and manage your trading strategies</p>
        </div>

        {/* Message Display */}
        {message && (
          <div className={`message-banner mb-6 p-4 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-100 border border-green-400 text-green-700'
              : 'bg-red-100 border border-red-400 text-red-700'
          }`}>
            <p>{message.text}</p>
          </div>
        )}

        {/* Market Data Overview */}
        <div className="market-overview mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Market Overview</h2>
          <div className="market-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {tradingPairs.map((pair) => {
              const data = marketData[pair.value];
              return (
                <div key={pair.value} className="market-card bg-white rounded-lg shadow-md p-4">
                  <div className="market-header flex justify-between items-center mb-2">
                    <h3 className="font-semibold text-gray-900">{pair.label}</h3>
                    <span className={`status-dot w-2 h-2 rounded-full ${data ? 'bg-green-400' : 'bg-red-400'}`}></span>
                  </div>
                  {data ? (
                    <div className="market-data">
                      <p className="text-lg font-bold text-gray-900">
                        {formatCurrency(data.ticker?.last_trade)}
                      </p>
                      <div className="text-xs text-gray-600 mt-1">
                        <p>Bid: {formatCurrency(data.ticker?.bid)}</p>
                        <p>Ask: {formatCurrency(data.ticker?.ask)}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="market-data">
                      <p className="text-gray-500">No data</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Trading Controls */}
        <div className="trading-controls">
          
          {/* Tab Navigation */}
          <div className="tab-navigation mb-6">
            <div className="flex border-b border-gray-200">
              <button
                onClick={() => setActiveTab('manual')}
                className={`px-6 py-3 font-medium text-sm ${
                  activeTab === 'manual'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Manual Trading
              </button>
              <button
                onClick={() => setActiveTab('ai')}
                className={`px-6 py-3 font-medium text-sm ${
                  activeTab === 'ai'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                AI Trading
              </button>
            </div>
          </div>

          {/* Manual Trading Tab */}
          {activeTab === 'manual' && (
            <div className="manual-trading bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Manual Trade Execution</h3>
              
              <form onSubmit={handleManualTrade} className="trade-form">
                <div className="form-grid grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  
                  {/* Trading Pair */}
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Trading Pair
                    </label>
                    <select
                      value={manualTradeForm.pair}
                      onChange={(e) => setManualTradeForm({...manualTradeForm, pair: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {tradingPairs.map(pair => (
                        <option key={pair.value} value={pair.value}>{pair.label}</option>
                      ))}
                    </select>
                  </div>

                  {/* Trade Side */}
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Trade Side
                    </label>
                    <select
                      value={manualTradeForm.side}
                      onChange={(e) => setManualTradeForm({...manualTradeForm, side: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="buy">Buy</option>
                      <option value="sell">Sell</option>
                    </select>
                  </div>

                  {/* Amount */}
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Amount (ZAR)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={manualTradeForm.amount}
                      onChange={(e) => setManualTradeForm({...manualTradeForm, amount: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter amount"
                      required
                    />
                  </div>

                  {/* Order Type */}
                  <div className="form-group">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Order Type
                    </label>
                    <select
                      value={manualTradeForm.orderType}
                      onChange={(e) => setManualTradeForm({...manualTradeForm, orderType: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="market">Market Order</option>
                      <option value="limit">Limit Order</option>
                    </select>
                  </div>
                </div>

                {/* Price (for limit orders) */}
                {manualTradeForm.orderType === 'limit' && (
                  <div className="form-group mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Limit Price (ZAR)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={manualTradeForm.price}
                      onChange={(e) => setManualTradeForm({...manualTradeForm, price: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter limit price"
                      required
                    />
                  </div>
                )}

                {/* Submit Button */}
                <div className="form-actions">
                  <button
                    type="submit"
                    disabled={loading || !manualTradeForm.amount}
                    className={`px-6 py-3 rounded-md font-medium ${
                      loading || !manualTradeForm.amount
                        ? 'bg-gray-400 cursor-not-allowed'
                        : manualTradeForm.side === 'buy'
                          ? 'bg-green-600 hover:bg-green-700'
                          : 'bg-red-600 hover:bg-red-700'
                    } text-white transition-colors`}
                  >
                    {loading ? 'Processing...' : `${manualTradeForm.side.toUpperCase()} ${manualTradeForm.pair}`}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* AI Trading Tab */}
          {activeTab === 'ai' && (
            <div className="ai-trading bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Trading Control</h3>
              
              <div className="ai-status-card mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="status-header flex justify-between items-center mb-4">
                  <div>
                    <h4 className="font-semibold text-gray-900">AI Trading Status</h4>
                    <p className="text-sm text-gray-600">Automated trading using machine learning strategies</p>
                  </div>
                  <div className={`status-indicator px-3 py-1 rounded-full text-sm font-medium ${
                    tradingStatus.ai 
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {tradingStatus.ai ? 'Active' : 'Inactive'}
                  </div>
                </div>
                
                <div className="ai-controls">
                  <button
                    onClick={toggleAITrading}
                    disabled={loading}
                    className={`px-6 py-3 rounded-md font-medium text-white transition-colors ${
                      loading
                        ? 'bg-gray-400 cursor-not-allowed'
                        : tradingStatus.ai
                          ? 'bg-red-600 hover:bg-red-700'
                          : 'bg-green-600 hover:bg-green-700'
                    }`}
                  >
                    {loading ? 'Processing...' : (tradingStatus.ai ? 'Stop AI Trading' : 'Start AI Trading')}
                  </button>
                </div>
              </div>

              <div className="ai-info">
                <h4 className="font-semibold text-gray-900 mb-3">AI Strategy Features</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center">
                    <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Machine learning-based price prediction
                  </li>
                  <li className="flex items-center">
                    <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Automated risk management
                  </li>
                  <li className="flex items-center">
                    <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Multi-pair trading optimization
                  </li>
                  <li className="flex items-center">
                    <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Real-time market analysis
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default TradingView;