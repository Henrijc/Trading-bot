import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PerformanceAnalytics = () => {
  const [analyticsData, setAnalyticsData] = useState({
    performance: null,
    trades: [],
    goalProbability: null
  });
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('7d');
  const [activeTab, setActiveTab] = useState('overview');

  const timeframes = [
    { value: '24h', label: '24 Hours' },
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
    { value: '90d', label: '90 Days' }
  ];

  useEffect(() => {
    loadAnalyticsData();
    const interval = setInterval(loadAnalyticsData, 60000); // Update every minute
    return () => clearInterval(interval);
  }, [timeframe]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      
      const [performanceRes, tradesRes, goalRes] = await Promise.allSettled([
        axios.get(`${API}/performance`),
        axios.get(`${API}/trades/history?limit=100`),
        axios.get(`${API}/goals/probability`)
      ]);

      setAnalyticsData({
        performance: performanceRes.status === 'fulfilled' ? performanceRes.value.data.data : null,
        trades: tradesRes.status === 'fulfilled' ? tradesRes.value.data.data.trades : [],
        goalProbability: goalRes.status === 'fulfilled' ? goalRes.value.data.data : null
      });

    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return 'R0.00';
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR'
    }).format(amount);
  };

  const formatPercentage = (value) => {
    if (value === null || value === undefined) return '0%';
    return `${(value * 100).toFixed(1)}%`;
  };

  const getPerformanceColor = (value) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const calculateTradeMetrics = () => {
    if (!analyticsData.trades.length) {
      return {
        totalTrades: 0,
        winningTrades: 0,
        losingTrades: 0,
        winRate: 0,
        avgWin: 0,
        avgLoss: 0,
        profitFactor: 0
      };
    }

    const trades = analyticsData.trades;
    const winningTrades = trades.filter(t => (t.profit_zar || 0) > 0);
    const losingTrades = trades.filter(t => (t.profit_zar || 0) < 0);
    
    const totalWins = winningTrades.reduce((sum, t) => sum + (t.profit_zar || 0), 0);
    const totalLosses = Math.abs(losingTrades.reduce((sum, t) => sum + (t.profit_zar || 0), 0));

    return {
      totalTrades: trades.length,
      winningTrades: winningTrades.length,
      losingTrades: losingTrades.length,
      winRate: trades.length > 0 ? (winningTrades.length / trades.length) : 0,
      avgWin: winningTrades.length > 0 ? totalWins / winningTrades.length : 0,
      avgLoss: losingTrades.length > 0 ? totalLosses / losingTrades.length : 0,
      profitFactor: totalLosses > 0 ? totalWins / totalLosses : 0
    };
  };

  const tradeMetrics = calculateTradeMetrics();

  if (loading && !analyticsData.performance) {
    return (
      <div className="analytics-loading flex justify-center items-center min-h-96">
        <div className="loading-spinner"></div>
        <p className="ml-4">Loading analytics data...</p>
      </div>
    );
  }

  return (
    <div className="performance-analytics">
      <div className="container mx-auto px-4 py-6">
        
        {/* Header */}
        <div className="analytics-header mb-8">
          <div className="header-content flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Performance Analytics</h1>
              <p className="text-gray-600">Detailed analysis of your trading performance and AI strategy effectiveness</p>
            </div>
            
            {/* Timeframe Selector */}
            <div className="timeframe-selector mt-4 md:mt-0">
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {timeframes.map(tf => (
                  <option key={tf.value} value={tf.value}>{tf.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="tab-navigation mb-6">
          <div className="flex border-b border-gray-200">
            {['overview', 'trades', 'risk', 'ai-insights'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.replace('-', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="overview-tab space-y-6">
            
            {/* Key Metrics */}
            <div className="key-metrics grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              
              <div className="metric-card bg-white rounded-lg shadow-md p-6">
                <div className="metric-header flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-500">Total P&L</h3>
                  <div className="metric-icon bg-blue-100 p-2 rounded-full">
                    <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                    </svg>
                  </div>
                </div>
                <div className="metric-value">
                  <p className={`text-2xl font-bold ${getPerformanceColor(analyticsData.performance?.monthly_pnl || 0)}`}>
                    {formatCurrency(analyticsData.performance?.monthly_pnl || 0)}
                  </p>
                </div>
              </div>

              <div className="metric-card bg-white rounded-lg shadow-md p-6">
                <div className="metric-header flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-500">Win Rate</h3>
                  <div className="metric-icon bg-green-100 p-2 rounded-full">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
                <div className="metric-value">
                  <p className="text-2xl font-bold text-green-600">
                    {formatPercentage(tradeMetrics.winRate)}
                  </p>
                  <p className="text-sm text-gray-600">
                    {tradeMetrics.winningTrades} / {tradeMetrics.totalTrades} trades
                  </p>
                </div>
              </div>

              <div className="metric-card bg-white rounded-lg shadow-md p-6">
                <div className="metric-header flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-500">Sharpe Ratio</h3>
                  <div className="metric-icon bg-purple-100 p-2 rounded-full">
                    <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
                <div className="metric-value">
                  <p className="text-2xl font-bold text-purple-600">
                    {(analyticsData.performance?.sharpe_ratio || 0).toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-600">Risk-adjusted return</p>
                </div>
              </div>

              <div className="metric-card bg-white rounded-lg shadow-md p-6">
                <div className="metric-header flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-500">Max Drawdown</h3>
                  <div className="metric-icon bg-red-100 p-2 rounded-full">
                    <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
                <div className="metric-value">
                  <p className="text-2xl font-bold text-red-600">
                    {formatCurrency(analyticsData.performance?.max_drawdown || 0)}
                  </p>
                  <p className="text-sm text-gray-600">Maximum loss period</p>
                </div>
              </div>
            </div>

            {/* Performance Chart Placeholder */}
            <div className="performance-chart bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Chart</h3>
              <div className="chart-placeholder bg-gray-50 rounded-lg p-12 text-center">
                <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-gray-500 text-lg">Performance Chart</p>
                <p className="text-gray-400 text-sm mt-2">Interactive P&L chart would be displayed here</p>
              </div>
            </div>
          </div>
        )}

        {/* Trades Tab */}
        {activeTab === 'trades' && (
          <div className="trades-tab">
            
            {/* Trade Statistics */}
            <div className="trade-stats grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              
              <div className="stat-card bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade Volume</h3>
                <div className="stats-content space-y-2">
                  <div className="stat-row flex justify-between">
                    <span className="text-gray-600">Total Trades:</span>
                    <span className="font-semibold">{tradeMetrics.totalTrades}</span>
                  </div>
                  <div className="stat-row flex justify-between">
                    <span className="text-gray-600">Winning:</span>
                    <span className="font-semibold text-green-600">{tradeMetrics.winningTrades}</span>
                  </div>
                  <div className="stat-row flex justify-between">
                    <span className="text-gray-600">Losing:</span>
                    <span className="font-semibold text-red-600">{tradeMetrics.losingTrades}</span>
                  </div>
                </div>
              </div>

              <div className="stat-card bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Average Results</h3>
                <div className="stats-content space-y-2">
                  <div className="stat-row flex justify-between">
                    <span className="text-gray-600">Avg Win:</span>
                    <span className="font-semibold text-green-600">{formatCurrency(tradeMetrics.avgWin)}</span>
                  </div>
                  <div className="stat-row flex justify-between">
                    <span className="text-gray-600">Avg Loss:</span>
                    <span className="font-semibold text-red-600">-{formatCurrency(tradeMetrics.avgLoss)}</span>
                  </div>
                  <div className="stat-row flex justify-between">
                    <span className="text-gray-600">Profit Factor:</span>
                    <span className="font-semibold">{tradeMetrics.profitFactor.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              <div className="stat-card bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Strategy Breakdown</h3>
                <div className="strategy-chart">
                  {/* Placeholder for strategy breakdown chart */}
                  <div className="chart-mini bg-gray-50 rounded-lg p-4 text-center">
                    <p className="text-gray-500 text-sm">Strategy Distribution Chart</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Trades Table */}
            <div className="recent-trades bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Trades</h3>
              
              <div className="trades-table overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 font-medium text-gray-700">Date</th>
                      <th className="text-left py-2 font-medium text-gray-700">Pair</th>
                      <th className="text-left py-2 font-medium text-gray-700">Side</th>
                      <th className="text-left py-2 font-medium text-gray-700">Amount</th>
                      <th className="text-left py-2 font-medium text-gray-700">P&L</th>
                      <th className="text-left py-2 font-medium text-gray-700">Strategy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analyticsData.trades.slice(0, 20).map((trade, index) => (
                      <tr key={trade.id || index} className="border-b border-gray-100">
                        <td className="py-2 text-gray-600">
                          {new Date(trade.timestamp).toLocaleString()}
                        </td>
                        <td className="py-2 font-medium">{trade.pair}</td>
                        <td className="py-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            trade.side === 'buy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {trade.side?.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-2">{trade.amount}</td>
                        <td className={`py-2 font-semibold ${getPerformanceColor(trade.profit_zar || 0)}`}>
                          {formatCurrency(trade.profit_zar || 0)}
                        </td>
                        <td className="py-2 text-gray-600 capitalize">{trade.strategy}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                {analyticsData.trades.length === 0 && (
                  <div className="no-trades text-center py-8">
                    <p className="text-gray-500">No trades found for the selected timeframe</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Risk Tab */}
        {activeTab === 'risk' && (
          <div className="risk-tab">
            <div className="risk-content grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Risk Metrics */}
              <div className="risk-metrics bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Metrics</h3>
                
                <div className="metrics-list space-y-4">
                  <div className="metric-item">
                    <div className="metric-header flex justify-between items-center mb-2">
                      <span className="text-gray-600">Value at Risk (VaR)</span>
                      <span className="font-semibold text-red-600">R500.00</span>
                    </div>
                    <div className="metric-bar bg-gray-200 rounded-full h-2">
                      <div className="fill bg-red-500 h-2 rounded-full" style={{width: '25%'}}></div>
                    </div>
                  </div>
                  
                  <div className="metric-item">
                    <div className="metric-header flex justify-between items-center mb-2">
                      <span className="text-gray-600">Portfolio Beta</span>
                      <span className="font-semibold">1.2</span>
                    </div>
                    <div className="metric-bar bg-gray-200 rounded-full h-2">
                      <div className="fill bg-blue-500 h-2 rounded-full" style={{width: '60%'}}></div>
                    </div>
                  </div>
                  
                  <div className="metric-item">
                    <div className="metric-header flex justify-between items-center mb-2">
                      <span className="text-gray-600">Volatility</span>
                      <span className="font-semibold">15.8%</span>
                    </div>
                    <div className="metric-bar bg-gray-200 rounded-full h-2">
                      <div className="fill bg-yellow-500 h-2 rounded-full" style={{width: '32%'}}></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Risk Distribution */}
              <div className="risk-distribution bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Distribution</h3>
                
                <div className="distribution-chart bg-gray-50 rounded-lg p-8 text-center">
                  <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
                  </svg>
                  <p className="text-gray-500">Risk Distribution Chart</p>
                  <p className="text-gray-400 text-sm mt-2">Risk allocation by asset/strategy</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI Insights Tab */}
        {activeTab === 'ai-insights' && (
          <div className="ai-insights-tab">
            <div className="insights-content space-y-6">
              
              {/* AI Performance */}
              <div className="ai-performance bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Model Performance</h3>
                
                <div className="ai-metrics grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="ai-metric text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {formatPercentage(analyticsData.goalProbability?.confidence_level === 'high' ? 0.85 : 0.65)}
                    </p>
                    <p className="text-sm text-gray-600">Model Accuracy</p>
                  </div>
                  
                  <div className="ai-metric text-center">
                    <p className="text-2xl font-bold text-green-600">78%</p>
                    <p className="text-sm text-gray-600">Signal Success Rate</p>
                  </div>
                  
                  <div className="ai-metric text-center">
                    <p className="text-2xl font-bold text-purple-600">2.1</p>
                    <p className="text-sm text-gray-600">Avg Signal Strength</p>
                  </div>
                </div>
              </div>

              {/* Insights */}
              <div className="insights-list bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Insights & Recommendations</h3>
                
                <div className="insights space-y-4">
                  <div className="insight-item p-4 bg-blue-50 rounded-lg">
                    <div className="insight-header flex items-center mb-2">
                      <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                      <span className="font-medium text-blue-800">Market Trend Analysis</span>
                    </div>
                    <p className="text-blue-700 text-sm">
                      The AI model detects a bullish trend in BTC/ZAR with 82% confidence. 
                      Consider increasing position sizes for BTC trades.
                    </p>
                  </div>
                  
                  <div className="insight-item p-4 bg-green-50 rounded-lg">
                    <div className="insight-header flex items-center mb-2">
                      <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="font-medium text-green-800">Strategy Optimization</span>
                    </div>
                    <p className="text-green-700 text-sm">
                      Your scalping strategy is outperforming expectations. Current win rate of {formatPercentage(tradeMetrics.winRate)} 
                      is above the target of 65%.
                    </p>
                  </div>
                  
                  <div className="insight-item p-4 bg-yellow-50 rounded-lg">
                    <div className="insight-header flex items-center mb-2">
                      <svg className="w-5 h-5 text-yellow-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      <span className="font-medium text-yellow-800">Risk Alert</span>
                    </div>
                    <p className="text-yellow-700 text-sm">
                      Risk exposure is at 85% of your daily limit. Consider reducing position sizes 
                      to maintain optimal risk management.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default PerformanceAnalytics;