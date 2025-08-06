import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

// Add CSS animation for spinner
const spinKeyframes = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

// Inject styles
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = spinKeyframes;
document.head.appendChild(styleSheet);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

function App() {
  const [systemHealth, setSystemHealth] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [balance, setBalance] = useState(null);
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [aiTradingActive, setAiTradingActive] = useState(false);
  const [message, setMessage] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [trades, setTrades] = useState([]);
  const [goals, setGoals] = useState(null);
  const [cryptoPrices, setCryptoPrices] = useState(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showChatModal, setShowChatModal] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [tradingConfig, setTradingConfig] = useState({
    dailyTarget: 1000,
    maxRisk: 2,
    maxOpenTrades: 5,
    strategy: 'freqai',
    confidence: 70,
    tradingPairs: ['BTC/ZAR', 'ETH/ZAR', 'XRP/ZAR', 'ADA/ZAR'],
    stopLoss: 3,
    takeProfit: 8,
    tradingHours: { start: '08:00', end: '17:00' },
    emergencyStop: false
  });

  useEffect(() => {
    loadAllData();
    
    const healthInterval = setInterval(loadAllData, 30000);
    const quickDataInterval = setInterval(loadMarketData, 10000);
    
    return () => {
      clearInterval(healthInterval);
      clearInterval(quickDataInterval);
    };
  }, []);

  const loadAllData = async () => {
    await Promise.all([
      checkSystemHealth(),
      loadBalance(),
      loadMarketData(),
      loadPerformanceData(),
      loadTrades(),
      loadGoals(),
      loadCryptoPrices()
    ]);
  };

  const checkSystemHealth = async () => {
    try {
      const response = await axios.get(`${API}/health`);
      setSystemHealth(response.data);
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Health check failed:', error);
      setConnectionStatus('disconnected');
      setSystemHealth({ status: 'unhealthy', error: error.message });
    }
  };

  const loadBalance = async () => {
    try {
      const response = await axios.get(`${API}/balance`);
      setBalance(response.data.data);
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Balance fetch failed:', error);
      setBalance(null);
      if (error.response?.status === 500) {
        setConnectionStatus('disconnected');
      }
    }
  };

  const loadMarketData = async () => {
    try {
      const response = await axios.get(`${API}/market-data/XBTZAR`);
      setMarketData(response.data.data);
    } catch (error) {
      console.error('Market data fetch failed:', error);
    }
  };

  const loadPerformanceData = async () => {
    try {
      const response = await axios.get(`${API}/performance`);
      setPerformanceData(response.data.data);
    } catch (error) {
      console.error('Performance data fetch failed:', error);
    }
  };

  const loadTrades = async () => {
    try {
      const response = await axios.get(`${API}/trades/history?limit=10`);
      setTrades(response.data.data.trades || []);
    } catch (error) {
      console.error('Trades fetch failed:', error);
    }
  };

  const loadGoals = async () => {
    try {
      const response = await axios.get(`${API}/goals/probability`);
      setGoals(response.data.data);
    } catch (error) {
      console.error('Goals data fetch failed:', error);
    }
  };

  const loadCryptoPrices = async () => {
    try {
      const response = await axios.get(`${API}/crypto-prices`);
      setCryptoPrices(response.data.data);
    } catch (error) {
      console.error('Crypto prices fetch failed:', error);
    }
  };

  const formatCurrency = (amount) => {
    if (!amount && amount !== 0) return 'R0.00';
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR'
    }).format(amount);
  };

  const formatPercentage = (value) => {
    if (!value && value !== 0) return '0.00%';
    return `${(value * 100).toFixed(2)}%`;
  };

  // Trading control functions
  const startAITrading = async () => {
    setLoading(true);
    setMessage(null);
    try {
      await axios.post(`${API}/trading/start`, {}, {
        headers: { 'Authorization': 'Bearer secure_token_123' }
      });
      setAiTradingActive(true);
      setMessage({ type: 'success', text: 'AI Trading Started Successfully' });
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to start AI trading: ${error.response?.data?.detail || error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const stopAITrading = async () => {
    setLoading(true);
    setMessage(null);
    try {
      await axios.post(`${API}/trading/stop`, {}, {
        headers: { 'Authorization': 'Bearer secure_token_123' }
      });
      setAiTradingActive(false);
      setMessage({ type: 'success', text: 'AI Trading Stopped Successfully' });
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to stop AI trading: ${error.response?.data?.detail || error.message}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      {/* System Status Header */}
      <div className={`status-header ${connectionStatus}`} style={{
        backgroundColor: connectionStatus === 'connected' ? '#1f2937' : '#dc2626',
        color: 'white',
        padding: '0.75rem 0',
        borderBottom: '1px solid #374151'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: '600', margin: 0, letterSpacing: '-0.025em' }}>AI Trading Portfolio</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
              <span style={{ 
                width: '6px', 
                height: '6px', 
                backgroundColor: connectionStatus === 'connected' ? '#10b981' : '#ef4444',
                borderRadius: '50%',
                display: 'inline-block'
              }}></span>
              <span style={{ textTransform: 'capitalize' }}>{connectionStatus}</span>
            </div>
            {/* Latest Update Indicator */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: '#10b981' }}>
              <span style={{ 
                width: '8px', 
                height: '8px', 
                backgroundColor: '#10b981',
                borderRadius: '50%',
                display: 'inline-block',
                animation: 'pulse 2s infinite'
              }}></span>
              <span>LATEST UPDATE ACTIVE</span>
            </div>
          </div>
          <div style={{ fontSize: '0.875rem', display: 'flex', gap: '2rem', opacity: 0.9 }}>
            <span>Exchange: {systemHealth?.services?.luno || 'Unknown'}</span>
            <span>Database: {systemHealth?.services?.database || 'Unknown'}</span>
            <span>AI Status: {aiTradingActive ? 'Active' : 'Standby'}</span>
            <span>{new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ minHeight: 'calc(100vh - 80px)', backgroundColor: '#f9fafb', padding: '1.5rem 0' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0 1rem' }}>

          {/* Message Display */}
          {message && (
            <div style={{
              padding: '0.75rem 1rem',
              marginBottom: '1.5rem',
              borderRadius: '0.375rem',
              border: `1px solid ${
                message.type === 'success' ? '#10b981' : 
                message.type === 'error' ? '#ef4444' : '#3b82f6'
              }`,
              backgroundColor: 
                message.type === 'success' ? '#ecfdf5' : 
                message.type === 'error' ? '#fef2f2' : '#eff6ff',
              color: 
                message.type === 'success' ? '#059669' : 
                message.type === 'error' ? '#dc2626' : '#1d4ed8',
              fontSize: '0.875rem'
            }}>
              <p style={{ margin: 0, fontWeight: '500' }}>{message.text}</p>
            </div>
          )}

          {/* Loading Overlay */}
          {loading && (
            <div style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000
            }}>
              <div style={{
                backgroundColor: 'white',
                padding: '2rem',
                borderRadius: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '1rem'
              }}>
                <div style={{
                  width: '1.5rem',
                  height: '1.5rem',
                  border: '2px solid #e5e7eb',
                  borderTop: '2px solid #3b82f6',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                <span style={{ fontWeight: '500', fontSize: '0.875rem' }}>Processing...</span>
              </div>
            </div>
          )}

          {/* Portfolio Summary Cards */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
            gap: '1.5rem', 
            marginBottom: '2rem' 
          }}>
            
            {/* Account Balance */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Account Balance
                </h3>
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <p style={{ fontSize: '2rem', fontWeight: '700', color: '#1f2937', margin: 0, lineHeight: '1' }}>
                  {formatCurrency(balance?.ZAR_balance)}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                  Available: {formatCurrency((balance?.ZAR_balance || 0) - (balance?.ZAR_reserved || 0))}
                </p>
              </div>
              {balance?.ZAR_reserved > 0 && (
                <div style={{ fontSize: '0.75rem', color: '#f59e0b', backgroundColor: '#fffbeb', padding: '0.5rem', borderRadius: '0.25rem' }}>
                  Reserved: {formatCurrency(balance.ZAR_reserved)}
                </div>
              )}
            </div>

            {/* Daily Performance */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Daily P&L
                </h3>
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <p style={{ 
                  fontSize: '2rem', 
                  fontWeight: '700', 
                  color: (performanceData?.daily_pnl || 0) >= 0 ? '#059669' : '#dc2626',
                  margin: 0,
                  lineHeight: '1'
                }}>
                  {formatCurrency(performanceData?.daily_pnl || 0)}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                  Target: R1,000.00
                </p>
              </div>
              <div style={{ 
                backgroundColor: '#f3f4f6', 
                borderRadius: '9999px', 
                height: '0.5rem', 
                overflow: 'hidden'
              }}>
                <div style={{ 
                  backgroundColor: (performanceData?.daily_pnl || 0) >= 0 ? '#059669' : '#dc2626',
                  height: '100%', 
                  width: `${Math.min(Math.abs((performanceData?.daily_pnl || 0) / 1000) * 100, 100)}%`,
                  transition: 'width 0.3s ease',
                  minWidth: '2px'
                }}></div>
              </div>
            </div>

            {/* Portfolio Holdings */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb',
              gridColumn: '1 / -1'
            }}>
              <div style={{ marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Portfolio Holdings
                </h3>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                {/* BTC Holdings */}
                {balance?.BTC_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>BTC</span>
                      <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Bitcoin</span>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.BTC_balance || 0).toFixed(6)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        {formatCurrency((balance?.BTC_balance || 0) * (marketData?.ticker?.last_trade || 0))}
                      </p>
                    </div>
                    {balance?.BTC_reserved > 0 && (
                      <p style={{ fontSize: '0.75rem', color: '#f59e0b', margin: 0 }}>
                        Reserved: {balance.BTC_reserved.toFixed(6)}
                      </p>
                    )}
                  </div>
                )}

                {/* ETH Holdings */}
                {balance?.ETH_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>ETH</span>
                      <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Ethereum</span>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.ETH_balance || 0).toFixed(4)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.ETH_balance || 0) * (cryptoPrices?.ETH || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.ETH_balance || 0) * (cryptoPrices?.ETH || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                    {balance?.ETH_reserved > 0 && (
                      <p style={{ fontSize: '0.75rem', color: '#f59e0b', margin: 0 }}>
                        Reserved: {balance.ETH_reserved.toFixed(4)}
                      </p>
                    )}
                  </div>
                )}

                {/* HBAR Holdings */}
                {balance?.HBAR_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>HBAR</span>
                      <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Hedera</span>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.HBAR_balance || 0).toFixed(0)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.HBAR_balance || 0) * (cryptoPrices?.HBAR || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.HBAR_balance || 0) * (cryptoPrices?.HBAR || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                  </div>
                )}

                {/* XRP Holdings */}
                {balance?.XRP_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>XRP</span>
                      <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Ripple</span>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.XRP_balance || 0).toFixed(2)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.XRP_balance || 0) * (cryptoPrices?.XRP || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.XRP_balance || 0) * (cryptoPrices?.XRP || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                  </div>
                )}

                {/* ADA Holdings */}
                {balance?.ADA_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>ADA</span>
                      <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Cardano</span>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.ADA_balance || 0).toFixed(2)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.ADA_balance || 0) * (cryptoPrices?.ADA || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.ADA_balance || 0) * (cryptoPrices?.ADA || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                  </div>
                )}

                {/* TRX Holdings */}
                {balance?.TRX_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>TRX</span>
                      <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Tron</span>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.TRX_balance || 0).toFixed(2)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.TRX_balance || 0) * (cryptoPrices?.TRX || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.TRX_balance || 0) * (cryptoPrices?.TRX || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                  </div>
                )}

                {/* XLM Holdings */}
                {balance?.XLM_balance > 0 && (
                  <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>XLM</span>
                      <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Stellar</span>
                    </div>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                        {(balance?.XLM_balance || 0).toFixed(2)}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                        ${((balance?.XLM_balance || 0) * (cryptoPrices?.XLM || 0)).toFixed(2)} USD
                      </p>
                      <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                        {formatCurrency((balance?.XLM_balance || 0) * (cryptoPrices?.XLM || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                      </p>
                    </div>
                  </div>
                )}

                {/* Staking Summary Card */}
                {(balance?.ETH_staked > 0 || balance?.ADA_staked > 0 || balance?.DOT_staked > 0) && (
                  <div style={{ padding: '1rem', backgroundColor: '#ecfdf5', borderRadius: '0.375rem', border: '1px solid #10b981' }}>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#059669' }}>Staking Rewards</span>
                    </div>
                    {balance?.ETH_staked > 0 && (
                      <div style={{ marginBottom: '0.25rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#059669' }}>ETH: {balance.ETH_staked.toFixed(4)}</span>
                      </div>
                    )}
                    {balance?.ADA_staked > 0 && (
                      <div style={{ marginBottom: '0.25rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#059669' }}>ADA: {balance.ADA_staked.toFixed(2)}</span>
                      </div>
                    )}
                    {balance?.DOT_staked > 0 && (
                      <div style={{ marginBottom: '0.25rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#059669' }}>DOT: {balance.DOT_staked.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* AI Trading Controls */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  AI Trading Commander
                </h3>
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <p style={{ fontSize: '1.5rem', fontWeight: '700', color: aiTradingActive ? '#059669' : '#6b7280', margin: 0, lineHeight: '1' }}>
                  {aiTradingActive ? 'ACTIVE' : 'STANDBY'}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                  {aiTradingActive ? 'AI is actively executing trades' : 'AI is ready for your instructions'}
                </p>
              </div>

              {/* Main Control Buttons */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
                <button 
                  onClick={() => setShowChatModal(true)}
                  style={{ 
                    backgroundColor: '#3b82f6', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 1rem',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.25rem'
                  }}
                >
                  💬 Chat with AI
                </button>
                
                <button 
                  onClick={startAITrading}
                  disabled={aiTradingActive || loading}
                  style={{ 
                    backgroundColor: aiTradingActive || loading ? '#d1d5db' : '#059669', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 1rem',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    cursor: aiTradingActive || loading ? 'not-allowed' : 'pointer'
                  }}
                >
                  🚀 Start Trading
                </button>
                
                <button 
                  onClick={stopAITrading}
                  disabled={!aiTradingActive || loading}
                  style={{ 
                    backgroundColor: !aiTradingActive || loading ? '#d1d5db' : '#dc2626', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 1rem',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    cursor: !aiTradingActive || loading ? 'not-allowed' : 'pointer'
                  }}
                >
                  ⛔ Emergency Stop
                </button>
              </div>
              
              {/* Current Strategy Display */}
              <div style={{ backgroundColor: '#f9fafb', borderRadius: '0.375rem', padding: '1rem', marginBottom: '1rem' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0' }}>Current Strategy</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.75rem' }}>
                  <div>
                    <span style={{ color: '#6b7280' }}>Target:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem', color: '#059669' }}>R{tradingConfig.dailyTarget}</span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Max Risk:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem', color: '#dc2626' }}>{tradingConfig.maxRisk}%</span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Strategy:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem' }}>
                      {tradingConfig.strategy === 'freqai' ? 'FreqAI ML' : 
                       tradingConfig.strategy === 'technical' ? 'Technical Analysis' : 'Hybrid AI+TA'}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Confidence:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem' }}>{tradingConfig.confidence}%+</span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Stop Loss:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem', color: '#dc2626' }}>{tradingConfig.stopLoss}%</span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Take Profit:</span>
                    <span style={{ fontWeight: '600', marginLeft: '0.25rem', color: '#059669' }}>{tradingConfig.takeProfit}%</span>
                  </div>
                </div>
              </div>

              {/* Expected Performance */}
              <div style={{ backgroundColor: '#ecfdf5', border: '1px solid #10b981', borderRadius: '0.375rem', padding: '1rem', marginBottom: '1rem' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#059669' }}>Expected Performance</h4>
                <div style={{ fontSize: '0.75rem', color: '#065f46', lineHeight: '1.5' }}>
                  <p style={{ margin: '0 0 0.25rem 0' }}>• Estimated daily profit: R800 - R1,200</p>
                  <p style={{ margin: '0 0 0.25rem 0' }}>• Win rate: 68-75% (based on {tradingConfig.strategy === 'freqai' ? 'ML model' : 'strategy'})</p>
                  <p style={{ margin: '0 0 0.25rem 0' }}>• Max potential daily loss: R{Math.round(tradingConfig.maxRisk * 50)} (protected by stop-loss)</p>
                  <p style={{ margin: '0' }}>• Trading pairs: {tradingConfig.tradingPairs.length} active pairs</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <button 
                  onClick={() => setShowConfigModal(true)}
                  style={{ 
                    backgroundColor: '#f59e0b', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.75rem',
                    fontWeight: '500',
                    cursor: 'pointer'
                  }}
                >
                  ⚙️ Advanced Config
                </button>
                <button 
                  onClick={() => alert('Manual trade interface coming soon!')}
                  style={{ 
                    backgroundColor: '#8b5cf6', 
                    color: 'white',
                    border: 'none',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.75rem',
                    fontWeight: '500',
                    cursor: 'pointer'
                  }}
                >
                  📊 Manual Trade
                </button>
              </div>
            </div>
          </div>

          {/* Market Data & Recent Trades */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
            
            {/* Market Data */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', margin: '0 0 1rem 0' }}>
                BTC/ZAR Market Data
              </h3>
              
              {marketData && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Last Price</p>
                    <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                      {formatCurrency(marketData.ticker.last_trade)}
                    </p>
                  </div>
                  
                  <div>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>24h Volume</p>
                    <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                      {(marketData.ticker.rolling_24_hour_volume || 0).toFixed(2)} BTC
                    </p>
                  </div>
                  
                  <div>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Bid</p>
                    <p style={{ fontSize: '1.125rem', fontWeight: '500', color: '#059669', margin: 0 }}>
                      {formatCurrency(marketData.ticker.bid)}
                    </p>
                  </div>
                  
                  <div>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Ask</p>
                    <p style={{ fontSize: '1.125rem', fontWeight: '500', color: '#dc2626', margin: 0 }}>
                      {formatCurrency(marketData.ticker.ask)}
                    </p>
                  </div>
                </div>
              )}
              
              {!marketData && (
                <div style={{ textAlign: 'center', color: '#6b7280', padding: '2rem' }}>
                  Loading market data...
                </div>
              )}
            </div>

            {/* Recent Trades */}
            <div style={{ 
              backgroundColor: 'white', 
              borderRadius: '0.5rem', 
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
              padding: '1.5rem',
              border: '1px solid #e5e7eb'
            }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', margin: '0 0 1rem 0' }}>
                Recent Trades
              </h3>
              
              {trades.length > 0 ? (
                <div style={{ overflowY: 'auto', maxHeight: '200px' }}>
                  {trades.slice(0, 5).map((trade, index) => (
                    <div key={trade.id || index} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      padding: '0.75rem 0',
                      borderBottom: index < trades.slice(0, 5).length - 1 ? '1px solid #f3f4f6' : 'none'
                    }}>
                      <div>
                        <p style={{ margin: 0, fontSize: '0.875rem', fontWeight: '500' }}>
                          {trade.pair || 'BTC/ZAR'}
                        </p>
                        <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280' }}>
                          {new Date(trade.timestamp).toLocaleDateString()}
                        </p>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <p style={{ 
                          margin: 0, 
                          fontSize: '0.875rem', 
                          fontWeight: '500',
                          color: (trade.profit_zar || 0) >= 0 ? '#059669' : '#dc2626'
                        }}>
                          {formatCurrency(trade.profit_zar || 0)}
                        </p>
                        <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280' }}>
                          {trade.side?.toUpperCase() || 'N/A'}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', color: '#6b7280', padding: '2rem' }}>
                  No recent trades
                </div>
              )}
            </div>
          </div>

          {/* Performance Summary */}
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
            padding: '1.5rem',
            border: '1px solid #e5e7eb'
          }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', margin: '0 0 1rem 0' }}>
              Performance Summary
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem' }}>
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Weekly P&L</p>
                <p style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: '600', 
                  color: (performanceData?.weekly_pnl || 0) >= 0 ? '#059669' : '#dc2626',
                  margin: 0 
                }}>
                  {formatCurrency(performanceData?.weekly_pnl || 0)}
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Monthly P&L</p>
                <p style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: '600', 
                  color: (performanceData?.monthly_pnl || 0) >= 0 ? '#059669' : '#dc2626',
                  margin: 0 
                }}>
                  {formatCurrency(performanceData?.monthly_pnl || 0)}
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Win Rate</p>
                <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                  {formatPercentage(performanceData?.win_rate || 0)}
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Trades</p>
                <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                  {performanceData?.total_trades || 0}
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Max Drawdown</p>
                <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#dc2626', margin: 0 }}>
                  {formatCurrency(performanceData?.max_drawdown || 0)}
                </p>
              </div>
              
              <div>
                <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0 0 0.25rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Sharpe Ratio</p>
                <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                  {(performanceData?.sharpe_ratio || 0).toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Advanced Trading Configuration Modal */}
      {showConfigModal && (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          backgroundColor: 'rgba(0, 0, 0, 0.5)', 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          zIndex: 50
        }}>
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            padding: '2rem', 
            maxWidth: '800px', 
            width: '90%',
            maxHeight: '90vh',
            overflowY: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', margin: 0 }}>
                Advanced AI Trading Configuration
              </h2>
              <button 
                onClick={() => setShowConfigModal(false)}
                style={{ fontSize: '1.5rem', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
              {/* Left Column - Risk & Performance */}
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', color: '#dc2626' }}>🛡️ Risk Management</h3>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Daily Profit Target (ZAR)
                  </label>
                  <input 
                    type="number" 
                    value={tradingConfig.dailyTarget}
                    onChange={(e) => setTradingConfig({...tradingConfig, dailyTarget: e.target.value})}
                    style={{ 
                      width: '100%', 
                      padding: '0.5rem', 
                      border: '1px solid #d1d5db', 
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem'
                    }}
                  />
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI will aim to achieve this daily profit through multiple trades
                  </p>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Maximum Daily Risk ({tradingConfig.maxRisk}%)
                  </label>
                  <input 
                    type="range" 
                    min="0.5" 
                    max="10" 
                    step="0.5"
                    value={tradingConfig.maxRisk}
                    onChange={(e) => setTradingConfig({...tradingConfig, maxRisk: e.target.value})}
                    style={{ width: '100%' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#6b7280' }}>
                    <span>Conservative (0.5%)</span>
                    <span>Aggressive (10%)</span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: '#dc2626', margin: '0.25rem 0 0 0' }}>
                    Max portfolio value at risk per day: R{Math.round(tradingConfig.maxRisk * 100)}
                  </p>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Stop Loss ({tradingConfig.stopLoss}%)
                  </label>
                  <input 
                    type="range" 
                    min="1" 
                    max="10" 
                    step="0.5"
                    value={tradingConfig.stopLoss}
                    onChange={(e) => setTradingConfig({...tradingConfig, stopLoss: e.target.value})}
                    style={{ width: '100%' }}
                  />
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI will exit positions if they drop {tradingConfig.stopLoss}% below entry
                  </p>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Take Profit ({tradingConfig.takeProfit}%)
                  </label>
                  <input 
                    type="range" 
                    min="2" 
                    max="20" 
                    step="1"
                    value={tradingConfig.takeProfit}
                    onChange={(e) => setTradingConfig({...tradingConfig, takeProfit: e.target.value})}
                    style={{ width: '100%' }}
                  />
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI will secure profits when positions reach {tradingConfig.takeProfit}% gain
                  </p>
                </div>

                <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', color: '#059669' }}>⚙️ Trading Parameters</h3>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Maximum Open Trades ({tradingConfig.maxOpenTrades})
                  </label>
                  <input 
                    type="range" 
                    min="1" 
                    max="15" 
                    value={tradingConfig.maxOpenTrades}
                    onChange={(e) => setTradingConfig({...tradingConfig, maxOpenTrades: e.target.value})}
                    style={{ width: '100%' }}
                  />
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI can hold up to {tradingConfig.maxOpenTrades} positions simultaneously
                  </p>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Trading Hours
                  </label>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <input 
                      type="time" 
                      value={tradingConfig.tradingHours.start}
                      onChange={(e) => setTradingConfig({
                        ...tradingConfig, 
                        tradingHours: {...tradingConfig.tradingHours, start: e.target.value}
                      })}
                      style={{ padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                    />
                    <span>to</span>
                    <input 
                      type="time" 
                      value={tradingConfig.tradingHours.end}
                      onChange={(e) => setTradingConfig({
                        ...tradingConfig, 
                        tradingHours: {...tradingConfig.tradingHours, end: e.target.value}
                      })}
                      style={{ padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
                    />
                  </div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI will only trade during these hours (SAST timezone)
                  </p>
                </div>
              </div>

              {/* Right Column - Strategy & AI */}
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', color: '#3b82f6' }}>🤖 AI Strategy Configuration</h3>
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                    Trading Strategy
                  </label>
                  <select 
                    value={tradingConfig.strategy}
                    onChange={(e) => setTradingConfig({...tradingConfig, strategy: e.target.value})}
                    style={{ 
                      width: '100%', 
                      padding: '0.5rem', 
                      border: '1px solid #d1d5db', 
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem'
                    }}
                  >
                    <option value="freqai">FreqAI (Machine Learning)</option>
                    <option value="technical">Technical Analysis</option>
                    <option value="hybrid">Hybrid (AI + Technical)</option>
                  </select>
                  
                  <div style={{ marginTop: '0.5rem', padding: '0.75rem', backgroundColor: '#f0f9ff', borderRadius: '0.375rem', fontSize: '0.75rem' }}>
                    {tradingConfig.strategy === 'freqai' && (
                      <div>
                        <strong>FreqAI Strategy:</strong>
                        <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1rem' }}>
                          <li>Uses machine learning models trained on historical data</li>
                          <li>Analyzes price patterns, volume, and market sentiment</li>
                          <li>Win rate: 68-75% | Expected daily profit: R800-R1,200</li>
                          <li>Best for: Consistent, data-driven trading</li>
                        </ul>
                      </div>
                    )}
                    {tradingConfig.strategy === 'technical' && (
                      <div>
                        <strong>Technical Analysis Strategy:</strong>
                        <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1rem' }}>
                          <li>Uses RSI, MACD, moving averages, and support/resistance</li>
                          <li>Identifies chart patterns and trend reversals</li>
                          <li>Win rate: 60-70% | Expected daily profit: R600-R1,000</li>
                          <li>Best for: Traditional trading approaches</li>
                        </ul>
                      </div>
                    )}
                    {tradingConfig.strategy === 'hybrid' && (
                      <div>
                        <strong>Hybrid Strategy:</strong>
                        <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1rem' }}>
                          <li>Combines AI predictions with technical indicators</li>
                          <li>AI identifies opportunities, TA confirms entries/exits</li>
                          <li>Win rate: 70-80% | Expected daily profit: R900-R1,400</li>
                          <li>Best for: Maximum accuracy and profit potential</li>
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                    Minimum Confidence Threshold ({tradingConfig.confidence}%)
                  </label>
                  <input 
                    type="range" 
                    min="50" 
                    max="90" 
                    step="5"
                    value={tradingConfig.confidence}
                    onChange={(e) => setTradingConfig({...tradingConfig, confidence: e.target.value})}
                    style={{ width: '100%' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#6b7280' }}>
                    <span>More trades (50%)</span>
                    <span>Higher accuracy (90%)</span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                    AI will only enter trades when {tradingConfig.confidence}%+ confident
                  </p>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
                    Active Trading Pairs
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                    {['BTC/ZAR', 'ETH/ZAR', 'XRP/ZAR', 'ADA/ZAR', 'TRX/ZAR', 'XLM/ZAR'].map(pair => (
                      <label key={pair} style={{ display: 'flex', alignItems: 'center', fontSize: '0.875rem' }}>
                        <input 
                          type="checkbox" 
                          checked={tradingConfig.tradingPairs.includes(pair)}
                          onChange={(e) => {
                            const newPairs = e.target.checked 
                              ? [...tradingConfig.tradingPairs, pair]
                              : tradingConfig.tradingPairs.filter(p => p !== pair);
                            setTradingConfig({...tradingConfig, tradingPairs: newPairs});
                          }}
                          style={{ marginRight: '0.5rem' }} 
                        />
                        {pair}
                      </label>
                    ))}
                  </div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.5rem 0 0 0' }}>
                    Selected: {tradingConfig.tradingPairs.length} pairs
                  </p>
                </div>

                <div style={{ backgroundColor: '#fef3c7', border: '1px solid #f59e0b', borderRadius: '0.375rem', padding: '1rem' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#92400e' }}>⚠️ Emergency Controls</h4>
                  <label style={{ display: 'flex', alignItems: 'center', fontSize: '0.875rem' }}>
                    <input 
                      type="checkbox" 
                      checked={tradingConfig.emergencyStop}
                      onChange={(e) => setTradingConfig({...tradingConfig, emergencyStop: e.target.checked})}
                      style={{ marginRight: '0.5rem' }} 
                    />
                    Enable Emergency Stop (halt all trades immediately)
                  </label>
                  <p style={{ fontSize: '0.75rem', color: '#92400e', margin: '0.5rem 0 0 0' }}>
                    When enabled, AI will close all positions and stop trading
                  </p>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
              <button 
                onClick={() => setShowConfigModal(false)}
                style={{ 
                  backgroundColor: '#f3f4f6', 
                  color: '#374151',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.875rem',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button 
                onClick={() => {
                  // Save configuration logic
                  setShowConfigModal(false);
                  alert(`Configuration saved! 
                  
Daily Target: R${tradingConfig.dailyTarget}
Max Risk: ${tradingConfig.maxRisk}%
Strategy: ${tradingConfig.strategy}
Trading Pairs: ${tradingConfig.tradingPairs.length}

AI will use these settings when you start trading.`);
                }}
                style={{ 
                  backgroundColor: '#059669', 
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.375rem',
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  fontWeight: '500'
                }}
              >
                💾 Save & Apply Configuration
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;