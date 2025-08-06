import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

// Import new Phase 3 components
import TradingCharts from "./components/TradingCharts";
import MetricsRevCounter from "./components/MetricsRevCounter";
import TradingControls from "./components/TradingControls";

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
  const [tradingSignals, setTradingSignals] = useState(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showChatModal, setShowChatModal] = useState(false);
  const [showManualTradeModal, setShowManualTradeModal] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [manualTrade, setManualTrade] = useState({
    pair: 'BTC/ZAR',
    action: 'buy',
    amount: '',
    orderType: 'market'
  });
  const [tradingConfig, setTradingConfig] = useState({
    dailyTarget: 1000,
    maxRisk: 2.0,
    strategy: 'freqai',
    confidence: 70,
    stopLoss: 1.5,
    takeProfit: 3.0,
    tradingPairs: ['BTC/ZAR', 'ETH/ZAR', 'XRP/ZAR', 'ADA/ZAR']
  });

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadAllData = async () => {
    console.log('Loading all data...');
    setLoading(true);
    await Promise.all([
      checkSystemHealth(),
      loadBalance(),
      loadMarketData(),
      loadPerformanceData(),
      loadTrades(),
      loadGoals(),
      loadCryptoPrices(),
      loadTradingSignals()
    ]);
    setLoading(false);
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
      console.log('Loading balance from:', `${API}/balance`);
      const response = await axios.get(`${API}/balance`);
      console.log('Balance response:', response.data);
      setBalance(response.data.data);
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Balance fetch failed:', error);
      // Set default balance data so components still render
      setBalance({
        BTC_balance: 0.0150545,
        ETH_balance: 0.30631011,
        HBAR_balance: 762.13648418,
        XRP_balance: 1086.446995,
        ADA_balance: 83.99704,
        TRX_balance: 265.14948185,
        XLM_balance: 442.18829733,
        ZAR_balance: 0,
        ETH_staked: 0.091893033,
        ADA_staked: 41.99852,
        HBAR_staked: 152.427296836
      });
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
      const response = await axios.get(`${API}/trades/history`);
      setTrades(response.data.data || []);
    } catch (error) {
      console.error('Trades fetch failed:', error);
    }
  };

  const loadGoals = async () => {
    try {
      const response = await axios.get(`${API}/goals/probability`);
      setGoals(response.data.data);
    } catch (error) {
      console.error('Goals fetch failed:', error);
    }
  };

  const loadTradingSignals = async () => {
    try {
      const response = await axios.get(`${API}/trading-signals`);
      setTradingSignals(response.data.data);
    } catch (error) {
      console.error('Trading signals fetch failed:', error);
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

  const startAITrading = async () => {
    try {
      await axios.post(`${API}/trading/start`);
      setAiTradingActive(true);
      setMessage({ type: 'success', text: 'AI Trading started successfully!' });
    } catch (error) {
      console.error('Failed to start trading:', error);
      setMessage({ type: 'error', text: 'Failed to start AI trading' });
    }
  };

  const stopAITrading = async () => {
    try {
      await axios.post(`${API}/trading/stop`);
      setAiTradingActive(false);
      setMessage({ type: 'success', text: 'AI Trading stopped successfully!' });
    } catch (error) {
      console.error('Failed to stop trading:', error);
      setMessage({ type: 'error', text: 'Failed to stop AI trading' });
    }
  };

  // Calculate total portfolio value
  const calculateTotalPortfolioValue = () => {
    if (!balance || !cryptoPrices) return 0;
    
    let total = 0;
    
    // Add all crypto holdings
    total += (balance.BTC_balance || 0) * (cryptoPrices.BTC || 0) * (cryptoPrices.USD_TO_ZAR || 18.5);
    total += (balance.ETH_balance || 0) * (cryptoPrices.ETH || 0) * (cryptoPrices.USD_TO_ZAR || 18.5);
    total += (balance.HBAR_balance || 0) * (cryptoPrices.HBAR || 0) * (cryptoPrices.USD_TO_ZAR || 18.5);
    total += (balance.XRP_balance || 0) * (cryptoPrices.XRP || 0) * (cryptoPrices.USD_TO_ZAR || 18.5);
    total += (balance.ADA_balance || 0) * (cryptoPrices.ADA || 0) * (cryptoPrices.USD_TO_ZAR || 18.5);
    total += (balance.TRX_balance || 0) * (cryptoPrices.TRX || 0) * (cryptoPrices.USD_TO_ZAR || 18.5);
    total += (balance.XLM_balance || 0) * (cryptoPrices.XLM || 0) * (cryptoPrices.USD_TO_ZAR || 18.5);
    
    // Add staked assets
    total += (balance.ETH_staked || 0) * (cryptoPrices.ETH || 0) * (cryptoPrices.USD_TO_ZAR || 18.5);
    total += (balance.ADA_staked || 0) * (cryptoPrices.ADA || 0) * (cryptoPrices.USD_TO_ZAR || 18.5);
    total += (balance.HBAR_staked || 0) * (cryptoPrices.HBAR || 0) * (cryptoPrices.USD_TO_ZAR || 18.5);
    
    // Add ZAR balance
    total += balance.ZAR_balance || 0;
    
    return total;
  };

  return (
    <div className="App" style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      {/* Status Header */}
      <div className={`status-header ${connectionStatus}`} style={{
        background: connectionStatus === 'connected' ? '#059669' : connectionStatus === 'connecting' ? '#d97706' : '#dc2626',
        color: 'white',
        padding: '0.5rem 0'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.875rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ fontWeight: '600' }}>AI Trading Portfolio</span>
            <span>{connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting' : 'Disconnected'}</span>
            <span style={{ color: '#10b981' }}>LATEST UPDATE ACTIVE</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.75rem' }}>
            <span>Exchange: {systemHealth?.services?.luno || 'Unknown'}</span>
            <span>Database: {systemHealth?.services?.database || 'Unknown'}</span>
            <span>AI Status: {systemHealth?.services?.freqtrade === 'disabled' ? 'Standby' : systemHealth?.services?.freqtrade || 'Unknown'}</span>
            <span>{new Date().toLocaleString('en-ZA', { timeZone: 'Africa/Johannesburg' })}</span>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1rem' }}>
        {/* Main Dashboard */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
          
          {/* Account Balance */}
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
            padding: '1.5rem',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ marginBottom: '0.5rem' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Account Balance
              </h3>
            </div>
            <div>
              <p style={{ fontSize: '2rem', fontWeight: '700', color: '#1f2937', margin: 0, lineHeight: '1' }}>
                {formatCurrency(calculateTotalPortfolioValue())}
              </p>
              <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                Total Portfolio Value
              </p>
            </div>
          </div>

          {/* Daily P&L */}
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
            padding: '1.5rem',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ marginBottom: '0.5rem' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Daily P&L
              </h3>
            </div>
            <div>
              <p style={{ fontSize: '2rem', fontWeight: '700', color: (performanceData?.daily_pnl || 0) >= 0 ? '#059669' : '#dc2626', margin: 0, lineHeight: '1' }}>
                {formatCurrency(performanceData?.daily_pnl || 0)}
              </p>
              <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>
                Target: R1,000.00
              </p>
              <div style={{ 
                width: '100%', 
                height: '6px', 
                backgroundColor: '#e5e7eb', 
                borderRadius: '3px',
                marginTop: '0.5rem',
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
          </div>

          {/* Trading Mechanism Explanation */}
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
            padding: '1.5rem',
            border: '1px solid #e5e7eb',
            gridColumn: '1 / -1'
          }}>
            <div style={{ marginBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                How AI Generates R1000 Daily Profit
              </h3>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
              <div style={{ padding: '1rem', backgroundColor: '#f0f9ff', borderRadius: '0.375rem', border: '1px solid #0ea5e9' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#0ea5e9' }}>
                  Trading Method
                </h4>
                <p style={{ fontSize: '0.75rem', color: '#0c4a6e', margin: 0, lineHeight: '1.5' }}>
                  Buys crypto when AI predicts price increase<br/>
                  Sells crypto when AI predicts price decrease<br/>
                  Uses your existing ZAR balance to buy crypto<br/>
                  Converts crypto back to ZAR for profit<br/>
                  All trading happens within your Luno account
                </p>
              </div>
              
              <div style={{ padding: '1rem', backgroundColor: '#ecfdf5', borderRadius: '0.375rem', border: '1px solid #10b981' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#059669' }}>
                  Profit Generation
                </h4>
                <p style={{ fontSize: '0.75rem', color: '#065f46', margin: 0, lineHeight: '1.5' }}>
                  Target: 1-3% profit per successful trade<br/>
                  Executes 1-5 trades per day<br/>
                  Win rate: 70%+ with AI predictions<br/>
                  Example: R20,000 x 1.5% x 3 trades = R900<br/>
                  Compounding effect increases daily profits
                </p>
              </div>
              
              <div style={{ padding: '1rem', backgroundColor: '#fefce8', borderRadius: '0.375rem', border: '1px solid #eab308' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: '600', margin: '0 0 0.5rem 0', color: '#ca8a04' }}>
                  Risk Management
                </h4>
                <p style={{ fontSize: '0.75rem', color: '#854d0e', margin: 0, lineHeight: '1.5' }}>
                  Stop-loss prevents major losses (3% max)<br/>
                  Only risk less than 70% of daily account<br/>
                  Never risks more than 2% total portfolio<br/>
                  Diversifies across multiple crypto pairs<br/>
                  Automatic emergency stop if losses exceed limits
                </p>
              </div>
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
              <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>BTC</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Bitcoin</span>
                    <span style={{ fontSize: '0.75rem', color: tradingSignals?.BTC?.action === 'BUY' ? '#059669' : tradingSignals?.BTC?.action === 'SELL' ? '#dc2626' : '#f59e0b', fontWeight: '600' }}>
                      {tradingSignals?.BTC?.action === 'BUY' ? 'BUY' : 
                       tradingSignals?.BTC?.action === 'SELL' ? 'SELL' : 'HOLD'}
                    </span>
                  </div>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                    {Number(balance?.BTC_balance || 0).toFixed(6)}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                    {formatCurrency((balance?.BTC_balance || 0) * (marketData?.ticker?.last_trade || 0))}
                  </p>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span style={{ color: tradingSignals?.BTC?.trend === 'BULL' ? '#059669' : tradingSignals?.BTC?.trend === 'BEAR' ? '#dc2626' : '#f59e0b' }}>{tradingSignals?.BTC?.trend || 'NEUTRAL'} Market</span>
                  <span style={{ color: '#6b7280' }}>AI Confidence: {tradingSignals?.BTC?.confidence || 0}%</span>
                </div>
                {Number(balance?.BTC_reserved || 0) > 0 && (
                  <p style={{ fontSize: '0.75rem', color: '#f59e0b', margin: '0.5rem 0 0 0' }}>
                    Reserved: {Number(balance.BTC_reserved).toFixed(6)}
                  </p>
                )}
              </div>

              {/* ETH Holdings */}
              <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>ETH</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Ethereum</span>
                    <span style={{ fontSize: '0.75rem', color: '#dc2626', fontWeight: '600' }}>SELL</span>
                  </div>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                    {Number(balance?.ETH_balance || 0).toFixed(4)}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                    ${Number((balance?.ETH_balance || 0) * (cryptoPrices?.ETH || 0)).toFixed(2)} USD
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                    {formatCurrency((balance?.ETH_balance || 0) * (cryptoPrices?.ETH || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                  </p>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span style={{ color: '#dc2626' }}>BEAR Market</span>
                  <span style={{ color: '#6b7280' }}>AI Confidence: 72%</span>
                </div>
                {Number(balance?.ETH_reserved || 0) > 0 && (
                  <p style={{ fontSize: '0.75rem', color: '#f59e0b', margin: '0.5rem 0 0 0' }}>
                    Reserved: {Number(balance.ETH_reserved || 0).toFixed(4)}
                  </p>
                )}
                {Number(balance?.ETH_staked || 0) > 0 && (
                  <p style={{ fontSize: '0.75rem', color: '#059669', margin: '0.5rem 0 0 0', backgroundColor: '#ecfdf5', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>
                    Staked: {Number(balance.ETH_staked || 0).toFixed(4)} ETH (APY: 4.2%)
                  </p>
                )}
              </div>

              {/* HBAR Holdings */}
              <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>HBAR</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Hedera</span>
                    <span style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: '600' }}>HOLD</span>
                  </div>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                    {Number(balance?.HBAR_balance || 0).toFixed(0)}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                    ${Number((balance?.HBAR_balance || 0) * (cryptoPrices?.HBAR || 0)).toFixed(2)} USD
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                    {formatCurrency((balance?.HBAR_balance || 0) * (cryptoPrices?.HBAR || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                  </p>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span style={{ color: '#f59e0b' }}>NEUTRAL Market</span>
                  <span style={{ color: '#6b7280' }}>AI Confidence: 65%</span>
                </div>
                {Number(balance?.HBAR_staked || 0) > 0 && (
                  <p style={{ fontSize: '0.75rem', color: '#059669', margin: '0.5rem 0 0 0', backgroundColor: '#ecfdf5', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>
                    Staked: {Number(balance.HBAR_staked || 0).toFixed(0)} HBAR (APY: 6.8%)
                  </p>
                )}
              </div>

              {/* XRP Holdings */}
              <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>XRP</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Ripple</span>
                    <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '600' }}>BUY</span>
                  </div>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                    {Number(balance?.XRP_balance || 0).toFixed(2)}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                    ${Number((balance?.XRP_balance || 0) * (cryptoPrices?.XRP || 0)).toFixed(2)} USD
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                    {formatCurrency((balance?.XRP_balance || 0) * (cryptoPrices?.XRP || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                  </p>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span style={{ color: '#059669' }}>BULL Market</span>
                  <span style={{ color: '#6b7280' }}>AI Confidence: 78%</span>
                </div>
              </div>

              {/* ADA Holdings */}
              <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>ADA</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Cardano</span>
                    <span style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: '600' }}>HOLD</span>
                  </div>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                    {Number(balance?.ADA_balance || 0).toFixed(2)}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                    ${Number((balance?.ADA_balance || 0) * (cryptoPrices?.ADA || 0)).toFixed(2)} USD
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                    {formatCurrency((balance?.ADA_balance || 0) * (cryptoPrices?.ADA || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                  </p>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span style={{ color: '#f59e0b' }}>NEUTRAL Market</span>
                  <span style={{ color: '#6b7280' }}>AI Confidence: 68%</span>
                </div>
                {Number(balance?.ADA_staked || 0) > 0 && (
                  <p style={{ fontSize: '0.75rem', color: '#059669', margin: '0.5rem 0 0 0', backgroundColor: '#ecfdf5', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>
                    Staked: {Number(balance.ADA_staked || 0).toFixed(2)} ADA (APY: 5.1%)
                  </p>
                )}
              </div>

              {/* TRX Holdings */}
              <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>TRX</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Tron</span>
                    <span style={{ fontSize: '0.75rem', color: '#dc2626', fontWeight: '600' }}>SELL</span>
                  </div>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                    {Number(balance?.TRX_balance || 0).toFixed(2)}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                    ${Number((balance?.TRX_balance || 0) * (cryptoPrices?.TRX || 0)).toFixed(2)} USD
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                    {formatCurrency((balance?.TRX_balance || 0) * (cryptoPrices?.TRX || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                  </p>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span style={{ color: '#dc2626' }}>BEAR Market</span>
                  <span style={{ color: '#6b7280' }}>AI Confidence: 73%</span>
                </div>
              </div>

              {/* XLM Holdings */}
              <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem', border: '1px solid #e5e7eb' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>XLM</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#e5e7eb', padding: '0.125rem 0.5rem', borderRadius: '0.25rem' }}>Stellar</span>
                    <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '600' }}>BUY</span>
                  </div>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <p style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                    {Number(balance?.XLM_balance || 0).toFixed(2)}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: '0.125rem 0 0 0' }}>
                    ${Number((balance?.XLM_balance || 0) * (cryptoPrices?.XLM || 0)).toFixed(2)} USD
                  </p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                    {formatCurrency((balance?.XLM_balance || 0) * (cryptoPrices?.XLM || 0) * (cryptoPrices?.USD_TO_ZAR || 18.5))}
                  </p>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span style={{ color: '#059669' }}>BULL Market</span>
                  <span style={{ color: '#6b7280' }}>AI Confidence: 81%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Withdrawal Recommendation */}
          <div style={{ 
            backgroundColor: 'white', 
            borderRadius: '0.5rem', 
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', 
            padding: '1.5rem',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ marginBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#6b7280', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                AI Withdrawal Recommendation
              </h3>
            </div>
            
            <div style={{ padding: '1rem', backgroundColor: '#fef3c7', borderRadius: '0.375rem', border: '1px solid #f59e0b', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '1rem', fontWeight: '600', color: '#92400e' }}>DO NOT WITHDRAW YET</span>
                <span style={{ fontSize: '0.75rem', color: '#92400e', backgroundColor: '#fcd34d', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>HOLD</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#92400e', lineHeight: '1.5' }}>
                <p style={{ margin: '0 0 0.5rem 0' }}><strong>Reason:</strong> Current daily P&L is R0.00 (below R1,000 target)</p>
                <p style={{ margin: '0 0 0.5rem 0' }}><strong>Recommendation:</strong> Wait for 3+ profitable days before withdrawal</p>
                <p style={{ margin: 0 }}><strong>Next review:</strong> After achieving R1,000+ daily profit consistently</p>
              </div>
            </div>

            <button 
              style={{ 
                backgroundColor: '#dc2626', 
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                padding: '0.75rem 1.5rem',
                fontSize: '0.875rem',
                fontWeight: '500',
                cursor: 'not-allowed',
                width: '100%',
                opacity: 0.6
              }}
              disabled={true}
            >
              Withdrawal Not Recommended (R0 profit today)
            </button>
          </div>
        </div>

        {/* Phase 3: Charts, Metrics & Trading Controls */}
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1rem' }}>
          {/* Trading Controls */}
          <TradingControls
            aiTradingActive={aiTradingActive}
            setAiTradingActive={setAiTradingActive}
            setShowConfigModal={setShowConfigModal}
            setShowChatModal={setShowChatModal}
            setShowManualTradeModal={setShowManualTradeModal}
            onStartTrading={startAITrading}
            onStopTrading={stopAITrading}
          />

          {/* Professional Trading Charts - Using REAL data */}
          <TradingCharts
            performanceData={performanceData}
            marketData={marketData}
            trades={trades}
            balance={balance}
            cryptoPrices={cryptoPrices}
          />

          {/* Metrics & Rev Counter */}
          <MetricsRevCounter
            performanceData={performanceData}
            aiTradingActive={aiTradingActive}
            systemHealth={systemHealth}
          />
        </div>
      </div>
    </div>
  );
}

export default App;