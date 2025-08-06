import React, { useState } from 'react';

const TradingControls = ({ 
  aiTradingActive, 
  setAiTradingActive, 
  setShowConfigModal, 
  setShowChatModal, 
  setShowManualTradeModal,
  onStartTrading,
  onStopTrading 
}) => {
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);

  const handleStartTrading = async () => {
    setIsStarting(true);
    try {
      await onStartTrading();
      setAiTradingActive(true);
    } catch (error) {
      console.error('Failed to start trading:', error);
    } finally {
      setIsStarting(false);
    }
  };

  const handleStopTrading = async () => {
    setIsStopping(true);
    try {
      await onStopTrading();
      setAiTradingActive(false);
    } catch (error) {
      console.error('Failed to stop trading:', error);
    } finally {
      setIsStopping(false);
    }
  };

  const handleEmergencyStop = async () => {
    if (window.confirm('EMERGENCY STOP: This will immediately halt all AI trading activity. Are you sure?')) {
      setIsStopping(true);
      try {
        await onStopTrading();
        setAiTradingActive(false);
      } catch (error) {
        console.error('Emergency stop failed:', error);
      } finally {
        setIsStopping(false);
      }
    }
  };

  return (
    <div className="trading-controls">
      <div className="controls-header">
        <h3>AI Trading Controls</h3>
        <div className="ai-status">
          <span className={`status-dot ${aiTradingActive ? 'active' : 'inactive'}`}></span>
          <span className="status-text">
            {aiTradingActive ? 'AI Trading Active' : 'AI Trading Inactive'}
          </span>
        </div>
      </div>

      <div className="controls-grid">
        {/* Main Trading Controls */}
        <div className="control-section primary-controls">
          <h4>Primary Controls</h4>
          <div className="button-group">
            <button
              className={`control-btn start-btn ${aiTradingActive ? 'disabled' : ''}`}
              onClick={handleStartTrading}
              disabled={aiTradingActive || isStarting}
            >
              {isStarting ? (
                <>
                  <div className="spinner"></div>
                  Starting...
                </>
              ) : (
                <>
                  <span className="btn-icon">▶</span>
                  Start AI Trading
                </>
              )}
            </button>

            <button
              className={`control-btn stop-btn ${!aiTradingActive ? 'disabled' : ''}`}
              onClick={handleStopTrading}
              disabled={!aiTradingActive || isStopping}
            >
              {isStopping ? (
                <>
                  <div className="spinner"></div>
                  Stopping...
                </>
              ) : (
                <>
                  <span className="btn-icon">⏸</span>
                  Stop AI Trading
                </>
              )}
            </button>
          </div>

          <button
            className="control-btn emergency-btn"
            onClick={handleEmergencyStop}
            disabled={isStopping}
          >
            <span className="btn-icon">🛑</span>
            EMERGENCY STOP
          </button>
        </div>

        {/* Configuration & Tools */}
        <div className="control-section secondary-controls">
          <h4>Configuration & Tools</h4>
          <div className="button-group">
            <button
              className="control-btn config-btn"
              onClick={() => setShowConfigModal(true)}
            >
              <span className="btn-icon">⚙</span>
              Advanced Config
            </button>

            <button
              className="control-btn manual-btn"
              onClick={() => setShowManualTradeModal(true)}
            >
              <span className="btn-icon">📈</span>
              Manual Trade
            </button>

            <button
              className="control-btn chat-btn"
              onClick={() => setShowChatModal(true)}
            >
              <span className="btn-icon">💬</span>
              Chat with AI
            </button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="control-section stats-section">
          <h4>Quick Overview</h4>
          <div className="quick-stats">
            <div className="stat-item">
              <span className="stat-label">Active Trades</span>
              <span className="stat-value">3</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Today's P&L</span>
              <span className="stat-value positive">+R 127.50</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Win Rate</span>
              <span className="stat-value">73.5%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingControls;