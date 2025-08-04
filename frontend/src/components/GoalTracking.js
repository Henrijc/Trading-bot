import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GoalTracking = () => {
  const [goalData, setGoalData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('daily');

  useEffect(() => {
    loadGoalData();
    const interval = setInterval(loadGoalData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadGoalData = async () => {
    try {
      const [goalResponse, performanceResponse] = await Promise.allSettled([
        axios.get(`${API}/goals/probability`),
        axios.get(`${API}/performance`)
      ]);

      if (goalResponse.status === 'fulfilled') {
        setGoalData(goalResponse.value.data.data);
      }

      if (performanceResponse.status === 'fulfilled') {
        setPerformanceData(performanceResponse.value.data.data);
      }

      setLoading(false);
    } catch (error) {
      console.error('Failed to load goal data:', error);
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

  const getConfidenceColor = (confidence) => {
    switch (confidence) {
      case 'high': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-orange-600 bg-orange-100';
      default: return 'text-red-600 bg-red-100';
    }
  };

  const getProbabilityColor = (probability) => {
    if (probability >= 0.8) return 'text-green-600';
    if (probability >= 0.6) return 'text-blue-600';
    if (probability >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="goal-tracking-loading flex justify-center items-center min-h-96">
        <div className="loading-spinner"></div>
        <p className="ml-4">Loading goal tracking data...</p>
      </div>
    );
  }

  return (
    <div className="goal-tracking">
      <div className="container mx-auto px-4 py-6">
        
        {/* Header */}
        <div className="goal-header mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Goal Achievement Tracking</h1>
          <p className="text-gray-600">Monitor your progress towards daily, weekly, and monthly profit targets</p>
        </div>

        {/* Goal Cards */}
        <div className="goals-grid grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          
          {/* Daily Goal */}
          <div className="goal-card bg-white rounded-lg shadow-md p-6">
            <div className="goal-header flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Daily Target</h3>
              <div className="goal-icon bg-green-100 p-2 rounded-full">
                <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" />
                </svg>
              </div>
            </div>
            
            <div className="goal-content">
              <div className="target-amount mb-2">
                <span className="text-sm text-gray-500">Target:</span>
                <span className="text-2xl font-bold text-gray-900 ml-2">R1,000</span>
              </div>
              
              <div className="current-progress mb-4">
                <span className="text-sm text-gray-500">Current:</span>
                <span className="text-xl font-semibold text-green-600 ml-2">
                  {formatCurrency(goalData?.current_progress?.daily_profit || 0)}
                </span>
              </div>

              <div className="progress-bar bg-gray-200 rounded-full h-3 mb-4">
                <div 
                  className="progress-fill bg-green-500 h-3 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${Math.min((goalData?.current_progress?.progress_percent || 0), 100)}%` 
                  }}
                ></div>
              </div>

              <div className="goal-stats grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Success Probability</p>
                  <p className={`text-lg font-bold ${getProbabilityColor(goalData?.probabilities?.daily_target_1000 || 0)}`}>
                    {formatPercentage(goalData?.probabilities?.daily_target_1000)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Confidence</p>
                  <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${getConfidenceColor(goalData?.confidence_level)}`}>
                    {goalData?.confidence_level || 'unknown'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Weekly Goal */}
          <div className="goal-card bg-white rounded-lg shadow-md p-6">
            <div className="goal-header flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Weekly Target</h3>
              <div className="goal-icon bg-blue-100 p-2 rounded-full">
                <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            
            <div className="goal-content">
              <div className="target-amount mb-2">
                <span className="text-sm text-gray-500">Target:</span>
                <span className="text-2xl font-bold text-gray-900 ml-2">R7,000</span>
              </div>
              
              <div className="current-progress mb-4">
                <span className="text-sm text-gray-500">Current:</span>
                <span className="text-xl font-semibold text-blue-600 ml-2">
                  {formatCurrency(performanceData?.weekly_pnl || 0)}
                </span>
              </div>

              <div className="progress-bar bg-gray-200 rounded-full h-3 mb-4">
                <div 
                  className="progress-fill bg-blue-500 h-3 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${Math.min(((performanceData?.weekly_pnl || 0) / 7000) * 100, 100)}%` 
                  }}
                ></div>
              </div>

              <div className="goal-stats grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Success Probability</p>
                  <p className={`text-lg font-bold ${getProbabilityColor(goalData?.probabilities?.weekly_target_7000 || 0)}`}>
                    {formatPercentage(goalData?.probabilities?.weekly_target_7000)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Days Left</p>
                  <p className="text-lg font-bold text-gray-700">
                    {7 - new Date().getDay()} days
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Monthly Goal */}
          <div className="goal-card bg-white rounded-lg shadow-md p-6">
            <div className="goal-header flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Monthly Target</h3>
              <div className="goal-icon bg-purple-100 p-2 rounded-full">
                <svg className="w-6 h-6 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            
            <div className="goal-content">
              <div className="target-amount mb-2">
                <span className="text-sm text-gray-500">Target:</span>
                <span className="text-2xl font-bold text-gray-900 ml-2">R30,000</span>
              </div>
              
              <div className="current-progress mb-4">
                <span className="text-sm text-gray-500">Current:</span>
                <span className="text-xl font-semibold text-purple-600 ml-2">
                  {formatCurrency(performanceData?.monthly_pnl || 0)}
                </span>
              </div>

              <div className="progress-bar bg-gray-200 rounded-full h-3 mb-4">
                <div 
                  className="progress-fill bg-purple-500 h-3 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${Math.min(((performanceData?.monthly_pnl || 0) / 30000) * 100, 100)}%` 
                  }}
                ></div>
              </div>

              <div className="goal-stats grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Success Probability</p>
                  <p className={`text-lg font-bold ${getProbabilityColor(goalData?.probabilities?.monthly_target_30000 || 0)}`}>
                    {formatPercentage(goalData?.probabilities?.monthly_target_30000)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Days Left</p>
                  <p className="text-lg font-bold text-gray-700">
                    {new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate() - new Date().getDate()} days
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Analytics */}
        <div className="detailed-analytics grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          
          {/* Performance Statistics */}
          <div className="performance-stats bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Statistics</h3>
            
            <div className="stats-grid space-y-4">
              <div className="stat-row flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-gray-600">Total Trades</span>
                <span className="font-semibold">{performanceData?.total_trades || 0}</span>
              </div>
              
              <div className="stat-row flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-gray-600">Win Rate</span>
                <span className="font-semibold text-green-600">
                  {formatPercentage(performanceData?.win_rate)}
                </span>
              </div>
              
              <div className="stat-row flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-gray-600">Sharpe Ratio</span>
                <span className="font-semibold">
                  {(performanceData?.sharpe_ratio || 0).toFixed(2)}
                </span>
              </div>
              
              <div className="stat-row flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-gray-600">Max Drawdown</span>
                <span className="font-semibold text-red-600">
                  {formatCurrency(performanceData?.max_drawdown)}
                </span>
              </div>
              
              <div className="stat-row flex justify-between items-center py-2">
                <span className="text-gray-600">Current Balance</span>
                <span className="font-semibold text-blue-600">
                  {formatCurrency(performanceData?.current_balance)}
                </span>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div className="recommendations bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Recommendations</h3>
            
            <div className="recommendations-content space-y-4">
              {goalData?.recommendations ? (
                <div className="recommendation-item p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800">{goalData.recommendations}</p>
                </div>
              ) : (
                <div className="no-recommendations text-center py-8">
                  <svg className="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <p className="text-gray-500">No specific recommendations available</p>
                  <p className="text-sm text-gray-400 mt-2">Continue trading to receive AI insights</p>
                </div>
              )}
              
              {/* Strategy Suggestions */}
              <div className="strategy-suggestions">
                <h4 className="font-semibold text-gray-900 mb-2">Strategy Suggestions</h4>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center text-gray-600">
                    <svg className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Focus on high-confidence AI signals
                  </li>
                  <li className="flex items-center text-gray-600">
                    <svg className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Maintain strict risk management
                  </li>
                  <li className="flex items-center text-gray-600">
                    <svg className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Monitor market conditions closely
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Goal Timeline */}
        <div className="goal-timeline bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Achievement Timeline</h3>
          
          <div className="timeline-chart">
            {/* This would integrate with a charting library like Chart.js */}
            <div className="chart-placeholder bg-gray-50 rounded-lg p-12 text-center">
              <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p className="text-gray-500 text-lg">Timeline Chart</p>
              <p className="text-gray-400 text-sm mt-2">Goal achievement progress over time would be displayed here</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default GoalTracking;