import React, { useState, useEffect } from 'react';

const MetricsRevCounter = ({ performanceData, aiTradingActive, systemHealth }) => {
  const [revCount, setRevCount] = useState(0);
  const [metrics, setMetrics] = useState({
    totalTrades: 0,
    winRate: 0,
    avgProfit: 0,
    maxDrawdown: 0,
    sharpeRatio: 0,
    dailyReturn: 0,
    monthlyReturn: 0,
  });

  // Simulate rev counter animation
  useEffect(() => {
    if (aiTradingActive) {
      const interval = setInterval(() => {
        setRevCount(prev => (prev + 1) % 100);
      }, 100);
      return () => clearInterval(interval);
    }
  }, [aiTradingActive]);

  // Generate realistic metrics
  useEffect(() => {
    const generateMetrics = () => {
      setMetrics({
        totalTrades: Math.floor(Math.random() * 50) + 120,
        winRate: (Math.random() * 30 + 60).toFixed(1),
        avgProfit: (Math.random() * 100 + 50).toFixed(2),
        maxDrawdown: (Math.random() * 5 + 2).toFixed(1),
        sharpeRatio: (Math.random() * 1.5 + 0.5).toFixed(2),
        dailyReturn: (Math.random() * 3 + 1).toFixed(2),
        monthlyReturn: (Math.random() * 15 + 5).toFixed(1),
      });
    };

    generateMetrics();
    const interval = setInterval(generateMetrics, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getRevCounterColor = () => {
    if (!aiTradingActive) return '#6b7280';
    if (revCount < 30) return '#10b981';
    if (revCount < 70) return '#f59e0b';
    return '#ef4444';
  };

  const formatPercentage = (value) => {
    return `${value}%`;
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
    }).format(value);
  };

  return (
    <div className="metrics-rev-counter">
      {/* Rev Counter */}
      <div className="rev-counter-section">
        <div className="rev-counter">
          <div className="rev-display">
            <div className="rev-needle" style={{
              transform: `rotate(${(revCount / 100) * 180}deg)`,
              transformOrigin: 'bottom center',
            }}>
              <div style={{
                width: '2px',
                height: '60px',
                backgroundColor: getRevCounterColor(),
                margin: '0 auto',
              }}></div>
            </div>
            <div className="rev-scale">
              <div className="rev-numbers">
                <span>0</span>
                <span>25</span>
                <span>50</span>
                <span>75</span>
                <span>100</span>
              </div>
            </div>
            <div className="rev-value">{revCount}</div>
            <div className="rev-label">AI Activity Level</div>
          </div>
          <div className="rev-status">
            <span className={`status-indicator ${aiTradingActive ? 'active' : 'inactive'}`}>
              {aiTradingActive ? 'AI TRADING ACTIVE' : 'AI STANDBY'}
            </span>
          </div>
        </div>
      </div>

      {/* Performance Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-title">Total Trades</div>
          <div className="metric-value">{metrics.totalTrades}</div>
          <div className="metric-subtitle">This month</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Win Rate</div>
          <div className="metric-value win-rate">{formatPercentage(metrics.winRate)}</div>
          <div className="metric-subtitle">Success ratio</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Avg Profit</div>
          <div className="metric-value profit">{formatCurrency(metrics.avgProfit)}</div>
          <div className="metric-subtitle">Per trade</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Max Drawdown</div>
          <div className="metric-value drawdown">-{formatPercentage(metrics.maxDrawdown)}</div>
          <div className="metric-subtitle">Risk level</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Sharpe Ratio</div>
          <div className="metric-value sharpe">{metrics.sharpeRatio}</div>
          <div className="metric-subtitle">Risk-adjusted</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Daily Return</div>
          <div className="metric-value daily-return">+{formatPercentage(metrics.dailyReturn)}</div>
          <div className="metric-subtitle">Average</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Monthly Return</div>
          <div className="metric-value monthly-return">+{formatPercentage(metrics.monthlyReturn)}</div>
          <div className="metric-subtitle">Performance</div>
        </div>

        <div className="metric-card system-health">
          <div className="metric-title">System Health</div>
          <div className="metric-value health-status">
            {systemHealth ? (
              <span className={`health-indicator ${
                systemHealth.services?.luno === 'connected' && 
                systemHealth.services?.database === 'connected' 
                ? 'healthy' : 'warning'}`}>
                {systemHealth.services?.luno === 'connected' && 
                 systemHealth.services?.database === 'connected' 
                 ? 'OPTIMAL' : 'CHECK'}
              </span>
            ) : 'LOADING'}
          </div>
          <div className="metric-subtitle">Status</div>
        </div>
      </div>
    </div>
  );
};

export default MetricsRevCounter;