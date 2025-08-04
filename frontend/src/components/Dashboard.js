import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    balance: null,
    performance: null,
    goalProbability: null,
    aiStatus: null,
    recentTrades: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load all dashboard data in parallel
      const [balanceRes, performanceRes, goalRes, aiRes, tradesRes] = await Promise.allSettled([
        axios.get(`${API}/balance`),
        axios.get(`${API}/performance`),
        axios.get(`${API}/goals/probability`),
        axios.get(`${API}/ai-strategy/status`),
        axios.get(`${API}/trades/history?limit=10`)
      ]);

      setDashboardData({
        balance: balanceRes.status === 'fulfilled' ? balanceRes.value.data.data : null,
        performance: performanceRes.status === 'fulfilled' ? performanceRes.value.data.data : null,
        goalProbability: goalRes.status === 'fulfilled' ? goalRes.value.data.data : null,
        aiStatus: aiRes.status === 'fulfilled' ? aiRes.value.data.data : null,
        recentTrades: tradesRes.status === 'fulfilled' ? tradesRes.value.data.data.trades : []
      });

      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Dashboard data loading failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount, currency = 'ZAR') => {
    if (amount === null || amount === undefined) return 'N/A';
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatPercentage = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };

  if (loading && !dashboardData.balance) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="container mx-auto px-4 py-6">
        
        {/* Header */}
        <div className="dashboard-header mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Dashboard</h1>
          <p className="text-gray-600">Real-time overview of your AI crypto trading performance</p>
          {error && (
            <div className="error-banner mt-2 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              Error loading data: {error}
            </div>
          )}
        </div>

        {/* Key Metrics Row */}
        <div className="metrics-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          
          {/* Account Balance */}
          <div className="metric-card bg-white rounded-lg shadow-md p-6">
            <div className="metric-header flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">Account Balance</h3>
              <div className="metric-icon bg-green-100 p-2 rounded-full">
                <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zM14 6a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2V8a2 2 0 012-2h8z" />
                </svg>
              </div>
            </div>
            <div className="metric-value">
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(dashboardData.balance?.ZAR_balance)}
              </p>
              <p className="text-sm text-gray-600">
                Available: {formatCurrency(dashboardData.balance?.ZAR_balance - (dashboardData.balance?.ZAR_reserved || 0))}
              </p>
            </div>
          </div>

          {/* Daily P&L */}
          <div className="metric-card bg-white rounded-lg shadow-md p-6">
            <div className="metric-header flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">Today's P&L</h3>
              <div className={`metric-icon p-2 rounded-full ${dashboardData.performance?.daily_pnl >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                <svg className={`w-5 h-5 ${dashboardData.performance?.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d={dashboardData.performance?.daily_pnl >= 0 ? "M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z" : "M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z"} clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="metric-value">
              <p className={`text-2xl font-bold ${dashboardData.performance?.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(dashboardData.performance?.daily_pnl)}
              </p>
              <p className="text-sm text-gray-600">
                Target: R1,000 ({dashboardData.goalProbability?.current_progress?.progress_percent?.toFixed(1) || 0}%)
              </p>
            </div>
          </div>

          {/* Success Probability */}
          <div className="metric-card bg-white rounded-lg shadow-md p-6">
            <div className="metric-header flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">Daily Goal Probability</h3>
              <div className="metric-icon bg-blue-100 p-2 rounded-full">
                <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="metric-value">
              <p className="text-2xl font-bold text-blue-600">
                {formatPercentage(dashboardData.goalProbability?.probabilities?.daily_target_1000)}
              </p>
              <p className="text-sm text-gray-600 capitalize">
                Confidence: {dashboardData.goalProbability?.confidence_level || 'Unknown'}
              </p>
            </div>
          </div>

          {/* AI Status */}
          <div className="metric-card bg-white rounded-lg shadow-md p-6">
            <div className="metric-header flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">AI Strategy</h3>
              <div className={`metric-icon p-2 rounded-full ${dashboardData.aiStatus?.is_active ? 'bg-green-100' : 'bg-gray-100'}`}>
                <svg className={`w-5 h-5 ${dashboardData.aiStatus?.is_active ? 'text-green-600' : 'text-gray-600'}`} fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            <div className="metric-value">
              <p className={`text-2xl font-bold ${dashboardData.aiStatus?.is_active ? 'text-green-600' : 'text-gray-600'}`}>
                {dashboardData.aiStatus?.is_active ? 'Active' : 'Inactive'}
              </p>
              <p className="text-sm text-gray-600">
                Confidence: {formatPercentage(dashboardData.aiStatus?.confidence)}
              </p>
            </div>
          </div>
        </div>

        {/* Charts and Tables Row */}
        <div className="dashboard-content grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Performance Chart */}
          <div className="performance-chart lg:col-span-2 bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Overview</h3>
            <div className="chart-container">
              <div className="performance-stats grid grid-cols-3 gap-4 mb-6">
                <div className="stat-item text-center">
                  <p className="text-sm text-gray-500">Weekly P&L</p>
                  <p className={`text-lg font-semibold ${dashboardData.performance?.weekly_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(dashboardData.performance?.weekly_pnl)}
                  </p>
                </div>
                <div className="stat-item text-center">
                  <p className="text-sm text-gray-500">Monthly P&L</p>
                  <p className={`text-lg font-semibold ${dashboardData.performance?.monthly_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(dashboardData.performance?.monthly_pnl)}
                  </p>
                </div>
                <div className="stat-item text-center">
                  <p className="text-sm text-gray-500">Win Rate</p>
                  <p className="text-lg font-semibold text-blue-600">
                    {formatPercentage(dashboardData.performance?.win_rate)}
                  </p>
                </div>
              </div>
              
              {/* Placeholder for actual chart - would integrate with Chart.js or similar */}
              <div className="chart-placeholder bg-gray-50 rounded-lg p-8 text-center">
                <p className="text-gray-500">Performance chart will be displayed here</p>
                <p className="text-sm text-gray-400 mt-2">Integration with charting library needed</p>
              </div>
            </div>
          </div>

          {/* Recent Trades */}
          <div className="recent-trades bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Trades</h3>
            <div className="trades-list space-y-3">
              {dashboardData.recentTrades.length > 0 ? (
                dashboardData.recentTrades.slice(0, 5).map((trade, index) => (
                  <div key={trade.id || index} className="trade-item p-3 bg-gray-50 rounded-lg">
                    <div className="trade-header flex justify-between items-center mb-1">
                      <span className="text-sm font-medium">{trade.pair}</span>
                      <span className={`text-xs px-2 py-1 rounded ${trade.side === 'buy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {trade.side?.toUpperCase()}
                      </span>
                    </div>
                    <div className="trade-details text-xs text-gray-600">
                      <p>Amount: {trade.amount}</p>
                      <p>P&L: {formatCurrency(trade.profit_zar)}</p>
                      <p>Strategy: {trade.strategy}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-trades text-center py-8">
                  <p className="text-gray-500">No recent trades</p>
                  <p className="text-sm text-gray-400 mt-2">Start trading to see activity here</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Goal Progress Section */}
        <div className="goal-progress mt-8 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Goal Achievement Progress</h3>
          <div className="progress-bars space-y-4">
            
            {/* Daily Goal */}
            <div className="goal-item">
              <div className="goal-header flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Daily Target (R1,000)</span>
                <span className="text-sm text-gray-600">
                  {formatCurrency(dashboardData.goalProbability?.current_progress?.daily_profit)} / R1,000
                </span>
              </div>
              <div className="progress-bar bg-gray-200 rounded-full h-2">
                <div 
                  className="progress-fill bg-green-500 h-2 rounded-full"
                  style={{ width: `${Math.min((dashboardData.goalProbability?.current_progress?.progress_percent || 0), 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Weekly Goal */}
            <div className="goal-item">
              <div className="goal-header flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Weekly Target (R7,000)</span>
                <span className="text-sm text-gray-600">
                  {formatPercentage(dashboardData.goalProbability?.probabilities?.weekly_target_7000)} probability
                </span>
              </div>
              <div className="progress-bar bg-gray-200 rounded-full h-2">
                <div 
                  className="progress-fill bg-blue-500 h-2 rounded-full"
                  style={{ width: `${(dashboardData.goalProbability?.probabilities?.weekly_target_7000 || 0) * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Monthly Goal */}
            <div className="goal-item">
              <div className="goal-header flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Monthly Target (R30,000)</span>
                <span className="text-sm text-gray-600">
                  {formatPercentage(dashboardData.goalProbability?.probabilities?.monthly_target_30000)} probability
                </span>
              </div>
              <div className="progress-bar bg-gray-200 rounded-full h-2">
                <div 
                  className="progress-fill bg-purple-500 h-2 rounded-full"
                  style={{ width: `${(dashboardData.goalProbability?.probabilities?.monthly_target_30000 || 0) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;